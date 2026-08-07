"""M22 earnings-day closing crosses harness (family ``earnings_close_v1``).

Registered 2026-07-23 (M3_REGISTRATION.md, final section "M22 — earnings-day
closing crosses (Q13)" + its "Pre-data clarifications" block) BEFORE any economics
exist. Frozen design: ``research/experiments/M22-earnings-close/DESIGN.md`` (the
orchestrator's A1-A8 rulings mirror the registration's clarifications). Nothing here
may be tuned; the family has ONE registered look, owned by the orchestrator.

The one catalyst x auction intersection never tested: the day0 earnings CLOSING
CROSS. Two gated cells + one report-only prong, NEVER pooled (L9):

* Cell A -- AMPLIFICATION on the champion 5 (NVDA TSLA AMD MU GOOGL): the M6-FINAL
  near-vs-mid basis rule VERBATIM via ``run_basis_trial`` (bbo-1s completed-bucket
  mid at 15:55:10, |basis| >= 10 -> taker, exit AT the 16:00 cross through
  ``auction_replay``; COST_MODEL v1 fees). day0 vs a same-run non-day0 baseline is
  ONE ``is_day0`` flag on ONE frame (ruling A2/A3).
* Cell B -- CATALYST REVIVAL on the broad 12: the M11 near-vs-ref apparatus VERBATIM
  (``run_m11.fire_near_ref_event``) behind a day0 whitelist; conservative 2.5 bps
  taker off ref, exit at the day0 RAW bars1d close. Proxy-priced evidence class.
* Cell C -- MECHANISM PRONG (report-only, no bar): day0 fired rows stratified by
  single-stock LETF complex presence x |F|/ADV tercile, AUM on ``public_date``
  (rulings A4/A5).

HOLDOUT/seal: the calendar max day0 is 2026-05-28 (structurally < the 2026-06-01
seal), but ``assert_before_holdout`` is still enforced in the whitelist loader and
the CLI, and the reused ``run_basis_trial`` session filter strips holdout regardless.
"""

from __future__ import annotations

import inspect
import json
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import polars as pl
import structlog

from enginev51.apps import run_basis_trial, run_m11
from enginev51.apps.run_m11 import (
    FIRE_BASIS_BPS as M11_FIRE_BASIS_BPS,
)
from enginev51.apps.run_m11 import (
    SEC_TAF_SELL_BPS as M11_SEC_TAF_SELL_BPS,
)
from enginev51.apps.run_m11 import (
    TAKER_COST_BPS as M11_TAKER_COST_BPS,
)
from enginev51.apps.run_m11 import (
    assert_before_holdout,
)
from enginev51.backtest import stress
from enginev51.backtest.auction_replay import replay_moc_event
from enginev51.config import Settings
from enginev51.protocol import HOLDOUT_START, experiments_dir, ledger_append, split_of

log = structlog.get_logger(__name__)

# --------------------------------------------------------------------------- #
# M22 registration (2026-07-23, M3_REGISTRATION.md § M22). Do not tune.
# --------------------------------------------------------------------------- #
SIGNAL_HMS = (15, 55, 10)
FIRE_BASIS_BPS = 10.0
START = date(2020, 1, 2)
END = date(2026, 5, 31)
EVENTS_PARQUET = "research/experiments/M21-earnings-regime/events.parquet"
CELL_A_UNIVERSE = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")
CELL_B_UNIVERSE = ("AAPL", "AVGO", "MSFT", "QCOM", "AMAT", "INTC",
                   "KLAC", "LRCX", "META", "MRVL", "NFLX", "TXN")
CELL_A_MIN_FIRED = 50
CELL_A_MIN_SESSIONS = 40
CELL_A_AMP_MULT = 2.0
CELL_B_MIN_FIRED = 60
OUT_SUBDIR = "M22-earnings-close"
# --------------------------------------------------------------------------- #

# Cell A cost convention (ruling A2): run_basis_trial replays every event through
# auction_replay.replay_moc_event VERBATIM (the M6-FINAL champion path). Its
# fee/slip constants are NOT re-declared here as tunables; they are READ from the
# replay kernel's own signature so the pin test reads the source of truth. Cell B
# imports run_m11.TAKER_COST_BPS / SEC_TAF_SELL_BPS / FIRE_BASIS_BPS the same way.
CELL_A_SLIP_BPS: float = inspect.signature(replay_moc_event).parameters["slip_bps"].default
CELL_A_SEC_TAF_SELL_BPS: float = (
    inspect.signature(replay_moc_event).parameters["sec_taf_sell_bps"].default
)

