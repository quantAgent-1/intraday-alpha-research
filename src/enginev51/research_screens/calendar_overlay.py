"""M25 calendar-flow forward overlay (family ``calendar_overlay_v1``).

Registered 2026-07-23 (M3_REGISTRATION.md, section "## M25 -- calendar-flow forward
overlay"), FORWARD-JUDGED ONLY. The motivating prior (the M14 ``moc_diagnostic_v1``
MONTH_END/QUAD_WITCH readout) is DISCLOSED-AS-SEEN and fully consumed, so this family
takes NO historical look of any kind: it freezes two calendar cells now and is judged
EXCLUSIVELY on genuinely forward sessions that accrue via the M10 clock (the M20F
pattern). ``$0``; no data purchases; no champion-rule motion.

Frozen cells (definitions VERBATIM from the M14 registration, no motion):

* C1 MONTH_END -- the last OWNED session of the calendar month (the M14 "within the
  owned session set" convention). When the owned-session set is unavailable the
  function falls back to the last BUSINESS day of the month (weekday-only); the two
  conventions differ on holiday-shortened month-ends, which is why the report always
  computes flags against the ledger's own distinct sessions. On an ACCRUING ledger a
  non-quad-witch session in the LATEST owned month is PENDING -- its month-end status
  is unresolvable until a later-month session exists (orchestrator ruling
  2026-07-23) -- and is excluded from the MONTH_END/ORDINARY counts and every
  evaluation until it resolves.
* C2 QUAD_WITCH -- the 3rd Friday of Mar/Jun/Sep/Dec (pure calendar).

A session is EXACTLY one of {MONTH_END, QUAD_WITCH, ORDINARY}. Tie rule
(registration): a month-end quad-witch -- rare -- counts QUAD_WITCH.

The overlay splits the M10 classical stream's per-event net by flag and reports it
next to the M10 status streams (display/report-only). A cell becomes eligible for its
ONE evaluation only when the FORWARD flagged sample first reaches n_flagged >= 30
(the registered floor; the harness refuses evaluation below it). A cell PASS requires
the forward flagged mean > forward ordinary mean AND the day-clustered CI-lower of the
flagged-minus-ordinary difference > 0 at that first n >= 30 evaluation. PASS makes a
calendar boost an ADMISSIBLE feature for the post-forward-gate adoption registration --
NEVER a standalone trading change; there is no trading consequence in this code.

Read-only on the forward ledger: this module imports ``forward_paper.load_ledger``
only and never appends to or writes the ledger.
"""

from __future__ import annotations

import calendar as _calmod
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import structlog

from enginev51.apps.forward_paper import load_ledger  # read-only forward-ledger access
from enginev51.backtest import stress
from enginev51.protocol import experiments_dir

log = structlog.get_logger(__name__)

# --------------------------------------------------------------------------- #
# M25 registration (2026-07-23, M3_REGISTRATION.md section M25). Do not tune.
# --------------------------------------------------------------------------- #
FAMILY = "calendar_overlay_v1"
CELLS: tuple[str, ...] = ("MONTH_END", "QUAD_WITCH")
ORDINARY = "ORDINARY"
# PENDING: a non-quad-witch session in the LATEST owned month, whose MONTH_END status
# is not yet resolvable (an accruing ledger cannot know a month's last owned session
# until a later-month session exists -- orchestrator ruling 2026-07-23). PENDING
# sessions are excluded from BOTH the MONTH_END and ORDINARY counts and from any
# evaluation sample; they resolve once a later month appears. QUAD_WITCH is
# calendar-pure and NEVER pends.
PENDING = "PENDING"
FLAGS: tuple[str, ...] = ("QUAD_WITCH", "MONTH_END", ORDINARY)
QUAD_WITCH_MONTHS = (3, 6, 9, 12)  # Mar/Jun/Sep/Dec
MIN_FLAGGED = 30  # registered forward evaluation floor (one evaluation per cell)
OUT_SUBDIR = "M25-calendar-overlay"
_CI_SEED = 7       # repo reproducibility constant (registration-pinned)
_CI_N_BOOT = 2000  # registration-pinned bootstrap count
# --------------------------------------------------------------------------- #

__all__ = [
    "CELLS",
    "FAMILY",
    "MIN_FLAGGED",
    "OUT_SUBDIR",
    "assert_not_evaluated",
    "canonical_out_dir",
    "eval_state_path",
    "evaluate",
    "flag_of",
    "latest_owned_month",
    "load_ledger",
    "mark_evaluated",
    "month_end_session_set",
    "out_dir_for",
    "overlay_report",
    "PENDING",
]


# --------------------------------------------------------------------------- flags


