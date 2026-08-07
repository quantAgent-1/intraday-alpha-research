"""M20 scheduled-macro-window mid-alpha atlas (family ``sched_window_v1``).

Registered 2026-07-22 (M3_REGISTRATION.md, final section) BEFORE any conditional
mean existed. STAGE 1 ONLY: a conditional MID-ALPHA SCREEN — mid-to-mid, no fills,
no replay, explicitly NOT economics. The sole output is which of the 40 registered
cells (5 macro classes x 4 horizons x 2 condition forms) carry conditional
continuation mid-alpha >= 2x the taker cost floor on TRAIN, and whether TRAIN
passers confirm on the single VALIDATE look.

Everything here is frozen by the registration; nothing in this module may be tuned.
The public entry points are:

* ``compute_cost_floors`` — writes ``cost_floors.json`` FIRST (median quoted spread
  per (class, symbol) + slip + fees, plus the class-level floor). PROTOCOL-critical
  ordering: no return is computed until this file is on disk.
* ``compute_atlas`` — REQUIRES the floors file (raises without it), assembles the
  sealed event frame (``apply_seal`` is the mandatory choke point), computes the
  per-cell day-clustered (CR0) statistics, writes the atlas markdown + audit
  parquet, and on TRAIN writes ``train_pass_list.json``. VALIDATE is refused unless
  that pass list exists and is then computed ONLY for the listed cells.

Price object: owned XNAS bbo-1s mid under the events/context ``quote_at``
COMPLETED-bucket convention (a bucket whose end is > the lookup instant is not
complete and would leak up to 1 s of future; only buckets with end <= lookup
qualify). All timestamps are UTC epoch ns internally; ET wall-clock anchors are
converted via ``data.noii.et_ns`` (America/New_York).
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
import structlog

from enginev51.data.bbo1s import bbo_root, partition_path
from enginev51.data.noii import et_ns
from enginev51.protocol import apply_seal, experiments_dir, split_of

log = structlog.get_logger(__name__)

# --------------------------------------------------------------------------- #
# REGISTERED M20 (2026-07-22) — do not tune
# --------------------------------------------------------------------------- #
W_REACT_S = 300
DECISION_LAG_S = 25
STALENESS_MAX_S = 5
HORIZONS: dict[str, int | None] = {"h30": 1800, "h60": 3600, "h120": 7200, "to1545": None}
EXIT_CAP_ET = time(15, 45)
EARLY_CLOSE_GUARD_S = 1800
SLIP_BPS_RT = 1.0
FEES_BPS_RT = 0.25
N_MIN = 150
SESSIONS_MIN = 40
C2_MIN_PRIORS = 10
UNIVERSE: tuple[str, ...] = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")
# --------------------------------------------------------------------------- #

# NYSE 13:00 ET early closes 2020-2026 — data-hygiene implementation of the
# registered early-close drop rule; verified against published NYSE holiday
# calendars 2026-07-22 (ICE/NYSE press releases: "2020,2021,2022"
# ir.theice.com/press/news-details/2019, "2023,2024,2025"
# ir.theice.com/press/news-details/2022, "2024,2025,2026"
# ir.theice.com/press/news-details/2023). Not a tunable: it corrects the
# bucket-inferred close so post-market 1s BBO on half-days cannot leak into an
# exit (the registered "infer close from the last bbo1s bucket" heuristic breaks
# when the partition carries extended-hours prints; this list is authoritative).
# NEGATIVES verified: no 2020 July half-day (Jul 4 Sat -> Jul 3 full holiday);
# 2021-12-24 is a FULL holiday (Christmas observed), NOT an early close; 2022 has
# no December early close (Christmas observed Mon 2022-12-26); no early close in
# Jan-Jun of any year. 2026-07-03 is EXCLUDED: Independence Day observed = full
# holiday (Jul 4 Sat) per the NYSE full-closure list, so no session exists. The
# 2026 H2 dates sit beyond the sealed window (holdout >= 2026-06-01) — harmless
# completeness for any future forward reuse.
EARLY_CLOSE_DATES: frozenset[str] = frozenset(
    {
        "2020-11-27", "2020-12-24",
        "2021-11-26",
        "2022-11-25",
        "2023-07-03", "2023-11-24",
        "2024-07-03", "2024-11-29", "2024-12-24",
        "2025-07-03", "2025-11-28", "2025-12-24",
        "2026-11-27", "2026-12-24",
    }
)

# Registered class identifiers (M20 A1..A5), fixed reporting order; the calendar's
# ``class`` column must carry these strings. The 5 x 4 x 2 grid is registered en
# bloc, so the atlas always reports all 40 cells (N may be 0 -> UNDERPOWERED).
CLASS_ORDER: tuple[str, ...] = (
    "fomc_stmt",       # A1  14:00 ET
    "fomc_minutes",    # A2  14:00 ET
    "cluster_1000",    # A3  10:00 ET (pooled subtypes)
    "tsy_auction_1300",  # A4  13:02 ET
    "pre_open_0830",   # A5  09:30 ET (open embeds the 08:30 futures reaction)
)
FORMS: tuple[str, ...] = ("C1", "C2")

NS_PER_S = 1_000_000_000
ET = ZoneInfo("America/New_York")
OUT_SUBDIR = "M20-sched-window"
VALIDATE_UNDERPOWERED_N = 30  # structural (~8 FOMC/yr): VALIDATE N < this is flagged

BbboGetter = Callable[[str, str], "pl.DataFrame | None"]

AUDIT_SCHEMA: dict[str, pl.DataType] = {
    "event_key": pl.Int64,     # internal es-row id (unique per event x symbol)
    "release_id": pl.Utf8,
    "class": pl.Utf8,
    "subtype": pl.Utf8,
    "symbol": pl.Utf8,
    "session": pl.Utf8,
    "split": pl.Utf8,
    "horizon": pl.Utf8,
    "form": pl.Utf8,
    "status": pl.Utf8,         # "kept" | drop reason | c2 exclusion reason
    "drop_level": pl.Utf8,     # "event" | "horizon" | null
    "entry_reached": pl.Boolean,
    "anchor_ts": pl.Int64,
    "decision_ts": pl.Int64,
    "exit_ts": pl.Int64,
    "close_ts": pl.Int64,
    "is_early_close": pl.Boolean,
    "anchor_mid": pl.Float64,
    "react_end_mid": pl.Float64,
    "reaction": pl.Float64,
    "entry_mid": pl.Float64,
    "exit_mid": pl.Float64,
    "signed_ret_bps": pl.Float64,
    "staleness_anchor_s": pl.Float64,
    "staleness_react_s": pl.Float64,
    "staleness_entry_s": pl.Float64,
    "staleness_exit_s": pl.Float64,
    "in_c2": pl.Boolean,
    "n_priors": pl.Int64,
    "past_median_absreaction": pl.Float64,
}


# --------------------------------------------------------------------------- paths


def out_dir_for(out_dir: str | Path | None = None) -> Path:
    """Resolve the M20 output directory (``research/experiments/M20-sched-window``)."""
    p = Path(out_dir) if out_dir is not None else (experiments_dir() / OUT_SUBDIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def floors_path(out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / "cost_floors.json"


def pass_list_path(out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / "train_pass_list.json"


def atlas_md_path(split: str, out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / f"atlas_{split}.md"


def atlas_events_path(split: str, out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / f"atlas_{split}_events.parquet"


# --------------------------------------------------------------------------- CR0 CI


def cluster_ci(
    values: np.ndarray, clusters: np.ndarray, *, z: float = 1.96
) -> tuple[float, float, float, int, int]:
    """CR0 cluster-robust 95% CI of the mean, clustered by session.

    se = sqrt( sum_c (S_c - n_c*mean)^2 ) / N, CI = mean +/- z*se, where S_c and
    n_c are the sum and count within cluster c, mean is the pooled mean and N the
    pooled count. Returns (mean, ci_lo, ci_hi, N, n_clusters). NaN values (and
    their clusters) are dropped pairwise. With fewer than 2 clusters the CR0 SE is
    degenerate (identically 0), so the CI is returned as (nan, nan) — an honest
    "cannot bound" rather than a false zero-width interval.
    """
    values = np.asarray(values, dtype=float)
    clusters = np.asarray(clusters)
    if values.shape[0] != clusters.shape[0]:
        raise ValueError("values and clusters must be the same length")
    mask = ~np.isnan(values)
    values = values[mask]
    clusters = clusters[mask]
    n = int(values.shape[0])
    if n == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    mean = float(values.mean())
    uniq = np.unique(clusters)
    n_clusters = int(uniq.shape[0])
    if n_clusters < 2 or n < 2:
        return mean, float("nan"), float("nan"), n, n_clusters
    ss = 0.0
    for c in uniq:
        v = values[clusters == c]
        ss += (float(v.sum()) - v.shape[0] * mean) ** 2
    se = (ss ** 0.5) / n
    return mean, mean - z * se, mean + z * se, n, n_clusters


# --------------------------------------------------------------------------- bbo loader


@lru_cache(maxsize=12)
def _read_month(path_str: str) -> pl.DataFrame:
    return pl.read_parquet(path_str)


def load_bbo_for_session(
    symbol: str, session_iso: str, *, out_dir: str | Path | None = None
) -> pl.DataFrame | None:
    """One (symbol, session)'s 1s BBO rows for the atlas, ts-sorted.

    Reads the monthly partition written by ``data.bbo1s.download_bbo1s`` and slices
    to the ET calendar day. UNLIKE ``bbo1s.load_bbo_session`` it KEEPS locked/crossed
    rows (bid >= ask) — the harness must be able to SEE a crossed used bucket to drop
    it with reason ``crossed_quote`` rather than silently skipping to an older quote.
    Only genuinely broken rows (bid <= 0 or ask <= 0) are dropped. Pre-market and
    post-market snapshots are retained (the 09:30 A5 anchor needs the 09:29:59
    pre-open bucket; the RTH-close clamp for early-close inference lives in
    ``measure_event_symbol``). ``None`` when the partition is absent or the slice
    is empty.
    """
    root = bbo_root(out_dir)
    path = partition_path(root, symbol, session_iso[:7])
    if not path.exists():
        return None
    df = _read_month(str(path))
    if df.height == 0:
        return None
    lo = et_ns(session_iso, 0, 0, 0)
    hi = et_ns((date.fromisoformat(session_iso) + timedelta(days=1)).isoformat(), 0, 0, 0)
    df = df.filter(
        (pl.col("ts") >= lo)
        & (pl.col("ts") < hi)
        & (pl.col("bid") > 0.0)
        & (pl.col("ask") > 0.0)
    ).sort("ts")
    return df if df.height else None


def make_bbo_getter(*, out_dir: str | Path | None = None) -> BbboGetter:
    """A ``(symbol, session_iso) -> frame|None`` loader over the real bbo-1s lake
    (month partitions are LRU-cached in ``_read_month``). Injected by the CLI; tests
    pass their own synthetic getter instead."""

    def getter(symbol: str, session_iso: str) -> pl.DataFrame | None:
        return load_bbo_for_session(symbol, session_iso, out_dir=out_dir)

    return getter


# --------------------------------------------------------------------------- lookups


def _completed_lookup(
    ts: np.ndarray, bid: np.ndarray, ask: np.ndarray, lookup_ts: int
) -> tuple[float, int, bool] | None:
    """(mid, staleness_ns, crossed) of the last COMPLETED bucket at ``lookup_ts``.

    Mirrors ``events.context.SessionContext.quote_at``: a bucket at start ``t`` covers
    [t, t+1s) and is complete only when t+1s <= lookup_ts, i.e. t <= lookup_ts - 1s.
    ``staleness_ns = lookup_ts - (t + 1s)`` (>= 0). ``crossed`` iff bid >= ask at that
    bucket. ``None`` when no bucket qualifies (treated by callers as a maximally-stale
    miss on the relevant lookup).
    """
    j = int(np.searchsorted(ts, lookup_ts - NS_PER_S, side="right")) - 1
    if j < 0:
        return None
    b = float(bid[j])
    a = float(ask[j])
    bucket_end = int(ts[j]) + NS_PER_S
    return (a + b) / 2.0, int(lookup_ts) - bucket_end, b >= a


def _s(ns: int | None) -> float | None:
    return None if ns is None else ns / NS_PER_S


# --------------------------------------------------------------------------- measurement


def measure_event_symbol(
    bbo: pl.DataFrame | None, *, anchor_ts: int, session: str
) -> dict:
    """Event-level (one event x one symbol) measurement under the frozen M20 rules.

    Returns a dict with anchor/react/reaction/entry mids and staleness, an
    ``event_drop`` reason (or None), the inferred RTH close + early-close flag, and a
    per-horizon ``hz`` map of {exit_ts, exit_mid, staleness_exit_s, signed_ret_bps,
    drop}. When a crossed used bucket coincides with a stale one, ``crossed_quote``
    takes precedence.
    """
    decision_ts = int(anchor_ts) + (W_REACT_S + DECISION_LAG_S) * NS_PER_S
    out: dict = {
        "anchor_ts": int(anchor_ts),
        "decision_ts": decision_ts,
        "close_ts": None,
        "is_early_close": False,
        "anchor_mid": None,
        "react_end_mid": None,
        "reaction": None,
        "entry_mid": None,
        "staleness_anchor_s": None,
        "staleness_react_s": None,
        "staleness_entry_s": None,
        "event_drop": None,
        "hz": {},
    }
    if bbo is None or bbo.height == 0:
        out["event_drop"] = "stale_anchor"
        return out

    ts = bbo["ts"].to_numpy()
    bid = bbo["bid"].to_numpy()
    ask = bbo["ask"].to_numpy()

    # RTH close reference. A LISTED NYSE half-day forces the authoritative 13:00 ET
    # close (post-market 1s BBO in the partition would otherwise defeat inference —
    # the registered heuristic's blind spot). Otherwise infer from the last bucket
    # ending <= 16:00 ET; an inferred close <= 14:00 still counts as early (covers
    # any half-day not on the list / synthetic RTH-only tapes).
    sixteen = et_ns(session, 16, 0)
    before = np.nonzero(ts < sixteen)[0]
    last_idx = int(before[-1]) if before.size else int(ts.shape[0] - 1)
    inferred_close_ts = int(ts[last_idx]) + NS_PER_S
    if session in EARLY_CLOSE_DATES:
        close_ts = et_ns(session, 13, 0)
        is_early = True
    else:
        close_ts = inferred_close_ts
        is_early = inferred_close_ts <= et_ns(session, 14, 0)
    out["close_ts"] = close_ts
    out["is_early_close"] = bool(is_early)

    if is_early and decision_ts >= close_ts - EARLY_CLOSE_GUARD_S * NS_PER_S:
        out["event_drop"] = "early_close"
        return out

    # anchor
    res = _completed_lookup(ts, bid, ask, anchor_ts)
    if res is None:
        out["event_drop"] = "stale_anchor"
        return out
    amid, astale, across = res
    out["staleness_anchor_s"] = _s(astale)
    if across:
        out["event_drop"] = "crossed_quote"
        return out
    if astale > STALENESS_MAX_S * NS_PER_S:
        out["event_drop"] = "stale_anchor"
        return out
    out["anchor_mid"] = amid

    # reaction endpoint
    res = _completed_lookup(ts, bid, ask, anchor_ts + W_REACT_S * NS_PER_S)
    if res is None:
        out["event_drop"] = "stale_react"
        return out
    rmid, rstale, rcross = res
    out["staleness_react_s"] = _s(rstale)
    if rcross:
        out["event_drop"] = "crossed_quote"
        return out
    if rstale > STALENESS_MAX_S * NS_PER_S:
        out["event_drop"] = "stale_react"
        return out
    out["react_end_mid"] = rmid

    reaction = rmid / amid - 1.0
    out["reaction"] = reaction
    if reaction == 0.0:
        out["event_drop"] = "zero_reaction"
        return out

    # entry at decision
    res = _completed_lookup(ts, bid, ask, decision_ts)
    if res is None:
        out["event_drop"] = "stale_entry"
        return out
    emid, estale, ecross = res
    out["staleness_entry_s"] = _s(estale)
    if ecross:
        out["event_drop"] = "crossed_quote"
        return out
    if estale > STALENESS_MAX_S * NS_PER_S:
        out["event_drop"] = "stale_entry"
        return out
    out["entry_mid"] = emid

    # per-horizon exits
    cap = et_ns(session, EXIT_CAP_ET.hour, EXIT_CAP_ET.minute)
    sign = 1.0 if reaction > 0 else -1.0
    for hz, h_s in HORIZONS.items():
        exit_ts = cap if h_s is None else min(decision_ts + h_s * NS_PER_S, cap)
        rec = {
            "exit_ts": int(exit_ts),
            "exit_mid": None,
            "staleness_exit_s": None,
            "signed_ret_bps": None,
            "drop": None,
        }
        # On an early-close session, any horizon whose exit lands within the last
        # minute of the (corrected) close is dropped rather than read — this stops a
        # kept morning event from booking a post-market mid at a 15:45 exit while its
        # short horizons still resolve inside RTH.
        if is_early and exit_ts > close_ts - 60 * NS_PER_S:
            rec["drop"] = "early_close"
            out["hz"][hz] = rec
            continue
        if exit_ts <= decision_ts:
            rec["drop"] = "no_room"
            out["hz"][hz] = rec
            continue
        xres = _completed_lookup(ts, bid, ask, exit_ts)
        if xres is None:
            rec["drop"] = "stale_exit"
            out["hz"][hz] = rec
            continue
        xmid, xstale, xcross = xres
        rec["staleness_exit_s"] = _s(xstale)
        if xcross:
            rec["drop"] = "crossed_quote"
            out["hz"][hz] = rec
            continue
        if xstale > STALENESS_MAX_S * NS_PER_S:
            rec["drop"] = "stale_exit"
            out["hz"][hz] = rec
            continue
        rec["exit_mid"] = xmid
        rec["signed_ret_bps"] = sign * (xmid / emid - 1.0) * 1e4
        out["hz"][hz] = rec
    return out


# --------------------------------------------------------------------------- calendar


def _norm_session(v: object) -> str:
    if isinstance(v, str):
        return v[:10]
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return str(v)[:10]


def _anchor_utc_ns(v: object, session: str) -> int:
    """UTC-ns of the event anchor. ``anchor_ts_et`` is interpreted as an ET
    wall-clock instant: tz-aware -> converted to ET; naive datetime/"HH:MM:SS" ->
    assumed ET; an integer is treated as an already-UTC-ns passthrough. The date is
    always taken from ``session`` (so a stray date component in the timestamp cannot
    move the event), the time-of-day from the value, combined via ``et_ns``.
    """
    if isinstance(v, bool):
        raise TypeError("anchor_ts_et must not be a bool")
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, datetime):
        dt = v.astimezone(ET) if v.tzinfo is not None else v.replace(tzinfo=ET)
        return et_ns(session, dt.hour, dt.minute, dt.second)
    if isinstance(v, time):
        return et_ns(session, v.hour, v.minute, v.second)
    if isinstance(v, str):
        s = v.strip()
        if len(s) > 10 and ("T" in s or " " in s):
            dt = datetime.fromisoformat(s)
            dt = dt.astimezone(ET) if dt.tzinfo is not None else dt.replace(tzinfo=ET)
            return et_ns(session, dt.hour, dt.minute, dt.second)
        parts = s.split(":")
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        sec = int(float(parts[2])) if len(parts) > 2 else 0
        return et_ns(session, h, m, sec)
    raise TypeError(f"unsupported anchor_ts_et type: {type(v)!r}")


def load_macro_calendar(path: str | Path) -> pl.DataFrame:
    """Load the anchor calendar parquet (columns release_id/class/subtype/
    session_date/sched_ts_et/anchor_ts_et/source). A thin reader; the QA gates on
    the calendar itself live with its builder (a parallel teammate deliverable)."""
    return pl.read_parquet(path)


# --------------------------------------------------------------------------- C2 gate


def c2_membership(es: pl.DataFrame) -> pl.DataFrame:
    """Attach the expanding PAST-ONLY magnitude gate within (class, symbol).

    For each event-symbol with a defined ``reaction``, priors are the STRICTLY
    earlier events (by ``anchor_ts``, ties excluded) in the same (class, symbol);
    ``in_c2`` iff n_priors >= C2_MIN_PRIORS AND |reaction| >= median(|reaction| of
    priors). The current event never enters its own median (PIT by construction).
    Adds columns in_c2, c2_reason ("c2_priors" | "c2_magnitude" | null), n_priors,
    past_median. Rows with null reaction get in_c2=False (they are event-dropped).
    """
    n = es.height
    cls = es["class"].to_list()
    sym = es["symbol"].to_list()
    anchor = es["anchor_ts"].to_numpy()
    absr = np.abs(es["reaction"].to_numpy().astype(float))

    in_c2 = [False] * n
    c2_reason: list[str | None] = [None] * n
    n_priors = [0] * n
    past_med: list[float | None] = [None] * n

    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for i in range(n):
        if not np.isnan(absr[i]):
            groups[(cls[i], sym[i])].append(i)

    for idxs in groups.values():
        idxs.sort(key=lambda i: int(anchor[i]))
        a = anchor[idxs]
        r = absr[idxs]
        for pos, i in enumerate(idxs):
            lo = int(np.searchsorted(a, a[pos], side="left"))  # strictly-earlier count
            n_priors[i] = lo
            if lo < C2_MIN_PRIORS:
                c2_reason[i] = "c2_priors"
                continue
            med = float(np.median(r[:lo]))
            past_med[i] = med
            if r[pos] >= med:
                in_c2[i] = True
            else:
                c2_reason[i] = "c2_magnitude"

    return es.with_columns(
        pl.Series("in_c2", in_c2, dtype=pl.Boolean),
        pl.Series("c2_reason", c2_reason, dtype=pl.Utf8),
        pl.Series("n_priors", n_priors, dtype=pl.Int64),
        pl.Series("past_median", past_med, dtype=pl.Float64),
    )


# --------------------------------------------------------------------------- assembly


def _audit_row(e: dict, key: int, hz: str, form: str, cm: dict, split: str) -> dict:
    """Flatten one (event-symbol, horizon, form) into an AUDIT_SCHEMA row."""
    event_drop = e["event_drop"]
    hr = e["hz"].get(hz)
    exit_ts = None
    exit_mid = None
    stale_exit = None
    signed = None
    if event_drop is not None:
        status = event_drop
        drop_level = "event"
    else:
        exit_ts = hr["exit_ts"]
        exit_mid = hr["exit_mid"]
        stale_exit = hr["staleness_exit_s"]
        if hr["drop"] is not None:
            status = hr["drop"]
            drop_level = "horizon"
        elif form == "C1":
            status = "kept"
            drop_level = None
            signed = hr["signed_ret_bps"]
        elif cm["in_c2"]:
            status = "kept"
            drop_level = None
            signed = hr["signed_ret_bps"]
        else:
            status = cm["c2_reason"]
            drop_level = None
    return {
        "event_key": key,
        "release_id": e["release_id"],
        "class": e["class"],
        "subtype": e["subtype"],
        "symbol": e["symbol"],
        "session": e["session"],
        "split": split,
        "horizon": hz,
        "form": form,
        "status": status,
        "drop_level": drop_level,
        "entry_reached": event_drop is None,
        "anchor_ts": e["anchor_ts"],
        "decision_ts": e["decision_ts"],
        "exit_ts": exit_ts,
        "close_ts": e["close_ts"],
        "is_early_close": e["is_early_close"],
        "anchor_mid": e["anchor_mid"],
        "react_end_mid": e["react_end_mid"],
        "reaction": e["reaction"],
        "entry_mid": e["entry_mid"],
        "exit_mid": exit_mid,
        "signed_ret_bps": signed,
        "staleness_anchor_s": e["staleness_anchor_s"],
        "staleness_react_s": e["staleness_react_s"],
        "staleness_entry_s": e["staleness_entry_s"],
        "staleness_exit_s": stale_exit,
        "in_c2": bool(cm["in_c2"]),
        "n_priors": int(cm["n_priors"]),
        "past_median_absreaction": cm["past_median"],
    }


def assemble(
    calendar: pl.DataFrame,
    get_bbo: BbboGetter,
    *,
    universe: tuple[str, ...] = UNIVERSE,
    unseal: bool = False,
) -> pl.DataFrame:
    """Assemble the sealed per-(event x symbol x horizon x form) audit frame.

    Measures every (calendar event, symbol), routes the event-level frame through
    ``apply_seal`` (the mandatory holdout choke point — forward sessions fall out by
    the same >= HOLDOUT_START bound), attaches the PAST-ONLY C2 gate on the sealed
    history, and expands to the two condition forms x four horizons. Deterministic:
    no RNG, explicit final sort.
    """
    es: list[dict] = []
    for row in calendar.iter_rows(named=True):
        session = _norm_session(row["session_date"])
        anchor_ts = _anchor_utc_ns(row["anchor_ts_et"], session)
        subtype = row.get("subtype")
        for sym in universe:
            m = measure_event_symbol(get_bbo(sym, session), anchor_ts=anchor_ts, session=session)
            m["release_id"] = str(row["release_id"])
            m["class"] = str(row["class"])
            m["subtype"] = "" if subtype is None else str(subtype)
            m["symbol"] = sym
            m["session"] = session
            es.append(m)

    # apply_seal on the assembled EVENT frame (holdout + forward stripped) BEFORE
    # any statistic; the surviving _ri set governs the expansion.
    es_df = pl.DataFrame(
        {
            "_ri": list(range(len(es))),
            "class": [e["class"] for e in es],
            "symbol": [e["symbol"] for e in es],
            "session": [e["session"] for e in es],
            "anchor_ts": [e["anchor_ts"] for e in es],
            "reaction": [e["reaction"] for e in es],
        },
        schema={
            "_ri": pl.Int64,
            "class": pl.Utf8,
            "symbol": pl.Utf8,
            "session": pl.Utf8,
            "anchor_ts": pl.Int64,
            "reaction": pl.Float64,
        },
    )
    sealed = c2_membership(apply_seal(es_df, unseal=unseal))
    cm_by_ri = {r["_ri"]: r for r in sealed.iter_rows(named=True)}

    rows: list[dict] = []
    for i, e in enumerate(es):
        cm = cm_by_ri.get(i)
        if cm is None:  # stripped by the seal
            continue
        split = split_of(e["session"])
        for hz in HORIZONS:
            for form in FORMS:
                rows.append(_audit_row(e, i, hz, form, cm, split))

    audit = (
        pl.DataFrame(rows, schema=AUDIT_SCHEMA)
        if rows
        else pl.DataFrame(schema=AUDIT_SCHEMA)
    )
    return audit.sort(
        ["session", "class", "subtype", "symbol", "release_id", "horizon", "form", "event_key"]
    )


# --------------------------------------------------------------------------- cost floors


def compute_cost_floors(
    calendar: pl.DataFrame,
    get_bbo: BbboGetter,
    *,
    out_dir: str | Path | None = None,
    universe: tuple[str, ...] = UNIVERSE,
) -> dict:
    """Compute and WRITE ``cost_floors.json`` FIRST (protocol ordering).

    For every TRAIN (event, symbol) it collects the per-second quoted spread (bps of
    mid) from non-crossed buckets inside [decision_ts - 60 s, decision_ts + 60 s];
    the per-(class, symbol) floor is median(spread) + SLIP_BPS_RT + FEES_BPS_RT, and
    the class-level floor (the screen bar) is the median of those across the 5 names.
    """
    win = 60 * NS_PER_S
    spreads: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in calendar.iter_rows(named=True):
        session = _norm_session(row["session_date"])
        if split_of(session) != "train":
            continue
        anchor_ts = _anchor_utc_ns(row["anchor_ts_et"], session)
        decision_ts = anchor_ts + (W_REACT_S + DECISION_LAG_S) * NS_PER_S
        cls = str(row["class"])
        for sym in universe:
            bbo = get_bbo(sym, session)
            if bbo is None or bbo.height == 0:
                continue
            ts = bbo["ts"].to_numpy()
            bid = bbo["bid"].to_numpy()
            ask = bbo["ask"].to_numpy()
            m = (ts >= decision_ts - win) & (ts <= decision_ts + win) & (ask > bid)
            if not m.any():
                continue
            a = ask[m].astype(float)
            b = bid[m].astype(float)
            spreads[(cls, sym)].extend(((a - b) / ((a + b) / 2.0) * 1e4).tolist())

    per_symbol: dict[str, dict] = {}
    class_floor: dict[str, float | None] = {}
    for cls in CLASS_ORDER:
        per_symbol[cls] = {}
        sym_floors: list[float] = []
        for sym in universe:
            vals = spreads.get((cls, sym))
            if not vals:
                continue
            med = float(np.median(vals))
            floor = med + SLIP_BPS_RT + FEES_BPS_RT
            per_symbol[cls][sym] = {
                "median_spread_bps": round(med, 4),
                "floor_bps": round(floor, 4),
                "n_spreads": len(vals),
            }
            sym_floors.append(floor)
        class_floor[cls] = round(float(np.median(sym_floors)), 4) if sym_floors else None

    out = {
        "generated_ts": datetime.now(UTC).isoformat(),
        "params": {
            "window_s": 60,
            "slip_bps_rt": SLIP_BPS_RT,
            "fees_bps_rt": FEES_BPS_RT,
            "split": "train",
        },
        "per_symbol": per_symbol,
        "class_floor_bps": class_floor,
    }
    fp = floors_path(out_dir)
    fp.write_text(json.dumps(out, indent=2), encoding="utf-8")
    log.info("m20_cost_floors_written", path=str(fp), class_floor_bps=class_floor)
    return out


# --------------------------------------------------------------------------- atlas


def _cell_stats(
    cid: str,
    cls: str,
    form: str,
    hz: str,
    kept: pl.DataFrame,
    floor: float | None,
    z: float,
    split: str,
    train_means: dict,
) -> dict:
    vals = kept["signed_ret_bps"].to_numpy() if kept.height else np.array([], dtype=float)
    sess = kept["session"].to_numpy() if kept.height else np.array([], dtype=object)
    mean, lo, hi, n, n_sessions = cluster_ci(vals, sess, z=z)
    bar = 2.0 * floor if floor is not None else None
    underpowered = (n < N_MIN) or (n_sessions < SESSIONS_MIN)
    screen_pass = bool(
        floor is not None
        and n >= N_MIN
        and n_sessions >= SESSIONS_MIN
        and (mean >= bar)
        and (lo > 0)
    )
    per_symbol: dict[str, float] = {}
    if kept.height:
        g = kept.group_by("symbol").agg(pl.col("signed_ret_bps").mean().alias("m"))
        for r in g.sort("symbol").iter_rows(named=True):
            per_symbol[r["symbol"]] = round(float(r["m"]), 3)
    d = {
        "cell_id": cid,
        "class": cls,
        "form": form,
        "horizon": hz,
        "N": n,
        "n_sessions": n_sessions,
        "mean_bps": round(mean, 4) if n else None,
        "ci_lo": round(lo, 4) if (n and not np.isnan(lo)) else None,
        "ci_hi": round(hi, 4) if (n and not np.isnan(hi)) else None,
        "floor_bps": floor,
        "bar_2x_floor": round(bar, 4) if bar is not None else None,
        "screen_pass": screen_pass,
        "underpowered": bool(underpowered),
        "per_symbol_mean": per_symbol,
    }
    if split == "validate":
        tmean = train_means.get(cid)
        same_sign = bool(tmean is not None and n > 0 and np.sign(mean) == np.sign(tmean))
        not_below_zero = bool(n > 0 and not np.isnan(hi) and hi > 0)
        d["validate_confirm"] = bool(same_sign and not_below_zero)
        d["validate_underpowered"] = bool(n < VALIDATE_UNDERPOWERED_N)
    return d


def compute_atlas(
    calendar: pl.DataFrame,
    get_bbo: BbboGetter,
    *,
    split: str,
    out_dir: str | Path | None = None,
    universe: tuple[str, ...] = UNIVERSE,
    z: float = 1.96,
) -> dict:
    """Compute the per-cell atlas for ``split`` and write its outputs.

    REQUIRES ``cost_floors.json`` on disk (raises otherwise — the floor-before-means
    ordering guard). For ``split == "validate"`` it also REQUIRES
    ``train_pass_list.json`` and computes ONLY the listed cells. Writes
    ``atlas_{split}.md`` + ``atlas_{split}_events.parquet``, and on TRAIN writes
    ``train_pass_list.json``. Returns a summary dict.
    """
    fp = floors_path(out_dir)
    if not fp.exists():
        raise FileNotFoundError(
            f"cost_floors.json missing at {fp}; compute_cost_floors must run FIRST "
            "(PROTOCOL: floors are frozen BEFORE any conditional mean exists)."
        )
    floors = json.loads(fp.read_text(encoding="utf-8"))
    class_floor: dict = floors.get("class_floor_bps", {})

    passing: set[str] | None = None
    train_means: dict = {}
    if split == "validate":
        pp = pass_list_path(out_dir)
        if not pp.exists():
            raise FileNotFoundError(
                f"train_pass_list.json missing at {pp}; VALIDATE is gated on the TRAIN "
                "screen-pass list (run the TRAIN atlas first). --include-validate refused."
            )
        pj = json.loads(pp.read_text(encoding="utf-8"))
        passing = set(pj.get("cells", []))
        train_means = pj.get("train_means", {})

    audit = assemble(calendar, get_bbo, universe=universe)
    audit_split = audit.filter(pl.col("split") == split)

    cells: list[dict] = []
    for cls in CLASS_ORDER:
        floor = class_floor.get(cls)
        for form in FORMS:
            for hz in HORIZONS:
                cid = f"{cls}|{form}|{hz}"
                if passing is not None and cid not in passing:
                    continue
                kept = audit_split.filter(
                    (pl.col("class") == cls)
                    & (pl.col("form") == form)
                    & (pl.col("horizon") == hz)
                    & (pl.col("status") == "kept")
                )
                cells.append(
                    _cell_stats(cid, cls, form, hz, kept, floor, z, split, train_means)
                )

    audit_split.write_parquet(atlas_events_path(split, out_dir))
    md = _render_md(split, cells, floors, audit_split)
    atlas_md_path(split, out_dir).write_text(md, encoding="utf-8")

    result = {
        "split": split,
        "n_cells": len(cells),
        "n_events_rows": audit_split.height,
        "cells": cells,
    }
    if split == "train":
        passers = [c["cell_id"] for c in cells if c["screen_pass"]]
        pj = {
            "generated_ts": datetime.now(UTC).isoformat(),
            "split": "train",
            "n_passing": len(passers),
            "cells": passers,
            "train_means": {c["cell_id"]: c["mean_bps"] for c in cells if c["screen_pass"]},
        }
        pass_list_path(out_dir).write_text(json.dumps(pj, indent=2), encoding="utf-8")
        result["n_passing"] = len(passers)
        result["passing_cells"] = passers
        log.info("m20_train_atlas", n_passing=len(passers), passers=passers)
    return result


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


def _drop_tables(audit_split: pl.DataFrame) -> tuple[str, str]:
    """(event-level, horizon-level) drop tables. Event-level reasons are counted
    once per event x symbol (deduped over horizons); horizon-level per event x
    symbol x horizon."""
    c1 = audit_split.filter(pl.col("form") == "C1")
    ev = (
        c1.filter(pl.col("drop_level") == "event")
        .unique(subset=["event_key"])
        .group_by(["class", "status"])
        .agg(pl.len().alias("n"))
        .sort(["class", "status"])
    )
    hz = (
        c1.filter(pl.col("drop_level") == "horizon")
        .group_by(["class", "status", "horizon"])
        .agg(pl.len().alias("n"))
        .sort(["class", "status", "horizon"])
    )
    ev_md = _ascii(ev) if ev.height else "(no event-level drops)"
    hz_md = _ascii(hz) if hz.height else "(no horizon-level drops)"
    return ev_md, hz_md


def _c2_table(audit_split: pl.DataFrame) -> str:
    u = audit_split.filter(pl.col("entry_reached")).unique(subset=["event_key"])
    if u.height == 0:
        return "(no entry-reached events)"
    t = (
        u.group_by("class")
        .agg(
            pl.len().alias("n_entry_reached"),
            pl.col("in_c2").sum().alias("n_in_c2"),
            (pl.col("n_priors") < C2_MIN_PRIORS).sum().alias("n_excl_priors"),
        )
        .with_columns(
            (pl.col("n_entry_reached") - pl.col("n_in_c2") - pl.col("n_excl_priors")).alias(
                "n_excl_magnitude"
            )
        )
        .sort("class")
    )
    return _ascii(t)


def _floors_table(floors: dict) -> str:
    rows: list[dict] = []
    per_symbol = floors.get("per_symbol", {})
    class_floor = floors.get("class_floor_bps", {})
    for cls in CLASS_ORDER:
        for sym in UNIVERSE:
            cell = per_symbol.get(cls, {}).get(sym)
            rows.append(
                {
                    "class": cls,
                    "symbol": sym,
                    "median_spread_bps": cell["median_spread_bps"] if cell else None,
                    "floor_bps": cell["floor_bps"] if cell else None,
                    "n_spreads": cell["n_spreads"] if cell else 0,
                    "class_floor_bps": class_floor.get(cls),
                }
            )
    return _ascii(pl.DataFrame(rows))


def _cells_table(split: str, cells: list[dict]) -> str:
    rows: list[dict] = []
    for c in cells:
        row = {
            "cell_id": c["cell_id"],
            "N": c["N"],
            "n_sessions": c["n_sessions"],
            "mean_bps": c["mean_bps"],
            "ci_lo": c["ci_lo"],
            "ci_hi": c["ci_hi"],
            "floor_bps": c["floor_bps"],
            "bar_2x_floor": c["bar_2x_floor"],
            "screen_pass": c["screen_pass"],
            "underpowered": c["underpowered"],
            "per_symbol_mean": " ".join(f"{k}:{v}" for k, v in c["per_symbol_mean"].items()),
        }
        if split == "validate":
            row["validate_confirm"] = c.get("validate_confirm")
            row["validate_underpowered"] = c.get("validate_underpowered")
        rows.append(row)
    return _ascii(pl.DataFrame(rows))


def _render_md(split: str, cells: list[dict], floors: dict, audit_split: pl.DataFrame) -> str:
    ev_md, hz_md = _drop_tables(audit_split)
    n_pass = sum(1 for c in cells if c["screen_pass"])
    lines = [
        f"# M20 scheduled-macro-window mid-alpha atlas — {split.upper()}",
        "",
        "Family `sched_window_v1` (registered 2026-07-22). STAGE-1 conditional "
        "MID-ALPHA SCREEN — mid-to-mid, no fills, no replay, NOT economics. "
        "Continuation hypothesis every cell: `signed_ret_bps = sign(reaction) x "
        "(exit_mid/entry_mid - 1) x 1e4`. Day-clustered CR0 95% CI (cluster = ET "
        "session), pooled across the 5 names.",
        "",
        f"generated: {datetime.now(UTC).isoformat()}    audit rows ({split}): "
        f"{audit_split.height}",
        f"cells computed: {len(cells)}    SCREEN-PASS: {n_pass}"
        + (
            "  (TRAIN bar: mean >= 2x class floor AND ci_lo > 0 AND N >= 150 AND "
            "sessions >= 40)"
            if split == "train"
            else "  (VALIDATE: listed TRAIN passers only; confirm = same sign AND CI "
            "not entirely < 0)"
        ),
        "",
        "## Cost floors (frozen; computed on TRAIN before any conditional mean)",
        "",
        _floors_table(floors),
        "",
        "## Atlas cells",
        "",
        _cells_table(split, cells),
        "",
        "## Drop reasons — event-level (per event x symbol)",
        "",
        ev_md,
        "",
        "## Drop reasons — horizon-level (per event x symbol x horizon)",
        "",
        hz_md,
        "",
        "## C2 magnitude-gate membership (per class, entry-reached events)",
        "",
        _c2_table(audit_split),
        "",
    ]
    return "\n".join(lines)
