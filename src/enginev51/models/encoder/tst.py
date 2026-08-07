"""PatchTST-small encoder for the M4 event-stream model (arch = ``tst``).

The ``fine`` stream [B, 1080, 22] is right-padded to 1088 (= 68 x 16) and cut into
68 non-overlapping patches of 16 steps. Each patch (16 x 22 = 352 values, channel-
mixing) is linearly embedded to ``d_model`` = 128; a learned CLS token is prepended
and learned positional embeddings are added (69 positions). A 4-layer, 8-head
TransformerEncoder processes the sequence and the CLS output is the fine
representation (128-d).

The ``sess`` and ``static`` streams reuse the SAME encoders as the TCN arch
(``SmallTCN`` -> 64-d, ``StaticMLP`` -> 64-d); the three are fused through the shared
``TrunkFuser`` to the common ``trunk_dim`` (256), so both archs expose one trunk
interface for ``heads.EncoderHeads``.

``dim_feedforward`` (default 2048) is the free knob sized to land total params in the
registered 2-4M band while keeping d_model/layers/heads frozen at 128/4/8.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

from enginev51.models.encoder.tcn import (
    DEFAULT_STATIC_DIM,
    FINE_DIM,
    SESS_DIM,
    TRUNK_DIM,
    SmallTCN,
    StaticMLP,
    TrunkFuser,
)

PATCH = 16
N_PATCHES = 68                     # ceil(1080 / 16); fine is right-padded to 1088
PADDED_LEN = PATCH * N_PATCHES     # 1088
D_MODEL = 128
N_LAYERS = 4
N_HEADS = 8


class PatchTSTFine(nn.Module):
    """Channel-mixing PatchTST over the fine stream -> ``out_dim`` (CLS pooling)."""

    def __init__(self, in_dim: int = FINE_DIM, d_model: int = D_MODEL, n_layers: int = N_LAYERS,
                 n_heads: int = N_HEADS, dim_feedforward: int = 2048, out_dim: int = 128) -> None:
        super().__init__()
        self.patch_embed = nn.Linear(PATCH * in_dim, d_model)
        self.cls = nn.Parameter(torch.zeros(1, 1, d_model))
        self.pos = nn.Parameter(torch.zeros(1, N_PATCHES + 1, d_model))
        nn.init.trunc_normal_(self.cls, std=0.02)
        nn.init.trunc_normal_(self.pos, std=0.02)
        layer = nn.TransformerEncoderLayer(
            d_model, n_heads, dim_feedforward=dim_feedforward, dropout=0.0,
            activation="gelu", batch_first=True, norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, n_layers, enable_nested_tensor=False)
        self.proj = nn.Linear(d_model, out_dim)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # x: [B, 1080, 22]
        b, t, c = x.shape
        mask = x[..., -1]
        x = x * mask.unsqueeze(-1)                        # zero padded steps
        if t < PADDED_LEN:
            x = F.pad(x, (0, 0, 0, PADDED_LEN - t))       # right-pad the time axis
        patches = x.reshape(b, N_PATCHES, PATCH * c)      # [B, 68, 352]
        tok = self.patch_embed(patches)                   # [B, 68, d_model]
        cls = self.cls.expand(b, -1, -1)
        seq = torch.cat([cls, tok], dim=1) + self.pos     # [B, 69, d_model]
        out = self.encoder(seq)
        return self.act(self.proj(out[:, 0]))             # CLS -> out_dim


class TSTEncoder(nn.Module):
    """Full PatchTST arch: fine (transformer) + sess + static -> trunk vector."""

    def __init__(self, static_dim: int = DEFAULT_STATIC_DIM, trunk_dim: int = TRUNK_DIM,
                 dim_feedforward: int = 2048, sess_channels: int = 64) -> None:
        super().__init__()
        self.trunk_dim = trunk_dim
        self.fine = PatchTSTFine(FINE_DIM, dim_feedforward=dim_feedforward, out_dim=128)
        self.sess = SmallTCN(SESS_DIM, sess_channels, out_dim=64)
        self.static = StaticMLP(static_dim, 128, 64)
        self.fuser = TrunkFuser(128, 64, 64, trunk_dim)

    def forward(self, batch: dict) -> torch.Tensor:
        f = self.fine(batch["fine"])
        s = self.sess(batch["sess"])
        st = self.static(batch["static"])
        return self.fuser(f, s, st)
