"""M21 earnings-reaction-regime diagnostic (family ``earnings_reaction_regime_v1``).

Registered 2026-07-22 (``research/ledger.jsonl`` M21-earnings-reaction-regime-v1)
BEFORE any outcome was computed. VERDICT CLASS = DIAGNOSTIC (M14/M17 precedent):
NO promotion rule, NO trading path, NO costs. The outcome windows are overnight
(day0+1..+5 / +1..+20) which is DEPLOY-BANNED under the mission; this module only
measures separations with CI receipts. Everything here is frozen by the
registration — nothing may be tuned.

What it does
------------
For each earnings event (from ``data/external/earnings_calendar.parquet``; the
``day0_session`` anchor is pre-computed there from the BMO/AMC acceptance rule —
this module NEVER recomputes it) it forms, strictly from data <= the session
BEFORE day0:

* ``runup60_rel`` — 60-trading-day cumulative return of the name minus the sector
  reference (SMH; fallback equal-weight semi basket), ending at day0-1 -> tercile.
* ``mom_12_1``    — return over sessions [day0-252, day0-21] -> percentile.
* ``streak``      — count of the prior 8 earnings events of that symbol whose day0
  reaction was positive -> hi (>=5) / lo. Events with < 8 priors are excluded from
  streak-conditioned cells but kept in the runup x gap margins.

and, AT/AFTER day0 (the reaction + outcome, not pre-event features):

* day0 ``gap`` = open(day0)/close(day0-1)-1  (SIGN is the registered bucketing var)
* day0 ``c2c`` = close(day0)/close(day0-1)-1 (reported as a margin)
* outcomes = cumulative close-to-close return over day0+1..+5 and day0+1..+20.

Cell grid (en bloc, registered): runup tercile (3) x gap sign (2) x streak (2) x
outcome window (2) = 24, plus the runup x gap margins collapsed over streak. Per
cell: N, n_event_dates, mean, CR0 95% CI clustered by day0_session date (the
``cluster_ci`` imported from ``sched_window`` — cross-sectional same-day reports
share a cluster), median, hit rate; UNDERPOWERED below N_MIN_CELL. Per-year and
per-symbol margin tables round out the atlas.

Data / adjustment (documented divergence from the intraday raw-lake rule)
-------------------------------------------------------------------------
This is a multi-year daily RETURNS diagnostic, so the daily series MUST be
split/dividend adjusted: a raw series books a fake ~-90% "return" on a 10:1 split
day (verified 2026-07-22: the owned ``data/raw/sip/bars1d`` lake is RAW — NVDA
2024-06-10 close 1208.88 -> 121.79). The intraday <1bps bar-vs-tape gate does NOT
apply here (no fills, no tape reconciliation). The bar getter therefore resolves
each symbol's ADJUSTED daily series from ``data/external/m21_bars/{SYM}.parquet``
(adjustment='all', cached for offline reproducibility) or an Alpaca 1Day
adjustment='all' fetch; the raw ``bars1d`` lake is an opt-in, warned fallback only
(``allow_raw_bars1d``) because it corrupts cross-split returns.

Split discipline
-----------------
The estimation frame is every event with day0_session <= VALIDATE end, routed
through ``apply_seal`` (holdout >= 2026-06-01 stripped). TRAIN and VALIDATE are
POOLED for this diagnostic (single estimation pass, no promotion decision, so no
split-gating) — the seal still binds. The tercile / percentile cuts are frozen
from that pooled estimation distribution, written to ``cuts.json`` and reused
verbatim by ``score``. OUTCOME CONTAINMENT (literal-seal standard, matching the
forward module): an event is estimation-eligible ONLY if its ENTIRE longest outcome
window is inside the dev period — day0 + 20 trading sessions (actual session index)
<= VALIDATE end — so no holdout bar is ever read for an in-sample outcome statistic.
Events failing this are excluded with reason ``outcome_crosses_seal`` (counted in
the drop table) and stay scoreable read-only like any forward event. Containment is
judged on the LONGEST window (20), so the two outcome windows share ONE identical
event set (if +5 fits but +20 does not, the event is excluded from both). Forward
events (day0 >= 2026-06-01) NEVER enter estimation; ``score`` evaluates ANY date
read-only against the frozen cuts and bucket base rates.

Outputs (``research/experiments/M21-earnings-regime/``): ``atlas.md`` +
``events.parquet`` (per-event audit) + ``cuts.json`` (tercile/percentile
boundaries + ref choice) + ``base_rates.json`` (bucket base-rate table used by
``score``). ``score`` READS those and writes NOTHING.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
import structlog

from enginev51.protocol import VALIDATE_END, apply_seal, experiments_dir, split_of

# cluster_ci is IMPORTED from the M20 house harness (registered requirement) so the
# CR0 cluster-robust CI is single-sourced and cannot drift between screens.
from enginev51.research_screens.sched_window import cluster_ci

log = structlog.get_logger(__name__)

ET = ZoneInfo("America/New_York")
NO_COST_MODEL = "NO-COST-MODEL (research-only diagnostic; returns are gross, no fills/fees/slippage)"

# --------------------------------------------------------------------------- #
# REGISTERED M21 (2026-07-22) — do not tune
# --------------------------------------------------------------------------- #
RUNUP_D = 60
MOM_WINDOW = (252, 21)  # 12-1: return over sessions [day0-252, day0-21]
STREAK_Q = 8
STREAK_HI = 5
OUTCOME_WINDOWS: dict[str, tuple[int, int]] = {"d1_5": (1, 5), "d1_20": (1, 20)}
MAX_OUTCOME_H = max(hi for _lo, hi in OUTCOME_WINDOWS.values())  # 20: longest window
N_MIN_CELL = 30

# The 26 frozen names from the ledger row (semis 18 + megacap tech 7 + ARM).
UNIVERSE: tuple[str, ...] = (
    "NVDA", "AMD", "MU", "AVGO", "QCOM", "TXN", "INTC", "AMAT", "LRCX", "KLAC",
    "MRVL", "ON", "MCHP", "ADI", "NXPI", "TSM", "ASML", "SMCI",
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NFLX",
    "ARM",
)
SEMIS: tuple[str, ...] = UNIVERSE[:18]  # the 18 semis feed the fallback basket
REF_SYMBOL = "SMH"

# The streak's underlying "positive reaction" variable. BINDING SOURCE = the registered
# ledger row ("prior-8-quarter positive-GAP streak (hi >= 5 / lo)"): the streak counts
# prior events whose day0 GAP was > 0. The frozen ledger text governs over the build-spec
# prose (which read close-to-close); the orchestrator confirmed GAP as the conformant
# reading pre-run (2026-07-22). A one-line flip to "c2c" is all that separates the two
# readings, kept auditable here.
STREAK_BASE = "gap"

TERCILE_LABELS: tuple[str, str, str] = ("T1", "T2", "T3")
# --------------------------------------------------------------------------- #

OUT_SUBDIR = "M21-earnings-regime"

# Injected daily-bar getter: symbol -> adjusted daily frame (session/open/close) or
# None. Tests pass a synthetic getter; the CLI wires the real adjusted-cache/Alpaca
# loader.
BarGetter = Callable[[str], "pl.DataFrame | None"]

EVENTS_SCHEMA: dict[str, pl.DataType] = {
    "event_id": pl.Utf8,
    "symbol": pl.Utf8,
    "day0_session": pl.Utf8,
    "timing": pl.Utf8,
    "fiscal_note": pl.Utf8,
    "split": pl.Utf8,
    "status": pl.Utf8,          # "ok" | drop/exclusion reason
    "ref_source": pl.Utf8,
    "runup60_rel": pl.Float64,
    "runup_pctile": pl.Float64,
    "runup_tercile": pl.Utf8,   # T1|T2|T3|null
    "mom_12_1": pl.Float64,
    "mom_pctile": pl.Float64,
    "gap": pl.Float64,
    "gap_sign": pl.Utf8,        # pos|neg|null
    "c2c": pl.Float64,
    "c2c_sign": pl.Utf8,        # pos|neg|null
    "n_priors": pl.Int64,
    "streak": pl.Int64,
    "streak_level": pl.Utf8,    # hi|lo|na
    "ret_d1_5": pl.Float64,
    "ret_d1_20": pl.Float64,
}


# --------------------------------------------------------------------------- paths


def out_dir_for(out_dir: str | Path | None = None) -> Path:
    """Resolve the M21 output directory (``research/experiments/M21-earnings-regime``)."""
    p = Path(out_dir) if out_dir is not None else (experiments_dir() / OUT_SUBDIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def atlas_md_path(out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / "atlas.md"


def events_path(out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / "events.parquet"


def cuts_path(out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / "cuts.json"


def base_rates_path(out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / "base_rates.json"


# --------------------------------------------------------------------------- bars


def ts_to_session(ts: int) -> str:
    """UTC-epoch-ns daily-bar timestamp -> ET session date (ISO). Alpaca daily bars
    are stamped at ET midnight, so the ET calendar date IS the session."""
    return datetime.fromtimestamp(int(ts) / 1e9, tz=UTC).astimezone(ET).date().isoformat()


def normalize_daily(df: pl.DataFrame) -> pl.DataFrame:
    """Normalize any daily-bar frame to (session, open, close), sorted, one row per
    session. Accepts either an already-normalized frame (a ``session`` string column)
    or a raw lake / Alpaca frame (a ``ts`` epoch-ns column)."""
    if "session" not in df.columns:
        if "ts" not in df.columns:
            raise ValueError("daily frame needs a 'session' or 'ts' column")
        df = df.with_columns(
            pl.col("ts")
            .map_elements(ts_to_session, return_dtype=pl.Utf8)
            .alias("session")
        )
    out = df.select(
        pl.col("session").cast(pl.Utf8),
        pl.col("open").cast(pl.Float64),
        pl.col("close").cast(pl.Float64),
    )
    return out.unique(subset=["session"], keep="last").sort("session")


class DailySeries:
    """One symbol's adjusted daily series indexed for O(1) session lookup."""

    __slots__ = ("sessions", "_idx", "open", "close")

    def __init__(self, df: pl.DataFrame) -> None:
        df = normalize_daily(df)
        self.sessions: list[str] = df["session"].to_list()
        self._idx: dict[str, int] = {s: i for i, s in enumerate(self.sessions)}
        self.open = df["open"].to_numpy()
        self.close = df["close"].to_numpy()

    def idx_of(self, session: str) -> int | None:
        return self._idx.get(session)

    def close_by_session(self) -> dict[str, float]:
        return {s: float(self.close[i]) for i, s in enumerate(self.sessions)}


