"""M23 dynamic-sizing shadow harness (family ``sizing_shadow_v1``).

Registered 2026-07-23 (M3_REGISTRATION.md, section "M23 -- dynamic-sizing shadow
(probability-scaled allocation)" + its "Pre-data clarifications" block) BEFORE any
economics exist. Frozen design: ``research/experiments/M23-sizing-shadow/DESIGN.md``
(the orchestrator's A1-A8 rulings mirror the registration's clarifications). Nothing
here may be tuned; the family is REPORT-ONLY -- no gate, no look-state, no promotion
rule -- a stateless idempotent derived measurement riding beside the M10 forward clock.

Doctrine (M18/M15): sizing MULTIPLIES edge, it cannot create it. This instrument
measures ONE thing -- pure allocation -- via the daily paired difference

    delta_t = (sized book P&L) - (equal-notional book P&L)   at MATCHED gross,

so leverage/gross effects cancel by construction. The sized book allocates the SAME
session gross across its events by weight w = T(p) * v:

  * T(p) tiers the frozen P(win): p<0.55 -> 0.0 ; 0.55<=p<0.60 -> 1.0 ; p>=0.60 -> 1.5.
  * v = clip(sigma_med5 / sigma_i, 0.5, 2.0); sigma_i = stdev of SIMPLE close-to-close
    RAW daily returns over the trailing 20 completed sessions ending t-1 (PAST-ONLY,
    raw bars1d -- L2); sigma_med5 = same-window median across the champion 5.

Statistics follow ADIA Lab Research Paper No. 19 (Lopez de Prado, Lipton & Zoonekynd,
2026): SR at NATIVE frequency; PSR under the generalized (non-Normal AR(1)) sampling
variance, evaluated with the bracket at the BENCHMARK SR0; MinTRL at alpha=0.05 next
to any significance claim; Pearson kurtosis (``fisher=False``). SR0 = 0 everywhere in
this family (ruling A7).

Boundaries enforced here:
  * NO write path to the forward ledger: this module reads ``forward_paper.load_ledger``
    and NEVER imports or reimplements any ledger append. It writes only .md/.json
    derived artifacts, never a parquet.
  * dev-reference and forward frames carry a ``source`` tag; any pooling raises
    (L9-analog) via ``assert_single_source``.
  * dev p_win = the leakage-free OOS walk-forward column already published in
    ``M8-meta-v1/oos_predictions.parquet`` (A1); forward p_win = the frozen model's
    stored ledger value.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import polars as pl
import structlog

from enginev51.apps.forward_paper import load_ledger
from enginev51.backtest import stress
from enginev51.models.moc_meta import CANDIDATE_BASIS_BPS
from enginev51.protocol import (
    INHERITED_TRIAL_FAMILIES,
    apply_seal,
    experiments_dir,
    refuse_end_on_or_after_holdout,
)

# ADIA Lab No.19 statistics. The definitions used to live in THIS module (M23 wrote
# and golden-anchored them); the 2026-08-01 structural review (J3a) MOVED them
# VERBATIM to ``enginev51.stats.adia`` so M24/M27/live/engine/the m28-m29 battery
# scripts stop importing a closed research screen for pure math. They are re-imported
# here -- NOT re-implemented -- so every historical importer keeps working with object
# IDENTITY preserved (``sizing_shadow.psr is stats.adia.psr``, test 20). ``_bracket``
# and ``lag1_autocorr`` are re-exported for the M23 golden tests that address them.
from enginev51.stats.adia import (  # noqa: F401  (identity-preserving re-export)
    _bracket,
    lag1_autocorr,
    min_trl,
    psr,
    sample_moments,
    sigma_sr,
    sr_native,
)

log = structlog.get_logger(__name__)

# --------------------------------------------------------------------------- #
# M23 registration constants (2026-07-23, M3_REGISTRATION.md section M23). Frozen;
# every constant is a counted variant. Do not tune.
# --------------------------------------------------------------------------- #
UNIVERSE: tuple[str, ...] = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")  # champion 5

P_CUT_LO = 0.55  # tier boundary: p < 0.55 -> 0
P_CUT_HI = 0.60  # tier boundary: p >= 0.60 -> 1.5
TIER_LO = 0.0
TIER_MID = 1.0
TIER_HI = 1.5

VOL_WINDOW = 20  # 20 SIMPLE returns from 21 prior closes (ruling A2/A3)
VOL_CLIP_LO = 0.5
VOL_CLIP_HI = 2.0

BOOK_NOTIONAL = 10_000.0  # $10k research book (gate-currency conventions)
DEPLOY_CAPITAL_USD = 1000.0  # deploy lens: report-only, NEVER in a comparison statistic
ALPHA = 0.05  # MinTRL / z_{1-alpha}
SEED = 7  # repo reproducibility constant
N_BOOT = 2000  # clustered-CI bootstrap draws
SR0 = 0.0  # ruling A7: SR0 = 0 everywhere in this family

# Raw bars1d ONLY (L2) -- do NOT reuse moc_gbm.trailing_vol20 (log returns).
RAW_BARS1D_DIR = Path("data/raw/sip/bars1d")

# In-house family count for the honest multiple-testing context line.
INHOUSE_TRIAL_FAMILIES = 23

# Source tags -- dev-reference and forward are NEVER pooled (L9-analog).
SOURCE_DEV = "dev"
SOURCE_FWD = "forward"

DEV_EVENTS_PARQUET = "research/experiments/M8-meta-v1/oos_predictions.parquet"
OUT_SUBDIR = "M23-sizing-shadow"

# The three existing M10 display streams -> the boolean ledger column selecting each.
M10_STREAM_COLS: dict[str, str] = {
    "classical": "taken_classical",
    "meta": "taken_meta",
    "portfolio": "selected",
}


# =========================================================================== guards


def assert_before_holdout(end: date) -> None:
    """Refuse any dev-reference run reaching the sealed holdout (PROTOCOL v6 section 1).

    The dev event stream is strictly <= 2026-05-31; forward is post-seal by
    construction and never routes through this guard. Delegates to the protocol's
    canonical date guard, which RAISES ``SealViolation`` -- the bare ``assert`` this
    used to carry is compiled out under ``python -O`` (code review 2026-08-01 J2 /
    2026-07-28 B7). Name and signature are unchanged for every existing caller."""
    refuse_end_on_or_after_holdout(end)


def strip_holdout(frame: pl.DataFrame) -> pl.DataFrame:
    """Drop holdout-era rows (session >= HOLDOUT_START) from a dev frame (the
    standard seal).

    Routed through ``protocol.apply_seal`` (J2 choke point) rather than re-expressing
    the filter: the predicate is the SAME expression apply_seal applies, so no
    pre-holdout row changes, but the split-consistency ceremony now runs on this path
    too. The shape early-return is kept byte-identical: apply_seal REQUIRES a
    ``session`` column, and this guard has always tolerated frames without one."""
    if "session" not in frame.columns or frame.height == 0:
        return frame
    return apply_seal(frame)


def assert_single_source(frame: pl.DataFrame) -> None:
    """Refuse a frame that mixes dev and forward rows (L9-analog: no statistic ever
    crosses the two sources)."""
    if "source" not in frame.columns or frame.height == 0:
        return
    srcs = set(frame["source"].unique().to_list())
    if len(srcs) > 1:
        raise ValueError(
            f"dev/forward pooling violation: {sorted(srcs)} -- the M23 sources are "
            "measured in strictly separate sections (L9-analog)"
        )


# =========================================================================== sizing


def tier(p: float) -> float:
    """P(win) tier T(p): p<0.55 -> 0.0 ; 0.55<=p<0.60 -> 1.0 ; p>=0.60 -> 1.5.

    Boundary convention (test_tier_pins): 0.549->0, 0.55->1.0, 0.599->1.0, 0.60->1.5."""
    if p < P_CUT_LO:
        return TIER_LO
    if p < P_CUT_HI:
        return TIER_MID
    return TIER_HI


def is_vol_history_skip(sigma_i: float | None) -> bool:
    """True when sigma_i signals INSUFFICIENT vol history (< 21 prior closes ->
    trailing_raw_vol NaN, or missing). This is distinct from a finite tiny/zero sigma,
    which is legitimate history that hits the HI clip. Such events are counted and
    reported as ``n_vol_history_skips`` per source section (orchestrator ruling)."""
    return bool(sigma_i is None or (isinstance(sigma_i, float) and np.isnan(sigma_i)))


def vol_norm(sigma_i: float | None, sigma_med5: float | None) -> float:
    """v = clip(sigma_med5 / sigma_i, 0.5, 2.0).

    Insufficient vol history (sigma_i missing/NaN) maps to v = 1.0 NEUTRAL, NOT the HI
    clip (orchestrator ruling): a symbol with no trailing window is not "low vol". A
    FINITE tiny/zero sigma is legitimate history whose ratio -> +inf and clips to
    VOL_CLIP_HI. A missing median is also neutral (1.0). No NaN/inf ever escapes."""
    if is_vol_history_skip(sigma_i):
        return 1.0  # NEUTRAL: insufficient history, not a low-vol reading
    if sigma_med5 is None or not np.isfinite(sigma_med5):
        return 1.0
    if sigma_i <= 0.0:
        return VOL_CLIP_HI  # finite zero-vol history -> ratio +inf -> legit HI clip
    return float(np.clip(sigma_med5 / sigma_i, VOL_CLIP_LO, VOL_CLIP_HI))


def trailing_raw_vol(pairs: list[tuple[str, float]], asof: str) -> float:
    """Stdev (ddof=1) of SIMPLE close-to-close returns over the trailing 20 completed
    sessions ending t-1.

    ``pairs`` = (session_iso, raw close) list from raw bars1d. The window is PAST-ONLY:
    every close with session >= ``asof`` is excluded, then the last 21 prior closes give
    20 simple returns. Fewer than 21 prior closes -> NaN (insufficient history).

    SIMPLE returns (r = c_t/c_{t-1} - 1) and ddof=1 are pinned (ruling A2); a log-return
    implementation must fail ``test_vol_simple_returns_ddof1``."""
    prior = sorted((s, c) for s, c in pairs if s < asof)
    if len(prior) < VOL_WINDOW + 1:
        return float("nan")
    closes = np.asarray([c for _, c in prior[-(VOL_WINDOW + 1):]], dtype=float)
    rets = closes[1:] / closes[:-1] - 1.0
    return float(np.std(rets, ddof=1))


def champion_sigma_med5(sigmas: list[float | None]) -> float:
    """Median of the champion 5's trailing sigmas in the SAME window (NaN/None dropped)."""
    vals = [s for s in sigmas if s is not None and np.isfinite(s)]
    if not vals:
        return float("nan")
    return float(np.median(vals))


