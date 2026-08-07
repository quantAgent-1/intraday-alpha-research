"""M8-v2 mechanism-informed meta-gate — the 6 frozen feature builders
(M3_REGISTRATION.md "M8-v2 — mechanism-informed meta-gate", REGISTERED
2026-07-20; M8-v2-FEATURE-DRAFT.md's candidate table). Every feature is
strictly observable at the 15:55:10 ET decision instant — the SAME leakage
boundary M6-FINAL/M8/M9 already enforce (M9's ``[15:50:00, 15:55:10]`` window
discipline is the direct precedent for the bbo-1s window reads here).

The 6 frozen features (``FEATURE_COLS``, order fixed):

    abs_f_over_adv    |F(t)| / ADV20_dollars
    flow_aligned       sign(F(t)) * sign(basis_bps)
    complex_intensity  complex total AUM (month t-1) / ADV20_dollars
    range_pos_1555     (P@15:55:10 - day_low) / (day_high - day_low), bbo-1s mids
    month_end          last-trading-day-of-month dummy (0.0/1.0)
    day_vol_ratio      realized vol 09:30->15:55 (1-min sampled bbo-1s mids) / vol20

F(t) PINNED r-window (registered 2026-07-20, supersedes M12's open->15:50 mid
variant, which stays a REPORT-ONLY cross-check): r = P@15:55:10 (last bbo-1s
mid at-or-before 15:55:10) / prior session's OFFICIAL close (data/raw/sip/
bars1d) - 1. F(t) = Sum over the name's SINGLE-STOCK LETF complex of
AUM_{t-1} * (L^2 - L) * r, AUM_{t-1} a STRICT step function (last anchor
BEFORE the session date, no interpolation, no exact-date match) -- M12 Cell
A's exact computation (scripts/m12_cell_a.py), ported verbatim (scripts/ is
not an importable package). Index-LETF legs (NDX/SOX/SPX) are EXCLUDED: M12
Cell A2 rejected the index leg (alignment lift 1.02 -> 0.08 diluted); F(t) is
SINGLE-STOCK ONLY, matching the frozen/registered definition.

FLAGGED CHOICES (spec under-determined; documented here for orchestrator
review -- see also the build report):

  1. ``complex_intensity``'s "AUM at month t-1" is a COARSER, MONTH-granular
     step function than F(t)'s session-level one (deliberately: the draft
     calls it "slow scale"): for a session in calendar month M, each fund's
     own latest anchor strictly BEFORE the first day of month M (i.e. anchors
     dated in a month < M). "Complex total AUM" = the RAW (un-leveraged,
     un-signed) sum of aum_usd over every single-stock ticker in the
     underlying's complex -- not the F(t) coef (leverage never enters this
     feature; it is a pure dollar-footprint-vs-ADV scale).
  2. ``day_vol_ratio``'s numerator is the STANDARD realized-volatility
     estimator sqrt(sum(1-min log-return^2)) over 09:30:00..15:55:00 ET
     (386 grid points, 1-minute spacing, PREVAILING bbo-1s mid at each
     boundary) -- NOT the sample std of the increments (which would sit on a
     ~1/sqrt(390) smaller scale and never be comparable to a daily vol20).
     This full-window quadratic-variation convention is what puts the
     numerator on the same "whole session" scale as vol20's daily sd.
  3. ``vol20`` (day_vol_ratio's denominator): REUSED from the M8 event frame
     when present (its `vol20` column is already exactly
     `models.moc_gbm.trailing_vol20` -- trailing 20-session sample std,
     ddof=1, of daily log-returns of official closes, strictly PIT); else
     recomputed via that SAME function from data/raw/sip/bars1d. One
     definition either way -- never a second competing "vol20".
  4. ``range_pos_1555`` uses EVERY bbo-1s snapshot in [09:30:00, 15:55:10] for
     day_low/day_high (a finer, truer intraday range than a 1-minute
     subsample); ``day_vol_ratio`` explicitly uses a 1-MINUTE subsample (the
     draft's own wording distinguishes "bbo-1s mids" from "1-min sampled
     bbo-1s mids") -- the standard microstructure-noise mitigation for a
     realized-vol estimator. range_pos_1555 is null (not 0/1) when
     day_high == day_low (an undefined ratio, never fabricated).
  5. ADV20 and basis_bps are ALWAYS reused from the input M8 event frame
     (never recomputed) -- both are hard-required input columns.

Every derived input (bbo mids, prior close, flow_coef, complex_aum, vol20) is
injectable on the pure per-row builder (``build_v2_feature_row``) so unit
tests exercise exact math with hand-built literals -- no disk, no network
(house style: models/evolution_features.py, models/moc_gbm.py).
``build_features_frame`` is the batch/disk-backed entry point.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from enginev51.backtest import fills as fk
from enginev51.data.bbo1s import bbo_root, partition_path
from enginev51.data.noii import et_ns
from enginev51.flows import ffcal
from enginev51.models.moc_gbm import trailing_vol20

NS_PER_S = 1_000_000_000

# Registered PIT instants (ET).
SESSION_OPEN_HMS: tuple[int, int, int] = (9, 30, 0)
DECISION_HMS: tuple[int, int, int] = (15, 55, 10)

# 1-minute grid for day_vol_ratio's numerator: 09:30:00 .. 15:55:00 inclusive,
# 60s spacing (386 points, 385 returns) -- the draft's literal "09:30->15:55"
# bound (distinct from range_pos_1555's "09:30->15:55:10").
_MINUTE_GRID_POINTS: int = 386

DEFAULT_REGISTRY_PATH = "data/external/letf_fund_registry.csv"
DEFAULT_ANCHORS_PATH = "data/external/letf_aum_anchors.csv"

# Index-LETF complexes: EXCLUDED from F(t)/complex_intensity (M12 Cell A2
# rejected the index leg; F(t) is single-stock only).
_INDEX_UNDERLYINGS: frozenset[str] = frozenset({"NDX", "SOX", "SPX"})

# The 6 frozen features, in the registered order. Removal-only at run time
# (data defects); never addition (M3_REGISTRATION.md M8-v2).
FEATURE_COLS: tuple[str, ...] = (
    "abs_f_over_adv",
    "flow_aligned",
    "complex_intensity",
    "range_pos_1555",
    "month_end",
    "day_vol_ratio",
)

# Diagnostic (NOT modeled) columns carried alongside FEATURE_COLS: the F(t)
# machinery + bbo-derived intermediates, useful for the smoke's null-rate
# table and the report-only M12 F/ADV cross-check.
DIAGNOSTIC_COLS: tuple[str, ...] = (
    "F_usd", "f_adv_signed", "r_pinned", "p_1555", "day_low", "day_high",
    "flow_coef", "complex_aum_usd",
)

# NOTE: ``flow_coef``/``complex_aum_usd`` are DELIBERATELY excluded from this
# schema even though ``build_v2_feature_row`` returns them (they are pure
# pass-throughs of its inputs, useful to the per-row unit tests): the batch
# frame (``build_features_frame``) already carries both columns from
# ``attach_flow_coef``/``attach_complex_aum`` on ``df`` BEFORE the per-row
# loop runs, so including them here would collide on the horizontal concat.
_ROW_SCHEMA: dict[str, pl.DataType] = {
    "abs_f_over_adv": pl.Float64,
    "flow_aligned": pl.Float64,
    "complex_intensity": pl.Float64,
    "range_pos_1555": pl.Float64,
    "month_end": pl.Float64,
    "day_vol_ratio": pl.Float64,
    "F_usd": pl.Float64,
    "f_adv_signed": pl.Float64,
    "r_pinned": pl.Float64,
    "p_1555": pl.Float64,
    "day_low": pl.Float64,
    "day_high": pl.Float64,
}

_BLANK_STATS: dict[str, float | None] = {
    "p_1555": None, "day_low": None, "day_high": None, "realized_vol_1min": None,
}


# --------------------------------------------------------------------------- calendar (M14 reuse)


def is_month_end(session_iso: str) -> bool:
    """last-trading-day-of-month dummy -- the M14 LOCKED MONTH_END rule
    (M3_REGISTRATION.md section M14: "MONTH_END = last session of the
    calendar month within the owned session set"), reimplemented directly
    over ``flows/ffcal`` (the SAME owned calendar primitives
    ``reversion/meta.calendar_stratum`` uses for its own M14-locked strata --
    ffcal is in-repo/owned, not a third-party dependency, so this is a reuse
    of the shared calendar tool per the build instruction's fallback clause,
    not a fresh reimplementation of holiday/trading-day logic). Month-end and
    the 3rd-Friday opex days never coincide (day-of-month 15-21 vs >=28), so
    no ordering-vs-QUAD_WITCH check is needed here (unlike
    ``calendar_stratum``, which returns one of several mutually exclusive
    strata and must check opex first)."""
    y, m, d = (int(x) for x in session_iso.split("-"))
    sd = date(y, m, d)
    hols = ffcal.us_holidays(y) | ffcal.us_holidays(y - 1) | ffcal.us_holidays(y + 1)
    tds = ffcal.trading_days(y, m, hols)
    return bool(tds) and sd == tds[-1]


# --------------------------------------------------------------------------- LETF anchors (M12 Cell A reuse)


_LEV_RE = re.compile(r"(\d+(?:\.\d+)?)\s*X", re.IGNORECASE)
_BEAR_RE = re.compile(r"bear|short|inverse", re.IGNORECASE)


def _lev_from_note(note: str | None, fallback: float) -> float:
    """Era-correct leverage parsed from an anchor's as-filed N-PORT
    ``seriesName`` note (e.g. "seriesName=GraniteShares 2x Long NVDA Daily
    ETF"); falls back to the registry's current leverage when the note
    doesn't parse. Ported VERBATIM from ``scripts/m12_cell_a.py`` (M12 Cell
    A, the frozen F(t) computation this module reuses) -- ``scripts/`` is not
    an importable package, so the logic is duplicated here rather than
    imported; any change to the M12 script does not silently drift this
    module (and vice versa)."""
    if not isinstance(note, str):
        return fallback
    m = _LEV_RE.search(note)
    if not m:
        return fallback
    mag = float(m.group(1))
    return -mag if _BEAR_RE.search(note) else mag


def load_letf_anchors(
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    anchors_path: str | Path = DEFAULT_ANCHORS_PATH,
) -> pl.DataFrame:
    """The AUM-anchors table with era-aware leverage + the F(t) coefficient
    ``L*(L-1)*AUM`` attached, per M12 Cell A (``scripts/m12_cell_a.py``).
    Columns: ``ticker, underlying, adate (Date), aum_usd, lev_era, coef``.
    Index-complex rows (underlying in NDX/SOX/SPX) are dropped here (single
    filter point for BOTH F(t) and complex_intensity)."""
    reg = pl.read_csv(registry_path)
    anc = pl.read_csv(anchors_path)
    anc = anc.join(reg.select("ticker", "underlying", "leverage"), on="ticker", how="inner")
    anc = anc.filter(~pl.col("underlying").is_in(list(_INDEX_UNDERLYINGS)))
    anc = anc.with_columns(
        pl.struct(["note", "leverage"]).map_elements(
            lambda s: _lev_from_note(s["note"], s["leverage"]), return_dtype=pl.Float64
        ).alias("lev_era")
    )
    # SIM_AUDIT 2026-07-21 F3: anchor the as-of join on the FILING/public date, not
    # the N-PORT reporting-period end (asof_date). The period-end value only became
    # public ~58-60 d later (lifted into public_date by scripts/add_public_dates.py);
    # AUM moves 3-10x inside that lag. ``adate`` now carries the public instant so
    # _asof_attach_sum joins only on information available at the session date.
    # (M8-v2, this module's only gated consumer, is KILLED; kept honest for reuse.)
    anc = anc.with_columns(
        (pl.col("lev_era") * (pl.col("lev_era") - 1.0) * pl.col("aum_usd")).alias("coef"),
        pl.col("public_date").str.to_date().alias("adate"),
    )
    return anc.select("ticker", "underlying", "adate", "aum_usd", "lev_era", "coef").sort(
        "ticker", "adate"
    )


def _asof_attach_sum(
    pairs: pl.DataFrame, anchors: pl.DataFrame, value_col: str, out_col: str
) -> pl.DataFrame:
    """For every (underlying, asof) pair, sum EACH matching ticker's own
    latest ``value_col`` anchor strictly before ``asof`` (a PER-TICKER step
    function; ``allow_exact_matches=False`` -- no interpolation, no exact-date
    use -- M12 Cell A's AUM(t-1) convention). An underlying with no anchored
    ticker before ``asof`` gets 0.0. Pure polars ``join_asof``, ported from
    ``scripts/m12_cell_a.py``'s per-ticker loop (lines 76-93) generalized over
    ``value_col`` so the SAME function serves F(t)'s session-level ``coef``
    sum and complex_intensity's month-level ``aum_usd`` sum.

    ``pairs`` columns: ``underlying`` (Utf8), ``asof`` (Date). Returns
    ``[underlying, asof, out_col]``, one row per DISTINCT input pair.

    NOTE (SIM_AUDIT 2026-07-21 F3): ``anchors.adate`` carries the FILING/public
    date (``load_letf_anchors`` now derives it from ``public_date``), not the
    N-PORT reporting-period end, so this backward join uses only publicly
    available AUM as of ``asof``."""
    keys = pairs.select("underlying", "asof").unique()
    out_parts: list[pl.DataFrame] = []
    for tkr in anchors["ticker"].unique().to_list():
        a = anchors.filter(pl.col("ticker") == tkr).select("underlying", "adate", value_col)
        if a.height == 0:
            continue
        und = a["underlying"][0]
        s = keys.filter(pl.col("underlying") == und).sort("asof")
        if s.height == 0:
            continue
        j = s.join_asof(
            a.select("adate", value_col).sort("adate"),
            left_on="asof",
            right_on="adate",
            strategy="backward",
            allow_exact_matches=False,
        )
        out_parts.append(j.select("underlying", "asof", value_col))
    if not out_parts:
        return keys.with_columns(pl.lit(0.0).alias(out_col))
    agg = (
        pl.concat(out_parts)
        .group_by("underlying", "asof")
        .agg(pl.col(value_col).sum().alias(out_col))
    )
    return keys.join(agg, on=["underlying", "asof"], how="left").with_columns(
        pl.col(out_col).fill_null(0.0)
    )


def attach_flow_coef(df: pl.DataFrame, anchors: pl.DataFrame) -> pl.DataFrame:
    """Adds ``flow_coef`` = the SESSION-level step function
    Sum_j L_j(L_j-1)*AUM_j(t-1) over ``symbol``'s single-stock LETF complex
    (M12 Cell A's F(t) coefficient; AUM anchored strictly before the SESSION
    date, no interpolation). Requires a ``_dte`` (Date) column on ``df``."""
    pairs = df.select(pl.col("symbol").alias("underlying"), pl.col("_dte").alias("asof"))
    fc = _asof_attach_sum(pairs, anchors, "coef", "flow_coef")
    return df.join(
        fc.rename({"underlying": "symbol", "asof": "_dte"}), on=["symbol", "_dte"], how="left"
    ).with_columns(pl.col("flow_coef").fill_null(0.0))


def attach_complex_aum(df: pl.DataFrame, anchors: pl.DataFrame) -> pl.DataFrame:
    """Adds ``complex_aum_usd`` = the MONTH-level step function
    Sum_j AUM_j(month t-1) over ``symbol``'s single-stock LETF complex (RAW
    dollar AUM, no leverage weighting -- a slow dollar-footprint scale, per
    FLAGGED CHOICE #1). Requires a ``_month_start`` (Date, first-of-month)
    column on ``df``."""
    pairs = df.select(pl.col("symbol").alias("underlying"), pl.col("_month_start").alias("asof"))
    ca = _asof_attach_sum(pairs, anchors, "aum_usd", "complex_aum_usd")
    return df.join(
        ca.rename({"underlying": "symbol", "asof": "_month_start"}),
        on=["symbol", "_month_start"],
        how="left",
    ).with_columns(pl.col("complex_aum_usd").fill_null(0.0))


# --------------------------------------------------------------------------- bbo-1s intraday stats


def _session_window(bbo_frame: pl.DataFrame, session_iso: str) -> pl.DataFrame:
    """bbo-1s rows for the ET session day, sane-filtered (bid>0 & ask>bid) and
    ts-sorted -- the SAME filter ``data/bbo1s.load_bbo_session`` applies,
    reimplemented here so a whole-MONTH partition can be read once and reused
    (filtered per-session in memory) across every session in that month."""
    lo = et_ns(session_iso, 0, 0, 0)
    hi = et_ns((date.fromisoformat(session_iso) + timedelta(days=1)).isoformat(), 0, 0, 0)
    return bbo_frame.filter(
        (pl.col("ts") >= lo)
        & (pl.col("ts") < hi)
        & (pl.col("bid") > 0.0)
        & (pl.col("ask") > pl.col("bid"))
    ).sort("ts")


def _intraday_stats(bbo_frame: pl.DataFrame | None, session_iso: str) -> dict[str, float | None]:
    """One pure pass over one session's bbo-1s mids -> the raw bbo-derived
    inputs of range_pos_1555 / day_vol_ratio / F(t)'s r-window:
    ``{p_1555, day_low, day_high, realized_vol_1min}``. ``bbo_frame`` may be a
    WHOLE-MONTH partition (filtered to the session internally), an
    already-session-scoped frame (idempotent), or ``None`` (no partition on
    disk) -- every value is ``None`` when unavailable.

    LEAKAGE (unit-tested): day_low/day_high and the realized-vol grid are
    STRICTLY bounded to [09:30:00, 15:55:10] / [09:30:00, 15:55:00] ET;
    p_1555 is ``prevailing_mid`` AT EXACTLY 15:55:10. ``prevailing_mid``
    searches backward from its query instant only (``searchsorted``), so no
    row with ts > the query instant can ever change the result -- appending
    bbo-1s rows dated after 15:55:10 cannot move any of these values,
    regardless of where they land in ``bbo_frame``."""
    if bbo_frame is None:
        return dict(_BLANK_STATS)
    win = _session_window(bbo_frame, session_iso)
    if win.height == 0:
        return dict(_BLANK_STATS)
    ts = win["ts"].to_numpy()
    bid = win["bid"].to_numpy()
    ask = win["ask"].to_numpy()

    ts_open = et_ns(session_iso, *SESSION_OPEN_HMS)
    ts_dec = et_ns(session_iso, *DECISION_HMS)

    p_1555_raw = fk.prevailing_mid(ts, bid, ask, ts_dec)
    p_1555 = float(p_1555_raw) if np.isfinite(p_1555_raw) else None

    day_mask = (ts >= ts_open) & (ts <= ts_dec)
    if day_mask.any():
        mids = 0.5 * (bid[day_mask] + ask[day_mask])
        day_low, day_high = float(mids.min()), float(mids.max())
    else:
        day_low = day_high = None

    grid_mids: list[float] = []
    for k in range(_MINUTE_GRID_POINTS):
        g = ts_open + k * 60 * NS_PER_S
        m = fk.prevailing_mid(ts, bid, ask, g)
        if np.isfinite(m) and m > 0.0:
            grid_mids.append(float(m))
    if len(grid_mids) >= 2:
        rets = np.diff(np.log(np.asarray(grid_mids, dtype=float)))
        realized_vol_1min = float(np.sqrt(np.sum(rets**2)))
    else:
        realized_vol_1min = None

    return {
        "p_1555": p_1555,
        "day_low": day_low,
        "day_high": day_high,
        "realized_vol_1min": realized_vol_1min,
    }


# --------------------------------------------------------------------------- per-row (pure)


def build_v2_feature_row(
    *,
    session: str,
    basis_bps: float | None,
    adv20_dollars: float,
    flow_coef: float,
    complex_aum_usd: float,
    vol20: float | None,
    bbo_frame: pl.DataFrame | None,
    prior_close: float | None,
) -> dict:
    """Pure computation of the 6 frozen features (+ diagnostics) for ONE
    (symbol, session) candidate from already-resolved inputs -- no disk, no
    network. ``build_features_frame`` is the batch/disk-backed entry point
    that resolves ``flow_coef``/``complex_aum_usd`` (LETF anchors),
    ``prior_close`` (bars1d) and ``vol20`` (frame column or
    ``moc_gbm.trailing_vol20``) before calling this.

    Null propagation: ``abs_f_over_adv``/``flow_aligned``/``r`` are ``None``
    when the bbo mid at 15:55:10 or the prior close is unavailable (an
    UNKNOWN r, never silently 0) -- distinct from ``flow_coef == 0.0``
    (a genuine no-complex-yet name-day, a legitimate 0). ``range_pos_1555``
    is ``None`` on a degenerate (zero-width) or uncovered day range.
    ``day_vol_ratio`` is ``None`` when fewer than 2 usable 1-minute samples
    exist or ``vol20`` is unusable."""
    stats = _intraday_stats(bbo_frame, session)

    r: float | None = None
    if stats["p_1555"] is not None and prior_close is not None and prior_close > 0.0:
        r = stats["p_1555"] / prior_close - 1.0

    f_usd: float | None = flow_coef * r if r is not None else None
    f_adv_signed: float | None = (
        f_usd / adv20_dollars if (f_usd is not None and adv20_dollars > 0.0) else None
    )
    abs_f_over_adv = abs(f_adv_signed) if f_adv_signed is not None else None
    flow_aligned = (
        float(np.sign(f_usd) * np.sign(basis_bps))
        if (f_usd is not None and basis_bps is not None)
        else None
    )
    complex_intensity = complex_aum_usd / adv20_dollars if adv20_dollars > 0.0 else None

    day_low, day_high, p_1555 = stats["day_low"], stats["day_high"], stats["p_1555"]
    if day_low is not None and day_high is not None and day_high > day_low and p_1555 is not None:
        range_pos_1555 = (p_1555 - day_low) / (day_high - day_low)
    else:
        range_pos_1555 = None

    day_vol_ratio = None
    rv = stats["realized_vol_1min"]
    if rv is not None and vol20 is not None and np.isfinite(vol20) and vol20 > 0.0:
        day_vol_ratio = rv / vol20

    return {
        "abs_f_over_adv": abs_f_over_adv,
        "flow_aligned": flow_aligned,
        "complex_intensity": complex_intensity,
        "range_pos_1555": range_pos_1555,
        "month_end": 1.0 if is_month_end(session) else 0.0,
        "day_vol_ratio": day_vol_ratio,
        # diagnostics (NOT in FEATURE_COLS -- report-only / null-rate context)
        "F_usd": f_usd,
        "f_adv_signed": f_adv_signed,
        "r_pinned": r,
        "p_1555": p_1555,
        "day_low": day_low,
        "day_high": day_high,
        "flow_coef": flow_coef,
        "complex_aum_usd": complex_aum_usd,
    }


# --------------------------------------------------------------------------- batch / disk-backed


def _prior_close(closes: list[tuple[str, float]], session_iso: str) -> float | None:
    """The prior SESSION's official close strictly before ``session_iso`` --
    F(t)'s pinned r-window denominator. ``closes`` is any-order
    (session_iso, close) pairs (bars1d); mirrors
    ``moc_gbm.trailing_vol20``'s PIT-filtering convention exactly."""
    prior = sorted((d, c) for d, c in closes if d < session_iso and c is not None and c > 0.0)
    return float(prior[-1][1]) if prior else None


def _load_daily_closes(symbol: str) -> list[tuple[str, float]]:
    """Daily (session_iso, close) pairs from ``data/raw/sip/bars1d`` (UTC-date
    key) -- the SAME convention ``models/moc_gbm.py`` and
    ``apps/run_basis_trial.py`` each already use (independently duplicated a
    3rd time here rather than importing a private underscored helper across
    modules)."""
    from datetime import UTC, datetime

    p = Path("data/raw/sip/bars1d") / f"{symbol.upper()}.parquet"
    if not p.exists():
        return []
    df = pl.read_parquet(p)
    out: list[tuple[str, float]] = []
    for r in df.iter_rows(named=True):
        d = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
        out.append((d, float(r["close"])))
    return out


def build_features_frame(
    events: pl.DataFrame,
    *,
    bbo_dir: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    anchors_path: str | Path = DEFAULT_ANCHORS_PATH,
    anchors: pl.DataFrame | None = None,
) -> tuple[pl.DataFrame, dict]:
    """Batch-build the 6 frozen features (+ diagnostics) onto every row of
    ``events`` (one row per (symbol, session) candidate; the M8 meta-frame
    shape). Returns ``(features_df, funnel)``.

    ADV20 (``adv20_dollars``) and ``basis_bps`` are REQUIRED input columns,
    always reused from ``events`` (never recomputed -- FLAGGED CHOICE #5).
    ``vol20`` is reused from ``events`` when present, else recomputed via
    ``moc_gbm.trailing_vol20`` (``funnel["vol20_source"]`` states which).
    """
    required = {"symbol", "session", "adv20_dollars", "basis_bps"}
    missing = required - set(events.columns)
    if missing:
        raise KeyError(f"m8v2 features require columns {sorted(missing)} on the input frame")

    if anchors is None:
        anchors = load_letf_anchors(registry_path, anchors_path)

    df = events.with_columns(pl.col("session").str.to_date().alias("_dte")).with_columns(
        pl.date(pl.col("_dte").dt.year(), pl.col("_dte").dt.month(), 1).alias("_month_start")
    )
    df = attach_flow_coef(df, anchors)
    df = attach_complex_aum(df, anchors)

    has_vol20 = "vol20" in events.columns

    root = bbo_root(bbo_dir)
    month_cache: dict[tuple[str, str], pl.DataFrame | None] = {}
    closes_cache: dict[str, list[tuple[str, float]]] = {}

    def _bbo_raw(sym: str, month: str) -> pl.DataFrame | None:
        key = (sym, month)
        if key not in month_cache:
            p = partition_path(root, sym, month)
            month_cache[key] = pl.read_parquet(p) if p.exists() else None
        return month_cache[key]

    def _closes(sym: str) -> list[tuple[str, float]]:
        if sym not in closes_cache:
            closes_cache[sym] = _load_daily_closes(sym)
        return closes_cache[sym]

    rows_out: list[dict] = []
    for row in df.iter_rows(named=True):
        sym, session = row["symbol"], row["session"]
        raw = _bbo_raw(sym, session[:7])
        closes = _closes(sym)
        vol20 = row["vol20"] if has_vol20 else trailing_vol20(closes, session)
        prior_c = _prior_close(closes, session)
        rows_out.append(
            build_v2_feature_row(
                session=session,
                basis_bps=row["basis_bps"],
                adv20_dollars=float(row["adv20_dollars"]),
                flow_coef=float(row["flow_coef"]),
                complex_aum_usd=float(row["complex_aum_usd"]),
                vol20=vol20,
                bbo_frame=raw,
                prior_close=prior_c,
            )
        )

    feat_df = pl.DataFrame(rows_out, schema=_ROW_SCHEMA, orient="row")
    out = pl.concat([df, feat_df], how="horizontal").drop("_dte", "_month_start")

    n = out.height
    funnel = {
        "n_events": n,
        "adv20_source": "event_frame",
        "vol20_source": "event_frame" if has_vol20 else "recomputed_moc_gbm.trailing_vol20",
        "basis_source": "event_frame",
        "no_p_1555_or_bbo": int(out["p_1555"].null_count()),
        "no_r_pinned": int(out["r_pinned"].null_count()),
        "no_day_range": int(
            (
                out["day_low"].is_null()
                | out["day_high"].is_null()
                | (out["day_high"] <= out["day_low"])
            ).sum()
        ),
        "no_day_vol_ratio": int(out["day_vol_ratio"].null_count()),
        "feature_null_counts": {c: int(out[c].null_count()) for c in FEATURE_COLS},
        "feature_null_rates": {
            c: (round(out[c].null_count() / n, 4) if n else None) for c in FEATURE_COLS
        },
    }
    return out, funnel


# --------------------------------------------------------------------------- report-only cross-check


def f_adv_cross_check(
    features_df: pl.DataFrame,
    cellA_path: str | Path = "research/experiments/M12-mechanism/cellA_events.parquet",
) -> dict:
    """REPORT-ONLY: Pearson corr of the recomputed SIGNED F/ADV
    (``f_adv_signed`` = F_usd/adv20, this module's PINNED r-window) vs M12's
    ``cellA_events.parquet`` ``F_adv`` column (M12's open->15:55 mid r-window),
    on overlapping (symbol, session). NEVER used in features -- the two
    r-windows differ by construction (registered 2026-07-20 supersession), so
    a strong-but-imperfect correlation is the EXPECTED, informative outcome,
    not a bug."""
    p = Path(cellA_path)
    if not p.exists():
        return {"available": False, "n_overlap": 0, "corr": None}
    other = pl.read_parquet(p).select(["symbol", "session", "F_adv"]).rename(
        {"F_adv": "F_adv_m12"}
    )
    mine = features_df.select(["symbol", "session", "f_adv_signed"]).drop_nulls()
    joined = mine.join(other, on=["symbol", "session"], how="inner").drop_nulls()
    if joined.height < 2:
        return {"available": True, "n_overlap": joined.height, "corr": None}
    corr = float(
        np.corrcoef(
            joined["f_adv_signed"].to_numpy(), joined["F_adv_m12"].to_numpy()
        )[0, 1]
    )
    return {"available": True, "n_overlap": joined.height, "corr": corr}
