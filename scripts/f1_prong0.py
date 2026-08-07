"""F1 prong 0 -- mechanism pre-check (PRE-DECLARED DIAGNOSTIC, NO ECONOMICS).

Spec frozen in ledger note `F1-prong0-predeclaration`
(context: research/HYPOTHESES_FABLE_MAX.md, F1 prong 0).

This script computes ONLY correlations between two CONTEMPORANEOUS state
variables observed on our owned tape. It NEVER computes a return, a P&L, or any
forward price change. The single decisive number is the PREDICTIVE Pearson rho
between the displayed-depth footprint and the NEXT bucket's realized signed
order-flow imbalance; the gate is rho >= 0.10 pooled.

Per (symbol, session), 15-minute buckets tile 10:00-15:30 ET (22 buckets):
  depth_state[t]  = mean over the bucket of (bid_size - ask_size)/(bid_size +
                    ask_size) from bbo1s, skipping seconds with zero total size.
  signed_flow[t]  = (buy_vol - sell_vol)/(buy_vol + sell_vol) using the quote
                    rule (Lee-Ready) vs the prevailing mid at each trade ts;
                    px>mid -> buy, px<mid -> sell, px==mid -> tick rule vs the
                    previous trade price (carry last sign on a further tie).
                    Prevailing mid via searchsorted-guarded lookup that never
                    wraps to a future quote.

Outputs:
  (a) contemporaneous pooled rho(depth_state[t], signed_flow[t])
  (b) PREDICTIVE pooled rho(depth_state[t], signed_flow[t+1])  <- GATE
  (c) per-name rows for (a) and (b)
  (d) day-clustered 95% CI on the predictive rho: bootstrap the SET of sessions
      with replacement (n_sessions draws), pool the drawn sessions' (t, t+1)
      pairs, recompute pooled rho; seed 7, 2000 draws (session-bootstrap idea of
      stress.clustered_mean_ci, implemented locally since the statistic is a
      correlation, not a mean).
  (e) persistence: pooled AR(1) slope of depth_state across consecutive buckets
      within a session, plus lag-1..6 autocorrelation (45-90 min horizon).
  coverage: sessions per name, buckets per session, total (t, t+1) pairs.

Tape hygiene (per src/enginev51/backtest/tape.py convention):
  - v1.4 condition-code blacklist 'ZLGU4WPCNRHXMQO569T' applied ONLY when the
    session carries non-empty condition codes; empty-conditions sessions fall
    back to keeping all prints (count reported).
  - trades price > 0.
  - drop trades < 100 shares (landmine L1).
  - quotes for the mid must satisfy bid > 0 AND ask > bid (crossed/locked out).

Self-contained, seeded, ASCII-only output. Writes
research/experiments/F1-prong0/result.json and summary.md. Touches no other file.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
REPO = Path(__file__).resolve().parents[1]
TRADES_DIR = REPO / "data" / "raw" / "sip" / "trades"
BBO_DIR = REPO / "data" / "raw" / "bbo1s"
OUT_DIR = REPO / "research" / "experiments" / "F1-prong0"

SYMBOLS = ["MU", "NVDA", "TSLA", "AMD", "GOOGL"]

BLACKLIST = "ZLGU4WPCNRHXMQO569T"  # tape.py v1.4 condition-code blacklist
MIN_FILL_SIZE = 100                # landmine L1

ET = ZoneInfo("America/New_York")

# Bucket grid: 10:00..15:30 ET, 15-min buckets => 22 buckets.
OPEN_MIN = 10 * 60          # 600  (10:00)
CLOSE_MIN = 15 * 60 + 30    # 930  (15:30)
BUCKET_W = 15
N_BUCKETS = (CLOSE_MIN - OPEN_MIN) // BUCKET_W  # 22

BOOT_SEED = 7
BOOT_DRAWS = 2000
GATE = 0.10


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _et_minute_and_date(ts_col: pl.Expr) -> tuple[pl.Expr, pl.Expr]:
    """Return (minutes-since-ET-midnight, ET date string) from int64 ns UTC ts."""
    dt = pl.from_epoch(ts_col, time_unit="ns").dt.convert_time_zone("America/New_York")
    minute = dt.dt.hour().cast(pl.Int32) * 60 + dt.dt.minute().cast(pl.Int32)
    date = dt.dt.strftime("%Y-%m-%d")
    return minute, date


def _bucket_expr(minute: pl.Expr) -> pl.Expr:
    return ((minute - OPEN_MIN) // BUCKET_W).cast(pl.Int32)


def _ffill_sign(sign: np.ndarray) -> np.ndarray:
    """Replace 0-signs with the most recent non-zero sign at or before them."""
    valid = sign != 0
    if not valid.any():
        return sign
    idx = np.where(valid, np.arange(sign.shape[0]), 0)
    np.maximum.accumulate(idx, out=idx)
    out = sign[idx]
    # positions before the first valid sign keep sign[0]; if sign[0]==0 they stay 0
    return out


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.shape[0] < 3:
        return float("nan")
    xd = x - x.mean()
    yd = y - y.mean()
    denom = math.sqrt(float((xd * xd).sum()) * float((yd * yd).sum()))
    if denom == 0.0:
        return float("nan")
    return float((xd * yd).sum() / denom)


# --------------------------------------------------------------------------- #
# Per-session computation
# --------------------------------------------------------------------------- #
def depth_by_bucket(bbo_day: pl.DataFrame) -> dict[int, float]:
    """Mean displayed-depth imbalance per bucket (skip zero-total-size seconds)."""
    df = bbo_day.filter(
        pl.col("bid_size").is_not_null()
        & pl.col("ask_size").is_not_null()
        & ((pl.col("bid_size") + pl.col("ask_size")) > 0)
    )
    if df.height == 0:
        return {}
    df = df.with_columns(
        (
            (pl.col("bid_size") - pl.col("ask_size"))
            / (pl.col("bid_size") + pl.col("ask_size"))
        ).alias("imb")
    )
    agg = df.group_by("bucket").agg(pl.col("imb").mean().alias("depth"))
    return {int(b): float(d) for b, d in zip(agg["bucket"], agg["depth"])}


def flow_by_bucket(
    trades_day: pl.DataFrame, bbo_day: pl.DataFrame
) -> dict[int, float]:
    """Signed order-flow imbalance per bucket via Lee-Ready vs prevailing mid."""
    q = bbo_day.filter((pl.col("bid") > 0) & (pl.col("ask") > pl.col("bid")))
    if q.height == 0 or trades_day.height == 0:
        return {}
    q = q.sort("ts")
    q_ts = q["ts"].to_numpy()
    q_mid = ((q["bid"] + q["ask"]) / 2.0).to_numpy()

    tr = trades_day.sort("ts")
    t_ts = tr["ts"].to_numpy()
    t_px = tr["price"].to_numpy()
    t_sz = tr["size"].to_numpy().astype(np.float64)
    t_bkt = tr["bucket"].to_numpy()

    # prevailing mid: last quote with q_ts <= t_ts (guarded, never future)
    pos = np.searchsorted(q_ts, t_ts, side="right") - 1
    have = pos >= 0
    mid = np.full(t_ts.shape[0], np.nan)
    mid[have] = q_mid[pos[have]]

    sign = np.zeros(t_ts.shape[0], dtype=np.int64)
    sign[have & (t_px > mid)] = 1
    sign[have & (t_px < mid)] = -1

    # tick rule for px == mid (or trades with no prior quote): compare to prev px
    prev_px = np.empty_like(t_px)
    prev_px[0] = np.nan
    prev_px[1:] = t_px[:-1]
    tick = np.zeros(t_ts.shape[0], dtype=np.int64)
    tick[t_px > prev_px] = 1
    tick[t_px < prev_px] = -1
    need_tick = sign == 0
    sign[need_tick] = tick[need_tick]

    # carry last non-zero sign for remaining ties
    sign = _ffill_sign(sign)

    buy = t_sz * (sign > 0)
    sell = t_sz * (sign < 0)
    fdf = pl.DataFrame({"bucket": t_bkt, "buy": buy, "sell": sell})
    agg = fdf.group_by("bucket").agg(
        pl.col("buy").sum().alias("b"), pl.col("sell").sum().alias("s")
    )
    out: dict[int, float] = {}
    for b, bv, sv in zip(agg["bucket"], agg["b"], agg["s"]):
        tot = bv + sv
        if tot > 0:
            out[int(b)] = float((bv - sv) / tot)
    return out


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def main() -> None:
    # Per-session records: name -> session -> {bucket: (depth, flow)}
    sessions: dict[str, dict[str, dict[int, tuple[float | None, float | None]]]] = {
        s: {} for s in SYMBOLS
    }
    # data-quality counters
    dq = {
        s: {
            "sessions_seen": 0,
            "sessions_used": 0,
            "sessions_no_codes": 0,
            "sessions_no_conditions_col": 0,
            "sessions_missing_bbo": 0,
            "trades_total": 0,
            "trades_after_blacklist": 0,
            "trades_after_minsize": 0,
        }
        for s in SYMBOLS
    }

    for sym in SYMBOLS:
        tdir = TRADES_DIR / sym
        if not tdir.exists():
            continue
        files = sorted(tdir.glob("*.parquet"))
        # group by month so each bbo month file is loaded once
        by_month: dict[str, list[Path]] = {}
        for f in files:
            month = f.stem[:7]  # YYYY-MM
            by_month.setdefault(month, []).append(f)

        for month, day_files in by_month.items():
            bbo_path = BBO_DIR / sym / f"{month}.parquet"
            if not bbo_path.exists():
                for f in day_files:
                    dq[sym]["sessions_seen"] += 1
                    dq[sym]["sessions_missing_bbo"] += 1
                continue
            bbo = pl.read_parquet(bbo_path)
            b_min, b_date = _et_minute_and_date(pl.col("ts"))
            bbo = bbo.with_columns(b_min.alias("_min"), b_date.alias("_date"))
            bbo = bbo.filter(
                (pl.col("_min") >= OPEN_MIN) & (pl.col("_min") < CLOSE_MIN)
            ).with_columns(_bucket_expr(pl.col("_min")).alias("bucket"))
            bbo_by_date = {d: g for d, g in bbo.group_by("_date", maintain_order=True)}
            # polars group_by returns tuple keys; normalize
            bbo_by_date = {
                (k[0] if isinstance(k, tuple) else k): g
                for k, g in bbo_by_date.items()
            }

            for f in day_files:
                dq[sym]["sessions_seen"] += 1
                session = f.stem  # YYYY-MM-DD
                tr = pl.read_parquet(f)
                dq[sym]["trades_total"] += tr.height

                # --- condition-code blacklist (tape.py convention) ---
                if "conditions" in tr.columns:
                    nonempty = tr.filter(pl.col("conditions") != "").height
                    if nonempty > 0:
                        tr = tr.filter(
                            ~pl.col("conditions").str.contains_any(list(BLACKLIST))
                        )
                    else:
                        dq[sym]["sessions_no_codes"] += 1
                else:
                    dq[sym]["sessions_no_conditions_col"] += 1
                tr = tr.filter(pl.col("price") > 0)
                dq[sym]["trades_after_blacklist"] += tr.height
                if "size" in tr.columns:
                    tr = tr.filter(pl.col("size") >= MIN_FILL_SIZE)
                dq[sym]["trades_after_minsize"] += tr.height

                m2, d2 = _et_minute_and_date(pl.col("ts"))
                tr = tr.with_columns(m2.alias("_min"), d2.alias("_date"))
                tr = tr.filter(pl.col("_date") == session)
                tr = tr.filter(
                    (pl.col("_min") >= OPEN_MIN) & (pl.col("_min") < CLOSE_MIN)
                ).with_columns(_bucket_expr(pl.col("_min")).alias("bucket"))

                bbo_day = bbo_by_date.get(session)
                if bbo_day is None or bbo_day.height == 0:
                    continue

                depth = depth_by_bucket(bbo_day)
                flow = flow_by_bucket(tr, bbo_day)
                if not depth and not flow:
                    continue

                rec: dict[int, tuple[float | None, float | None]] = {}
                for b in range(N_BUCKETS):
                    d = depth.get(b)
                    fl = flow.get(b)
                    if d is not None or fl is not None:
                        rec[b] = (d, fl)
                if rec:
                    sessions[sym][session] = rec
                    dq[sym]["sessions_used"] += 1

    # ----------------------------------------------------------------------- #
    # Build pooled arrays
    # ----------------------------------------------------------------------- #
    # contemporaneous pairs (depth[t], flow[t]); predictive (depth[t], flow[t+1])
    # per-session predictive pairs kept grouped for the cluster bootstrap
    contemp_all: dict[str, list[tuple[float, float]]] = {s: [] for s in SYMBOLS}
    pred_by_session: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {
        s: [] for s in SYMBOLS
    }
    ar_pairs_all: dict[str, list[tuple[float, float]]] = {s: [] for s in SYMBOLS}
    # lag autocorrelation accumulators: per lag -> list of (x_t, x_{t+lag})
    lag_pairs: dict[int, list[tuple[float, float]]] = {k: [] for k in range(1, 7)}

    coverage_buckets: dict[str, list[int]] = {s: [] for s in SYMBOLS}

    for sym in SYMBOLS:
        for session, rec in sessions[sym].items():
            # depth/flow arrays indexed by bucket (NaN where missing)
            depth = np.full(N_BUCKETS, np.nan)
            flow = np.full(N_BUCKETS, np.nan)
            for b, (d, fl) in rec.items():
                if d is not None:
                    depth[b] = d
                if fl is not None:
                    flow[b] = fl
            coverage_buckets[sym].append(int(np.isfinite(depth).sum()))

            # contemporaneous
            for b in range(N_BUCKETS):
                if np.isfinite(depth[b]) and np.isfinite(flow[b]):
                    contemp_all[sym].append((depth[b], flow[b]))

            # predictive depth[t] vs flow[t+1]
            xs, ys = [], []
            for b in range(N_BUCKETS - 1):
                if np.isfinite(depth[b]) and np.isfinite(flow[b + 1]):
                    xs.append(depth[b])
                    ys.append(flow[b + 1])
            if xs:
                pred_by_session[sym].append(
                    (np.asarray(xs), np.asarray(ys))
                )

            # AR(1) consecutive depth pairs
            for b in range(N_BUCKETS - 1):
                if np.isfinite(depth[b]) and np.isfinite(depth[b + 1]):
                    ar_pairs_all[sym].append((depth[b], depth[b + 1]))

            # lag-k autocorr of depth
            for k in range(1, 7):
                for b in range(N_BUCKETS - k):
                    if np.isfinite(depth[b]) and np.isfinite(depth[b + k]):
                        lag_pairs[k].append((depth[b], depth[b + k]))

    def _rho_from_pairs(pairs: list[tuple[float, float]]) -> float:
        if len(pairs) < 3:
            return float("nan")
        arr = np.asarray(pairs)
        return _pearson(arr[:, 0], arr[:, 1])

    # pooled contemporaneous
    contemp_pool = [p for s in SYMBOLS for p in contemp_all[s]]
    rho_contemp = _rho_from_pairs(contemp_pool)
    rho_contemp_by_name = {s: _rho_from_pairs(contemp_all[s]) for s in SYMBOLS}

    # pooled predictive
    def _pred_arrays(sess_list: list[tuple[np.ndarray, np.ndarray]]):
        if not sess_list:
            return np.array([]), np.array([])
        xs = np.concatenate([a for a, _ in sess_list])
        ys = np.concatenate([b for _, b in sess_list])
        return xs, ys

    all_pred = [pair for s in SYMBOLS for pair in pred_by_session[s]]
    px, py = _pred_arrays(all_pred)
    rho_pred = _pearson(px, py)
    rho_pred_by_name = {}
    n_pred_by_name = {}
    for s in SYMBOLS:
        xs, ys = _pred_arrays(pred_by_session[s])
        rho_pred_by_name[s] = _pearson(xs, ys)
        n_pred_by_name[s] = int(xs.shape[0])

    # cluster (session) bootstrap on predictive rho
    rng = np.random.default_rng(BOOT_SEED)
    n_sess = len(all_pred)
    boot = np.empty(BOOT_DRAWS)
    idx_all = np.arange(n_sess)
    for i in range(BOOT_DRAWS):
        draw = rng.integers(0, n_sess, n_sess)
        xs = np.concatenate([all_pred[j][0] for j in draw])
        ys = np.concatenate([all_pred[j][1] for j in draw])
        boot[i] = _pearson(xs, ys)
    boot = boot[np.isfinite(boot)]
    ci_lo = float(np.quantile(boot, 0.025))
    ci_hi = float(np.quantile(boot, 0.975))

    # AR(1) slope pooled (regress depth[t+1] on depth[t])
    def _ar1_slope(pairs: list[tuple[float, float]]):
        if len(pairs) < 3:
            return float("nan"), float("nan")
        arr = np.asarray(pairs)
        x = arr[:, 0]
        y = arr[:, 1]
        xd = x - x.mean()
        yd = y - y.mean()
        vx = float((xd * xd).sum())
        if vx == 0:
            return float("nan"), _pearson(x, y)
        slope = float((xd * yd).sum() / vx)
        return slope, _pearson(x, y)

    ar_pool = [p for s in SYMBOLS for p in ar_pairs_all[s]]
    ar1_slope, ar1_corr = _ar1_slope(ar_pool)
    ar1_by_name = {}
    for s in SYMBOLS:
        sl, co = _ar1_slope(ar_pairs_all[s])
        ar1_by_name[s] = {"slope": sl, "corr": co, "n": len(ar_pairs_all[s])}

    lag_autocorr = {}
    for k in range(1, 7):
        lag_autocorr[k] = {
            "corr": _rho_from_pairs(lag_pairs[k]),
            "n": len(lag_pairs[k]),
        }

    # coverage
    coverage = {}
    for s in SYMBOLS:
        bk = coverage_buckets[s]
        coverage[s] = {
            "sessions_used": len(bk),
            "mean_buckets_per_session": float(np.mean(bk)) if bk else 0.0,
            "min_buckets": int(np.min(bk)) if bk else 0,
            "max_buckets": int(np.max(bk)) if bk else 0,
            "predictive_pairs": n_pred_by_name[s],
        }

    total_pred_pairs = int(px.shape[0])
    total_sessions_used = sum(len(sessions[s]) for s in SYMBOLS)

    # ----------------------------------------------------------------------- #
    # Assemble result
    # ----------------------------------------------------------------------- #
    result = {
        "spec": "F1-prong0-predeclaration",
        "note": "PRE-DECLARED DIAGNOSTIC -- correlations of contemporaneous state "
        "variables only; no returns, no P&L computed.",
        "config": {
            "symbols": SYMBOLS,
            "blacklist": BLACKLIST,
            "min_fill_size": MIN_FILL_SIZE,
            "bucket_window_min": BUCKET_W,
            "n_buckets": N_BUCKETS,
            "session_window_et": "10:00-15:30",
            "boot_seed": BOOT_SEED,
            "boot_draws": BOOT_DRAWS,
            "gate": GATE,
        },
        "gate_metric_predictive_rho": {
            "rho": rho_pred,
            "ci95_lo": ci_lo,
            "ci95_hi": ci_hi,
            "n_pairs": total_pred_pairs,
            "n_sessions": n_sess,
            "gate": GATE,
            "passes_gate": bool(np.isfinite(rho_pred) and abs(rho_pred) >= GATE),
        },
        "contemporaneous_rho": {
            "rho": rho_contemp,
            "n_pairs": len(contemp_pool),
        },
        "per_name": {
            s: {
                "rho_contemporaneous": rho_contemp_by_name[s],
                "rho_predictive": rho_pred_by_name[s],
                "n_predictive_pairs": n_pred_by_name[s],
                "n_contemp_pairs": len(contemp_all[s]),
            }
            for s in SYMBOLS
        },
        "persistence_ar1": {
            "pooled_slope": ar1_slope,
            "pooled_lag1_corr": ar1_corr,
            "n_pairs": len(ar_pool),
            "by_name": ar1_by_name,
            "lag_autocorr_15min_steps": lag_autocorr,
        },
        "coverage": {
            "total_sessions_used": total_sessions_used,
            "total_predictive_pairs": total_pred_pairs,
            "by_name": coverage,
        },
        "data_quality": dq,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    _write_summary(OUT_DIR / "summary.md", result)
    _print_console(result)


def _fmt(x: float, nd: int = 4) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "n/a"
    return f"{x:.{nd}f}"


def _write_summary(path: Path, r: dict) -> None:
    g = r["gate_metric_predictive_rho"]
    lines = []
    lines.append("# F1 prong 0 -- mechanism pre-check (PRE-DECLARED DIAGNOSTIC)")
    lines.append("")
    lines.append(
        "No economics: correlations between contemporaneous state variables only. "
        "No returns or P&L were computed."
    )
    lines.append("")
    lines.append("## GATE -- predictive rho(depth_state[t], signed_flow[t+1])")
    lines.append("")
    verdict = "PASS" if g["passes_gate"] else "FAIL"
    lines.append(
        f"rho = {_fmt(g['rho'])}  |  95% CI (session-clustered) "
        f"[{_fmt(g['ci95_lo'])}, {_fmt(g['ci95_hi'])}]  |  gate |rho|>={g['gate']}  "
        f"->  {verdict}"
    )
    lines.append(
        f"({g['n_pairs']} (t,t+1) pairs over {g['n_sessions']} sessions; "
        f"seed {r['config']['boot_seed']}, {r['config']['boot_draws']} draws)"
    )
    lines.append("")
    c = r["contemporaneous_rho"]
    lines.append("## Contemporaneous rho(depth_state[t], signed_flow[t])")
    lines.append("")
    lines.append(f"rho = {_fmt(c['rho'])}  ({c['n_pairs']} pairs)")
    lines.append("")
    lines.append("## Per-name")
    lines.append("")
    lines.append("| name | rho_contemp | rho_predictive | n_pred_pairs | n_contemp |")
    lines.append("|------|-------------|----------------|--------------|-----------|")
    for s in r["config"]["symbols"]:
        pn = r["per_name"][s]
        lines.append(
            f"| {s} | {_fmt(pn['rho_contemporaneous'])} | "
            f"{_fmt(pn['rho_predictive'])} | {pn['n_predictive_pairs']} | "
            f"{pn['n_contemp_pairs']} |"
        )
    lines.append("")
    p = r["persistence_ar1"]
    lines.append("## Persistence -- AR(1) of depth_state across buckets")
    lines.append("")
    lines.append(
        f"pooled AR(1) slope = {_fmt(p['pooled_slope'])}  "
        f"(lag-1 corr = {_fmt(p['pooled_lag1_corr'])}, {p['n_pairs']} pairs)"
    )
    lines.append("")
    lines.append("| lag (x15min) | horizon min | autocorr | n |")
    lines.append("|--------------|-------------|----------|---|")
    for k in range(1, 7):
        la = p["lag_autocorr_15min_steps"][str(k)] if str(k) in p[
            "lag_autocorr_15min_steps"
        ] else p["lag_autocorr_15min_steps"][k]
        lines.append(f"| {k} | {k*15} | {_fmt(la['corr'])} | {la['n']} |")
    lines.append("")
    lines.append("| name | AR(1) slope | lag1 corr | n |")
    lines.append("|------|-------------|-----------|---|")
    for s in r["config"]["symbols"]:
        bn = p["by_name"][s]
        lines.append(
            f"| {s} | {_fmt(bn['slope'])} | {_fmt(bn['corr'])} | {bn['n']} |"
        )
    lines.append("")
    cov = r["coverage"]
    lines.append("## Coverage")
    lines.append("")
    lines.append(
        f"total sessions used = {cov['total_sessions_used']}  |  "
        f"total (t,t+1) pairs = {cov['total_predictive_pairs']}"
    )
    lines.append("")
    lines.append(
        "| name | sessions | mean buckets/session | min | max | pred pairs |"
    )
    lines.append("|------|----------|----------------------|-----|-----|------------|")
    for s in r["config"]["symbols"]:
        cb = cov["by_name"][s]
        lines.append(
            f"| {s} | {cb['sessions_used']} | "
            f"{_fmt(cb['mean_buckets_per_session'], 2)} | {cb['min_buckets']} | "
            f"{cb['max_buckets']} | {cb['predictive_pairs']} |"
        )
    lines.append("")
    lines.append("## Data quality")
    lines.append("")
    lines.append(
        "| name | seen | used | no-codes sess | no-cond-col | missing bbo | "
        "trades total | after blacklist | after minsize |"
    )
    lines.append(
        "|------|------|------|---------------|-------------|-------------|"
        "--------------|-----------------|---------------|"
    )
    for s in r["config"]["symbols"]:
        d = r["data_quality"][s]
        lines.append(
            f"| {s} | {d['sessions_seen']} | {d['sessions_used']} | "
            f"{d['sessions_no_codes']} | {d['sessions_no_conditions_col']} | "
            f"{d['sessions_missing_bbo']} | {d['trades_total']} | "
            f"{d['trades_after_blacklist']} | {d['trades_after_minsize']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _print_console(r: dict) -> None:
    g = r["gate_metric_predictive_rho"]
    print("=" * 70)
    print("F1 PRONG 0 -- MECHANISM PRE-CHECK (PRE-DECLARED DIAGNOSTIC)")
    print("=" * 70)
    verdict = "PASS" if g["passes_gate"] else "FAIL"
    print(
        f"GATE predictive rho = {_fmt(g['rho'])}  "
        f"CI95 [{_fmt(g['ci95_lo'])}, {_fmt(g['ci95_hi'])}]  "
        f"gate |rho|>={g['gate']} -> {verdict}"
    )
    print(
        f"  ({g['n_pairs']} pairs, {g['n_sessions']} sessions)"
    )
    print(f"contemporaneous rho = {_fmt(r['contemporaneous_rho']['rho'])} "
          f"({r['contemporaneous_rho']['n_pairs']} pairs)")
    print("-" * 70)
    print("per-name  rho_contemp / rho_pred / n_pred")
    for s in r["config"]["symbols"]:
        pn = r["per_name"][s]
        print(
            f"  {s:6s} {_fmt(pn['rho_contemporaneous'])} / "
            f"{_fmt(pn['rho_predictive'])} / {pn['n_predictive_pairs']}"
        )
    print("-" * 70)
    p = r["persistence_ar1"]
    print(f"AR(1) depth slope = {_fmt(p['pooled_slope'])} "
          f"(lag1 corr {_fmt(p['pooled_lag1_corr'])})")
    for k in range(1, 7):
        la = p["lag_autocorr_15min_steps"][k]
        print(f"  lag {k} ({k*15}min): autocorr {_fmt(la['corr'])} (n={la['n']})")
    print("-" * 70)
    cov = r["coverage"]
    print(f"coverage: {cov['total_sessions_used']} sessions, "
          f"{cov['total_predictive_pairs']} predictive pairs")
    print("=" * 70)
    print(f"wrote {OUT_DIR / 'result.json'}")
    print(f"wrote {OUT_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()