# --------------------------------------------------------------------------- reference


def build_reference_index(
    get_bars: BarGetter, *, semis: tuple[str, ...] = SEMIS, ref_symbol: str = REF_SYMBOL
) -> tuple[dict[str, float], str]:
    """Sector reference level-by-session and the source tag.

    Primary: the adjusted ``SMH`` close by session. Fallback (registered): an
    equal-weight index built from the semis' own daily returns — index(t) =
    index(t-1) * (1 + mean over names present of close_t/close_{t-1}-1), so a
    cumulative return over any window matches ``level_end/level_start-1``. The
    choice is made ONCE per run and recorded so ``score`` reuses it verbatim.
    """
    ref = get_bars(ref_symbol)
    if ref is not None and ref.height >= RUNUP_D + 2:
        return DailySeries(ref).close_by_session(), ref_symbol

    # ---- equal-weight semi basket ----------------------------------------- #
    rets: dict[str, dict[str, float]] = {}
    all_sessions: set[str] = set()
    for sym in semis:
        df = get_bars(sym)
        if df is None or df.height < 2:
            continue
        s = DailySeries(df)
        all_sessions.update(s.sessions)
        r: dict[str, float] = {}
        for i in range(1, len(s.sessions)):
            prev = float(s.close[i - 1])
            if prev > 0:
                r[s.sessions[i]] = float(s.close[i]) / prev - 1.0
        rets[sym] = r
    grid = sorted(all_sessions)
    index: dict[str, float] = {}
    level = 1.0
    for j, sess in enumerate(grid):
        if j == 0:
            index[sess] = level
            continue
        day_rets = [r[sess] for r in rets.values() if sess in r]
        level *= 1.0 + (float(np.mean(day_rets)) if day_rets else 0.0)
        index[sess] = level
    return index, "ew_semi_basket"