# Era split for the reported (never gated) per-era rows.
ERA_EARLY = ("2020", "2021", "2022")
ERA_LATE = ("2023", "2024", "2025", "2026")

_CI_SEED = 7          # ruling A7 / registration reproducibility constant
_CI_N_BOOT = 2000     # ruling A1


# --------------------------------------------------------------------------- paths


def canonical_out_dir() -> Path:
    """The ONE canonical M22 output/look-state directory. The one-look gate is
    anchored here so it can never be relocated (a fresh --out-dir would otherwise
    find no look_state.json and defeat the single-registered-look guarantee); the
    CLI passes no directory and always resolves to this path."""
    return experiments_dir() / OUT_SUBDIR


def out_dir_for(out_dir: str | Path | None = None) -> Path:
    """Resolve the M22 output directory. ``out_dir`` exists ONLY for hermetic tests
    (a tmp path); the CLI never supplies it, so the default IS ``canonical_out_dir``
    and the look state is unrelocatable in production."""
    p = Path(out_dir) if out_dir is not None else canonical_out_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p


def look_state_path(out_dir: str | Path | None = None) -> Path:
    return out_dir_for(out_dir) / "look_state.json"


# --------------------------------------------------------------------------- CI


def _ci(df: pl.DataFrame) -> tuple[float, float, float, int, int]:
    """(mean, lo, hi, n_events, n_sessions), day-clustered over ``net_bps``.

    Wraps ``stress.clustered_mean_ci`` (session bootstrap, cluster key = the ET
    ``session`` string, ``n_boot=2000``, ``seed=7`` -- ruling A1). A session with
    2+ reporters is ONE cluster automatically (the cluster key is the session)."""
    if df.height == 0:
        return float("nan"), float("nan"), float("nan"), 0, 0
    m, lo, hi = stress.clustered_mean_ci(
        df["net_bps"].to_numpy(), df["session"].to_numpy(),
        n_boot=_CI_N_BOOT, seed=_CI_SEED,
    )
    return m, lo, hi, df.height, df["session"].n_unique()


def _era_of(session_iso: str) -> str:
    return "2020-22" if session_iso[:4] in ERA_EARLY else "2023-26"


# --------------------------------------------------------------------------- whitelist


def load_day0_whitelist(
    events_path: str | Path,
    universe: tuple[str, ...],
    *,
    end: date = END,
) -> set[tuple[str, str]]:
    """{(symbol, day0_session_iso)} for ``universe`` names with day0 <= ``end``.

    ``day0_session`` IS the ET reaction session -- M21 already resolved AMC/BMO to
    the correct session (an AMC report maps to the NEXT session), so it is used
    DIRECTLY and NEVER re-mapped (double-shift risk, DESIGN reviewer attack #2).
    M21 ``status`` is IGNORED per the registration (it concerns the d1_20 forward
    window; M22's outcome completes at the day0 cross itself). The holdout is
    refused two ways: ``assert_before_holdout(end)`` up front (a caller-supplied
    ``end`` >= 2026-06-01 raises) AND ``assert_before_holdout`` on the realised max
    day0 (belt-and-suspenders; the seal can never be silently crossed)."""
    assert_before_holdout(end)
    df = pl.read_parquet(events_path)
    keep = df.filter(
        pl.col("symbol").is_in(list(universe))
        & (pl.col("day0_session") <= end.isoformat())
    )
    pairs = {
        (str(r["symbol"]), str(r["day0_session"]))
        for r in keep.select("symbol", "day0_session").iter_rows(named=True)
    }
    if pairs:
        max_day0 = max(s for _, s in pairs)
        assert_before_holdout(date.fromisoformat(max_day0))
    return pairs


