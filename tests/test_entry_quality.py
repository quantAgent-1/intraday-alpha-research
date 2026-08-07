"""Tests for the entry-quality features + authoring gate (M3-H2-entry-quality-v1).

Synthetic event-bar frames with hand-computed f1-f4 (arithmetic in the comments),
completed-second point-in-time discipline, warmup, and the gate boundary cases at
every registered threshold including the f3 sign-agreement branch.

NS = 1e9 ns/s. Event-bar row ``ts`` is the bucket START covering [ts, ts+1s); a
bucket is completed for decision instant ``q`` iff ts <= q - 1s. We lay bars at
ts = i*NS for i = 0,1,2,... so the completed set at q = M*NS is exactly rows
i = 0..M-1 (the bucket that STARTS at q, i.e. i = M, is excluded).
"""

from __future__ import annotations

import polars as pl
import pytest

from enginev51.events.entry_quality import (
    F1_MAX,
    F2_MAX,
    F3_ABS_MAX,
    WARMUP_SECONDS,
    features_at,
    gate,
)

NS = 1_000_000_000


def _ev(spread: list, n_quotes: list, ofi: list, locked: list) -> pl.DataFrame:
    """Build a minimal event-bar frame (one row per second, ts = i*NS).

    Only the five columns features_at reads are populated; that is a strict
    subset of events.event_bars.EVENT_BARS_COLUMNS, which is all the function
    touches. ``spread`` entries may be None (a second with no quote update).
    """
    n = len(spread)
    assert len(n_quotes) == len(ofi) == len(locked) == n
    return pl.DataFrame(
        {
            "ts": [i * NS for i in range(n)],
            "spread_bps_close": spread,
            "n_quotes": [float(x) for x in n_quotes],
            "ofi": [float(x) for x in ofi],
            "locked_crossed_n": [float(x) for x in locked],
        },
        schema={
            "ts": pl.Int64,
            "spread_bps_close": pl.Float64,
            "n_quotes": pl.Float64,
            "ofi": pl.Float64,
            "locked_crossed_n": pl.Float64,
        },
    )


# --------------------------------------------------------------------------- #
# features_at — hand-computed arithmetic
# --------------------------------------------------------------------------- #


def test_features_arithmetic_single_spike_last_second():
    # 60 completed seconds (i = 0..59), all constant except a spike at i = 59.
    # Query at q = 60*NS -> cutoff 59*NS -> completed = rows i = 0..59 (60 rows).
    #
    # spread_bps_close = 10.0 for i=0..58, 13.0 at i=59
    #   non-null spread = [10]*59 + [13]; median of 60 vals = mean(30th,31st) = 10
    #   current (last completed second) = 13  ->  f1 = 13 / 10 = 1.3
    #
    # n_quotes = 3 for i=0..58, 33 at i=59
    #   last 10 completed (i=50..59) sum = 3*9 + 33 = 60
    #   rolling-10 sums (51 windows): only the window i=50..59 contains i=59,
    #   so 50 windows sum to 30 and 1 window sums to 60; median = 30
    #   ->  f2 = 60 / 30 = 2.0
    #
    # ofi = 0 for i=0..58, 10 at i=59
    #   last-10 sum = 10
    #   rolling-10 sums = [0]*50 + [10]; mean = 10/51
    #   pop var = (50*(10/51)^2 + (500/51)^2)/51 = 255000/132651 = 1.922261...
    #   pop std = 1.386456...  ->  f3 = 10 / 1.386456 = 7.212489...
    #
    # locked_crossed_n = 0 for i=0..58, 2 at i=59
    #   last-10 sum = 2  ->  f4 = 2.0
    spread = [10.0] * 59 + [13.0]
    nq = [3.0] * 59 + [33.0]
    ofi = [0.0] * 59 + [10.0]
    lck = [0.0] * 59 + [2.0]
    ev = _ev(spread, nq, ofi, lck)

    f = features_at(ev, 60 * NS)
    assert f is not None
    assert f["f1"] == pytest.approx(1.3)
    assert f["f2"] == pytest.approx(2.0)
    assert f["f3"] == pytest.approx(7.212489, abs=1e-5)
    assert f["f4"] == pytest.approx(2.0)


def test_features_div0_and_degenerate_guards():
    # spread constant 10 -> f1 = 10/10 = 1.0
    # n_quotes all 0 -> every rolling-10 sum = 0 -> median 0 -> f2 = None (div0)
    # ofi constant 5 -> every rolling-10 sum = 50 -> pop std = 0 -> f3 = 0.0 (guard)
    # locked all 0 -> f4 = 0.0
    ev = _ev([10.0] * 60, [0] * 60, [5] * 60, [0] * 60)
    f = features_at(ev, 60 * NS)
    assert f is not None
    assert f["f1"] == pytest.approx(1.0)
    assert f["f2"] is None
    assert f["f3"] == 0.0
    assert f["f4"] == 0.0


def test_features_f1_none_when_no_nonnull_spread():
    # >= 60 completed seconds but every spread is null (no quote updates) ->
    # f1 cannot be computed (no evidence); flow features still compute.
    ev = _ev([None] * 60, [4] * 60, [1] * 60, [0] * 60)
    f = features_at(ev, 60 * NS)
    assert f is not None
    assert f["f1"] is None
    # n_quotes constant 4 -> every window = 40, median 40, last-10 = 40 -> f2 = 1.0
    assert f["f2"] == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# warmup + point-in-time discipline
# --------------------------------------------------------------------------- #


