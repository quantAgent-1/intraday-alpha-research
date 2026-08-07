"""M4 event-stream dataset layer for the GPU encoder (NO training here).

Three deliverables, all point-in-time and holdout-safe:

1. ``build_norm_stats`` — per (symbol, session) median + IQR of every fine channel,
   pooled over the TRAILING 20 sessions strictly before the session (PIT). Used to
   normalize the tensors. Skips sessions with < 12 priors. IQR floored at 1e-9.
2. ``build_decision_index`` — one row per decision point (every 60 s, 11:00–15:30 ET)
   per (symbol, session) with forward / excursion / barrier labels derived from the
   1-second event-bar mid series. Labels whose horizon window crosses the session
   close are NULL (kept in the index, dropped at train time).
3. ``EncoderDataset`` — a ``torch.utils.data.Dataset`` yielding, per decision point:
   ``fine`` [1080 x 22]  (90 min of 1s bars downsampled to 5s, ending just before ts),
   ``sess`` [390 x 12]   (the session-so-far aggregated to 1 min, zero+mask padded),
   ``static`` [41]       (37 f_* PIT features + minute-of-session + dow + symbol 1-hot;
                          the f_* asof is lagged by ``PRED_STAMP_TO_AVAILABILITY_NS``
                          -- rows are stamped at bar OPEN but hold that bar's CLOSE),
   ``labels`` dict, ``meta`` dict.

Frozen design choices (documented in the module constants below):
- Price *levels* (px_*, bid, ask, mid) never enter a tensor (non-stationary). They are
  replaced by ret_close (5s log-mid return), hl_range_bps, close_loc; spread / micro-dev
  stay in bps. See ``FINE_DATA_CHANNELS``.
- Summed flow channels are stored as PER-SECOND RATES (sum / bar_seconds) so the 5s
  ``fine`` stream and the 1-min ``sess`` stream share one scale and one norm-stats table.
- ``build_norm_stats`` is computed at the 5s ``fine`` resolution; the same med/iqr also
  normalizes the 1-min ``sess`` subset (rate-matched by construction; the derived
  range/return channels carry a small, learnable scale offset at 1-min — documented).
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl

from enginev51.config import PROJECT_ROOT, Settings
from enginev51.events.event_bars import EVENT_BARS_COLUMNS
from enginev51.features import slow
from enginev51.features.grid import PRED_STAMP_TO_AVAILABILITY_NS
from enginev51.protocol import HOLDOUT_START, SealViolation

try:  # torch is present via the gpu extra; keep norm/index builds importable without it
    from torch.utils.data import Dataset as _DatasetBase
except Exception:  # pragma: no cover
    _DatasetBase = object  # type: ignore[assignment,misc]

NS_PER_S = 1_000_000_000
ET = ZoneInfo("America/New_York")
DAY_MINUTES = 390.0

# ------------------------------------------------------------------ downsample
# FROZEN aggregation semantics (the tensor path and the tests depend on this).
SUM_COLS = [
    "n_trades", "volume", "dollar_vol", "signed_vol", "signed_dollar",
    "at_ask_vol", "at_bid_vol", "large_trade_vol", "n_quotes", "ofi",
    "locked_crossed_n",
]
LAST_COLS = ["px_close", "bid", "ask", "mid", "spread_bps_close", "imb_close", "micro_dev_bps"]
FIRST_COLS = ["px_open"]
MAX_COLS = ["px_high", "max_trade_size"]
MIN_COLS = ["px_low"]
MEAN_COLS = ["spread_bps_mean", "imb_mean", "odd_lot_frac"]

# price / state columns forward-filled within a session before slicing (PIT: past only);
# summed-flow columns are already 0 in empty seconds and are never ffilled.
_FFILL_COLS = ["px_open", "px_high", "px_low", "px_close", "bid", "ask", "mid",
               "spread_bps_close", "spread_bps_mean", "imb_close", "imb_mean", "micro_dev_bps"]

# ------------------------------------------------------------------ channels
# The FROZEN fine-channel list: 21 data channels + 1 validity mask = 22 wide.
# Sum channels (rate-converted) come after the derived price / spread / imbalance block.
FINE_DATA_CHANNELS: list[str] = [
    "ret_close", "hl_range_bps", "close_loc",          # derived from price levels
    "spread_bps_close", "spread_bps_mean", "micro_dev_bps",
    "imb_close", "imb_mean",
    "n_trades", "volume", "dollar_vol", "signed_vol", "signed_dollar",
    "at_ask_vol", "at_bid_vol", "large_trade_vol", "n_quotes", "ofi",
    "locked_crossed_n", "max_trade_size", "odd_lot_frac",
]
FINE_CHANNELS: list[str] = [*FINE_DATA_CHANNELS, "valid_mask"]  # width 22

# sum channels are stored as per-second rates (divide the summed bar by its seconds).
_RATE_CHANNELS = set(SUM_COLS)

# The session-context stream is a curated 11-channel subset + mask = 12 wide
# (the deliverable pins sess to [390 x 12]; a full-width copy of the fine stream
# would be redundant, so the 11 most informative stationary channels are kept).
SESS_DATA_CHANNELS: list[str] = [
    "ret_close", "hl_range_bps", "spread_bps_close", "imb_close", "close_loc",
    "n_trades", "volume", "signed_vol", "at_ask_vol", "at_bid_vol", "ofi",
]
SESS_CHANNELS: list[str] = [*SESS_DATA_CHANNELS, "valid_mask"]  # width 12

FINE_STEP_S = 5
FINE_STEPS = 1080          # 90 min / 5 s
FINE_WINDOW_S = FINE_STEP_S * FINE_STEPS  # 5400 s = 90 min
SESS_STEP_S = 60
SESS_STEPS = 390           # one full RTH session in minutes

# ------------------------------------------------------------------ labels
FWD_HORIZONS = [30, 60, 120]          # minutes; z-scored forward mid returns
EXC_HORIZONS = [60, 120]              # MFE / MAE horizons (minutes)
BARRIER_AB = [(0.75, 0.75), (0.75, 1.25), (1.25, 0.75), (1.25, 1.25)]
BARRIER_H = [60, 120]                 # minutes
RV_HORIZON_MIN = 30                   # next-30m realized-vol label horizon (H5)


def _barrier_name(a: float, b: float, h: int) -> str:
    """UP-FIRST barrier: +a*sigma touched STRICTLY BEFORE -b*sigma within H."""
    return f"hit_{a:g}sig_before_{b:g}sig_{h}m"


def _barrier_dn_name(a: float, b: float, h: int) -> str:
    """DOWN-FIRST barrier (mirror): -b*sigma touched STRICTLY BEFORE +a*sigma within H."""
    return f"hit_dn_{a:g}x{b:g}_{h}"


FWD_LABELS = [f"l_fwd_{h}m_z" for h in FWD_HORIZONS] + ["l_fwd_close_z"]
EXC_LABELS = [f"l_mfe_{h}m_z" for h in EXC_HORIZONS] + [f"l_mae_{h}m_z" for h in EXC_HORIZONS]
# Barrier grid: 8 UP-FIRST (frozen) + 8 mirrored DOWN-FIRST = 16 barrier labels.
BARRIER_UP_LABELS = [_barrier_name(a, b, h) for h in BARRIER_H for (a, b) in BARRIER_AB]
BARRIER_DN_LABELS = [_barrier_dn_name(a, b, h) for h in BARRIER_H for (a, b) in BARRIER_AB]
BARRIER_LABELS = BARRIER_UP_LABELS  # backwards-compatible alias (the up-first block)
RV_LABEL = "l_rv_30m"               # next-30m realized std of 5s log-mid returns (H5)
# 4 fwd + 4 exc + 8 up-barrier + 8 dn-barrier + 1 rv = 25 label columns.
LABEL_COLS: list[str] = [*FWD_LABELS, *EXC_LABELS, *BARRIER_UP_LABELS, *BARRIER_DN_LABELS, RV_LABEL]
BARRIER_ALL_LABELS: list[str] = [*BARRIER_UP_LABELS, *BARRIER_DN_LABELS]  # 16, head-order

DECISION_START_MIN = 11 * 60          # 11:00 ET
DECISION_END_MIN = 15 * 60 + 30       # 15:30 ET


# ================================================================== IO helpers
def _session_partitions(settings: Settings, symbol: str) -> dict[str, Path]:
    """session-date str -> partition path, primary read-root winning; holdout excluded."""
    out: dict[str, Path] = {}
    hold = HOLDOUT_START.isoformat()
    for root in settings.read_roots:
        d = root / "sip" / "event_bars1s" / symbol.upper()
        if not d.is_dir():
            continue
        for f in d.glob("*.parquet"):
            sess = f.stem
            if sess >= hold:
                continue
            out.setdefault(sess, f)
    return out


def _load_session_bars(path: Path) -> pl.DataFrame:
    """One session's 1-second event bars, sorted, with price/state columns ffilled."""
    df = pl.read_parquet(path).select(EVENT_BARS_COLUMNS).sort("ts")
    return df.with_columns([pl.col(c).forward_fill() for c in _FFILL_COLS])