def annotate_cell(events: pl.DataFrame, *, whitelist: set[tuple[str, str]], cell: str) -> pl.DataFrame:
    """Attach ``is_day0`` (keyed (symbol, session) against ``whitelist``) and a
    literal ``cell`` tag. Pure; ONE frame carries both day0 and baseline rows for
    Cell A (ruling A2/A3), so the day0/baseline split is later a filter of this
    single frame, never a second build."""
    if events.height == 0:
        return events.with_columns(
            pl.lit(False, dtype=pl.Boolean).alias("is_day0"),
            pl.lit(cell, dtype=pl.Utf8).alias("cell"),
        )
    is_day0 = [
        (str(r["symbol"]), str(r["session"])) in whitelist
        for r in events.select("symbol", "session").iter_rows(named=True)
    ]
    return events.with_columns(
        pl.Series("is_day0", is_day0, dtype=pl.Boolean),
        pl.lit(cell, dtype=pl.Utf8).alias("cell"),
    )


# --------------------------------------------------------------------------- Cell A


def build_cell_a_events(
    settings: Settings,
    *,
    whitelist: set[tuple[str, str]],
    start: date = START,
    end: date = END,
    seed: int = _CI_SEED,
    run_fn=run_basis_trial.run_basis_trial,
) -> tuple[pl.DataFrame, dict]:
    """Cell A ALL-events + funnel via ``run_basis_trial`` VERBATIM (ruling A2).

    Runs the M6-FINAL champion pipeline ONCE over the champion 5 (bbo-1s mid at
    15:55:10, taker entry, exit AT the 16:00 cross, COST_MODEL v1 fees), then
    annotates ``is_day0`` (from ``whitelist``) + ``cell="A"``. The returned frame
    is the ALL-events universe; ``cell_a_stats`` derives the |basis| >= 10 fired
    subset and the day0/baseline split from THIS one frame."""
    events, stats = run_fn(
        settings, symbols=list(CELL_A_UNIVERSE), start=start, end=end, seed=seed,
    )
    annotated = annotate_cell(events, whitelist=whitelist, cell="A")
    return annotated, stats


def _sub_rows(df: pl.DataFrame, key: str, key_name: str) -> list[dict]:
    rows: list[dict] = []
    for k in sorted(df[key].unique().to_list()) if df.height else []:
        sub = df.filter(pl.col(key) == k)
        m, lo, hi, n, ns = _ci(sub)
        rows.append({
            key_name: str(k), "n": n, "n_sessions": ns,
            "mean_net_bps": round(m, 4) if n else None,
            "ci_lo": round(lo, 4) if n else None,
            "ci_hi": round(hi, 4) if n else None,
        })
    return rows


def cell_a_stats(events: pl.DataFrame) -> dict:
    """Cell A day0-vs-baseline statistics + the registered PASS/UNDERPOWERED flags.

    ``fired`` = |basis_bps| >= 10 rows of the ONE annotated frame; ``day0`` and
    ``baseline`` are the ``is_day0`` / ``~is_day0`` partitions of that fired set
    (disjoint, exhaustive -- ruling A3 baseline has no min-N floor). PASS
    (registration + ruling A8): n_fired >= 50 across >= 40 sessions AND day0
    CI-lower > 0 AND (day0 mean >= 2x baseline mean, a prong that BINDS only when
    baseline mean > 0; when baseline mean <= 0 it is vacuous-ill-defined and PASS
    reduces to the n/sessions floors + CI-lower > 0, ratio reported unGated).
    n_fired < 50 -> UNDERPOWERED (neither PASS nor a kill)."""
    fired = events.filter(pl.col("basis_bps").abs() >= FIRE_BASIS_BPS)
    day0 = fired.filter(pl.col("is_day0"))
    baseline = fired.filter(~pl.col("is_day0"))

    dm, dlo, dhi, dn, dns = _ci(day0)
    bm, blo, bhi, bn, bns = _ci(baseline)

    underpowered = dn < CELL_A_MIN_FIRED
    n_ok = (dn >= CELL_A_MIN_FIRED) and (dns >= CELL_A_MIN_SESSIONS)
    ci_ok = bool(dn and not np.isnan(dlo) and dlo > 0.0)

    baseline_pos = bool(bn and bm > 0.0)
    amp_ratio = (dm / bm) if baseline_pos else None
    amp_ok = bool(baseline_pos and dm >= CELL_A_AMP_MULT * bm)
    # Ruling A8: the 2x prong binds ONLY if baseline mean > 0; else it is vacuous
    # and PASS reduces to the remaining conditions.
    amp_prong = amp_ok if baseline_pos else True

    cell_a_pass = bool((not underpowered) and n_ok and ci_ok and amp_prong)

    return {
        "n_fired_day0": dn,
        "n_sessions_day0": dns,
        "day0_mean_net_bps": round(dm, 4) if dn else None,
        "day0_ci_lo": round(dlo, 4) if dn else None,
        "day0_ci_hi": round(dhi, 4) if dn else None,
        "n_baseline": bn,
        "n_sessions_baseline": bns,
        "baseline_mean_net_bps": round(bm, 4) if bn else None,
        "baseline_ci_lo": round(blo, 4) if bn else None,
        "baseline_ci_hi": round(bhi, 4) if bn else None,
        "baseline_mean_positive": baseline_pos,
        "amp_ratio_day0_over_baseline": round(amp_ratio, 4) if amp_ratio is not None else None,
        "amp_prong_binds": baseline_pos,
        "meets_n_sessions_floor": bool(n_ok),
        "meets_ci_lower_gt_0": ci_ok,
        "meets_2x_amplification": amp_ok,
        "underpowered": bool(underpowered),
        "pass": cell_a_pass,
        "per_era": _sub_rows(day0.with_columns(
            pl.col("session").map_elements(_era_of, return_dtype=pl.Utf8).alias("_era")
        ), "_era", "era"),
        "per_name": _sub_rows(day0, "symbol", "symbol"),
    }