# --------------------------------------------------------------------------- features


def _sign(x: float | None) -> str | None:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    return "pos" if x > 0 else "neg"


def _cumret(close: np.ndarray, i_end: int, i_start: int) -> float | None:
    a, b = float(close[i_end]), float(close[i_start])
    if b <= 0.0:
        return None
    return a / b - 1.0


def compute_reaction_and_outcomes(series: DailySeries, day0: str) -> dict:
    """day0-anchored reaction (gap, c2c) + forward outcomes, from the adjusted series.

    Returns a partial event dict. ``status`` here only flags the HARD bar-availability
    stops (no day0 bar / no prior bar); runup/mom completeness is assessed separately
    so a short-history event still contributes its c2c to later events' streaks.
    """
    out: dict = {
        "gap": None, "gap_sign": None, "c2c": None, "c2c_sign": None,
        "ret_d1_5": None, "ret_d1_20": None, "status": "ok",
    }
    i = series.idx_of(day0)
    if i is None:
        out["status"] = "no_day0_bar"
        return out
    if i < 1:
        out["status"] = "no_prev_bar"
        return out
    prev_close = float(series.close[i - 1])
    if prev_close <= 0.0:
        out["status"] = "no_prev_bar"
        return out
    out["gap"] = float(series.open[i]) / prev_close - 1.0
    out["gap_sign"] = _sign(out["gap"])
    out["c2c"] = float(series.close[i]) / prev_close - 1.0
    out["c2c_sign"] = _sign(out["c2c"])
    for name, (_lo, hi) in OUTCOME_WINDOWS.items():
        j = i + hi
        out[f"ret_{name}"] = _cumret(series.close, j, i) if j < len(series.sessions) else None
    return out


def compute_prefeatures(
    series: DailySeries, day0: str, ref_close: dict[str, float]
) -> dict:
    """Pre-event conditioning features (runup60_rel, mom_12_1), strictly <= day0-1.

    PIT by construction: every index used is <= i-1, so the day0 bar (and anything
    later) is never read. ``runup60_rel`` = name's 60-session cumret ending at day0-1
    minus the reference's over the same two calendar dates.
    """
    out: dict = {"runup60_rel": None, "mom_12_1": None}
    i = series.idx_of(day0)
    if i is None or i < 1:
        return out
    end = i - 1  # day0-1: the last PIT-legal session

    start = end - RUNUP_D
    if start >= 0:
        name_ret = _cumret(series.close, end, start)
        r_end = ref_close.get(series.sessions[end])
        r_start = ref_close.get(series.sessions[start])
        if name_ret is not None and r_end and r_start and r_start > 0:
            out["runup60_rel"] = name_ret - (r_end / r_start - 1.0)

    look, skip = MOM_WINDOW
    m_end, m_start = i - skip, i - look
    if m_start >= 0:
        out["mom_12_1"] = _cumret(series.close, m_end, m_start)
    return out


# --------------------------------------------------------------------------- assembly


def _outcome_contained(series: DailySeries, i: int) -> bool:
    """Literal-seal gate: the WHOLE longest outcome window must land on or before
    VALIDATE end. True iff the session at index ``i + MAX_OUTCOME_H`` exists AND its
    date <= VALIDATE end. A missing +20 session (bars end first) also fails — the
    window cannot be contained-and-measured in the dev period."""
    j = i + MAX_OUTCOME_H
    return j < len(series.sessions) and series.sessions[j] <= VALIDATE_END.isoformat()


def _iso_session(v: object) -> str:
    if isinstance(v, str):
        return v[:10]
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return str(v)[:10]


def _streak_level(n_priors: int, streak: int | None) -> str:
    if streak is None or n_priors < STREAK_Q:
        return "na"
    return "hi" if streak >= STREAK_HI else "lo"


def _reaction_value(row: dict) -> float | None:
    """The streak's per-event reaction variable (frozen STREAK_BASE)."""
    return row["c2c"] if STREAK_BASE == "c2c" else row["gap"]