def event_weight(p: float, sigma_i: float | None, sigma_med5: float | None) -> float:
    """Event weight w = T(p) * v (both frozen)."""
    return tier(p) * vol_norm(sigma_i, sigma_med5)


def matched_gross_notional(
    weights: np.ndarray | list[float], book: float = BOOK_NOTIONAL
) -> np.ndarray:
    """PER-SESSION matched-gross sizing (DESIGN section 4 -- the doctrinal core).

    sized_i = book * n * w_i / sum(w)  so the sized book's gross == the equal-notional
    book's gross (n * book) THAT SESSION. This is NOT run_meta_trial.sizing_overlay's
    global-mean normalization (reviewer attack 3): the renormalization denominator is
    the session's own weight sum.

    Invariants:
      * T==1 and v==1 for all events => w_i==1 => sized_i == book (bit-identical to
        equal) => delta_t == 0 (the invariant hook, test_matched_gross_invariant).
      * sum(w)==0 (all events p<0.55, or a single p<0.55 event) => ruling A4 fallback
        to EQUAL (never NaN/inf; test_matched_gross_degenerate_session)."""
    w = np.asarray(weights, dtype=float)
    n = w.shape[0]
    equal = np.full(n, book, dtype=float)
    total = float(np.nansum(w))
    if not np.isfinite(total) or total <= 0.0:
        return equal  # A4: degenerate session falls back to equal, delta_t == 0
    return book * n * w / total