def test_warmup_returns_none_below_60_completed_seconds():
    ev = _ev([10.0] * 60, [3] * 60, [0] * 60, [0] * 60)
    # q = 59*NS -> cutoff 58*NS -> completed = i=0..58 = 59 rows < 60 -> None
    assert features_at(ev, 59 * NS) is None
    # q = 60*NS -> cutoff 59*NS -> completed = i=0..59 = 60 rows -> not None
    assert features_at(ev, 60 * NS) is not None
    assert WARMUP_SECONDS == 60


def test_pit_bucket_starting_at_ts_is_excluded():
    # Base 60-second frame (i=0..59) with a spike at i=59, plus an EXTRA future
    # row at i=60 (ts = 60*NS) carrying wild values. Querying at q = 60*NS must
    # exclude the i=60 bucket (it only STARTS at q) and use i=59 as the last
    # completed second -> identical result to the 60-row frame.
    spread = [10.0] * 59 + [13.0]
    nq = [3.0] * 59 + [33.0]
    ofi = [0.0] * 59 + [10.0]
    lck = [0.0] * 59 + [2.0]
    base = features_at(_ev(spread, nq, ofi, lck), 60 * NS)

    ev_future = _ev(
        spread + [999.0], nq + [999.0], ofi + [999.0], lck + [999.0]
    )  # append i=60 with wild values
    got = features_at(ev_future, 60 * NS)

    assert got == base  # the bucket AT q leaked nothing


def test_features_none_on_empty_or_missing():
    assert features_at(None, 100 * NS) is None
    empty = _ev([], [], [], [])
    assert features_at(empty, 100 * NS) is None


# --------------------------------------------------------------------------- #
# gate — boundary cases at each registered threshold
# --------------------------------------------------------------------------- #


def _f(f1=1.0, f2=1.0, f3=0.0, f4=0.0):
    return {"f1": f1, "f2": f2, "f3": f3, "f4": f4}


def test_gate_none_features_allows_no_veto():
    # "no evidence, no veto" — regardless of direction.
    assert gate(None, 1) is True
    assert gate(None, -1) is True


def test_gate_all_pass_baseline():
    assert gate(_f(), 1) is True
    assert gate(_f(), -1) is True


def test_gate_f1_boundary():
    assert F1_MAX == 1.5
    assert gate(_f(f1=1.5), 1) is True          # <= 1.5 passes
    assert gate(_f(f1=1.5001), 1) is False       # just over fails


def test_gate_f2_boundary():
    assert F2_MAX == 3.0
    assert gate(_f(f2=3.0), 1) is True
    assert gate(_f(f2=3.0001), 1) is False


def test_gate_f4_must_be_zero():
    assert gate(_f(f4=0.0), 1) is True
    assert gate(_f(f4=1.0), 1) is False          # any locked/crossed vetoes
    # f4 vetoes even when everything else passes cleanly.
    assert gate(_f(f1=1.0, f2=1.0, f3=0.0, f4=2.0), 1) is False


def test_gate_f3_magnitude_boundary_direction_agnostic():
    assert F3_ABS_MAX == 2.0
    # |f3| <= 2.0 passes for either direction regardless of sign.
    assert gate(_f(f3=2.0), 1) is True
    assert gate(_f(f3=-2.0), 1) is True
    assert gate(_f(f3=2.0), -1) is True
    assert gate(_f(f3=-2.0), -1) is True


def test_gate_f3_sign_agreement_branch():
    # |f3| > 2.0 is allowed ONLY when sign(f3) == direction.
    # f3 = +3 (sign +1)
    assert gate(_f(f3=3.0), 1) is True           # sign matches long
    assert gate(_f(f3=3.0), -1) is False          # sign disagrees with short
    # f3 = -3 (sign -1)
    assert gate(_f(f3=-3.0), -1) is True          # sign matches short
    assert gate(_f(f3=-3.0), 1) is False          # sign disagrees with long
    # just past the magnitude boundary with a disagreeing sign -> veto
    assert gate(_f(f3=2.0001), -1) is False
    assert gate(_f(f3=-2.0001), 1) is False


def test_gate_subfeature_none_does_not_veto_its_clause():
    # div0/no-evidence guards yield None on a single dimension; that dimension
    # must not veto (per-dimension "no evidence, no veto").
    assert gate(_f(f1=None), 1) is True
    assert gate(_f(f2=None), 1) is True
    # but a genuinely failing OTHER clause still vetoes.
    assert gate(_f(f1=None, f4=1.0), 1) is False


def test_gate_conjunction_all_must_hold():
    # every clause individually satisfied except one -> veto.
    assert gate(_f(f1=2.0), 1) is False          # f1 fails
    assert gate(_f(f2=4.0), 1) is False          # f2 fails
    assert gate(_f(f3=5.0), -1) is False         # f3 sign/mag fails
    assert gate(_f(f4=1.0), 1) is False          # f4 fails


# --------------------------------------------------------------------------- #
# run_trial flag-off byte-identity (reasoning, not a heavy integration test)
# --------------------------------------------------------------------------- #


def test_run_trial_entry_gate_defaults_off_and_is_isolated():
    """The gate is guarded by ``if entry_gate and arm == "a0"``; ``entry_gate``
    defaults to False on both ``run_trial.run_trial`` and the CLI ``--entry-gate``
    flag. With the flag off, the guarded block is never entered, no counter is
    touched, and no plan is dropped — so every authored/taken/replayed path is
    byte-identical to the ungated baseline. That identity is a property of the
    guard placement (asserted here on the defaults), not something a re-run of the
    whole pipeline could add confidence to.
    """
    import inspect

    from enginev51.apps import run_trial

    sig = inspect.signature(run_trial.run_trial)
    assert sig.parameters["entry_gate"].default is False

    opt = next(p for p in run_trial.main.params if p.name == "entry_gate")
    assert opt.is_flag is True
    assert opt.default is False