def _attach_streaks(rows: list[dict]) -> None:
    """In place: n_priors / streak / streak_level from PRIOR events only.

    For each event, priors are the strictly-earlier events of the same symbol with a
    COMPUTABLE reaction (bars present). ``streak`` counts the positive reactions among
    the last STREAK_Q of them; fewer than STREAK_Q computable priors -> level 'na'
    (excluded from streak cells, kept in the runup x gap margins). The current event
    never enters its own history (PIT).
    """
    hist: dict[str, list[int]] = {}  # symbol -> chronological list of prior signs (1/0)
    for r in sorted(rows, key=lambda x: (x["symbol"], x["day0_session"], x["event_id"])):
        prior = hist.setdefault(r["symbol"], [])
        n_priors = len(prior)
        r["n_priors"] = n_priors
        if n_priors >= STREAK_Q:
            r["streak"] = int(sum(prior[-STREAK_Q:]))
        else:
            r["streak"] = None
        r["streak_level"] = _streak_level(n_priors, r["streak"])
        rv = _reaction_value(r)
        if rv is not None and not (isinstance(rv, float) and np.isnan(rv)):
            prior.append(1 if rv > 0 else 0)


def assemble_events(
    calendar: pl.DataFrame,
    get_bars: BarGetter,
    *,
    universe: tuple[str, ...] = UNIVERSE,
    unseal: bool = False,
) -> tuple[pl.DataFrame, str]:
    """Assemble the SEALED per-event estimation audit (features + reaction + outcomes).

    Deterministic (no RNG, explicit final sort). Returns (audit, ref_source). The
    holdout (and every forward event) is stripped by ``apply_seal`` on the
    ``day0_session`` anchor. Terciles/percentiles are NOT assigned here — that happens
    in ``compute_cuts`` on the pooled sealed distribution.
    """
    uni = set(universe)
    series_cache: dict[str, DailySeries | None] = {}

    def series_of(sym: str) -> DailySeries | None:
        if sym not in series_cache:
            df = get_bars(sym)
            series_cache[sym] = DailySeries(df) if df is not None and df.height else None
        return series_cache[sym]

    ref_close, ref_source = build_reference_index(get_bars)

    rows: list[dict] = []
    for row in calendar.iter_rows(named=True):
        sym = str(row["symbol"]).upper()
        if sym not in uni:
            continue
        day0 = _iso_session(row["day0_session"])
        s = series_of(sym)
        rec: dict = {
            "event_id": str(row.get("event_id", f"{sym}-{day0}")),
            "symbol": sym,
            "day0_session": day0,
            "timing": ("" if row.get("timing") is None else str(row.get("timing"))),
            "fiscal_note": ("" if row.get("fiscal_note") is None else str(row.get("fiscal_note"))),
            "ref_source": ref_source,
            "runup60_rel": None, "mom_12_1": None,
            "gap": None, "gap_sign": None, "c2c": None, "c2c_sign": None,
            "ret_d1_5": None, "ret_d1_20": None,
            "n_priors": 0, "streak": None, "streak_level": "na",
        }
        if s is None:
            rec["status"] = "no_bars"
            rows.append(rec)
            continue
        rec.update(compute_reaction_and_outcomes(s, day0))
        if rec["status"] == "ok":
            pre = compute_prefeatures(s, day0, ref_close)
            rec["runup60_rel"] = pre["runup60_rel"]
            rec["mom_12_1"] = pre["mom_12_1"]
            i0 = s.idx_of(day0)
            if pre["runup60_rel"] is None:
                # runup is the sole cell-gating pre-feature; flag its absence loudly.
                rec["status"] = "short_runup_history"
            elif i0 is None or not _outcome_contained(s, i0):
                # literal-seal: the +20 window crosses VALIDATE end -> not an estimation
                # event. Exclude ENTIRELY (both windows nulled) so no holdout-derived
                # return enters estimation stats and the two windows share one event set.
                rec["status"] = "outcome_crosses_seal"
                rec["ret_d1_5"] = None
                rec["ret_d1_20"] = None
        rows.append(rec)

    _attach_streaks(rows)

    # Seal on the day0 anchor (holdout + forward stripped) BEFORE any statistic.
    frame = pl.DataFrame(
        [{**r, "runup_pctile": None, "runup_tercile": None, "mom_pctile": None,
          "split": split_of(r["day0_session"])} for r in rows],
        schema=EVENTS_SCHEMA,
    ).with_columns(pl.col("day0_session").alias("session"))
    sealed = apply_seal(frame, unseal=unseal).drop("session")
    sealed = sealed.sort(["symbol", "day0_session", "event_id"])
    return sealed, ref_source


# --------------------------------------------------------------------------- cuts


def _pctile_of(value: float, sorted_vals: list[float]) -> float | None:
    if value is None or not sorted_vals:
        return None
    return float(np.searchsorted(sorted_vals, value, side="right")) / len(sorted_vals)


def assign_tercile(value: float | None, edges: tuple[float, float]) -> str | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    e1, e2 = edges
    if value <= e1:
        return TERCILE_LABELS[0]
    if value <= e2:
        return TERCILE_LABELS[1]
    return TERCILE_LABELS[2]


