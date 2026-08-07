"""Dilated causal TCN encoder for the M4 event-stream model (arch = ``tcn``).

Three input streams (see ``dataset.EncoderDataset`` item schema) are encoded and
fused into a single trunk vector consumed by ``heads.EncoderHeads``:

* ``fine``   [B, 1080, 22] -> deep dilated causal TCN (kernel 5, 128 channels,
  dilations 1..256 => receptive field 2045 >= 1080), masked mean+last pooling -> 256-d.
* ``sess``   [B, 390, 12]  -> a small 4-layer causal TCN (``SmallTCN``) -> 64-d.
  ``SmallTCN`` is factored out here and REUSED by ``tst.py`` (same sess encoder for
  both archs, per the registered spec).
* ``static`` [B, 41]       -> a 2-layer MLP -> 64-d.

The three are concatenated (256+64+64 = 384) and projected to a common
``trunk_dim`` (default 256) so both archs expose an identical trunk interface.

Causality: every temporal conv left-pads by ``(kernel-1)*dilation`` and the pad is
sliced off the RIGHT, so output step t sees only inputs <= t (no leakage). The last
tensor channel of each stream is the validity mask (used for masked pooling and to
zero padded steps before convolving).
"""

from __future__ import annotations

import torch
from torch import nn
from torch.nn.utils.parametrizations import weight_norm

FINE_DIM = 22
SESS_DIM = 12
DEFAULT_STATIC_DIM = 41
TRUNK_DIM = 256


class CausalConv1d(nn.Module):
    """Weight-normed dilated causal 1d conv: pads left, trims the right overhang."""

    def __init__(self, in_ch: int, out_ch: int, kernel: int, dilation: int) -> None:
        super().__init__()
        self.pad = (kernel - 1) * dilation
        self.conv = weight_norm(
            nn.Conv1d(in_ch, out_ch, kernel, padding=self.pad, dilation=dilation)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # x: [B, C, T]
        y = self.conv(x)
        return y[..., : -self.pad] if self.pad else y


class TCNBlock(nn.Module):
    """Residual dilated causal block: (CausalConv -> GELU) x2 + 1x1 residual."""

    def __init__(self, in_ch: int, out_ch: int, kernel: int, dilation: int) -> None:
        super().__init__()
        self.conv1 = CausalConv1d(in_ch, out_ch, kernel, dilation)
        self.conv2 = CausalConv1d(out_ch, out_ch, kernel, dilation)
        self.act = nn.GELU()
        self.down = nn.Conv1d(in_ch, out_ch, 1) if in_ch != out_ch else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.act(self.conv1(x))
        y = self.act(self.conv2(y))
        return self.act(y + self.down(x))


def _masked_mean_last(feat: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """feat [B, C, T], mask [B, T] (1=valid) -> [B, 2C] (masked mean ++ last valid)."""
    m = mask.unsqueeze(1)                                  # [B,1,T]
    denom = m.sum(dim=-1).clamp_min(1.0)                  # [B,1]
    mean = (feat * m).sum(dim=-1) / denom                 # [B,C]
    # last VALID step per row (fall back to the final step if a row is all-pad).
    idx = torch.arange(mask.shape[1], device=mask.device)
    last_idx = torch.where(mask > 0, idx, torch.zeros_like(idx)).max(dim=1).values  # [B]
    last = feat[torch.arange(feat.shape[0], device=feat.device), :, last_idx]       # [B,C]
    return torch.cat([mean, last], dim=-1)


class SmallTCN(nn.Module):
    """4-layer causal TCN over a [B, T, in_dim] stream -> ``out_dim`` vector.

    Shared session encoder (imported by both ``tcn`` and ``tst`` archs). The last
    input channel is treated as the validity mask for masked pooling.
    """

    def __init__(self, in_dim: int = SESS_DIM, channels: int = 64, out_dim: int = 64,
                 kernel: int = 5) -> None:
        super().__init__()
        dils = [1, 2, 4, 8]
        chs = [in_dim] + [channels] * len(dils)
        self.blocks = nn.ModuleList(
            TCNBlock(chs[i], chs[i + 1], kernel, dils[i]) for i in range(len(dils))
        )
        self.proj = nn.Linear(2 * channels, out_dim)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # x: [B, T, in_dim]
        mask = x[..., -1]                                 # [B, T]
        h = (x * mask.unsqueeze(-1)).transpose(1, 2)      # [B, in_dim, T], pad zeroed
        for blk in self.blocks:
            h = blk(h)
        pooled = _masked_mean_last(h, mask)               # [B, 2*channels]
        return self.act(self.proj(pooled))


class FineTCN(nn.Module):
    """Deep dilated causal TCN over ``fine`` -> ``out_dim`` (default 256) trunk.

    Dilations 1,2,4,...,256 (9 blocks, kernel 5) => receptive field 2045 >= 1080.
    """

    def __init__(self, in_dim: int = FINE_DIM, channels: int = 128, out_dim: int = TRUNK_DIM,
                 kernel: int = 5) -> None:
        super().__init__()
        dils = [1, 2, 4, 8, 16, 32, 64, 128, 256]
        self.receptive_field = 1 + sum(2 * (kernel - 1) * d for d in dils)
        chs = [in_dim] + [channels] * len(dils)
        self.blocks = nn.ModuleList(
            TCNBlock(chs[i], chs[i + 1], kernel, dils[i]) for i in range(len(dils))
        )
        self.proj = nn.Linear(2 * channels, out_dim)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # x: [B, 1080, 22]
        mask = x[..., -1]
        h = (x * mask.unsqueeze(-1)).transpose(1, 2)
        for blk in self.blocks:
            h = blk(h)
        pooled = _masked_mean_last(h, mask)               # [B, 2*channels]
        return self.act(self.proj(pooled))


class StaticMLP(nn.Module):
    def __init__(self, in_dim: int = DEFAULT_STATIC_DIM, hidden: int = 128, out_dim: int = 64) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden), nn.GELU(), nn.Linear(hidden, out_dim), nn.GELU()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TrunkFuser(nn.Module):
    """Concatenate the three stream vectors and project to a common trunk_dim."""

    def __init__(self, fine_dim: int, sess_dim: int, static_dim: int, trunk_dim: int = TRUNK_DIM) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(fine_dim + sess_dim + static_dim, trunk_dim), nn.GELU(),
            nn.Linear(trunk_dim, trunk_dim), nn.GELU(),
        )

    def forward(self, fine: torch.Tensor, sess: torch.Tensor, static: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([fine, sess, static], dim=-1))


class TCNEncoder(nn.Module):
    """Full TCN arch: fine + sess + static -> fused ``trunk_dim`` vector.

    ``forward(batch)`` takes a dict with keys ``fine``/``sess``/``static`` and
    returns the trunk [B, trunk_dim]. ``trunk_dim`` is exposed for the head factory.
    """

    def __init__(self, static_dim: int = DEFAULT_STATIC_DIM, trunk_dim: int = TRUNK_DIM,
                 fine_channels: int = 128, sess_channels: int = 64) -> None:
        super().__init__()
        self.trunk_dim = trunk_dim
        self.fine = FineTCN(FINE_DIM, fine_channels, out_dim=256)
        self.sess = SmallTCN(SESS_DIM, sess_channels, out_dim=64)
        self.static = StaticMLP(static_dim, 128, 64)
        self.fuser = TrunkFuser(256, 64, 64, trunk_dim)

    def forward(self, batch: dict) -> torch.Tensor:
        f = self.fine(batch["fine"])
        s = self.sess(batch["sess"])
        st = self.static(batch["static"])
        return self.fuser(f, s, st)