# --------------------------------------------------------------------------- Cell B


_CELL_B_EXTRA = {"is_day0": pl.Boolean, "cell": pl.Utf8}
CELL_B_SCHEMA: dict[str, pl.DataType] = {**run_m11.EVENT_SCHEMA, **_CELL_B_EXTRA}


def build_cell_b_events(
    settings: Settings,
    *,
    whitelist: set[tuple[str, str]],
    start: date = START,
    end: date = END,
    noii_dir: str | Path | None = None,
    bars_dir: Path = run_m11.BARS1D_DIR,
    fire_fn=run_m11.fire_near_ref_event,
    load_noii=run_m11.load_noii_session,
) -> tuple[pl.DataFrame, dict]:
    """Cell B fired events + funnel: the M11 apparatus VERBATIM behind the day0
    whitelist (registration Cell B). Iterates ONLY whitelisted (sym, session) pairs
    whose symbol is in the broad 12 and whose session is in [start, end] and < the
    seal; each pair goes through ``run_m11.fire_near_ref_event`` (near-vs-ref basis,
    |basis| >= 10, conservative 2.5 bps taker off ref, exit at the day0 RAW bars1d
    close). Every produced row is by construction a fired day0 event
    (``is_day0=True``); tagged ``cell="B"`` and NEVER pooled with Cell A (L9)."""
    counts = {
        "pairs_considered": 0,
        "out_of_range": 0,
        "no_noii_partition": 0,
        "no_noii_msgs": 0,
        "no_near_ref": 0,
        "zero_basis": 0,
        "inactive": 0,
        "no_close": 0,
        "fired": 0,
    }
    closes_cache: dict[str, list[tuple[str, float]]] = {}
    rows: list[dict] = []
    universe = set(CELL_B_UNIVERSE)
    start_iso, end_iso, hold_iso = start.isoformat(), end.isoformat(), HOLDOUT_START.isoformat()

    pairs = sorted((s, d) for (s, d) in whitelist if s in universe)
    for sym, session_iso in pairs:
        counts["pairs_considered"] += 1
        if not (start_iso <= session_iso <= end_iso) or session_iso >= hold_iso:
            counts["out_of_range"] += 1
            continue
        noii = load_noii(sym, session_iso, out_dir=noii_dir)
        if noii is None:
            counts["no_noii_partition"] += 1
            continue
        if noii.height == 0:
            counts["no_noii_msgs"] += 1
            continue
        row, reason = fire_fn(
            settings, sym, session_iso, noii, closes_cache=closes_cache, bars_dir=bars_dir,
        )
        if reason is not None:
            counts[reason] += 1
            continue
        row["is_day0"] = True
        row["cell"] = "B"
        rows.append(row)
        counts["fired"] += 1

    df = (
        pl.DataFrame(rows, schema=CELL_B_SCHEMA, orient="row")
        if rows
        else pl.DataFrame(schema=CELL_B_SCHEMA)
    )
    return df, counts