def _is_quad_witch(d: date) -> bool:
    """3rd Friday of Mar/Jun/Sep/Dec (pure calendar).

    The 3rd Friday always falls on day-of-month 15..21 (the first Friday is day
    1..7), so ``weekday() == 4`` within that window pins it exactly.
    """
    return d.month in QUAD_WITCH_MONTHS and d.weekday() == 4 and 15 <= d.day <= 21


def _last_business_day(year: int, month: int) -> date:
    """Last weekday (Mon-Fri) of the calendar month -- the owned-set fallback."""
    d = date(year, month, _calmod.monthrange(year, month)[1])
    while d.weekday() >= 5:  # Saturday=5, Sunday=6
        d -= timedelta(days=1)
    return d


def month_end_session_set(owned_sessions: list[str]) -> set[str]:
    """The last OWNED session of each calendar month present in ``owned_sessions``.

    ISO date strings sort lexicographically in chronological order, so the max
    string per ``YYYY-MM`` key IS that month's last owned session (the M14 "within
    the owned session set" convention).
    """
    best: dict[str, str] = {}
    for s in owned_sessions:
        ym = s[:7]
        if ym not in best or s > best[ym]:
            best[ym] = s
    return set(best.values())


def latest_owned_month(owned_sessions: list[str]) -> str | None:
    """The max ``YYYY-MM`` present in ``owned_sessions`` (``None`` if empty).

    A non-quad-witch session in this month cannot yet be resolved to MONTH_END: on
    an accruing ledger its month's LAST owned session is unknown until a later-month
    session arrives, so such sessions are PENDING (orchestrator ruling 2026-07-23).
    """
    return max((s[:7] for s in owned_sessions), default=None)


def flag_of(session_iso: str, owned_sessions: list[str] | None = None) -> str:
    """Classify ``session_iso`` as QUAD_WITCH | MONTH_END | ORDINARY | PENDING.

    QUAD_WITCH (pure calendar) is checked FIRST so the registration tie rule holds:
    a month-end that is also a 3rd-Friday quad-witch counts QUAD_WITCH, and a
    current-month quad-witch flags QW immediately (it never pends). MONTH_END is the
    last OWNED session of the month when ``owned_sessions`` is supplied (the M14
    convention).

    PENDING (owned path only): a non-quad-witch session in the LATEST owned month is
    PENDING because the month's last owned session is not yet resolvable on an
    accruing ledger (orchestrator ruling 2026-07-23); it resolves once a later-month
    session exists. When ``owned_sessions`` is ``None`` the function falls back to
    the last BUSINESS day of the month (weekday-only) and NEVER pends -- that path is
    a pure calendar convention that can differ from the owned convention on
    holiday-shortened month-ends.
    """
    d = date.fromisoformat(session_iso)
    if _is_quad_witch(d):
        return "QUAD_WITCH"
    if owned_sessions is not None:
        if session_iso[:7] == latest_owned_month(owned_sessions):
            return PENDING
        return "MONTH_END" if session_iso in month_end_session_set(owned_sessions) else ORDINARY
    return "MONTH_END" if d == _last_business_day(d.year, d.month) else ORDINARY


def _classify(session_iso: str, month_end_set: set[str], latest_ym: str | None) -> str:
    """Row-level flag against a PRECOMPUTED month-end set + latest owned month.

    QUAD_WITCH wins the tie and never pends; a non-QW session in ``latest_ym`` is
    PENDING (month-end unresolved on an accruing ledger).
    """
    d = date.fromisoformat(session_iso)
    if _is_quad_witch(d):
        return "QUAD_WITCH"
    if session_iso[:7] == latest_ym:
        return PENDING
    return "MONTH_END" if session_iso in month_end_set else ORDINARY


# --------------------------------------------------------------------------- CI


def _cell_ci(values: np.ndarray, sessions: np.ndarray) -> dict:
    """(mean, ci_lo, ci_hi, n, n_sessions) day-clustered over ``net_bps``.

    Wraps ``stress.clustered_mean_ci`` (session bootstrap, cluster key = the ISO
    ``session`` string, n_boot=2000, seed=7 -- registration-pinned).
    """
    n = int(values.shape[0])
    if n == 0:
        return {"n": 0, "sessions": 0, "mean_net_bps": None, "ci_lo": None, "ci_hi": None}
    m, lo, hi = stress.clustered_mean_ci(values, sessions, n_boot=_CI_N_BOOT, seed=_CI_SEED)
    return {
        "n": n,
        "sessions": int(np.unique(sessions).shape[0]),
        "mean_net_bps": round(m, 4),
        "ci_lo": round(lo, 4),
        "ci_hi": round(hi, 4),
    }


# --------------------------------------------------------------------------- report