def compute_cuts(sealed: pl.DataFrame, ref_source: str) -> dict:
    """Freeze the tercile edges + percentile reference distributions from the pooled
    (TRAIN+VALIDATE) sealed sample. Only status=="ok" events (feature-complete AND
    outcome-contained) define the distribution — crossed/short events are not
    estimation events. Stored to disk and reused verbatim by ``score`` — never
    refit."""
    est = sealed.filter(pl.col("status") == "ok")
    runup = sorted(
        v for v in est["runup60_rel"].to_list() if v is not None and not np.isnan(v)
    )
    mom = sorted(
        v for v in est["mom_12_1"].to_list() if v is not None and not np.isnan(v)
    )
    if len(runup) >= 3:
        e1, e2 = (float(x) for x in np.quantile(runup, [1 / 3, 2 / 3]))
    else:
        e1 = e2 = 0.0
    return {
        "generated_ts": datetime.now(UTC).isoformat(),
        "ref_source": ref_source,
        "n_estimation_events": int(est.height),
        "runup_tercile_edges": [e1, e2],
        "runup_sorted": runup,
        "mom_sorted": mom,
        "constants": {
            "RUNUP_D": RUNUP_D, "MOM_WINDOW": list(MOM_WINDOW), "STREAK_Q": STREAK_Q,
            "STREAK_HI": STREAK_HI, "STREAK_BASE": STREAK_BASE, "N_MIN_CELL": N_MIN_CELL,
        },
        "note": NO_COST_MODEL,
    }


def apply_cuts(sealed: pl.DataFrame, cuts: dict) -> pl.DataFrame:
    """Attach runup_tercile / runup_pctile / mom_pctile from frozen cuts."""
    edges = (cuts["runup_tercile_edges"][0], cuts["runup_tercile_edges"][1])
    runup_sorted = cuts["runup_sorted"]
    mom_sorted = cuts["mom_sorted"]
    terc, rp, mp = [], [], []
    for r in sealed.iter_rows(named=True):
        terc.append(assign_tercile(r["runup60_rel"], edges))
        rp.append(_pctile_of(r["runup60_rel"], runup_sorted) if r["runup60_rel"] is not None else None)
        mp.append(_pctile_of(r["mom_12_1"], mom_sorted) if r["mom_12_1"] is not None else None)
    return sealed.with_columns(
        pl.Series("runup_tercile", terc, dtype=pl.Utf8),
        pl.Series("runup_pctile", rp, dtype=pl.Float64),
        pl.Series("mom_pctile", mp, dtype=pl.Float64),
    )


# --------------------------------------------------------------------------- base rates


def _cell_record(
    kind: str, tercile: str, gap_sign: str, streak_level: str, window: str, sub: pl.DataFrame
) -> dict:
    ret = sub[f"ret_{window}"].to_numpy().astype(float)
    dates = sub["day0_session"].to_numpy()
    bps = ret * 1e4
    mean, lo, hi, n, n_dates = cluster_ci(bps, dates)
    valid = ret[~np.isnan(ret)]
    return {
        "kind": kind,
        "runup_tercile": tercile,
        "gap_sign": gap_sign,
        "streak_level": streak_level,
        "window": window,
        "N": int(n),
        "n_event_dates": int(n_dates),
        "mean_bps": round(mean, 4) if n else None,
        "ci_lo_bps": round(lo, 4) if (n and not np.isnan(lo)) else None,
        "ci_hi_bps": round(hi, 4) if (n and not np.isnan(hi)) else None,
        "median_bps": round(float(np.median(valid)) * 1e4, 4) if valid.size else None,
        "hit_rate": round(float((valid > 0).mean()), 4) if valid.size else None,
        "underpowered": bool(n < N_MIN_CELL),
    }


def compute_base_rates(scored: pl.DataFrame) -> list[dict]:
    """The 24 full cells (tercile x gap x streak x window) plus the runup x gap
    margins (streak collapsed to 'any'). A row enters a window's cell only with a
    non-null runup_tercile, gap_sign and that window's outcome."""
    records: list[dict] = []
    for window in OUTCOME_WINDOWS:
        base = scored.filter(
            (pl.col("status") == "ok")
            & pl.col("runup_tercile").is_not_null()
            & pl.col("gap_sign").is_not_null()
            & pl.col(f"ret_{window}").is_not_null()
        )
        for tercile in TERCILE_LABELS:
            for gap_sign in ("pos", "neg"):
                cut = base.filter(
                    (pl.col("runup_tercile") == tercile) & (pl.col("gap_sign") == gap_sign)
                )
                for streak_level in ("hi", "lo"):
                    sub = cut.filter(pl.col("streak_level") == streak_level)
                    records.append(
                        _cell_record("cell", tercile, gap_sign, streak_level, window, sub)
                    )
                records.append(_cell_record("margin", tercile, gap_sign, "any", window, cut))
    return records


def base_rate_lookup(
    records: list[dict], tercile: str, gap_sign: str, streak_level: str, window: str
) -> dict | None:
    want_kind = "margin" if streak_level in ("na", "any") else "cell"
    want_level = "any" if streak_level in ("na", "any") else streak_level
    for r in records:
        if (
            r["kind"] == want_kind
            and r["runup_tercile"] == tercile
            and r["gap_sign"] == gap_sign
            and r["streak_level"] == want_level
            and r["window"] == window
        ):
            return r
    return None


# --------------------------------------------------------------------------- atlas


