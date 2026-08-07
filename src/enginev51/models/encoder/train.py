"""M4 encoder training + emission (arch = tcn|tst), registered trial m4_encoder_v1.

Expanding walk-forward over the encoder decision-index sessions (aligned to
``models.cv.walk_forward_folds`` 21-session test blocks, 1-session embargo), taking
every ``--folds-every`` fold. Per fold: fit on sessions strictly before the block
(early stop patience 5 on the last-10%-of-train tail, AdamW, bf16 autocast), then
infer the test block and append the A1 prediction-contract columns PLUS the 16
barrier-probability columns to ``{out}/{SYMBOL}.parquet``.

PIT: every emitted row carries ``trained_through < session`` (code-asserted).

Throughput: the fine stream is GPU-starved at the ~1700 items/s single-worker
Dataset rate (~6.6 batch/s). We use OPTION (a): a per-fold in-RAM bfloat16 tensor
cache of every stream, filled once, then trained at RAM/GPU speed (bf16 not f16 so
IQR-normalized outliers cannot overflow). See ``_train_report``.

Acceptance benchmark (``--benchmark``): runs ONE fold for ``--bench-epochs`` (2)
epochs, prints losses moving + throughput + VRAM, writes NOTHING. The orchestrator
runs the full walk-forward.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import click
import numpy as np
import polars as pl
import torch
from torch import nn
from torch.utils.data import DataLoader, Subset

from enginev51.config import PROJECT_ROOT, get_settings
from enginev51.models.cv import Fold, walk_forward_folds
from enginev51.models.encoder import dataset as ds
from enginev51.models.encoder import heads as H
from enginev51.models.encoder.heads import EncoderHeads, head_loss
from enginev51.models.encoder.tcn import TCNEncoder
from enginev51.models.encoder.tst import TSTEncoder

SEED = 7

# label-name -> column index in ds.LABEL_COLS (fixed head <-> target wiring)
_FWD_IDX = [ds.LABEL_COLS.index(c) for c in H.FWD_TARGET_LABELS]
_EXC_IDX = [ds.LABEL_COLS.index(c) for c in H.EXC_TARGET_LABELS]
_BAR_IDX = [ds.LABEL_COLS.index(c) for c in H.BARRIER_TARGET_LABELS]
_RV_IDX = ds.LABEL_COLS.index(H.RV_TARGET_LABEL)

# emission slot indices
_Q50 = H.Q_FWD.index(0.50)
_FWD60 = H.FWD_TARGET_LABELS.index("l_fwd_60m_z")
_FWD120 = H.FWD_TARGET_LABELS.index("l_fwd_120m_z")
_MFE60 = H.EXC_TARGET_LABELS.index("l_mfe_60m_z")
_MFE120 = H.EXC_TARGET_LABELS.index("l_mfe_120m_z")
_MAE60 = H.EXC_TARGET_LABELS.index("l_mae_60m_z")
_MAE120 = H.EXC_TARGET_LABELS.index("l_mae_120m_z")
_EQ50, _EQ75 = H.Q_EXC.index(0.50), H.Q_EXC.index(0.75)

P_UP_COLS = [f"p_up_{a:g}x{b:g}_{h}" for h in ds.BARRIER_H for (a, b) in ds.BARRIER_AB]
P_DN_COLS = [f"p_dn_{a:g}x{b:g}_{h}" for h in ds.BARRIER_H for (a, b) in ds.BARRIER_AB]

# diagnostic barrier column (stop-relevant): 0.75 vs 1.25 sigma at 60m, both signs.
_DIAG_UP = ds.BARRIER_UP_LABELS.index(ds._barrier_name(0.75, 1.25, 60))
_DIAG_DN = ds.BARRIER_DN_LABELS.index(ds._barrier_dn_name(0.75, 1.25, 60))


# ============================================================== model wrapper
class M4Model(nn.Module):
    """Encoder (tcn|tst) + multitask head bank; ``forward(batch)`` -> head dict."""

    def __init__(self, arch: str, static_dim: int) -> None:
        super().__init__()
        if arch == "tcn":
            self.enc: nn.Module = TCNEncoder(static_dim=static_dim)
        elif arch == "tst":
            self.enc = TSTEncoder(static_dim=static_dim)
        else:  # pragma: no cover
            raise ValueError(f"unknown arch {arch!r}")
        self.heads = EncoderHeads(self.enc.trunk_dim)

    def forward(self, batch: dict) -> dict[str, torch.Tensor]:
        return self.heads(self.enc(batch))


def n_params(m: nn.Module) -> int:
    return sum(p.numel() for p in m.parameters())


# ============================================================== label splitting
def split_labels(labels: torch.Tensor) -> tuple[dict, dict]:
    """[B, 25] label matrix (nan = null) -> (targets, masks) per head group."""
    def grp(idx: list[int]) -> tuple[torch.Tensor, torch.Tensor]:
        t = labels[:, idx]
        m = torch.isfinite(t).float()
        return torch.nan_to_num(t, nan=0.0), m

    fwd_t, fwd_m = grp(_FWD_IDX)
    exc_t, exc_m = grp(_EXC_IDX)
    bar_t, bar_m = grp(_BAR_IDX)
    rv = labels[:, _RV_IDX]
    rv_m = torch.isfinite(rv).float()
    rv_t = torch.nan_to_num(rv, nan=0.0)
    targets = {"fwd": fwd_t, "exc": exc_t, "barrier": bar_t, "rv": rv_t}
    masks = {"fwd": fwd_m, "exc": exc_m, "barrier": bar_m, "rv": rv_m}
    return targets, masks


# ============================================================== fold cache (option a)
def _collate(items: list[dict]) -> tuple:
    fine = torch.stack([it["fine"] for it in items])
    sess = torch.stack([it["sess"] for it in items])
    static = torch.stack([it["static"] for it in items])
    labels = torch.stack(
        [torch.stack([it["labels"][c] for c in ds.LABEL_COLS]) for it in items]
    )
    return fine, sess, static, labels


def materialize(dataset: ds.EncoderDataset, indices: list[int], num_workers: int,
                batch: int = 512) -> dict[str, torch.Tensor]:
    """Fill an in-RAM bfloat16 tensor cache of every stream for ``indices``."""
    sub = Subset(dataset, indices)
    dl = DataLoader(sub, batch_size=batch, shuffle=False, num_workers=num_workers,
                    collate_fn=_collate, persistent_workers=False)
    # bf16 (not f16): same 2 bytes but full f32 exponent range, so IQR-normalized
    # outliers in the fine stream cannot overflow to inf (f16 max ~6.5e4).
    fines, sesss, statics, labels = [], [], [], []
    for fine, sess, static, lab in dl:
        fines.append(fine.bfloat16())
        sesss.append(sess.bfloat16())
        statics.append(static.float())
        labels.append(lab.float())
    return {
        "fine": torch.cat(fines), "sess": torch.cat(sesss),
        "static": torch.cat(statics), "labels": torch.cat(labels),
    }


def cache_bytes(cache: dict[str, torch.Tensor]) -> int:
    return sum(t.element_size() * t.nelement() for t in cache.values())


# ============================================================== train / infer
def run_epoch(model: M4Model, cache: dict, opt, device: str, batch_size: int,
              train: bool, autocast_dtype) -> float:
    model.train(train)
    n = cache["fine"].shape[0]
    order = torch.randperm(n) if train else torch.arange(n)
    tot, seen = 0.0, 0
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for s in range(0, n, batch_size):
            idx = order[s:s + batch_size]
            batch = {
                "fine": cache["fine"][idx].to(device, non_blocking=True).float(),
                "sess": cache["sess"][idx].to(device, non_blocking=True).float(),
                "static": cache["static"][idx].to(device, non_blocking=True),
            }
            labels = cache["labels"][idx].to(device, non_blocking=True)
            targets, masks = split_labels(labels)
            with torch.autocast(device_type=device.split(":")[0], dtype=autocast_dtype,
                                enabled=(device != "cpu")):
                out = model(batch)
                loss, _ = head_loss(out, targets, masks)
            if train:
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
            tot += float(loss.detach()) * len(idx)
            seen += len(idx)
    return tot / max(seen, 1)


@torch.no_grad()
def infer(model: M4Model, cache: dict, device: str, batch_size: int, autocast_dtype):
    """Return (fwd60,fwd120, mfe60_50,mfe60_75,mfe120_50,mfe120_75, mae60_75,mae120_75,
    probs[N,16]) as numpy — the emission payload."""
    model.eval()
    n = cache["fine"].shape[0]
    fwd60, fwd120 = [], []
    mfe = {k: [] for k in ("m60_50", "m60_75", "m120_50", "m120_75")}
    mae = {k: [] for k in ("a60_75", "a120_75")}
    probs = []
    for s in range(0, n, batch_size):
        sl = slice(s, s + batch_size)
        batch = {
            "fine": cache["fine"][sl].to(device).float(),
            "sess": cache["sess"][sl].to(device).float(),
            "static": cache["static"][sl].to(device),
        }
        with torch.autocast(device_type=device.split(":")[0], dtype=autocast_dtype,
                            enabled=(device != "cpu")):
            out = model(batch)
        f = out["fwd"].float().cpu().numpy()
        e = out["exc"].float().cpu().numpy()
        p = torch.sigmoid(out["barrier_logits"]).float().cpu().numpy()
        fwd60.append(f[:, _FWD60, _Q50])
        fwd120.append(f[:, _FWD120, _Q50])
        mfe["m60_50"].append(e[:, _MFE60, _EQ50])
        mfe["m60_75"].append(e[:, _MFE60, _EQ75])
        mfe["m120_50"].append(e[:, _MFE120, _EQ50])
        mfe["m120_75"].append(e[:, _MFE120, _EQ75])
        mae["a60_75"].append(e[:, _MAE60, _EQ75])
        mae["a120_75"].append(e[:, _MAE120, _EQ75])
        probs.append(p)
    cat = np.concatenate
    return {
        "pred_fwd60_z": cat(fwd60), "pred_fwd120_z": cat(fwd120),
        "pred_mfe60_q50_z": cat(mfe["m60_50"]), "pred_mfe60_q75_z": cat(mfe["m60_75"]),
        "pred_mfe120_q50_z": cat(mfe["m120_50"]), "pred_mfe120_q75_z": cat(mfe["m120_75"]),
        "pred_mae60_q75_z": cat(mae["a60_75"]), "pred_mae120_q75_z": cat(mae["a120_75"]),
        "probs": cat(probs),
    }


# ============================================================== folds / metrics
def build_folds(dataset: ds.EncoderDataset, folds_every: int, test_block: int,
                min_train: int, embargo: int) -> list[Fold]:
    sess_df = dataset.index.select("session")
    all_folds = walk_forward_folds(sess_df, test_block, min_train, embargo)
    return all_folds[::folds_every]


def _row_meta(dataset: ds.EncoderDataset) -> dict[str, np.ndarray]:
    idx = dataset.index
    return {
        "symbol": idx["symbol"].to_numpy(), "session": idx["session"].to_numpy(),
        "ts": idx["ts"].to_numpy(), "vol20": idx["vol20"].to_numpy(),
    }


def _indices_for(meta_sess: np.ndarray, sessions: set[str]) -> list[int]:
    return [i for i, s in enumerate(meta_sess) if s in sessions]


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Mann-Whitney U ROC-AUC; nan labels dropped. nan if a class is empty."""
    m = np.isfinite(labels) & np.isfinite(scores)
    s, y = scores[m], labels[m]
    n1 = float((y == 1).sum())
    n0 = float((y == 0).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = s.argsort(kind="mergesort")
    ranks = np.empty(len(s), dtype=np.float64)
    ranks[order] = np.arange(1, len(s) + 1)
    # average ranks over ties
    _, inv, counts = np.unique(s, return_inverse=True, return_counts=True)
    csum = np.cumsum(counts)
    avg = (csum - counts / 2.0 + 0.5)
    ranks = avg[inv]
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


# ============================================================== drivers
def make_model_and_opt(arch: str, static_dim: int, device: str, lr: float, wd: float):
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    model = M4Model(arch, static_dim).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    return model, opt


def fit_fold(model, opt, fit_cache, val_cache, device, batch_size, max_epochs,
             patience, autocast_dtype, log: list | None = None) -> dict:
    best_val, best_state, bad = math.inf, None, 0
    hist = []
    for ep in range(max_epochs):
        tr = run_epoch(model, fit_cache, opt, device, batch_size, True, autocast_dtype)
        va = run_epoch(model, val_cache, None, device, batch_size, False, autocast_dtype)
        hist.append({"epoch": ep, "train": tr, "val": va})
        if log is not None:
            log.append(f"    epoch {ep}: train={tr:.4f} val={va:.4f}")
        if va < best_val - 1e-5:
            best_val, bad = va, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return {"history": hist, "best_val": best_val, "epochs_run": len(hist)}


def full_run(settings, arch, symbols, out_dir, folds_every, test_block, min_train,
             embargo, batch_size, max_epochs, patience, lr, wd, num_workers, device):
    autocast_dtype = torch.bfloat16
    dataset = ds.EncoderDataset(settings, symbols)
    static_dim = int(dataset[0]["static"].shape[0])
    meta = _row_meta(dataset)
    folds = build_folds(dataset, folds_every, test_block, min_train, embargo)
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    param_counts = {}
    tmp = M4Model(arch, static_dim)
    param_counts = {"encoder": n_params(tmp.enc), "heads": n_params(tmp.heads),
                    "total": n_params(tmp)}
    del tmp

    emit_rows: dict[str, list[dict]] = {s: [] for s in symbols}
    fold_reports = []
    for fold_id, fold in enumerate(folds):
        t0 = time.time()
        train_sessions = list(fold.train_sessions)
        n_val = max(1, math.ceil(0.10 * len(train_sessions)))
        val_sessions = set(train_sessions[-n_val:])
        fit_sessions = set(train_sessions) - val_sessions
        test_sessions = set(fold.test_sessions)
        trained_through = max(train_sessions)

        fit_idx = _indices_for(meta["session"], fit_sessions)
        val_idx = _indices_for(meta["session"], val_sessions)
        test_idx = _indices_for(meta["session"], test_sessions)

        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        fit_cache = materialize(dataset, fit_idx, num_workers)
        val_cache = materialize(dataset, val_idx, num_workers)
        model, opt = make_model_and_opt(arch, static_dim, device, lr, wd)
        fit_res = fit_fold(model, opt, fit_cache, val_cache, device, batch_size,
                           max_epochs, patience, autocast_dtype)
        del fit_cache, val_cache

        test_cache = materialize(dataset, test_idx, num_workers)
        pred = infer(model, test_cache, device, batch_size, autocast_dtype)
        del test_cache

        test_sess = meta["session"][test_idx]
        test_sym = meta["symbol"][test_idx]
        test_ts = meta["ts"][test_idx]
        test_vol = meta["vol20"][test_idx]
        test_labels = dataset._labels[test_idx]  # [n,25]
        for j in range(len(test_idx)):
            sess = str(test_sess[j])
            assert trained_through < sess, f"PIT violation: trained_through {trained_through} !< {sess}"
            row = {
                "symbol": str(test_sym[j]), "session": sess, "ts": int(test_ts[j]),
                "pred_fwd60_z": float(pred["pred_fwd60_z"][j]),
                "pred_fwd120_z": float(pred["pred_fwd120_z"][j]),
                "pred_mfe60_q50_z": float(pred["pred_mfe60_q50_z"][j]),
                "pred_mfe60_q75_z": float(pred["pred_mfe60_q75_z"][j]),
                "pred_mfe120_q50_z": float(pred["pred_mfe120_q50_z"][j]),
                "pred_mfe120_q75_z": float(pred["pred_mfe120_q75_z"][j]),
                "pred_mae60_q75_z": float(pred["pred_mae60_q75_z"][j]),
                "pred_mae120_q75_z": float(pred["pred_mae120_q75_z"][j]),
                "vol20": float(test_vol[j]),
                "fold_id": fold_id, "trained_through": trained_through,
            }
            for k, c in enumerate(P_UP_COLS):
                row[c] = float(pred["probs"][j, k])
            for k, c in enumerate(P_DN_COLS):
                row[c] = float(pred["probs"][j, 8 + k])
            emit_rows[row["symbol"]].append(row)

        # diagnostic stop-relevant AUCs on the test block
        up_scores = pred["probs"][:, _DIAG_UP]
        dn_scores = pred["probs"][:, 8 + _DIAG_DN]
        up_lab = test_labels[:, _BAR_IDX[_DIAG_UP]]
        dn_lab = test_labels[:, _BAR_IDX[8 + _DIAG_DN]]
        wall = time.time() - t0
        items = len(fit_idx) * fit_res["epochs_run"]
        fold_reports.append({
            "fold_id": fold_id, "trained_through": trained_through,
            "n_train_sessions": len(fit_sessions), "n_val_sessions": len(val_sessions),
            "n_test_sessions": len(test_sessions),
            "n_fit_items": len(fit_idx), "n_test_items": len(test_idx),
            "epochs_run": fit_res["epochs_run"], "best_val": fit_res["best_val"],
            "history": fit_res["history"],
            "auc_dn_075x125_60": roc_auc(dn_scores, dn_lab),
            "auc_up_075x125_60": roc_auc(up_scores, up_lab),
            "wall_s": round(wall, 1),
            "train_items_per_s": round(items / wall, 1) if wall > 0 else None,
            "gpu_mem_peak_gb": round(torch.cuda.max_memory_allocated() / 1e9, 3)
            if device == "cuda" else None,
        })

    for sym, rows in emit_rows.items():
        if rows:
            pl.DataFrame(rows).sort(["session", "ts"]).write_parquet(out_dir / f"{sym}.parquet")

    report = {
        "arch": arch, "symbols": symbols, "n_folds": len(folds),
        "param_counts": param_counts, "throughput_option": "a_inram_bf16_cache",
        "folds": fold_reports,
    }
    (out_dir / "_train_report.json").write_text(json.dumps(report, indent=2, default=str))
    return report


def benchmark_run(settings, arch, symbols, folds_every, test_block, min_train,
                  embargo, batch_size, bench_epochs, lr, wd, num_workers, device,
                  bench_fold: int) -> dict:
    """1 fold x ``bench_epochs`` epochs (no early stop). Report the acceptance numbers."""
    autocast_dtype = torch.bfloat16
    dataset = ds.EncoderDataset(settings, symbols)
    static_dim = int(dataset[0]["static"].shape[0])
    meta = _row_meta(dataset)
    folds = build_folds(dataset, folds_every, test_block, min_train, embargo)
    fold = folds[bench_fold]
    train_sessions = list(fold.train_sessions)
    n_val = max(1, math.ceil(0.10 * len(train_sessions)))
    fit_sessions = set(train_sessions[:-n_val])
    val_sessions = set(train_sessions[-n_val:])
    fit_idx = _indices_for(meta["session"], fit_sessions)
    val_idx = _indices_for(meta["session"], val_sessions)

    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    t_fill = time.time()
    fit_cache = materialize(dataset, fit_idx, num_workers)
    val_cache = materialize(dataset, val_idx, num_workers)
    fill_s = time.time() - t_fill
    fill_items = len(fit_idx) + len(val_idx)

    model, opt = make_model_and_opt(arch, static_dim, device, lr, wd)
    pcounts = {"encoder": n_params(model.enc), "heads": n_params(model.heads),
               "total": n_params(model)}

    epoch_times, losses = [], []
    for ep in range(bench_epochs):
        te = time.time()
        tr = run_epoch(model, fit_cache, opt, device, batch_size, True, autocast_dtype)
        et = time.time() - te
        va = run_epoch(model, val_cache, None, device, batch_size, False, autocast_dtype)
        epoch_times.append(et)
        losses.append({"epoch": ep, "train": round(tr, 4), "val": round(va, 4),
                       "epoch_s": round(et, 2)})

    mean_epoch_s = float(np.mean(epoch_times))
    gpu_items_per_s = len(fit_idx) / mean_epoch_s
    # project full walk-forward: assume every fold trains ~n_folds fit blocks; use
    # the expanding-window average fit size, ~20 effective epochs (early stop).
    n_folds = len(folds)
    assumed_epochs = 20
    # expanding folds: fit size grows ~linearly; average ~ mid fold size.
    avg_fit_frac = 0.6  # heuristic mean of expanding-train fraction across folds
    total_items = dataset.index.height
    est_fit_avg = total_items * avg_fit_frac
    proj_train_s = n_folds * (assumed_epochs * est_fit_avg / gpu_items_per_s)
    proj_fill_s = n_folds * (fill_items / (fill_items / fill_s if fill_s > 0 else 1))
    proj_total_h = (proj_train_s + proj_fill_s) / 3600.0

    return {
        "arch": arch, "device": device, "bench_fold": bench_fold, "n_folds": n_folds,
        "param_counts": pcounts,
        "n_fit_items": len(fit_idx), "n_val_items": len(val_idx),
        "cache_fill_s": round(fill_s, 1),
        "cache_fill_items_per_s": round(fill_items / fill_s, 1) if fill_s > 0 else None,
        "fit_cache_gb": round(cache_bytes(fit_cache) / 1e9, 2),
        "mean_epoch_s": round(mean_epoch_s, 2),
        "gpu_train_items_per_s": round(gpu_items_per_s, 1),
        "gpu_mem_peak_gb": round(torch.cuda.max_memory_allocated() / 1e9, 3)
        if device == "cuda" else None,
        "losses_moving": losses,
        "projected_full_run_h": round(proj_total_h, 2),
        "projection_assumes": {"epochs_per_fold": assumed_epochs,
                               "avg_fit_fraction": avg_fit_frac, "n_folds": n_folds},
    }


# ============================================================== cli
@click.command()
@click.option("--arch", type=click.Choice(["tcn", "tst"]), required=True)
@click.option("--out", default="data/preds/m4_v1", help="Emission dir.")
@click.option("--symbols", default="NVDA,TSLA")
@click.option("--folds-every", default=3, type=int)
@click.option("--test-block", default=21, type=int)
@click.option("--min-train", default=63, type=int, help="Min train sessions (encoder has ~187).")
@click.option("--embargo", default=1, type=int)
@click.option("--batch-size", default=256, type=int)
@click.option("--max-epochs", default=40, type=int)
@click.option("--patience", default=5, type=int)
@click.option("--lr", default=3e-4, type=float)
@click.option("--wd", default=1e-2, type=float)
@click.option("--num-workers", default=0, type=int)
@click.option("--benchmark", is_flag=True, help="Run 1 fold x bench-epochs; write nothing.")
@click.option("--bench-epochs", default=2, type=int)
@click.option("--bench-fold", default=0, type=int)
def main(arch, out, symbols, folds_every, test_block, min_train, embargo, batch_size,
         max_epochs, patience, lr, wd, num_workers, benchmark, bench_epochs, bench_fold):
    settings = get_settings()
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if benchmark:
        rep = benchmark_run(settings, arch, syms, folds_every, test_block, min_train,
                            embargo, batch_size, bench_epochs, lr, wd, num_workers,
                            device, bench_fold)
        click.echo(json.dumps(rep, indent=2, default=str))
    else:
        rep = full_run(settings, arch, syms, out, folds_every, test_block, min_train,
                       embargo, batch_size, max_epochs, patience, lr, wd, num_workers,
                       device)
        click.echo(json.dumps({k: v for k, v in rep.items() if k != "folds"},
                              indent=2, default=str))
        click.echo(f"folds: {len(rep['folds'])}  out: {out}")


if __name__ == "__main__":
    main()