def _flagged_classical(ledger: pl.DataFrame) -> pl.DataFrame:
    """The taken_classical stream annotated with a ``flag`` column.

    Flags are computed against ``owned_sessions`` = the LEDGER's distinct sessions
    (the M14 owned-set convention), so a month-end is the last session actually
    collected in that calendar month, never a bare calendar date.
    """
    if ledger.height == 0:
        return ledger.with_columns(pl.lit(None, dtype=pl.Utf8).alias("flag")).head(0)
    owned = sorted(ledger["session"].unique().to_list())
    me_set = month_end_session_set(owned)
    latest_ym = latest_owned_month(owned)
    taken = ledger.filter(pl.col("taken_classical").fill_null(False))
    if taken.height == 0:
        return taken.with_columns(pl.lit(None, dtype=pl.Utf8).alias("flag"))
    flags = [_classify(s, me_set, latest_ym) for s in taken["session"].to_list()]
    return taken.with_columns(pl.Series("flag", flags, dtype=pl.Utf8))


def overlay_report(ledger: pl.DataFrame) -> dict:
    """Split the taken_classical stream by calendar flag (display/report-only).

    Returns per-flag n / sessions / mean net_bps / day-clustered CI plus an
    ``eligible_for_evaluation`` map (``{cell: n_flagged >= 30}`` for the two frozen
    cells). Sessions in the LATEST owned month whose MONTH_END status is not yet
    resolvable are PENDING (orchestrator ruling 2026-07-23): they are EXCLUDED from
    both the MONTH_END and ORDINARY counts (and from every eligibility count) and
    reported separately as ``n_pending`` / ``pending_sessions``. ALWAYS display-only
    -- there is no trading consequence here, and the registered evaluation is a
    separate, state-gated one-shot (:func:`evaluate`).
    """
    flagged = _flagged_classical(ledger)
    by_flag: dict[str, dict] = {}
    for flag in FLAGS:
        sub = flagged.filter(pl.col("flag") == flag) if flagged.height else flagged
        vals = sub["net_bps"].to_numpy() if sub.height else np.array([], dtype=float)
        sess = sub["session"].to_numpy() if sub.height else np.array([], dtype=object)
        by_flag[flag] = _cell_ci(vals, sess)
    pending = flagged.filter(pl.col("flag") == PENDING) if flagged.height else flagged
    return {
        "family": FAMILY,
        "n_sessions_total": int(ledger["session"].n_unique()) if ledger.height else 0,
        "n_taken_classical": int(flagged.height),
        "asof_span": (
            [ledger["session"].min(), ledger["session"].max()] if ledger.height else []
        ),
        "by_flag": by_flag,
        "n_pending": int(pending.height),
        "pending_sessions": int(pending["session"].n_unique()) if pending.height else 0,
        "eligible_for_evaluation": {
            cell: by_flag[cell]["n"] >= MIN_FLAGGED for cell in CELLS
        },
        "min_flagged": MIN_FLAGGED,
    }


# --------------------------------------------------------------------------- one-shot state


def canonical_out_dir() -> Path:
    """The ONE canonical M25 evaluation-state directory.

    The one-evaluation-per-cell gate is anchored here so it can never be relocated
    (a fresh out-dir would otherwise find no state file and defeat the guarantee);
    the CLI passes no directory and always resolves to this path.
    """
    return experiments_dir() / OUT_SUBDIR


def out_dir_for(out_dir: str | Path | None = None) -> Path:
    """Resolve the M25 state directory. ``out_dir`` exists ONLY for hermetic tests
    (a tmp path); the CLI never supplies it, so the default IS ``canonical_out_dir``
    and the evaluation state is unrelocatable in production."""
    p = Path(out_dir) if out_dir is not None else canonical_out_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p


def eval_state_path(cell: str, out_dir: str | Path | None = None) -> Path:
    """Per-cell evaluation-state file (one evaluation per cell -> one file each)."""
    return out_dir_for(out_dir) / f"eval_state_{cell}.json"


def assert_not_evaluated(cell: str, out_dir: str | Path | None = None) -> None:
    """Enforce the family's SINGLE registered evaluation per cell.

    A present ``eval_state_<cell>.json`` refuses a second evaluation of that cell --
    the registration allows ONE evaluation per cell at the first n >= 30 crossing.
    """
    path = eval_state_path(cell, out_dir)
    if path.exists():
        raise RuntimeError(
            f"M25 cell {cell} already evaluated ({path}); the family allows ONE "
            "evaluation per cell (first n_flagged >= 30 crossing). No re-look."
        )