# =========================================================================== panels


def _round_or_none(v: float, ndigits: int) -> float | None:
    """Round a finite value; a non-finite (NaN/inf) becomes None so no invalid token
    reaches the JSON (written with allow_nan=False)."""
    return round(float(v), ndigits) if np.isfinite(v) else None


def daily_paired_diff(frame: pl.DataFrame) -> tuple[pl.DataFrame, dict]:
    """Per-session daily paired difference delta_t = sized - equal at MATCHED gross.

    ``frame`` columns: session, net_bps, weight (+ optional ``source`` tag and
    ``vol_skip`` flag). Returns the daily delta series (one row per session, USD) and a
    counts dict (degenerate / single-event / multi-event sessions + vol-history skips --
    so the panel's effective T and the neutral-vol event count are honest)."""
    assert_single_source(frame)
    rows: list[dict] = []
    n_degen = n_single = n_multi = 0
    for sess in sorted(frame["session"].unique().to_list()):
        sub = frame.filter(pl.col("session") == sess)
        net = sub["net_bps"].to_numpy()
        w = sub["weight"].to_numpy()
        sized = matched_gross_notional(w)
        equal = np.full(net.shape, BOOK_NOTIONAL, dtype=float)
        delta = float(np.sum((sized - equal) * net) / 1e4)
        rows.append({"session": str(sess), "n_events": int(net.shape[0]), "delta_usd": delta})
        if net.shape[0] == 1:
            n_single += 1
        else:
            n_multi += 1
        if not (float(np.nansum(w)) > 0.0):
            n_degen += 1
    daily = pl.DataFrame(
        rows,
        schema={"session": pl.Utf8, "n_events": pl.Int64, "delta_usd": pl.Float64},
        orient="row",
    )
    n_vol_skips = (
        int(frame["vol_skip"].sum()) if "vol_skip" in frame.columns else 0
    )
    counts = {
        "n_degenerate_sessions": n_degen,
        "n_single_event_sessions": n_single,
        "n_multi_event_sessions": n_multi,
        "n_vol_history_skips": n_vol_skips,
    }
    return daily, counts


