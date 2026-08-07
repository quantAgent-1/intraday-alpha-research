"""Tests for the M4 encoder models + heads (tcn / tst / heads / dataset dn-labels).

All synthetic and CPU-only; no dependence on the materialized lake.
Covers: end-to-end shapes for both archs, enforced quantile monotonicity, the
non-negative MAE head, masked-loss null invariance, a tiny-TCN overfit smoke, and
the mirrored DOWN-FIRST barrier hand-case in the dataset extension.
"""

from __future__ import annotations

import numpy as np
import torch

from enginev51.models.encoder import dataset as ds
from enginev51.models.encoder import heads as H
from enginev51.models.encoder.heads import EncoderHeads, head_loss
from enginev51.models.encoder.tcn import TCNEncoder
from enginev51.models.encoder.train import split_labels
from enginev51.models.encoder.tst import TSTEncoder

torch.manual_seed(0)


def _fake_batch(b: int, static_dim: int = 41, fine_t: int = 1080, sess_t: int = 390) -> dict:
    fine = torch.randn(b, fine_t, len(ds.FINE_CHANNELS))
    sess = torch.randn(b, sess_t, len(ds.SESS_CHANNELS))
    static = torch.randn(b, static_dim)
    fine[..., -1] = 1.0  # validity mask
    sess[..., -1] = 1.0
    return {"fine": fine, "sess": sess, "static": static}


# ------------------------------------------------------------------ shapes
def test_both_archs_end_to_end_shapes():
    b = 4
    batch = _fake_batch(b)
    for Enc in (TCNEncoder, TSTEncoder):
        enc = Enc(static_dim=41)
        heads = EncoderHeads(enc.trunk_dim)
        trunk = enc(batch)
        assert tuple(trunk.shape) == (b, enc.trunk_dim)
        out = heads(trunk)
        assert tuple(out["fwd"].shape) == (b, H.N_FWD, len(H.Q_FWD))       # [4,4,5]
        assert tuple(out["exc"].shape) == (b, H.N_EXC, len(H.Q_EXC))       # [4,4,2]
        assert tuple(out["barrier_logits"].shape) == (b, H.N_BARRIER)      # [4,16]
        assert tuple(out["rv"].shape) == (b,)


def test_receptive_field_covers_fine_window():
    assert TCNEncoder().fine.receptive_field >= ds.FINE_STEPS


# ------------------------------------------------------------------ monotonicity / non-neg
def test_quantile_monotonicity_and_mae_nonneg():
    heads = EncoderHeads(64)
    trunk = torch.randn(32, 64) * 5.0  # large magnitudes stress the parametrisation
    out = heads(trunk)
    fwd, exc, rv = out["fwd"], out["exc"], out["rv"]
    assert torch.all(fwd[..., 1:] >= fwd[..., :-1] - 1e-6), "fwd quantiles not monotone"
    assert torch.all(exc[..., 1:] >= exc[..., :-1] - 1e-6), "exc quantiles not monotone"
    # every excursion quantile is a non-negative magnitude (MFE and MAE)
    assert torch.all(exc >= -1e-6)
    mae60 = H.EXC_TARGET_LABELS.index("l_mae_60m_z")
    mae120 = H.EXC_TARGET_LABELS.index("l_mae_120m_z")
    assert torch.all(exc[:, mae60, :] >= -1e-6) and torch.all(exc[:, mae120, :] >= -1e-6)
    assert torch.all(rv >= -1e-6), "rv must be non-negative"


# ------------------------------------------------------------------ masked loss invariance
def test_masked_loss_ignores_null_labels():
    b = 8
    torch.manual_seed(1)
    out = {
        "fwd": torch.randn(b, H.N_FWD, len(H.Q_FWD)),
        "exc": torch.nn.functional.softplus(torch.randn(b, H.N_EXC, len(H.Q_EXC))),
        "barrier_logits": torch.randn(b, H.N_BARRIER),
        "rv": torch.nn.functional.softplus(torch.randn(b)),
    }
    targets = {"fwd": torch.randn(b, H.N_FWD), "exc": torch.rand(b, H.N_EXC),
               "barrier": (torch.rand(b, H.N_BARRIER) > 0.5).float(),
               "rv": torch.rand(b)}
    masks = {k: torch.ones_like(v) for k, v in targets.items()}
    # mask out a handful of entries across every head group
    masks["fwd"][0, 0] = 0.0
    masks["exc"][1, 2] = 0.0
    masks["barrier"][2, 5] = 0.0
    masks["rv"][3] = 0.0

    base, _ = head_loss(out, targets, masks)
    # flip the MASKED targets to wildly different values -> loss must not change
    targets["fwd"][0, 0] += 100.0
    targets["exc"][1, 2] += 100.0
    targets["barrier"][2, 5] = 1.0 - targets["barrier"][2, 5]
    targets["rv"][3] += 100.0
    after, _ = head_loss(out, targets, masks)
    assert torch.allclose(base, after, atol=1e-6)

    # sanity: flipping an UNMASKED target DOES change the loss
    targets["rv"][4] += 100.0
    changed, _ = head_loss(out, targets, masks)
    assert not torch.allclose(base, changed, atol=1e-6)