def cell_b_stats(events: pl.DataFrame) -> dict:
    """Cell B PASS: n_fired >= 60 AND day-clustered CI-lower > 0 (registration).

    Every Cell B row is already a fired day0 event, so ``n_fired`` == events.height.
    Any confirmed positive flip against M11's unconditioned -3.0 bps baseline is the
    finding; the ~2.3-point ref-proxy handicap makes the bar conservative."""
    m, lo, hi, n, ns = _ci(events)
    ci_ok = bool(n and not np.isnan(lo) and lo > 0.0)
    n_ok = n >= CELL_B_MIN_FIRED
    return {
        "n_fired": n,
        "n_sessions": ns,
        "mean_net_bps": round(m, 4) if n else None,
        "ci_lo": round(lo, 4) if n else None,
        "ci_hi": round(hi, 4) if n else None,
        "meets_n_ge_60": bool(n_ok),
        "meets_ci_lower_gt_0": ci_ok,
        "underpowered": bool(n < CELL_B_MIN_FIRED),
        "pass": bool(n_ok and ci_ok),
        "per_era": _sub_rows(events.with_columns(
            pl.col("session").map_elements(_era_of, return_dtype=pl.Utf8).alias("_era")
        ), "_era", "era"),
        "per_name": _sub_rows(events, "symbol", "symbol"),
    }


# --------------------------------------------------------------------------- Cell C


def _day0_open_to_close_return(sym: str, session_iso: str, *, bars_dir: Path) -> float | None:
    """day0 (open -> close) return from the RAW daily bar (owned data).

    DELIBERATE PROXY (flagged): ruling A5's registered r-window is open -> 15:50,
    but the broad-12 half of the Cell C pool has NO owned intraday quote feed, so
    the exact 15:50 mid is uncomputable pool-wide. Cell C is REPORT-ONLY with no
    promotion bar; the strata (complex presence, |F|/ADV tercile) are robust to a
    monotone daily-return proxy, so the open->close daily return stands in for the
    registered window. Returns ``None`` when the raw bar is absent (that row falls
    into the ``unknown_F`` stratum, never a fabricated 0)."""
    p = Path(bars_dir) / f"{sym.upper()}.parquet"
    if not p.exists():
        return None
    df = pl.read_parquet(p)
    for r in df.iter_rows(named=True):
        d = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
        if d == session_iso and r["open"] and r["open"] > 0.0:
            return float(r["close"]) / float(r["open"]) - 1.0
    return None