def sizing_panel(frame: pl.DataFrame, source: str) -> dict:
    """The primary-object panel for ONE source (dev OR forward), never pooled.

    Reports mean, day-clustered CI (ordinary bootstrap on the one-row-per-session delta
    series, ruling A8), native SR, PSR[SR0=0], displayed SE sigma_sr(SR_hat), MinTRL,
    T-to-date, and the degenerate/single/multi session counts. The $1k deploy lens is
    an INFORMATIONAL column only -- never a comparison statistic."""
    assert_single_source(frame)
    daily, counts = daily_paired_diff(frame)
    x = daily["delta_usd"].to_numpy()
    t = int(x.shape[0])
    if t == 0:
        return {
            "source": source, "T": 0, "mean_usd": None, "ci_lo_usd": None,
            "ci_hi_usd": None, "sr_native": None, "psr_sr0_0": None,
            "sigma_sr_hat": None, "min_trl": None, "gamma3": None, "gamma4": None,
            "rho": None, "mean_deploy_usd": None, **counts,
        }
    mean, lo, hi = stress.clustered_mean_ci(
        x, daily["session"].to_numpy(), n_boot=N_BOOT, seed=SEED
    )
    g3, g4, rho = sample_moments(x)
    sr = sr_native(x)
    mtrl = min_trl(sr, SR0, ALPHA, rho, g3, g4)  # computed once (N1)
    scale = DEPLOY_CAPITAL_USD / BOOK_NOTIONAL  # deploy lens: pure display rescale
    return {
        "source": source,
        "T": t,
        "mean_usd": round(float(mean), 4),
        "ci_lo_usd": round(float(lo), 4),
        "ci_hi_usd": round(float(hi), 4),
        "sr_native": round(sr, 4),
        "psr_sr0_0": _round_or_none(psr(sr, SR0, t, rho, g3, g4), 4),
        "sigma_sr_hat": _round_or_none(sigma_sr(sr, t, rho, g3, g4), 4),
        "min_trl": _round_or_none(mtrl, 2),  # +inf (sr==sr0) -> None
        "gamma3": round(g3, 4),
        "gamma4": round(g4, 4),
        "rho": round(rho, 4),
        "mean_deploy_usd": round(float(mean) * scale, 4),  # informational only
        **counts,
    }