def mark_evaluated(
    cell: str,
    result: dict,
    out_dir: str | Path | None = None,
    *,
    git_sha: str | None = None,
) -> Path:
    """Record the spent evaluation (``eval_state_<cell>.json``): verdict + numbers."""
    path = eval_state_path(cell, out_dir)
    path.write_text(
        json.dumps(
            {
                "family": FAMILY,
                "cell": cell,
                "verdict": result.get("verdict"),
                "git_sha": git_sha,
                "spent_ts": datetime.now(UTC).isoformat(),
                "result": result,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


# --------------------------------------------------------------------------- evaluate


def evaluate(ledger: pl.DataFrame, cell: str, out_dir: str | Path | None = None) -> dict:
    """The family's SINGLE registered evaluation of one frozen cell.

    REFUSES (raises) when n_flagged < 30 (the registered floor) and when the cell
    has already been evaluated (state file present). When eligible it computes the
    flagged-minus-ordinary difference bar per the registration:

    * point = forward flagged mean - forward ordinary mean;
    * the CI is the day-clustered bootstrap (cluster = ISO session, seed 7,
      2000 draws) of the flagged events SHIFTED by the fixed ordinary mean -- i.e.
      the CI of the flagged-mean-minus-ordinary-mean gap;
    * PASS = flagged mean > ordinary mean AND gap CI-lower > 0;
    * FAIL = gap CI-upper < 0 (the gap is clearly negative);
    * BETWEEN = the gap CI straddles 0.

    PASS/FAIL/BETWEEN are display flags; there is NO trading consequence in code. The
    result is written to the per-cell state file, spending the one evaluation.
    ``out_dir`` is for hermetic tests only; the CLI resolves the canonical path.
    """
    if cell not in CELLS:
        raise ValueError(f"unknown M25 cell {cell!r}; expected one of {CELLS}")

    # Already-evaluated guard first (a second call of any kind is refused), then the
    # registered n >= 30 floor (a below-floor call is NOT a spent look).
    assert_not_evaluated(cell, out_dir)

    flagged = _flagged_classical(ledger)
    cell_rows = flagged.filter(pl.col("flag") == cell) if flagged.height else flagged
    ord_rows = flagged.filter(pl.col("flag") == ORDINARY) if flagged.height else flagged
    n_flagged = int(cell_rows.height)

    if n_flagged < MIN_FLAGGED:
        raise RuntimeError(
            f"M25 cell {cell} not eligible: n_flagged={n_flagged} < {MIN_FLAGGED} "
            "(the registered forward evaluation floor). The overlay report is safe "
            "any time; evaluation waits for the first n >= 30 crossing."
        )
    if ord_rows.height == 0:
        raise RuntimeError(
            f"M25 cell {cell}: no ORDINARY comparator events; cannot form the "
            "flagged-minus-ordinary gap. Refusing."
        )

    flagged_vals = cell_rows["net_bps"].to_numpy()
    flagged_sess = cell_rows["session"].to_numpy()
    ord_vals = ord_rows["net_bps"].to_numpy()
    ord_vals = ord_vals[~np.isnan(ord_vals)]
    ordinary_mean = float(ord_vals.mean())
    flagged_mean = float(flagged_vals[~np.isnan(flagged_vals)].mean())

    # Gap CI: bootstrap the flagged events shifted by the FIXED ordinary mean, so the
    # point estimate is flagged_mean - ordinary_mean and the cluster (session) draw
    # widens the interval for autocorrelated days (registration bar).
    gap_mean, gap_lo, gap_hi = stress.clustered_mean_ci(
        flagged_vals - ordinary_mean, flagged_sess, n_boot=_CI_N_BOOT, seed=_CI_SEED
    )

    passes = bool(flagged_mean > ordinary_mean and gap_lo > 0)
    if passes:
        verdict = "PASS"
    elif gap_hi < 0:
        verdict = "FAIL"
    else:
        verdict = "BETWEEN"

    result = {
        "family": FAMILY,
        "cell": cell,
        "verdict": verdict,
        "n_flagged": n_flagged,
        "n_flagged_sessions": int(cell_rows["session"].n_unique()),
        "n_ordinary": int(ord_rows.height),
        "flagged_mean_net_bps": round(flagged_mean, 4),
        "ordinary_mean_net_bps": round(ordinary_mean, 4),
        "gap_mean_bps": round(float(gap_mean), 4),
        "gap_ci_lo": round(float(gap_lo), 4),
        "gap_ci_hi": round(float(gap_hi), 4),
        "flagged_gt_ordinary": bool(flagged_mean > ordinary_mean),
        "gap_ci_lo_gt_0": bool(gap_lo > 0),
        "min_flagged": MIN_FLAGGED,
        "ci_seed": _CI_SEED,
        "ci_n_boot": _CI_N_BOOT,
    }
    mark_evaluated(cell, result, out_dir)
    log.info("m25_evaluate", cell=cell, verdict=verdict, n_flagged=n_flagged)
    return result