def cell_c_strata(
    cell_a_events: pl.DataFrame,
    cell_b_events: pl.DataFrame,
    *,
    aum_source: pl.DataFrame | str | Path | None = None,
    r_by_event: dict[tuple[str, str], float] | None = None,
    bars_dir: Path = run_m11.BARS1D_DIR,
) -> pl.DataFrame:
    """REPORT-ONLY mechanism prong (no bar): day0 fired rows (Cell A |basis| >= 10
    day0 + all Cell B) stratified by single-stock LETF complex presence x |F|/ADV
    tercile. AUM anchored on ``public_date`` (rulings A4/A5, the F3-corrected
    artifact); complex membership from the LETF fund registry. F = flow_coef * r
    with flow_coef = sum L(L-1)*AUM over the name's single-stock complex (M12 Cell
    A machinery via ``models.m8v2_features``); ``r`` from ``r_by_event`` else the
    day0 open->close proxy (see ``_day0_open_to_close_return``). No CI, no gate;
    feeds the F/ADV-forward-filter / M8-v2 path only."""
    from enginev51.models import m8v2_features as m8

    a_day0 = cell_a_events.filter(
        (pl.col("basis_bps").abs() >= FIRE_BASIS_BPS) & pl.col("is_day0")
    ).select("symbol", "session", "adv20_dollars", "net_bps", "cell")
    b = cell_b_events.select("symbol", "session", "adv20_dollars", "net_bps", "cell")
    pool = pl.concat([a_day0, b], how="vertical") if (a_day0.height or b.height) else a_day0
    if pool.height == 0:
        return pl.DataFrame(schema={
            "complex_present": pl.Boolean, "f_adv_tercile": pl.Utf8,
            "n": pl.Int64, "mean_net_bps": pl.Float64,
        })

    if isinstance(aum_source, pl.DataFrame):
        anchors = aum_source
    elif aum_source is not None:
        anchors = m8.load_letf_anchors(anchors_path=aum_source)
    else:
        anchors = m8.load_letf_anchors()

    pool = pool.with_columns(pl.col("session").str.to_date().alias("_dte"))
    pool = m8.attach_flow_coef(pool, anchors)  # flow_coef on the day0 session (public_date)

    r_vals: list[float | None] = []
    for r in pool.select("symbol", "session").iter_rows(named=True):
        key = (str(r["symbol"]), str(r["session"]))
        if r_by_event is not None and key in r_by_event:
            r_vals.append(r_by_event[key])
        else:
            r_vals.append(_day0_open_to_close_return(str(r["symbol"]), str(r["session"]), bars_dir=bars_dir))

    pool = pool.with_columns(pl.Series("_r", r_vals, dtype=pl.Float64)).with_columns(
        pl.col("flow_coef").ne(0.0).alias("complex_present"),
        (pl.col("flow_coef") * pl.col("_r")).alias("_f_usd"),
    ).with_columns(
        pl.when(
            pl.col("_f_usd").is_not_null()
            & pl.col("adv20_dollars").is_not_null()
            & (pl.col("adv20_dollars") > 0.0)
        )
        .then(pl.col("_f_usd").abs() / pl.col("adv20_dollars"))
        .otherwise(None)
        .alias("_f_adv")
    )

    finite = pool.filter(pl.col("_f_adv").is_not_null())
    if finite.height >= 3:
        qs = finite["_f_adv"].qcut(3, labels=["lo", "mid", "hi"], allow_duplicates=True)
        finite = finite.with_columns(qs.cast(pl.Utf8).alias("f_adv_tercile"))
    else:
        finite = finite.with_columns(pl.lit("all", dtype=pl.Utf8).alias("f_adv_tercile"))
    unknown = pool.filter(pl.col("_f_adv").is_null()).with_columns(
        pl.lit("unknown_F", dtype=pl.Utf8).alias("f_adv_tercile")
    )
    tagged = pl.concat([finite, unknown], how="diagonal") if unknown.height else finite

    return (
        tagged.group_by("complex_present", "f_adv_tercile")
        .agg(pl.len().alias("n"), pl.col("net_bps").mean().alias("mean_net_bps"))
        .sort("complex_present", "f_adv_tercile")
    )


# --------------------------------------------------------------------------- ground truth