def _vol20_map(settings: Settings, symbol: str) -> dict[str, float]:
    """session -> vol20 (constant within a session) from the materialized features frame."""
    p = settings.data_dir / "features" / "v1" / f"{symbol.upper()}.parquet"
    if not p.exists():
        return {}
    f = (
        pl.read_parquet(p, columns=["session", "vol20"])
        .group_by("session")
        .agg(pl.col("vol20").first())
    )
    return {s: v for s, v in zip(f["session"], f["vol20"], strict=True) if v is not None}


# ================================================================== downsample
def downsample_bars(df: pl.DataFrame, step_s: int) -> pl.DataFrame:
    """FROZEN semantics. ``df`` is a contiguous 1-second frame (sorted by ts); collapse
    every ``step_s`` consecutive seconds into one bucket with the frozen aggregations.

    Returns one row per bucket (partial trailing bucket kept) with the aggregated source
    columns plus ``bucket``. This is the canonical, human-readable reference; the dataset
    uses a numpy reshape fast-path that ``tests/test_encoder_dataset.py`` cross-checks.
    """
    d = df.with_columns((pl.int_range(pl.len()) // step_s).alias("bucket"))
    aggs = (
        [pl.col(c).sum().alias(c) for c in SUM_COLS]
        + [pl.col(c).last().alias(c) for c in LAST_COLS]
        + [pl.col(c).first().alias(c) for c in FIRST_COLS]
        + [pl.col(c).max().alias(c) for c in MAX_COLS]
        + [pl.col(c).min().alias(c) for c in MIN_COLS]
        + [pl.col(c).mean().alias(c) for c in MEAN_COLS]
    )
    return d.group_by("bucket", maintain_order=True).agg(aggs).sort("bucket")


def _agg_window_np(src: dict[str, np.ndarray], s0: int, nb: int, step: int) -> dict[str, np.ndarray]:
    """Reshape fast-path of ``downsample_bars`` for a full window [s0, s0+nb*step).

    ``src`` maps source-column -> 1s float array. Requires the window fully inside the
    array (caller guarantees). Matches ``downsample_bars`` aggregation-for-aggregation.
    """
    out: dict[str, np.ndarray] = {}
    with np.errstate(invalid="ignore"):
        for col in SUM_COLS:
            out[col] = src[col][s0:s0 + nb * step].reshape(nb, step).sum(axis=1)
        for col in LAST_COLS:
            out[col] = src[col][s0:s0 + nb * step].reshape(nb, step)[:, -1]
        for col in FIRST_COLS:
            out[col] = src[col][s0:s0 + nb * step].reshape(nb, step)[:, 0]
        for col in MAX_COLS:
            out[col] = np.nanmax(src[col][s0:s0 + nb * step].reshape(nb, step), axis=1)
        for col in MIN_COLS:
            out[col] = np.nanmin(src[col][s0:s0 + nb * step].reshape(nb, step), axis=1)
        for col in MEAN_COLS:
            out[col] = np.nanmean(src[col][s0:s0 + nb * step].reshape(nb, step), axis=1)
    return out


def _derive_channels(agg: dict[str, np.ndarray], step_s: int, channels: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Turn aggregated source columns into the (stationary) data matrix + validity mask.

    Returns (data [nb, len(channels)], mask [nb]). Price levels are converted to
    ret_close / hl_range_bps / close_loc; summed flows become per-second rates.
    """
    nb = len(agg["mid"])
    mid = agg["mid"].astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        logmid = np.log(mid)
        ret_close = np.zeros(nb, dtype=np.float64)
        ret_close[1:] = logmid[1:] - logmid[:-1]
        ret_close[~np.isfinite(ret_close)] = 0.0

        hi, lo, cl = agg["px_high"], agg["px_low"], agg["px_close"]
        hl_range_bps = np.where(
            (lo > 0) & np.isfinite(hi) & np.isfinite(lo), 1e4 * np.log(hi / lo), 0.0
        )
        hl_range_bps[~np.isfinite(hl_range_bps)] = 0.0
        rng = hi - lo
        close_loc = np.where(rng > 0, (cl - lo) / rng, 0.5)
        close_loc[~np.isfinite(close_loc)] = 0.5

    derived = {
        "ret_close": ret_close,
        "hl_range_bps": hl_range_bps,
        "close_loc": close_loc,
        "spread_bps_close": agg["spread_bps_close"],
        "spread_bps_mean": agg["spread_bps_mean"],
        "micro_dev_bps": agg["micro_dev_bps"],
        "imb_close": agg["imb_close"],
        "imb_mean": agg["imb_mean"],
        "max_trade_size": agg["max_trade_size"],
        "odd_lot_frac": agg["odd_lot_frac"],
    }
    for c in SUM_COLS:
        derived[c] = agg[c] / float(step_s)  # per-second rate

    data = np.stack([np.asarray(derived[c], dtype=np.float64) for c in channels], axis=1)
    mask = ((agg["n_quotes"] > 0) | (agg["n_trades"] > 0)).astype(np.float32)
    return data, mask


def _session_channel_frame(df: pl.DataFrame, step_s: int, channels: list[str]) -> pl.DataFrame:
    """The full-session derived-channel frame at ``step_s`` resolution (for norm-stats)."""
    src = {c: df[c].to_numpy().astype(np.float64) for c in _all_source_cols()}
    n = df.height
    nb = n // step_s
    if nb == 0:
        return pl.DataFrame({c: [] for c in channels}, schema={c: pl.Float64 for c in channels})
    agg = _agg_window_np(src, 0, nb, step_s)
    data, _ = _derive_channels(agg, step_s, channels)
    return pl.DataFrame({c: data[:, i] for i, c in enumerate(channels)})


def _all_source_cols() -> list[str]:
    return [*SUM_COLS, *LAST_COLS, *FIRST_COLS, *MAX_COLS, *MIN_COLS, *MEAN_COLS]


# ================================================================== norm stats
def build_norm_stats(
    settings: Settings,
    symbols: list[str],
    out_dir: str | Path = "data/encoder/norm_stats",
    trailing: int = 20,
    min_priors: int = 12,
) -> dict[str, int]:
    """Per (symbol, session) median + IQR of each fine channel over the trailing
    ``trailing`` sessions strictly before the session (PIT). Sessions with fewer than
    ``min_priors`` priors are skipped. Nulls excluded; IQR floored at 1e-9.

    Writes ``{out_dir}/{SYM}.parquet`` with columns (session, channel, med, iqr).
    Returns {symbol: rows_written}.
    """
    out_path = Path(out_dir)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    out_path.mkdir(parents=True, exist_ok=True)
    written: dict[str, int] = {}

    for sym in symbols:
        parts = _session_partitions(settings, sym)
        sessions = sorted(parts)
        if any(s >= HOLDOUT_START.isoformat() for s in sessions):
            raise SealViolation("holdout leaked into norm-stats")

        # one 5s channel frame per session (computed once, reused as a trailing prior)
        frames: list[pl.DataFrame] = []
        for s in sessions:
            df = _load_session_bars(parts[s])
            frames.append(_session_channel_frame(df, FINE_STEP_S, FINE_DATA_CHANNELS))

        rows: list[dict] = []
        for i, s in enumerate(sessions):
            lo = max(0, i - trailing)
            priors = frames[lo:i]
            if len(priors) < min_priors:
                continue
            pooled = pl.concat(priors, how="vertical")
            for ch in FINE_DATA_CHANNELS:
                col = pooled[ch].drop_nulls().drop_nans()
                if col.len() == 0:
                    med, iqr = 0.0, 1e-9
                else:
                    med = float(col.median())
                    q75 = float(col.quantile(0.75))
                    q25 = float(col.quantile(0.25))
                    iqr = max(q75 - q25, 1e-9)
                rows.append({"session": s, "channel": ch, "med": med, "iqr": iqr})

        frame = pl.DataFrame(
            rows,
            schema={"session": pl.Utf8, "channel": pl.Utf8, "med": pl.Float64, "iqr": pl.Float64},
        )
        frame.write_parquet(out_path / f"{sym.upper()}.parquet", compression="zstd")
        written[sym.upper()] = frame.height
    return written


def _load_norm_stats(out_dir: Path, symbol: str) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """session -> (med_vec, iqr_vec) aligned to FINE_DATA_CHANNELS."""
    p = out_dir / f"{symbol.upper()}.parquet"
    if not p.exists():
        return {}
    df = pl.read_parquet(p)
    idx = {c: i for i, c in enumerate(FINE_DATA_CHANNELS)}
    stats: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for s, part in df.group_by("session"):
        med = np.zeros(len(FINE_DATA_CHANNELS), dtype=np.float64)
        iqr = np.ones(len(FINE_DATA_CHANNELS), dtype=np.float64)
        for ch, m, q in zip(part["channel"], part["med"], part["iqr"], strict=True):
            k = idx.get(ch)
            if k is not None:
                med[k], iqr[k] = m, q
        stats[s[0] if isinstance(s, tuple) else s] = (med, iqr)
    return stats


# ================================================================== decision index
def _decision_offsets(session: str, open_ns: int, n_sec: int) -> tuple[np.ndarray, np.ndarray]:
    """(offsets_s, ts_ns) for every 60s decision point 11:00-15:30 ET inside the session."""
    d = date.fromisoformat(session)
    offs: list[int] = []
    tss: list[int] = []
    for minute in range(DECISION_START_MIN, DECISION_END_MIN + 1):
        dt = datetime(d.year, d.month, d.day, minute // 60, minute % 60, tzinfo=ET)
        ts = int(dt.astimezone(UTC).timestamp()) * NS_PER_S
        off = (ts - open_ns) // NS_PER_S
        if 0 <= off < n_sec:
            offs.append(int(off))
            tss.append(ts)
    return np.asarray(offs, dtype=np.int64), np.asarray(tss, dtype=np.int64)


def _labels_for_session(
    logmid: np.ndarray, n_sec: int, offsets: np.ndarray, vol20: float | None
) -> dict[str, np.ndarray]:
    """Compute every label column for all decision offsets of one session.

    logmid: log(ffilled mid) over the session, length n_sec. Entry index e = off-1
    (last completed second < t). Windows crossing the close -> NaN.
    """
    npt = len(offsets)
    cols: dict[str, np.ndarray] = {c: np.full(npt, np.nan, dtype=np.float64) for c in LABEL_COLS}
    if vol20 is None or not np.isfinite(vol20) or vol20 <= 0:
        return cols

    for j, off in enumerate(offsets):
        e = max(0, int(off) - 1)
        p0 = logmid[e]
        if not np.isfinite(p0):
            continue

        # forward z-returns
        for h in FWD_HORIZONS:
            tgt = e + h * 60
            if tgt < n_sec and np.isfinite(logmid[tgt]):
                sigma = vol20 * np.sqrt(h / DAY_MINUTES)
                cols[f"l_fwd_{h}m_z"][j] = (logmid[tgt] - p0) / sigma
        # to-close
        h_close = (n_sec - int(off)) / 60.0
        if h_close > 0 and np.isfinite(logmid[n_sec - 1]):
            sigma = vol20 * np.sqrt(h_close / DAY_MINUTES)
            cols["l_fwd_close_z"][j] = (logmid[n_sec - 1] - p0) / sigma

        # excursions + barriers share the forward path
        for h in EXC_HORIZONS:
            end = e + h * 60
            if end >= n_sec:
                continue  # window crosses close
            path = logmid[e + 1:end + 1] - p0
            path = path[np.isfinite(path)]
            if path.size == 0:
                continue
            sigma = vol20 * np.sqrt(h / DAY_MINUTES)
            cols[f"l_mfe_{h}m_z"][j] = max(0.0, float(path.max())) / sigma
            cols[f"l_mae_{h}m_z"][j] = max(0.0, float(-path.min())) / sigma

        for h in BARRIER_H:
            end = e + h * 60
            if end >= n_sec:
                continue
            path = logmid[e + 1:end + 1] - p0
            valid = np.isfinite(path)
            sigma = vol20 * np.sqrt(h / DAY_MINUTES)
            first_up = {a: _first_cross(path, valid, a * sigma, up=True) for a in (0.75, 1.25)}
            first_dn = {b: _first_cross(path, valid, -b * sigma, up=False) for b in (0.75, 1.25)}
            for (a, b) in BARRIER_AB:
                # up-first: +a*sigma STRICTLY before -b*sigma; dn-first is its mirror
                # (-b*sigma STRICTLY before +a*sigma). Both 0 when neither is touched.
                cols[_barrier_name(a, b, h)][j] = 1.0 if first_up[a] < first_dn[b] else 0.0
                cols[_barrier_dn_name(a, b, h)][j] = 1.0 if first_dn[b] < first_up[a] else 0.0

        # H5: realized std of 5s log-mid returns over the NEXT 30 min (null if it
        # crosses the close). Sampled on the same 5s grid the fine stream uses.
        rv_end = e + RV_HORIZON_MIN * 60
        if rv_end < n_sec:
            seg = logmid[e:rv_end + 1:FINE_STEP_S]
            rets = np.diff(seg)
            rets = rets[np.isfinite(rets)]
            if rets.size >= 2:
                cols[RV_LABEL][j] = float(np.std(rets))
    return cols


def _first_cross(path: np.ndarray, valid: np.ndarray, thr: float, up: bool) -> float:
    """Index (as float) of the first bar that crosses the barrier, or +inf if never."""
    hit = valid & (path >= thr) if up else valid & (path <= thr)
    idx = np.argmax(hit)
    return float(idx) if hit[idx] else np.inf


def build_decision_index(
    settings: Settings,
    symbols: list[str],
    out_dir: str | Path = "data/encoder/index",
) -> dict[str, int]:
    """Build the decision-point index with labels for each symbol; write
    ``{out_dir}/{SYM}.parquet``. Returns {symbol: rows_written}.
    """
    out_path = Path(out_dir)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    out_path.mkdir(parents=True, exist_ok=True)
    written: dict[str, int] = {}

    for sym in symbols:
        parts = _session_partitions(settings, sym)
        sessions = sorted(parts)
        if any(s >= HOLDOUT_START.isoformat() for s in sessions):
            raise SealViolation("holdout leaked into index")
        vmap = _vol20_map(settings, sym)

        blocks: list[pl.DataFrame] = []
        for s in sessions:
            df = _load_session_bars(parts[s])
            n_sec = df.height
            open_ns = int(df["ts"][0])
            offsets, tss = _decision_offsets(s, open_ns, n_sec)
            if offsets.size == 0:
                continue
            logmid = np.log(df["mid"].to_numpy().astype(np.float64))
            v = vmap.get(s)
            labels = _labels_for_session(logmid, n_sec, offsets, v)
            block = pl.DataFrame(
                {
                    "symbol": [sym.upper()] * len(offsets),
                    "session": [s] * len(offsets),
                    "ts": tss,
                    "offset_s": offsets,
                    # vol20 rides along (constant per session) for the emission de-norm.
                    "vol20": np.full(len(offsets), v if v is not None else np.nan, dtype=np.float64),
                    **{c: labels[c] for c in LABEL_COLS},
                }
            )
            blocks.append(block)

        frame = pl.concat(blocks, how="vertical") if blocks else pl.DataFrame()
        if frame.height:  # NaN placeholders -> true nulls (window-crosses-close = NULL)
            frame = frame.with_columns(
                [pl.col(c).fill_nan(None) for c in [*LABEL_COLS, "vol20"]]
            )
        frame.write_parquet(out_path / f"{sym.upper()}.parquet", compression="zstd")
        written[sym.upper()] = frame.height
    return written


# ================================================================== dataset
class EncoderDataset(_DatasetBase):
    """Map-style dataset over decision points. See module docstring for item schema.

    Per-day RAM cache (LRU, ``cache_size`` days) holds the ffilled 1s arrays + PIT
    feature matrix so every decision point in a day reuses one parquet read.
    """

    def __init__(
        self,
        settings: Settings,
        symbols: list[str],
        index_dir: str | Path = "data/encoder/index",
        norm_dir: str | Path = "data/encoder/norm_stats",
        features_dir: str | Path = "data/features/v1",
        cache_size: int = 50,
    ) -> None:
        self.settings = settings
        self.symbols = [s.upper() for s in symbols]
        self._sym_idx = {s: i for i, s in enumerate(self.symbols)}
        self.index_dir = _abs(index_dir)
        self.norm_dir = _abs(norm_dir)
        self.features_dir = _abs(features_dir)
        self.cache_size = cache_size

        # decision index (all symbols), meta + label matrix
        blocks = []
        for sym in self.symbols:
            p = self.index_dir / f"{sym}.parquet"
            if p.exists() and pl.read_parquet(p).height:
                blocks.append(pl.read_parquet(p))
        self.index = pl.concat(blocks, how="vertical") if blocks else pl.DataFrame()
        self._meta = list(
            zip(
                self.index["symbol"], self.index["session"],
                self.index["ts"], self.index["offset_s"], strict=True,
            )
        ) if self.index.height else []
        self._labels = (
            self.index.select(LABEL_COLS).to_numpy().astype(np.float32)
            if self.index.height else np.zeros((0, len(LABEL_COLS)), dtype=np.float32)
        )

        self._norm = {s: _load_norm_stats(self.norm_dir, s) for s in self.symbols}
        self._parts = {s: _session_partitions(settings, s) for s in self.symbols}
        self._feat = {s: self._load_features(s) for s in self.symbols}
        self._cache: OrderedDict[tuple[str, str], dict] = OrderedDict()

    # -------------------------------------------------------------- torch API
    def __len__(self) -> int:
        return len(self._meta)

    def __getitem__(self, i: int) -> dict:
        import torch

        symbol, session, ts, offset = self._meta[i]
        day = self._day(symbol, session)
        e = max(0, int(offset) - 1)

        fine = self._build_stream(day, symbol, session, e, FINE_STEP_S, FINE_STEPS,
                                  FINE_DATA_CHANNELS, window_end=e, right_aligned=True)
        sess = self._build_stream(day, symbol, session, e, SESS_STEP_S, SESS_STEPS,
                                  SESS_DATA_CHANNELS, window_end=e, right_aligned=False)
        static = self._static_vector(day, symbol, ts, offset)
        labels = {c: torch.tensor(self._labels[i, k], dtype=torch.float32)
                  for k, c in enumerate(LABEL_COLS)}
        return {
            "fine": torch.from_numpy(fine),
            "sess": torch.from_numpy(sess),
            "static": torch.from_numpy(static),
            "labels": labels,
            "meta": {"symbol": symbol, "session": session, "ts": int(ts)},
        }

    # -------------------------------------------------------------- internals
    def _day(self, symbol: str, session: str) -> dict:
        key = (symbol, session)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        df = _load_session_bars(self._parts[symbol][session])
        payload = {
            "src": {c: df[c].to_numpy().astype(np.float64) for c in _all_source_cols()},
            "n_sec": df.height,
            "open_ns": int(df["ts"][0]),
        }
        # PIT feature matrix for the session (asof by ts)
        feat = self._feat[symbol]
        fsub = feat.filter(pl.col("session") == session).sort("ts")
        payload["feat_ts"] = fsub["ts"].to_numpy() if fsub.height else np.zeros(0, dtype=np.int64)
        payload["feat_mat"] = (
            fsub.select(slow.FEATURE_COLS).to_numpy().astype(np.float32)
            if fsub.height else np.zeros((0, len(slow.FEATURE_COLS)), dtype=np.float32)
        )
        norm = self._norm[symbol].get(session)
        payload["med"], payload["iqr"] = (
            norm if norm is not None
            else (np.zeros(len(FINE_DATA_CHANNELS)), np.ones(len(FINE_DATA_CHANNELS)))
        )
        self._cache[key] = payload
        if len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)
        return payload

    def _build_stream(
        self, day: dict, symbol: str, session: str, e: int, step_s: int, n_steps: int,
        channels: list[str], window_end: int, right_aligned: bool,
    ) -> np.ndarray:
        """Assemble one normalized [n_steps, len(channels)+1] stream (last col = mask)."""
        width = len(channels) + 1
        out = np.zeros((n_steps, width), dtype=np.float32)
        src, n_sec = day["src"], day["n_sec"]
        med_full, iqr_full = day["med"], day["iqr"]
        ch_idx = [FINE_DATA_CHANNELS.index(c) for c in channels]
        med = med_full[ch_idx]
        iqr = iqr_full[ch_idx]

        if right_aligned:
            # newest bar at window_end (inclusive); fixed n_steps*step_s lookback.
            s0 = window_end - n_steps * step_s + 1
            s0 = max(0, s0)
            avail = window_end - s0 + 1
            nb = avail // step_s
            if nb == 0:
                return out
            s0 = window_end + 1 - nb * step_s
            agg = _agg_window_np(src, s0, nb, step_s)
            data, mask = _derive_channels(agg, step_s, channels)
            block = self._normalize(data, mask, med, iqr)
            out[n_steps - nb:] = block  # right-align (newest last)
        else:
            # session-so-far from open; oldest at row 0, pad the tail.
            avail = min(window_end + 1, n_sec)
            nb = min(avail // step_s, n_steps)
            if nb == 0:
                return out
            agg = _agg_window_np(src, 0, nb, step_s)
            data, mask = _derive_channels(agg, step_s, channels)
            block = self._normalize(data, mask, med, iqr)
            out[:nb] = block
        return out

    @staticmethod
    def _normalize(data: np.ndarray, mask: np.ndarray, med: np.ndarray, iqr: np.ndarray) -> np.ndarray:
        with np.errstate(invalid="ignore"):
            norm = (data - med) / iqr
        norm[~np.isfinite(norm)] = 0.0          # nulls -> 0
        norm[mask == 0] = 0.0                    # ...after masking
        return np.concatenate([norm, mask[:, None]], axis=1).astype(np.float32)

    def _static_vector(self, day: dict, symbol: str, ts: int, offset: int) -> np.ndarray:
        """Static channels: PIT slow features + minute-of-session + dow + symbol 1-hot.

        The slow-feature rows are stamped at bar OPEN but contain that bar's CLOSE,
        so a decision at ``ts`` may consume only rows stamped at or before
        ``ts - PRED_STAMP_TO_AVAILABILITY_NS`` -- the same one-bar availability lag
        the A1/M4 overlays apply (features/grid.py contract, SIM_AUDIT_2026-07-21 §3
        defect F2; code review 2026-07-28 B1). The pre-fix asof at ``<= ts`` leaked
        up to ~60 s of future tape into the 37 f_* channels on any decision landing
        on a feature stamp.
        """
        feat_ts, feat_mat = day["feat_ts"], day["feat_mat"]
        nf = len(slow.FEATURE_COLS)
        fvec = np.zeros(nf, dtype=np.float32)
        if feat_ts.size:
            avail_ts = int(ts) - PRED_STAMP_TO_AVAILABILITY_NS
            k = int(np.searchsorted(feat_ts, avail_ts, side="right")) - 1  # asof <= avail
            if k >= 0:
                fvec = np.nan_to_num(feat_mat[k], nan=0.0)
        minute_of_session = (int(offset) // 60) / DAY_MINUTES
        dow = datetime.fromtimestamp(ts / 1e9, tz=ET).weekday() / 5.0
        onehot = np.zeros(len(self.symbols), dtype=np.float32)
        onehot[self._sym_idx[symbol]] = 1.0
        return np.concatenate(
            [fvec, np.array([minute_of_session, dow], dtype=np.float32), onehot]
        ).astype(np.float32)

    def _load_features(self, symbol: str) -> pl.DataFrame:
        p = self.features_dir / f"{symbol}.parquet"
        if not p.exists():
            return pl.DataFrame(schema={"session": pl.Utf8, "ts": pl.Int64,
                                        **{c: pl.Float64 for c in slow.FEATURE_COLS}})
        return pl.read_parquet(p, columns=["session", "ts", *slow.FEATURE_COLS])


def _abs(p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else PROJECT_ROOT / p


# ================================================================== benchmark / cli
def benchmark(ds: EncoderDataset, n: int = 200) -> dict:
    """Build one day's items and time ``n`` __getitem__ calls (single worker)."""
    import time

    if len(ds) == 0:
        return {"items_per_sec": 0.0, "n": 0}
    n = min(n, len(ds))
    _ = ds[0]  # warm the day cache
    t0 = time.perf_counter()
    for i in range(n):
        _ = ds[i]
    dt = time.perf_counter() - t0
    return {"items_per_sec": n / dt if dt > 0 else float("inf"), "n": n, "seconds": dt}


def main() -> None:  # pragma: no cover - acceptance driver
    from enginev51.config import get_settings

    settings = get_settings()
    syms = ["NVDA", "TSLA"]
    ns = build_norm_stats(settings, syms)
    print("norm_stats rows:", ns)
    di = build_decision_index(settings, syms)
    print("decision_index rows:", di)

    ds = EncoderDataset(settings, syms)
    print("dataset items:", len(ds))
    bm = benchmark(ds, 200)
    print("benchmark:", bm)


if __name__ == "__main__":  # pragma: no cover
    main()