def stream_psr_panel(frame: pl.DataFrame) -> list[dict]:
    """Display-only PSR/MinTRL panel for the three existing M10 streams
    (classical / meta / portfolio), each DAILY-aggregated (session-mean net_bps).

    The registered M10 gate is UNTOUCHED (no gate motion): this is a lens, SR0=0. A
    stream whose selector column is absent from ``frame`` is skipped."""
    assert_single_source(frame)
    out: list[dict] = []
    for name, col in M10_STREAM_COLS.items():
        if col not in frame.columns:
            continue
        sub = frame.filter(pl.col(col))
        if sub.height == 0:
            out.append({"stream": name, "T": 0, "sr_native": None, "psr_sr0_0": None,
                        "sigma_sr_hat": None, "min_trl": None})
            continue
        daily = (
            sub.group_by("session")
            .agg(pl.col("net_bps").mean().alias("net_bps"))
            .sort("session")
        )
        x = daily["net_bps"].to_numpy()
        t = int(x.shape[0])
        g3, g4, rho = sample_moments(x)
        sr = sr_native(x)
        mtrl = min_trl(sr, SR0, ALPHA, rho, g3, g4)
        out.append({
            "stream": name,
            "T": t,
            "sr_native": round(sr, 4),
            "psr_sr0_0": _round_or_none(psr(sr, SR0, t, rho, g3, g4), 4),
            "sigma_sr_hat": _round_or_none(sigma_sr(sr, t, rho, g3, g4), 4),
            "min_trl": _round_or_none(mtrl, 2),
        })
    return out


def multiple_testing_line() -> str:
    """The honest multiple-testing context line (inherited + in-house family counts)."""
    inherited = sum(INHERITED_TRIAL_FAMILIES.values())
    return (
        f"Multiple-testing context: {inherited} inherited trial families "
        f"(protocol.INHERITED_TRIAL_FAMILIES) + ~{INHOUSE_TRIAL_FAMILIES} in-house "
        "families. PSR/MinTRL are read against these honest counts; SR0=0 (ruling A7)."
    )


# =========================================================================== writers
# The instrument writes ONLY .md/.json derived artifacts. It NEVER writes a parquet and
# NEVER touches the forward ledger (test_forward_ledger_read_only).


def _fmt(v: object) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _panel_section_md(panel: dict, source_label: str) -> str:
    lines = [
        f"### {source_label} section (source={panel['source']})",
        "",
        f"- T-to-date (sessions): {panel['T']}",
        f"- mean delta_t (USD, $10k book): {_fmt(panel['mean_usd'])}",
        f"- day-clustered 95% CI: [{_fmt(panel['ci_lo_usd'])}, {_fmt(panel['ci_hi_usd'])}]",
        f"- native-frequency SR: {_fmt(panel['sr_native'])}",
        f"- PSR[SR0=0]: {_fmt(panel['psr_sr0_0'])}",
        f"- displayed SE sigma_sr(SR_hat): {_fmt(panel['sigma_sr_hat'])}",
        f"- MinTRL(alpha=0.05): {_fmt(panel['min_trl'])}",
        f"- (gamma3, gamma4, rho): ({_fmt(panel['gamma3'])}, {_fmt(panel['gamma4'])}, "
        f"{_fmt(panel['rho'])})",
        f"- degenerate / single-event / multi-event sessions: "
        f"{panel['n_degenerate_sessions']} / {panel['n_single_event_sessions']} / "
        f"{panel['n_multi_event_sessions']}",
        f"- vol-history skips (events sized at v=1.0 NEUTRAL, <21 prior closes): "
        f"{panel.get('n_vol_history_skips', 0)}",
        f"- deploy lens ($1k, informational only): mean {_fmt(panel['mean_deploy_usd'])}",
        "",
    ]
    return "\n".join(lines)