def ground_truth_a(cell_a_events: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """<=k stratified Cell A fills vs the tape (v6.1) via the champion sampler."""
    fired = cell_a_events.filter(pl.col("basis_bps").abs() >= FIRE_BASIS_BPS)
    return run_basis_trial._stratified_ground_truth(fired, k)


def ground_truth_b(cell_b_events: pl.DataFrame, k: int = 10) -> pl.DataFrame:
    """<=k stratified Cell B extraction rows (near/ref vs close) via the M11 sampler."""
    return run_m11.stratified_ground_truth(cell_b_events, k)


# --------------------------------------------------------------------------- no-pooling guard


def _assert_cell_tag(df: pl.DataFrame, expected: str) -> None:
    """L9 guard: the frame's ``cell`` tag set must be EXACTLY ``{expected}``.

    A mixed frame (Cell A price objects pooled with Cell B proxy-priced ones) is a
    protocol violation -- the two evidence classes are never combined in a CI, an
    atlas row, or a parquet."""
    tags = set(df["cell"].unique().to_list()) if df.height else {expected}
    if tags != {expected}:
        raise ValueError(
            f"cell-tag pooling violation (L9): expected exactly {{'{expected}'}}, got {sorted(tags)}"
        )


# --------------------------------------------------------------------------- atlas


def _ascii(df: pl.DataFrame) -> str:
    with pl.Config(
        tbl_formatting="ASCII_MARKDOWN",
        tbl_hide_dataframe_shape=True,
        tbl_hide_column_data_types=True,
        tbl_rows=200,
        tbl_cols=-1,
        tbl_width_chars=260,
    ):
        return str(df)


def build_atlas_md(
    trial_id: str,
    cell_a_events: pl.DataFrame,
    a_stats: dict,
    a_funnel: dict,
    cell_b_events: pl.DataFrame,
    b_stats: dict,
    b_funnel: dict,
    cell_c: pl.DataFrame,
    *,
    seed: int,
) -> str:
    """Assemble the atlas markdown. Cell A and Cell B ALWAYS live in SEPARATE
    sections (L9); a mixed tag set on either frame raises before any rendering."""
    _assert_cell_tag(cell_a_events, "A")
    _assert_cell_tag(cell_b_events, "B")
    md: list[str] = [
        f"# M22 earnings-day closing crosses atlas -- {trial_id}",
        "",
        "Family `earnings_close_v1` (registered 2026-07-23, M3_REGISTRATION.md "
        "§ M22). ONE pooled look over TRAIN+VALIDATE (<= 2026-05-31); confirmation "
        "authority is FORWARD (M20F pattern). Cell A (champion 5, bbo-1s mid, exit "
        "AT the 16:00 cross) and Cell B (broad 12, ref-proxy, exit at the day0 raw "
        "close) are DISJOINT evidence classes -- never pooled (L9). NO ledger "
        "verdict here; the orchestrator owns it.",
        "",
        f"seed={seed}    holdout seal: {HOLDOUT_START.isoformat()} (calendar max day0 "
        "structurally < seal)",
        "",
        "## Cell A -- AMPLIFICATION (champion 5; day0 vs same-run non-day0 baseline)",
        "",
        f"Fired day0 events: {a_stats['n_fired_day0']} across {a_stats['n_sessions_day0']} "
        f"sessions.  PASS = n>=50 & sessions>=40 & CI-lo>0 & (day0 mean >= 2x baseline "
        "mean when baseline>0; ruling A8).",
        "```",
        json.dumps(a_stats, indent=2, default=str),
        "```",
        "Cell A funnel (run_basis_trial ALL-events):",
        "```",
        json.dumps(a_funnel.get("counts", a_funnel), indent=2, default=str),
        "```",
        "Per-era day0 (reported, never gated):",
        "",
        _ascii(pl.DataFrame(a_stats["per_era"])) if a_stats["per_era"] else "(none)",
        "",
        "Per-name day0 (reported, never gated):",
        "",
        _ascii(pl.DataFrame(a_stats["per_name"])) if a_stats["per_name"] else "(none)",
        "",
        "## Cell B -- CATALYST REVIVAL (broad 12; proxy-priced, day0 only)",
        "",
        f"Fired day0 events: {b_stats['n_fired']} across {b_stats['n_sessions']} "
        "sessions.  PASS = n>=60 & CI-lo>0.",
        "```",
        json.dumps(b_stats, indent=2, default=str),
        "```",
        "Cell B funnel:",
        "```",
        json.dumps(b_funnel, indent=2, default=str),
        "```",
        "Per-era (reported, never gated):",
        "",
        _ascii(pl.DataFrame(b_stats["per_era"])) if b_stats["per_era"] else "(none)",
        "",
        "Per-name (reported, never gated):",
        "",
        _ascii(pl.DataFrame(b_stats["per_name"])) if b_stats["per_name"] else "(none)",
        "",
        "## Cell C -- MECHANISM PRONG (report-only, no bar)",
        "",
        "day0 fired rows (Cell A day0 + Cell B) x single-stock complex presence x "
        "|F|/ADV tercile. AUM on public_date (rulings A4/A5). Prediction: "
        "amplification concentrates in complex names. NO promotion consequence.",
        "",
        _ascii(cell_c) if cell_c.height else "(no strata)",
        "",
    ]
    return "\n".join(md)


def write_outputs(
    out_dir: Path,
    trial_id: str,
    cell_a_events: pl.DataFrame,
    cell_b_events: pl.DataFrame,
    cell_c: pl.DataFrame,
    a_stats: dict,
    b_stats: dict,
    atlas_md: str,
    gt_a: pl.DataFrame,
    gt_b: pl.DataFrame,
) -> dict[str, Path]:
    """Write the M22 artifacts. Cell A and Cell B events go to SEPARATE parquet
    files, NEVER merged (L9); ``write_outputs`` asserts each frame's tag set is
    exactly {"A"} / {"B"} before touching disk."""
    _assert_cell_tag(cell_a_events, "A")
    _assert_cell_tag(cell_b_events, "B")
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "atlas": out_dir / "atlas.md",
        "cells": out_dir / "cells.json",
        "cell_a_events": out_dir / "cell_a_events.parquet",
        "cell_b_events": out_dir / "cell_b_events.parquet",
        "cell_c_strata": out_dir / "cell_c_strata.parquet",
        "ground_truth_a": out_dir / "ground_truth_a.parquet",
        "ground_truth_b": out_dir / "ground_truth_b.parquet",
    }
    paths["atlas"].write_text(atlas_md, encoding="utf-8")
    # Disjoint keys cell_a/cell_b/cell_c; pass/underpowered are FLAGS, not verdicts.
    # cell_c is report-only strata (also on disk as cell_c_strata.parquet).
    paths["cells"].write_text(
        json.dumps(
            {"cell_a": a_stats, "cell_b": b_stats, "cell_c": cell_c.to_dicts()},
            indent=2, default=str,
        ),
        encoding="utf-8",
    )
    cell_a_events.write_parquet(paths["cell_a_events"])
    cell_b_events.write_parquet(paths["cell_b_events"])
    cell_c.write_parquet(paths["cell_c_strata"])
    gt_a.write_parquet(paths["ground_truth_a"])
    gt_b.write_parquet(paths["ground_truth_b"])
    return paths