def compute_atlas(
    calendar: pl.DataFrame,
    get_bars: BarGetter,
    *,
    out_dir: str | Path | None = None,
    universe: tuple[str, ...] = UNIVERSE,
) -> dict:
    """The single estimation pass: assemble -> seal -> freeze cuts -> base rates ->
    write ``events.parquet`` + ``cuts.json`` + ``base_rates.json`` + ``atlas.md``.
    Returns a summary dict."""
    sealed, ref_source = assemble_events(calendar, get_bars, universe=universe)
    cuts = compute_cuts(sealed, ref_source)
    scored = apply_cuts(sealed, cuts)
    records = compute_base_rates(scored)

    scored.write_parquet(events_path(out_dir))
    cuts_path(out_dir).write_text(json.dumps(cuts, indent=2), encoding="utf-8")
    base_rates_path(out_dir).write_text(
        json.dumps(
            {"generated_ts": datetime.now(UTC).isoformat(), "ref_source": ref_source,
             "note": NO_COST_MODEL, "cells": records},
            indent=2,
        ),
        encoding="utf-8",
    )
    md = _render_atlas_md(scored, cuts, records, ref_source)
    atlas_md_path(out_dir).write_text(md, encoding="utf-8")

    n_cells = sum(1 for r in records if r["kind"] == "cell")
    log.info(
        "m21_atlas", n_events=scored.height, ref_source=ref_source,
        n_ok=int((scored["status"] == "ok").sum()), n_cells=n_cells,
    )
    return {
        "n_events": scored.height,
        "ref_source": ref_source,
        "n_ok": int((scored["status"] == "ok").sum()),
        "n_cells": n_cells,
        "records": records,
        "cuts": cuts,
    }


# --------------------------------------------------------------------------- score


def score_event(
    symbol: str,
    day0: str,
    get_bars: BarGetter,
    calendar: pl.DataFrame,
    *,
    out_dir: str | Path | None = None,
    n_analogs: int = 5,
) -> dict:
    """READ-ONLY differentiator: place one (symbol, date) event in its bucket and
    print the frozen historical base rates. Computes the event's features live from
    bars (any date, incl. forward), maps them through the FROZEN cuts, and writes
    NOTHING. Raises if the atlas artifacts are absent."""
    symbol = symbol.upper()
    day0 = _iso_session(day0)
    cp, bp = cuts_path(out_dir), base_rates_path(out_dir)
    if not cp.exists() or not bp.exists():
        raise FileNotFoundError(
            f"missing atlas artifacts ({cp.name}/{bp.name}) in {out_dir_for(out_dir)}; "
            "run the atlas estimation pass first."
        )
    cuts = json.loads(cp.read_text(encoding="utf-8"))
    records = json.loads(bp.read_text(encoding="utf-8"))["cells"]
    ref_source = cuts["ref_source"]

    df = get_bars(symbol)
    if df is None or df.height == 0:
        raise ValueError(f"no daily bars available for {symbol}")
    series = DailySeries(df)
    # Rebuild the reference with the FROZEN source choice (SMH vs basket), extended to
    # the scored date; the frozen part is the CUTS, not the reference level series.
    if ref_source == REF_SYMBOL:
        ref = get_bars(REF_SYMBOL)
        ref_close = DailySeries(ref).close_by_session() if ref is not None else {}
    else:
        ref_close, _ = build_reference_index(get_bars, ref_symbol="__force_basket__")

    reaction = compute_reaction_and_outcomes(series, day0)
    if reaction["status"] in ("no_day0_bar", "no_prev_bar", "no_bars"):
        raise ValueError(f"{symbol} {day0}: {reaction['status']} — cannot score")
    pre = compute_prefeatures(series, day0, ref_close)

    edges = (cuts["runup_tercile_edges"][0], cuts["runup_tercile_edges"][1])
    tercile = assign_tercile(pre["runup60_rel"], edges)
    runup_pctile = _pctile_of(pre["runup60_rel"], cuts["runup_sorted"])
    mom_pctile = _pctile_of(pre["mom_12_1"], cuts["mom_sorted"])
    gap_sign = reaction["gap_sign"]

    n_priors, streak = _prior_streak(calendar, symbol, day0, get_bars, series_cache={symbol: series})
    streak_level = _streak_level(n_priors, streak)

    base_rates: dict[str, dict | None] = {}
    for window in OUTCOME_WINDOWS:
        if tercile is None or gap_sign is None:
            base_rates[window] = None
        else:
            base_rates[window] = base_rate_lookup(records, tercile, gap_sign, streak_level, window)

    analogs = _nearest_analogs(
        out_dir, tercile, gap_sign, streak_level, runup_pctile, mom_pctile,
        n=n_analogs, exclude=(symbol, day0),
    )
    return {
        "symbol": symbol,
        "day0_session": day0,
        "ref_source": ref_source,
        "runup60_rel": pre["runup60_rel"],
        "runup_pctile": runup_pctile,
        "runup_tercile": tercile,
        "mom_12_1": pre["mom_12_1"],
        "mom_pctile": mom_pctile,
        "gap": reaction["gap"],
        "gap_sign": gap_sign,
        "c2c": reaction["c2c"],
        "c2c_sign": reaction["c2c_sign"],
        "n_priors": n_priors,
        "streak": streak,
        "streak_level": streak_level,
        "bucket_id": _bucket_id(tercile, gap_sign, streak_level),
        "realized": {w: reaction[f"ret_{w}"] for w in OUTCOME_WINDOWS},
        "base_rates": base_rates,
        "analogs": analogs,
        "note": NO_COST_MODEL,
    }


def _bucket_id(tercile: str | None, gap_sign: str | None, streak_level: str) -> str:
    t = tercile or "T?"
    g = "gap+" if gap_sign == "pos" else ("gap-" if gap_sign == "neg" else "gap?")
    sl = streak_level if streak_level in ("hi", "lo") else "streak-na(->margin)"
    return f"{t}|{g}|{sl}"


