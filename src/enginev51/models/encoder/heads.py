"""Multi-task heads + masked losses on the fused encoder trunk (M4).

From a trunk vector [B, trunk_dim] the head bank emits four groups, matching the
registered loss menu:

* H1 — forward quantiles q{10,25,50,75,90} x fwd{30,60,120,close} (20 outputs).
  Monotone in the quantile axis via a cumulative-softplus parametrisation:
  q10 is free, each higher quantile = previous + softplus(offset) >= previous.
* H2 — excursion quantiles q{50,75} x {MFE,MAE}{60,120} (8 outputs). All are
  NON-NEGATIVE magnitudes (softplus base) and monotone (q75 = q50 + softplus).
* H3 — 16 barrier logits (8 up-first ++ 8 dn-first, ``dataset.BARRIER_ALL_LABELS``
  order). BCE with per-label masking of null (window-crosses-close) labels.
* H5 — next-30m realized vol (1 output, softplus -> non-negative). Huber loss.

``head_loss`` applies the frozen weights (1.0 H1, 1.0 H2, 1.0 H3, 0.5 H5) and masks
every term per-element, so a masked (null) label never affects the loss.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

from enginev51.models.encoder import dataset as ds

# ---- ordering constants shared with train.py (label-name -> tensor slot) ----
Q_FWD = [0.10, 0.25, 0.50, 0.75, 0.90]
FWD_TARGET_LABELS = list(ds.FWD_LABELS)          # 30m,60m,120m,close
Q_EXC = [0.50, 0.75]
EXC_TARGET_LABELS = list(ds.EXC_LABELS)          # mfe60,mfe120,mae60,mae120
BARRIER_TARGET_LABELS = list(ds.BARRIER_ALL_LABELS)  # 16 (up8 ++ dn8)
RV_TARGET_LABEL = ds.RV_LABEL

N_FWD = len(FWD_TARGET_LABELS)     # 4
N_EXC = len(EXC_TARGET_LABELS)     # 4
N_BARRIER = len(BARRIER_TARGET_LABELS)  # 16

DEFAULT_WEIGHTS = {"h1": 1.0, "h2": 1.0, "h3": 1.0, "h5": 0.5}


def _cumulative_monotone(raw: torch.Tensor, nonneg_base: bool) -> torch.Tensor:
    """raw [..., Q] -> monotone-increasing [..., Q].

    First column is the base (softplus-clamped >= 0 when ``nonneg_base``), each
    subsequent column adds softplus(offset) so the sequence never decreases.
    """
    base = F.softplus(raw[..., :1]) if nonneg_base else raw[..., :1]
    steps = F.softplus(raw[..., 1:])
    return torch.cat([base, base + torch.cumsum(steps, dim=-1)], dim=-1)


class EncoderHeads(nn.Module):
    """The four-group head bank over a trunk vector."""

    def __init__(self, trunk_dim: int, hidden: int = 128) -> None:
        super().__init__()

        def _head(out: int) -> nn.Module:
            return nn.Sequential(nn.Linear(trunk_dim, hidden), nn.GELU(), nn.Linear(hidden, out))

        self.h1 = _head(N_FWD * len(Q_FWD))     # 20
        self.h2 = _head(N_EXC * len(Q_EXC))     # 8
        self.h3 = _head(N_BARRIER)              # 16 logits
        self.h5 = _head(1)                      # rv

    def forward(self, trunk: torch.Tensor) -> dict[str, torch.Tensor]:
        b = trunk.shape[0]
        fwd = _cumulative_monotone(self.h1(trunk).view(b, N_FWD, len(Q_FWD)), nonneg_base=False)
        exc = _cumulative_monotone(self.h2(trunk).view(b, N_EXC, len(Q_EXC)), nonneg_base=True)
        barrier = self.h3(trunk)                # logits [B,16]
        rv = F.softplus(self.h5(trunk).squeeze(-1))  # [B] >= 0
        return {"fwd": fwd, "exc": exc, "barrier_logits": barrier, "rv": rv}


# ------------------------------------------------------------------ losses
def _pinball_masked(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor,
                    quantiles: list[float]) -> torch.Tensor:
    """pred [B,G,Q], target/mask [B,G]. Mean pinball over valid (mask=1) groups."""
    u = target.unsqueeze(-1) - pred                        # [B,G,Q]
    taus = torch.tensor(quantiles, device=pred.device, dtype=pred.dtype).view(1, 1, -1)
    loss = torch.maximum(taus * u, (taus - 1.0) * u).mean(dim=-1)  # [B,G]
    denom = mask.sum().clamp_min(1.0)
    return (loss * mask).sum() / denom


def _bce_masked(logits: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    bce = F.binary_cross_entropy_with_logits(logits, target, reduction="none")
    denom = mask.sum().clamp_min(1.0)
    return (bce * mask).sum() / denom


def _huber_masked(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor,
                  delta: float = 1.0) -> torch.Tensor:
    h = F.huber_loss(pred, target, reduction="none", delta=delta)
    denom = mask.sum().clamp_min(1.0)
    return (h * mask).sum() / denom


def head_loss(
    outputs: dict[str, torch.Tensor],
    targets: dict[str, torch.Tensor],
    masks: dict[str, torch.Tensor],
    weights: dict[str, float] | None = None,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    """Weighted, per-term-masked multitask loss. Returns (total, per-term dict).

    ``targets``/``masks`` keys: ``fwd`` [B,4], ``exc`` [B,4], ``barrier`` [B,16],
    ``rv`` [B]. Null labels must be masked (mask=0); their target value is ignored.
    """
    w = weights or DEFAULT_WEIGHTS
    h1 = _pinball_masked(outputs["fwd"], targets["fwd"], masks["fwd"], Q_FWD)
    h2 = _pinball_masked(outputs["exc"], targets["exc"], masks["exc"], Q_EXC)
    h3 = _bce_masked(outputs["barrier_logits"], targets["barrier"], masks["barrier"])
    h5 = _huber_masked(outputs["rv"], targets["rv"], masks["rv"])
    total = w["h1"] * h1 + w["h2"] * h2 + w["h3"] * h3 + w["h5"] * h5
    return total, {"h1": h1, "h2": h2, "h3": h3, "h5": h5}