# --------------------------------------------------------------------------- one-look gate


def assert_look_not_spent(
    out_dir: str | Path | None = None,
    *,
    defect_rerun: bool = False,
    reason: str | None = None,
) -> None:
    """Enforce the family's SINGLE registered look.

    A present ``look_state.json`` refuses a second look UNLESS ``defect_rerun`` is
    set with a non-empty ``reason`` (a ledgered code-defect fix; never threshold
    motion). A defect rerun appends a ledger note so the extra look is auditable."""
    path = look_state_path(out_dir)
    if not path.exists():
        return
    if not defect_rerun:
        raise RuntimeError(
            f"M22 look already spent ({path}); the family has ONE registered look. "
            "A ledgered code-defect fix may re-run with --defect-rerun and --reason."
        )
    if not (reason and reason.strip()):
        raise ValueError("--defect-rerun requires a non-empty --reason (ledgered).")
    ledger_append("note", {
        "event": "M22_DEFECT_RERUN",
        "reason": reason.strip(),
        "look_state": str(path),
    })


def mark_look_spent(
    out_dir: str | Path | None = None,
    *,
    trial_id: str,
    git_sha: str | None = None,
) -> Path:
    """Record the spent look (``look_state.json``): trial id, git sha, timestamp."""
    path = look_state_path(out_dir)
    path.write_text(
        json.dumps({
            "trial_id": trial_id,
            "git_sha": git_sha,
            "spent_ts": datetime.now(UTC).isoformat(),
            "family": "earnings_close_v1",
        }, indent=2),
        encoding="utf-8",
    )
    return path


__all__ = [
    "CELL_A_SEC_TAF_SELL_BPS",
    "CELL_A_SLIP_BPS",
    "CELL_A_UNIVERSE",
    "CELL_B_UNIVERSE",
    "END",
    "EVENTS_PARQUET",
    "FIRE_BASIS_BPS",
    "M11_FIRE_BASIS_BPS",
    "M11_SEC_TAF_SELL_BPS",
    "M11_TAKER_COST_BPS",
    "START",
    "annotate_cell",
    "assert_before_holdout",
    "assert_look_not_spent",
    "build_atlas_md",
    "canonical_out_dir",
    "build_cell_a_events",
    "build_cell_b_events",
    "cell_a_stats",
    "cell_b_stats",
    "cell_c_strata",
    "ground_truth_a",
    "ground_truth_b",
    "load_day0_whitelist",
    "mark_look_spent",
    "split_of",
    "write_outputs",
]