def _prior_streak(
    calendar: pl.DataFrame,
    symbol: str,
    day0: str,
    get_bars: BarGetter,
    *,
    series_cache: dict[str, DailySeries],
) -> tuple[int, int | None]:
    """(n_priors, streak) for a scored event from the calendar's prior events of that
    symbol — same PIT rule as the atlas (strictly earlier, computable reaction)."""
    def series_of(sym: str) -> DailySeries | None:
        if sym not in series_cache:
            df = get_bars(sym)
            series_cache[sym] = DailySeries(df) if df is not None and df.height else None
        return series_cache[sym]

    priors = calendar.filter(pl.col("symbol").cast(pl.Utf8).str.to_uppercase() == symbol)
    signs: list[int] = []
    events = sorted(
        {_iso_session(r["day0_session"]) for r in priors.iter_rows(named=True)}
    )
    s = series_of(symbol)
    for ev in events:
        if ev >= day0:
            continue
        if s is None:
            continue
        rr = compute_reaction_and_outcomes(s, ev)
        rv = _reaction_value(rr)
        if rv is not None and not (isinstance(rv, float) and np.isnan(rv)):
            signs.append(1 if rv > 0 else 0)
    n_priors = len(signs)
    streak = int(sum(signs[-STREAK_Q:])) if n_priors >= STREAK_Q else None
    return n_priors, streak


def _nearest_analogs(
    out_dir: str | Path | None,
    tercile: str | None,
    gap_sign: str | None,
    streak_level: str,
    runup_pctile: float | None,
    mom_pctile: float | None,
    *,
    n: int,
    exclude: tuple[str, str] | None = None,
) -> list[dict]:
    """Top-n historical estimation events in the same bucket by feature distance
    (normalized-percentile Euclidean on runup_pctile / mom_pctile). Read-only. The
    scored event itself (``exclude`` = (symbol, day0)) is dropped so it never appears
    as its own analog."""
    ep = events_path(out_dir)
    if not ep.exists() or tercile is None or gap_sign is None or runup_pctile is None:
        return []
    ev = pl.read_parquet(ep).filter(
        (pl.col("status") == "ok")
        & (pl.col("runup_tercile") == tercile)
        & (pl.col("gap_sign") == gap_sign)
        & pl.col("runup_pctile").is_not_null()
    )
    if streak_level in ("hi", "lo"):
        ev = ev.filter(pl.col("streak_level") == streak_level)
    if exclude is not None:
        ev = ev.filter(
            ~((pl.col("symbol") == exclude[0]) & (pl.col("day0_session") == exclude[1]))
        )
    if ev.height == 0:
        return []
    out: list[dict] = []
    for r in ev.iter_rows(named=True):
        d = (r["runup_pctile"] - runup_pctile) ** 2
        if mom_pctile is not None and r["mom_pctile"] is not None:
            d += (r["mom_pctile"] - mom_pctile) ** 2
        out.append({
            "event_id": r["event_id"], "symbol": r["symbol"],
            "day0_session": r["day0_session"], "runup60_rel": r["runup60_rel"],
            "mom_12_1": r["mom_12_1"], "gap_sign": r["gap_sign"],
            "streak_level": r["streak_level"], "ret_d1_5": r["ret_d1_5"],
            "ret_d1_20": r["ret_d1_20"], "distance": round(float(d) ** 0.5, 5),
        })
    out.sort(key=lambda x: (x["distance"], x["event_id"]))
    return out[:n]


# --------------------------------------------------------------------------- rendering


def _ascii(df: pl.DataFrame) -> str:
    with pl.Config(
        tbl_formatting="ASCII_MARKDOWN",
        tbl_hide_dataframe_shape=True,
        tbl_hide_column_data_types=True,
        tbl_rows=400,
        tbl_cols=-1,
        tbl_width_chars=280,
    ):
        return str(df)


def _cells_table(records: list[dict], kind: str) -> str:
    rows = [
        {
            # "/" not "|": a literal pipe here would break the markdown table columns.
            "bucket": f"{r['runup_tercile']}/{r['gap_sign']}/{r['streak_level']}",
            "window": r["window"],
            "N": r["N"],
            "n_dates": r["n_event_dates"],
            "mean_bps": r["mean_bps"],
            "ci_lo_bps": r["ci_lo_bps"],
            "ci_hi_bps": r["ci_hi_bps"],
            "median_bps": r["median_bps"],
            "hit_rate": r["hit_rate"],
            "underpowered": r["underpowered"],
        }
        for r in records
        if r["kind"] == kind
    ]
    if not rows:
        return "(none)"
    return _ascii(pl.DataFrame(rows))


def _margin_by(scored: pl.DataFrame, col: str) -> str:
    rows: list[dict] = []
    ok = scored.filter(pl.col("status") == "ok")
    for window in OUTCOME_WINDOWS:
        sub = ok.filter(pl.col(f"ret_{window}").is_not_null())
        g = (
            sub.group_by(col)
            .agg(
                pl.len().alias("N"),
                (pl.col(f"ret_{window}").mean() * 1e4).round(2).alias("mean_bps"),
                (pl.col(f"ret_{window}") > 0).mean().round(4).alias("hit_rate"),
            )
            .sort(col)
        )
        for r in g.iter_rows(named=True):
            rows.append({col: r[col], "window": window, "N": r["N"],
                         "mean_bps": r["mean_bps"], "hit_rate": r["hit_rate"]})
    return _ascii(pl.DataFrame(rows)) if rows else "(none)"