def _stream_panel_md(streams: list[dict]) -> str:
    lines = [
        "### M10 display streams (gate UNTOUCHED -- display only)",
        "",
        "| stream | T | SR | PSR[SR0=0] | sigma_sr | MinTRL |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for s in streams:
        lines.append(
            f"| {s['stream']} | {s['T']} | {_fmt(s['sr_native'])} | "
            f"{_fmt(s['psr_sr0_0'])} | {_fmt(s['sigma_sr_hat'])} | {_fmt(s['min_trl'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_panel_md(
    dev_panel: dict | None,
    fwd_panel: dict | None,
    streams: list[dict] | None,
    *,
    note: str = "",
) -> str:
    """Assemble panel.md with dev-reference and forward in STRICTLY SEPARATE sections.

    This is document assembly only -- no statistic is ever computed across the two
    sources; each section carries its own self-contained panel dict."""
    parts = [
        "# M23 dynamic-sizing shadow -- panel",
        "",
        "REPORT-ONLY (family sizing_shadow_v1). No gate, no promotion rule. "
        "delta_t = sized - equal at matched gross; SR0=0 (ruling A7).",
        "",
        "> dev-reference p_win = leakage-free OOS walk-forward column "
        "(M8-meta-v1/oos_predictions.parquet, ruling A1). The FORWARD path uses the "
        "frozen model's stored p_win.",
        "",
        multiple_testing_line(),
        "",
    ]
    if note:
        parts += [f"_{note}_", ""]
    parts += ["## Dev reference", ""]
    parts.append(
        _panel_section_md(dev_panel, "Dev reference") if dev_panel
        else "_(no dev-reference section written yet)_\n"
    )
    parts += ["## Forward to date", ""]
    parts.append(
        _panel_section_md(fwd_panel, "Forward to date") if fwd_panel
        else "_(no forward section written yet)_\n"
    )
    if streams:
        parts += ["## M10 streams", "", _stream_panel_md(streams)]
    return "\n".join(parts) + "\n"


def _out_dir(out_dir: str | Path | None = None) -> Path:
    p = Path(out_dir) if out_dir is not None else (experiments_dir() / OUT_SUBDIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_source_panel(
    panel: dict, source: str, streams: list[dict] | None = None,
    out_dir: str | Path | None = None,
) -> Path:
    """Write the per-source panel_<source>.json (self-contained; idempotent overwrite),
    then refresh the combined panel.md/json from whatever sections exist on disk."""
    d = _out_dir(out_dir)
    payload = {
        "source": source,
        "asof": datetime.now(UTC).isoformat(),
        "panel": panel,
        "streams": streams or [],
    }
    (d / f"panel_{source}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True, allow_nan=False),
        encoding="utf-8",
    )
    refresh_combined(d)
    return d / f"panel_{source}.json"


def refresh_combined(out_dir: str | Path | None = None) -> Path:
    """Regenerate panel.md + panel.json from the persisted per-source sections.

    Reads panel_dev.json / panel_forward.json if present and renders both sections;
    this is pure document assembly and never mixes a statistic across sources."""
    d = _out_dir(out_dir)

    def _load(src: str) -> dict | None:
        p = d / f"panel_{src}.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    dev = _load(SOURCE_DEV)
    fwd = _load(SOURCE_FWD)
    dev_panel = dev["panel"] if dev else None
    fwd_panel = fwd["panel"] if fwd else None
    # M10 display streams belong to the forward ledger; use the forward section's.
    streams = (fwd or {}).get("streams") if fwd else None
    md = build_panel_md(dev_panel, fwd_panel, streams)
    (d / "panel.md").write_text(md, encoding="utf-8")
    combined = {
        "family": "sizing_shadow_v1",
        "report_only": True,
        "sr0": SR0,
        "dev": dev,       # each self-contained; never pooled
        "forward": fwd,
        "multiple_testing": multiple_testing_line(),
    }
    (d / "panel.json").write_text(
        json.dumps(combined, indent=2, ensure_ascii=True, allow_nan=False),
        encoding="utf-8",
    )
    return d / "panel.md"


# =========================================================================== assembly
# Lake-touching assembly (dev + forward) lives here but is driven by the CLI. Tests are
# synthetic-only and exercise the pure kernels above; these helpers read raw bars1d.


def load_raw_closes(symbol: str, bars_dir: Path = RAW_BARS1D_DIR) -> list[tuple[str, float]]:
    """Daily (session_iso, close) pairs from RAW bars1d (L2). Mirrors
    run_basis_trial._load_daily_closes -- UTC-date key, raw closes only."""
    p = bars_dir / f"{symbol.upper()}.parquet"
    if not p.exists():
        return []
    df = pl.read_parquet(p)
    out: list[tuple[str, float]] = []
    for r in df.iter_rows(named=True):
        d = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
        out.append((d, float(r["close"])))
    return out


def attach_weights(
    events: pl.DataFrame, closes_by_symbol: dict[str, list[tuple[str, float]]]
) -> pl.DataFrame:
    """Add the frozen ``weight`` and ``vol_skip`` columns to a classical event frame.

    For each (symbol, session): sigma_i = trailing_raw_vol of that symbol; sigma_med5 =
    median over the champion 5's sigma in the SAME window; w = T(p_win) * clip(...).
    ``vol_skip`` marks events whose sigma_i is a vol-history skip (<21 prior closes ->
    NEUTRAL v=1.0), counted and reported per source section. Requires columns session,
    symbol, p_win, net_bps."""
    weights: list[float] = []
    vol_skips: list[bool] = []
    sigma_cache: dict[tuple[str, str], float] = {}

    def _sigma(sym: str, sess: str) -> float:
        key = (sym, sess)
        if key not in sigma_cache:
            sigma_cache[key] = trailing_raw_vol(closes_by_symbol.get(sym, []), sess)
        return sigma_cache[key]

    for r in events.iter_rows(named=True):
        sess = r["session"]
        sym = r["symbol"]
        sig_i = _sigma(sym, sess)
        med5 = champion_sigma_med5([_sigma(s, sess) for s in UNIVERSE])
        weights.append(event_weight(float(r["p_win"]), sig_i, med5))
        vol_skips.append(is_vol_history_skip(sig_i))
    return events.with_columns(
        pl.Series("weight", weights, dtype=pl.Float64),
        pl.Series("vol_skip", vol_skips, dtype=pl.Boolean),
    )


def load_dev_events(path: str | Path = DEV_EVENTS_PARQUET) -> pl.DataFrame:
    """Load + seal the dev event stream (A1 OOS walk-forward p_win), classical base
    universe (|basis|>=CANDIDATE_BASIS_BPS, all p), champion 5, tagged source=dev."""
    df = pl.read_parquet(path)
    df = strip_holdout(df)
    df = df.filter(
        (pl.col("basis_bps").abs() >= CANDIDATE_BASIS_BPS)
        & (pl.col("symbol").is_in(UNIVERSE))
    )
    return df.with_columns(pl.lit(SOURCE_DEV).alias("source"))


def load_forward_classical() -> pl.DataFrame:
    """Read the forward ledger (READ-ONLY via forward_paper.load_ledger) and select the
    classical base (taken_classical, |basis|>=threshold, champion 5), tagged
    source=forward. NEVER writes the ledger."""
    led = load_ledger()
    if led.height == 0:
        return led.with_columns(pl.lit(SOURCE_FWD).alias("source"))
    led = led.filter(
        pl.col("taken_classical")
        & (pl.col("basis_bps").abs() >= CANDIDATE_BASIS_BPS)
        & (pl.col("symbol").is_in(UNIVERSE))
    )
    return led.with_columns(pl.lit(SOURCE_FWD).alias("source"))