def test_split_labels_masks_nulls():
    labels = torch.full((3, len(ds.LABEL_COLS)), float("nan"))
    labels[0, :] = 0.5  # row 0 fully valid
    targets, masks = split_labels(labels)
    assert masks["barrier"][0].sum() == H.N_BARRIER
    assert masks["barrier"][1].sum() == 0.0
    assert torch.isfinite(targets["fwd"]).all()  # nan -> 0


# ------------------------------------------------------------------ overfit smoke
def test_tiny_tcn_overfits_fixed_batch():
    """A tiny TCN drives the multitask loss down >75% in <=60 full-batch steps on
    200 fixed samples whose labels are a (learnable) function of the inputs."""
    torch.manual_seed(7)
    n = 200
    # short streams + tiny channels keep this fast on CPU
    fine = torch.randn(n, 128, len(ds.FINE_CHANNELS))
    sess = torch.randn(n, 60, len(ds.SESS_CHANNELS))
    static = torch.randn(n, 8)
    fine[..., -1] = 1.0
    sess[..., -1] = 1.0
    batch = {"fine": fine, "sess": sess, "static": static}

    enc = TCNEncoder(static_dim=8, fine_channels=32, sess_channels=16)
    heads = EncoderHeads(enc.trunk_dim, hidden=128)
    params = list(enc.parameters()) + list(heads.parameters())
    opt = torch.optim.Adam(params, lr=1e-2)

    # fixed, learnable labels: deterministic functions of the static vector, all valid
    wf, we = torch.randn(8, H.N_FWD), torch.randn(8, H.N_EXC)
    wb, wr = torch.randn(8, H.N_BARRIER), torch.randn(8)
    targets = {"fwd": static @ wf, "exc": (static @ we).abs(),
               "barrier": ((static @ wb) > 0).float(), "rv": (static @ wr).abs()}
    masks = {k: torch.ones_like(v) for k, v in targets.items()}

    losses = []
    for _ in range(60):
        opt.zero_grad()
        out = heads(enc(batch))
        loss, _ = head_loss(out, targets, masks)
        loss.backward()
        opt.step()
        losses.append(float(loss.detach()))
    assert losses[-1] < 0.25 * losses[0], f"no memorization: {losses[0]:.3f} -> {losses[-1]:.3f}"


# ------------------------------------------------------------------ dn-first barrier hand-case
def test_dn_first_barrier_hand_case():
    vol20 = 0.01
    h = 60
    sigma = vol20 * np.sqrt(h / ds.DAY_MINUTES)
    n_sec = 8000
    lvl = 0.75 * sigma
    offsets = np.array([1], dtype=np.int64)  # e=0, p0=logmid[0]=0

    # DOWN path: falls to -0.75*sigma by sec 600, then plateaus (never reaches -1.25).
    logdown = np.zeros(n_sec)
    logdown[1:601] = np.linspace(-lvl / 600, -lvl, 600)
    logdown[601:] = -lvl
    lab = ds._labels_for_session(logdown, n_sec, offsets, vol20)
    # -0.75 STRICTLY before +0.75 (never) -> dn-first hit
    assert lab["hit_dn_0.75x0.75_60"][0] == 1.0
    assert lab["hit_dn_1.25x0.75_60"][0] == 1.0   # up +1.25 never -> dn wins
    # down barrier at -1.25 never touched -> those dn labels are 0
    assert lab["hit_dn_0.75x1.25_60"][0] == 0.0
    assert lab["hit_dn_1.25x1.25_60"][0] == 0.0
    # mirror consistency: up-first is 0 where dn-first is 1
    assert lab["hit_0.75sig_before_0.75sig_60m"][0] == 0.0

    # UP path: rises to +0.75*sigma -> dn-first must be 0, up-first 1
    logup = -logdown
    lab2 = ds._labels_for_session(logup, n_sec, offsets, vol20)
    assert lab2["hit_dn_0.75x0.75_60"][0] == 0.0
    assert lab2["hit_0.75sig_before_0.75sig_60m"][0] == 1.0
    # rv label present (30m window fits inside 8000s)
    assert np.isfinite(lab2["l_rv_30m"][0])