def _drop_table(scored: pl.DataFrame) -> str:
    d = (
        scored.filter(pl.col("status") != "ok")
        .group_by("status")
        .agg(pl.len().alias("n"))
        .sort("status")
    )
    return _ascii(d) if d.height else "(no dropped/excluded events)"


def _render_atlas_md(
    scored: pl.DataFrame, cuts: dict, records: list[dict], ref_source: str
) -> str:
    n_ok = int((scored["status"] == "ok").sum())
    e1, e2 = cuts["runup_tercile_edges"]
    year = scored.with_columns(pl.col("day0_session").str.slice(0, 4).alias("year"))
    lines = [
        "# M21 earnings-reaction-regime diagnostic",
        "",
        f"**{NO_COST_MODEL}**",
        "",
        "Family `earnings_reaction_regime_v1` (registered 2026-07-22). VERDICT CLASS "
        "DIAGNOSTIC: no promotion rule, no trading path. Outcomes are cumulative "
        "close-to-close returns over day0+1..+5 and day0+1..+20; means/CIs in bps "
        "(1 bps = 0.01%). CR0 95% CI clustered by day0_session date (`cluster_ci` "
        "imported from the M20 harness).",
        "",
        f"generated: {datetime.now(UTC).isoformat()}",
        f"estimation events (sealed, day0 <= VALIDATE end): {scored.height}    "
        f"feature-complete (status=ok): {n_ok}",
        f"sector reference: {ref_source}    "
        f"streak base: {STREAK_BASE} (>0 reaction; hi>= {STREAK_HI} of {STREAK_Q} priors)",
        f"runup60_rel tercile edges (frozen): T1<= {e1:.6f} < T2 <= {e2:.6f} < T3",
        "",
        "TRAIN and VALIDATE are POOLED for this diagnostic (single estimation pass, "
        "no promotion decision); the holdout (>= 2026-06-01) and all forward events "
        "are stripped by `apply_seal`. OUTCOME CONTAINMENT (literal-seal): an event "
        "enters estimation only if day0 + 20 trading sessions <= VALIDATE end; events "
        "failing this are excluded with reason `outcome_crosses_seal` (see drop table) "
        "— both windows share one event set. UNDERPOWERED flags cells below "
        f"N={N_MIN_CELL}.",
        "",
        "## Full cells — runup tercile x gap sign x streak x window (24)",
        "",
        _cells_table(records, "cell"),
        "",
        "## Margins — runup tercile x gap sign, streak collapsed (12)",
        "",
        _cells_table(records, "margin"),
        "",
        "## Per-year margin (status=ok events)",
        "",
        _margin_by(year, "year"),
        "",
        "## Per-symbol margin (status=ok events)",
        "",
        _margin_by(scored, "symbol"),
        "",
        "## Dropped / excluded events (never silent)",
        "",
        _drop_table(scored),
        "",
    ]
    return "\n".join(lines)


def _fmt(x: float | None, *, pct: bool = False) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x * 100:+.2f}%" if pct else f"{x:+.4f}"


def _fmt_base(r: dict | None) -> str:
    if r is None:
        return "no matching bucket"
    ci = (
        f"[{r['ci_lo_bps']}, {r['ci_hi_bps']}]"
        if r["ci_lo_bps"] is not None
        else "[n/a] (<2 event-dates)"
    )
    flag = "  UNDERPOWERED" if r["underpowered"] else ""
    return (
        f"N={r['N']} dates={r['n_event_dates']}  mean={r['mean_bps']} bps  CI95={ci}  "
        f"median={r['median_bps']} bps  hit={r['hit_rate']}{flag}"
    )


def format_score(res: dict) -> str:
    """Human-readable ``score`` printout (the CLI echoes this)."""
    lines = [
        f"== M21 earnings-regime score: {res['symbol']} day0={res['day0_session']} ==",
        res["note"],
        f"sector reference: {res['ref_source']}",
        "",
        "features (PIT, <= day0-1):",
        f"  runup60_rel = {_fmt(res['runup60_rel'])}  "
        f"(pctile {_fmt(res['runup_pctile'])}, tercile {res['runup_tercile']})",
        f"  mom_12_1    = {_fmt(res['mom_12_1'])}  (pctile {_fmt(res['mom_pctile'])})",
        f"  streak      = {res['streak']} of last {STREAK_Q} priors positive "
        f"(n_priors={res['n_priors']} -> level {res['streak_level']})",
        "day0 reaction:",
        f"  gap = {_fmt(res['gap'], pct=True)} ({res['gap_sign']})   "
        f"c2c = {_fmt(res['c2c'], pct=True)} ({res['c2c_sign']})",
        "",
        f"BUCKET: {res['bucket_id']}",
        "historical base rates (frozen estimation):",
    ]
    for window in OUTCOME_WINDOWS:
        realized = res["realized"].get(window)
        realized_s = f"    [this event realized: {_fmt(realized, pct=True)}]" if realized is not None else ""
        lines.append(f"  {window}: {_fmt_base(res['base_rates'].get(window))}{realized_s}")
    lines.append("")
    lines.append(f"nearest analogs (same bucket, top {len(res['analogs'])} by feature distance):")
    if not res["analogs"]:
        lines.append("  (none)")
    for a in res["analogs"]:
        lines.append(
            f"  {a['symbol']} {a['day0_session']}  dist={a['distance']}  "
            f"runup_rel={_fmt(a['runup60_rel'])}  d1_5={_fmt(a['ret_d1_5'], pct=True)}  "
            f"d1_20={_fmt(a['ret_d1_20'], pct=True)}"
        )
    return "\n".join(lines)
