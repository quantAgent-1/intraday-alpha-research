"""Tests for the M23 dynamic-sizing shadow harness
(``research_screens.sizing_shadow``).

Synthetic fixtures + hand-derived literals ONLY -- no real data lake, no network
(the family's dev reference is the orchestrator's single computation). Mirrors the
fixture style of ``test_m22_earnings_close``. Covers the 15 checks in DESIGN.md
section 6 + the mandatory off-anchor PSR case (a bracket(SR0)/bracket(SR_hat) swap
must fail): the PSR/MinTRL golden anchor, the off-anchor PSR, the Pearson-kurtosis
convention, the matched-gross invariant + degenerate fallback, the PAST-ONLY vol
window, SIMPLE-return ddof=1 vol, the raw-bars pin, the tier/clip pins, the
forward-ledger read-only guard, the dev holdout guard, the session-clustered CI, the
dev/forward no-pool guard, and the M10 display-stream panel.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import polars as pl
import pytest
from scipy.stats import norm

from enginev51.research_screens import sizing_shadow as ss

# --------------------------------------------------------------------------- builders


def _weighted_frame(rows: list[dict], source: str = ss.SOURCE_DEV) -> pl.DataFrame:
    """A synthetic weighted event frame (the columns daily_paired_diff reads)."""
    return pl.DataFrame(
        [{**r, "source": source} for r in rows],
        schema={"session": pl.Utf8, "symbol": pl.Utf8, "net_bps": pl.Float64,
                "p_win": pl.Float64, "weight": pl.Float64, "source": pl.Utf8},
        orient="row",
    )


def _events_frame(rows: list[dict], source: str = ss.SOURCE_DEV) -> pl.DataFrame:
    """A raw (pre-weight) classical event frame, as attach_weights consumes it."""
    return pl.DataFrame(
        [{**r, "source": source} for r in rows],
        schema={"session": pl.Utf8, "symbol": pl.Utf8, "p_win": pl.Float64,
                "net_bps": pl.Float64, "source": pl.Utf8},
        orient="row",
    )


def _flat_closes(dates: list[str]) -> list[tuple[str, float]]:
    """Closes shared by ALL champions so every sigma_i is equal => sigma_med5 == sigma_i
    => v = clip(1.0) = 1.0 (weights reduce to the tier alone -- hand-checkable)."""
    return [(d, 100.0 + (i % 5)) for i, d in enumerate(dates)]  # nonzero, finite sigma


# =========================================================================== 1


def test_psr_mintrl_golden():
    """ADIA Lab No.19 worked example -- exact external validation anchor (abs 5e-3).

    (mu, sigma, g3, g4, rho, T) = (0.036%, 0.079%, -2.448, 10.164, 0.2, 24) =>
    SR*=0.456 ; sigma_sr(SR*)=0.379 ; PSR(SR0=0)=0.966 ; MinTRL(alpha=.05)=19.54."""
    mu, sigma = 0.00036, 0.00079
    g3, g4, rho, t = -2.448, 10.164, 0.2, 24
    sr = mu / sigma
    assert sr == pytest.approx(0.456, abs=5e-3)
    assert ss.sigma_sr(sr, t, rho, g3, g4) == pytest.approx(0.379, abs=5e-3)
    assert ss.psr(sr, 0.0, t, rho, g3, g4) == pytest.approx(0.966, abs=5e-3)
    assert ss.min_trl(sr, 0.0, 0.05, rho, g3, g4) == pytest.approx(19.54, abs=5e-3)


# =========================================================================== 2


def test_psr_off_anchor():
    """Off-anchor PSR with SR0!=0, rho!=0, g3!=0 -- HAND-DERIVED so a bracket(SR0) vs
    bracket(SR_hat) swap in the denominator cannot pass.

    Inputs: sr_hat=0.5, sr0=0.2, T=100, rho=0.1, g3=-1.0, g4=6.0.
    rho=0.1 -> (1+r)/(1-r)=1.1/0.9=1.2222222 ; (1+r+r^2)/(1-r^2)=1.11/0.99=1.1212121 ;
              (1+r^2)/(1-r^2)=1.01/0.99=1.0202020.
    bracket(SR0=0.2) = 1.2222222
        - 1.1212121*(-1.0)*0.2         (= +0.2242424)
        + 1.0202020*((6-1)/4)*0.2^2    (= 1.0202020*1.25*0.04 = +0.0510101)
      = 1.4974747.
    sigma_sr(SR0) = sqrt(1.4974747/100) = sqrt(0.014974747) = 0.1223714.
    z = (0.5 - 0.2)/0.1223714 = 0.3/0.1223714 = 2.451551.
    PSR = Phi(2.451551) = 0.992888.
    A wrong bracket(SR_hat=0.5) denominator gives sigma_sr=0.1449704 -> z=2.069395 ->
    Phi=0.980745, which differs by >1e-2 (the swap is caught)."""
    got = ss.psr(0.5, 0.2, 100, 0.1, -1.0, 6.0)
    assert got == pytest.approx(0.992888, abs=5e-4)

    # bracket(SR0=0.2) hand value drives sigma_sr at the BENCHMARK:
    assert ss._bracket(0.2, 0.1, -1.0, 6.0) == pytest.approx(1.4974747, abs=1e-6)
    assert ss.sigma_sr(0.2, 100, 0.1, -1.0, 6.0) == pytest.approx(0.1223714, abs=1e-6)

    # The bracket(SR_hat) swap: a materially different number -> the golden suite catches it.
    swapped = float(norm.cdf((0.5 - 0.2) / ss.sigma_sr(0.5, 100, 0.1, -1.0, 6.0)))
    assert swapped == pytest.approx(0.980745, abs=5e-4)
    assert abs(got - swapped) > 1e-2


# =========================================================================== 3


def test_kurtosis_pearson_convention():
    """sample_moments uses PEARSON kurtosis (fisher=False): a Normal sample -> ~3, not
    ~0. A fisher=True (excess) implementation would fail the >2.5 assertion."""
    rng = np.random.default_rng(7)
    x = rng.standard_normal(40_000)
    g3, g4, _rho = ss.sample_moments(x)
    assert g4 == pytest.approx(3.0, abs=0.15)  # Pearson, not the ~0 excess convention
    assert g4 > 2.5
    assert g3 == pytest.approx(0.0, abs=0.05)


# =========================================================================== 4


def test_matched_gross_invariant():
    """T==1 and v==1 for every event => w_i==1 => sized == equal BIT-IDENTICALLY =>
    delta_t == 0 (DESIGN section 4 hook)."""
    sized = ss.matched_gross_notional([1.0, 1.0, 1.0])
    assert sized.tolist() == [ss.BOOK_NOTIONAL] * 3  # bit-identical to equal

    # And through the whole daily path: a 2-event session, all weights 1 -> delta 0.
    fr = _weighted_frame([
        {"session": "2024-02-21", "symbol": "NVDA", "net_bps": 10.0, "p_win": 0.57, "weight": 1.0},
        {"session": "2024-02-21", "symbol": "AMD", "net_bps": -4.0, "p_win": 0.57, "weight": 1.0},
    ])
    daily, counts = ss.daily_paired_diff(fr)
    assert daily["delta_usd"].to_list() == [0.0]
    assert counts["n_multi_event_sessions"] == 1

    # A weighted multi-event session: hand-checked delta. weights [1.5, 1.0], sum 2.5,
    # n 2, book 10k -> sized [12000, 8000]; gross 20000 == equal gross.
    # delta = ((12000-10000)*10 + (8000-10000)*(-4))/1e4 = (20000 + 8000)/1e4 = 2.8.
    fr2 = _weighted_frame([
        {"session": "2024-03-01", "symbol": "NVDA", "net_bps": 10.0, "p_win": 0.62, "weight": 1.5},
        {"session": "2024-03-01", "symbol": "AMD", "net_bps": -4.0, "p_win": 0.57, "weight": 1.0},
    ])
    sized2 = ss.matched_gross_notional([1.5, 1.0])
    assert sized2.tolist() == [12000.0, 8000.0]
    assert sized2.sum() == pytest.approx(2 * ss.BOOK_NOTIONAL)  # matched gross
    daily2, _ = ss.daily_paired_diff(fr2)
    assert daily2["delta_usd"].to_list()[0] == pytest.approx(2.8)


# =========================================================================== 5


def test_matched_gross_degenerate_session():
    """sum(w)==0 (ruling A4) -> fallback to EQUAL, delta_t==0, counted -- never NaN/inf."""
    sized = ss.matched_gross_notional([0.0, 0.0])
    assert sized.tolist() == [ss.BOOK_NOTIONAL, ss.BOOK_NOTIONAL]  # equal fallback
    assert np.all(np.isfinite(sized))

    fr = _weighted_frame([
        {"session": "2024-02-21", "symbol": "NVDA", "net_bps": 12.0, "p_win": 0.40, "weight": 0.0},
        {"session": "2024-02-21", "symbol": "AMD", "net_bps": -9.0, "p_win": 0.51, "weight": 0.0},
    ])
    daily, counts = ss.daily_paired_diff(fr)
    assert daily["delta_usd"].to_list() == [0.0]
    assert counts["n_degenerate_sessions"] == 1

    # The panel must not be poisoned by the degenerate (constant) delta series.
    panel = ss.sizing_panel(fr, ss.SOURCE_DEV)
    assert panel["sr_native"] == 0.0
    assert panel["psr_sr0_0"] == pytest.approx(0.5)  # Phi(0), never NaN
    assert panel["min_trl"] is None  # sr_hat==sr0 -> +inf -> reported as None


# =========================================================================== 6


def test_vol_window_past_only():
    """The trailing window is PAST-ONLY: closes on/after ``asof`` are excluded (window
    strictly ends t-1). Adding the asof-session close and a FUTURE close must not change
    the result."""
    # 21 prior closes (sessions 01..21 of 2024-03), then asof = 2024-03-22.
    pairs = [(f"2024-03-{d:02d}", 100.0 + d) for d in range(1, 22)]
    asof = "2024-03-22"
    base = ss.trailing_raw_vol(pairs, asof)

    poisoned = pairs + [("2024-03-22", 999.0), ("2024-03-25", 1234.0)]  # asof + future
    assert ss.trailing_raw_vol(poisoned, asof) == pytest.approx(base)
    assert np.isfinite(base)

    # Fewer than 21 prior closes -> NaN (insufficient history).
    assert np.isnan(ss.trailing_raw_vol(pairs[:20], asof))


# =========================================================================== 7


def test_vol_simple_returns_ddof1():
    """Vol = stdev(ddof=1) of SIMPLE close-to-close returns. A log-return implementation
    yields a different number and must fail this pin."""
    rng = np.random.default_rng(11)
    closes = list(100.0 + np.cumsum(rng.standard_normal(21)))  # 21 closes -> 20 returns
    pairs = [(f"2024-03-{d + 1:02d}", c) for d, c in enumerate(closes)]
    asof = "2024-04-01"

    arr = np.asarray(closes, dtype=float)
    simple = arr[1:] / arr[:-1] - 1.0
    expected = float(np.std(simple, ddof=1))
    assert ss.trailing_raw_vol(pairs, asof) == pytest.approx(expected)

    # ddof=0 (population) is a different value -> our function is NOT using it.
    assert expected != pytest.approx(float(np.std(simple, ddof=0)))
    # A LOG-return implementation is a different value -> the pin rejects it.
    logret = np.log(arr[1:] / arr[:-1])
    assert ss.trailing_raw_vol(pairs, asof) != pytest.approx(float(np.std(logret, ddof=1)))


# =========================================================================== 8


def test_raw_bars_pin(tmp_path):
    """Vol reads RAW bars1d only (L2): the dir constant is data/raw/sip/bars1d (never an
    adjusted path), and the module does not reuse moc_gbm.trailing_vol20 (log returns)."""
    assert ss.RAW_BARS1D_DIR == Path("data/raw/sip/bars1d")
    assert "adj" not in str(ss.RAW_BARS1D_DIR).lower()
    # The module must not IMPORT the log-return vol (moc_gbm.trailing_vol20); a prose
    # reference to it in a docstring is fine, an import is not.
    src = inspect.getsource(ss)
    assert "import moc_gbm" not in src
    assert "models.moc_gbm" not in src

    # Functional: load_raw_closes reads (ts, close) from a raw parquet, UTC-date keyed.
    df = pl.DataFrame({"ts": [1_700_000_000_000_000_000], "close": [123.5]})
    df.write_parquet(tmp_path / "NVDA.parquet")
    pairs = ss.load_raw_closes("NVDA", bars_dir=tmp_path)
    assert pairs == [("2023-11-14", 123.5)]


# =========================================================================== 9


def test_tier_pins():
    """Tier boundaries: 0.549->0, 0.55->1.0, 0.599->1.0, 0.60->1.5."""
    assert ss.tier(0.549) == 0.0
    assert ss.tier(0.55) == 1.0
    assert ss.tier(0.599) == 1.0
    assert ss.tier(0.60) == 1.5
    assert (ss.TIER_LO, ss.TIER_MID, ss.TIER_HI) == (0.0, 1.0, 1.5)
    assert (ss.P_CUT_LO, ss.P_CUT_HI) == (0.55, 0.60)


# =========================================================================== 10


def test_clip_pins():
    """v = clip(sigma_med5/sigma_i, 0.5, 2.0). Both rails pinned. A FINITE zero-vol
    history hits the HI rail; a vol-history SKIP (NaN/None sigma_i) is NEUTRAL 1.0, NOT
    the HI clip (orchestrator ruling). Never NaN."""
    assert (ss.VOL_CLIP_LO, ss.VOL_CLIP_HI) == (0.5, 2.0)
    assert ss.vol_norm(100.0, 10.0) == 0.5    # ratio 0.1 -> LO rail
    assert ss.vol_norm(10.0, 100.0) == 2.0    # ratio 10  -> HI rail
    assert ss.vol_norm(10.0, 15.0) == pytest.approx(1.5)  # inside the band
    assert ss.vol_norm(0.0, 5.0) == ss.VOL_CLIP_HI        # finite zero-vol -> HI clip
    # Insufficient history: NEUTRAL, distinguished from a finite tiny sigma:
    assert ss.vol_norm(float("nan"), 5.0) == 1.0
    assert ss.vol_norm(None, 5.0) == 1.0
    assert ss.is_vol_history_skip(float("nan")) is True
    assert ss.is_vol_history_skip(None) is True
    assert ss.is_vol_history_skip(1e-9) is False          # finite tiny sigma is NOT a skip


# =========================================================================== 11


def test_forward_ledger_read_only():
    """The instrument NEVER writes the forward ledger: no ledger-append API is imported
    or reimplemented, and the module writes NO parquet at all (only .md/.json)."""
    src = inspect.getsource(ss)
    assert "append_ledger" not in src   # forward_paper's write API
    assert "ledger_append" not in src   # protocol's jsonl append
    assert "write_parquet" not in src   # writes nothing to any parquet

    # The only ledger touch point is the read function.
    assert ss.load_ledger.__name__ == "load_ledger"
    from enginev51.apps import forward_paper
    assert ss.load_ledger is forward_paper.load_ledger


# =========================================================================== 12


def test_holdout_guard_dev():
    """Dev reference refuses the sealed holdout; strip_holdout drops holdout rows.

    FAILURE MODE (code review 2026-08-01 J2): the guard RAISES ``SealViolation`` --
    it used to be a bare ``assert``, which ``python -O`` strips. Numeric behaviour is
    unchanged: the same dates are refused and the same rows survive the filter."""
    from datetime import date

    from enginev51.protocol import SealViolation

    with pytest.raises(SealViolation):
        ss.assert_before_holdout(date(2026, 6, 1))   # the seal boundary
    with pytest.raises(SealViolation):
        ss.assert_before_holdout(date(2026, 7, 20))  # deep in holdout
    ss.assert_before_holdout(date(2026, 5, 31))      # last legal session -> fine

    fr = pl.DataFrame({
        "session": ["2026-05-29", "2026-06-01", "2026-07-20"],
        "symbol": ["NVDA", "NVDA", "AMD"],
        "net_bps": [1.0, 2.0, 3.0],
    })
    kept = ss.strip_holdout(fr)
    assert kept["session"].to_list() == ["2026-05-29"]


# =========================================================================== 13


def test_clustered_ci_session_cluster():
    """CI is a session-clustered bootstrap on the one-row-per-session daily series
    (ruling A8). A single session cluster is degenerate -> lo == hi == mean; the panel
    reports T==1 with a point CI."""
    fr = _weighted_frame([
        {"session": "2024-02-21", "symbol": "NVDA", "net_bps": 10.0, "p_win": 0.62, "weight": 1.5},
        {"session": "2024-02-21", "symbol": "AMD", "net_bps": -4.0, "p_win": 0.57, "weight": 1.0},
    ])
    panel = ss.sizing_panel(fr, ss.SOURCE_DEV)
    assert panel["T"] == 1
    assert panel["mean_usd"] == pytest.approx(2.8)
    assert panel["ci_lo_usd"] == pytest.approx(2.8)
    assert panel["ci_hi_usd"] == pytest.approx(2.8)  # single cluster -> point interval

    # Two distinct sessions -> two clusters; the bootstrap is well-defined and brackets
    # the mean.
    fr2 = _weighted_frame([
        {"session": "2024-02-21", "symbol": "NVDA", "net_bps": 10.0, "p_win": 0.62, "weight": 1.5},
        {"session": "2024-02-21", "symbol": "AMD", "net_bps": -4.0, "p_win": 0.57, "weight": 1.0},
        {"session": "2024-02-22", "symbol": "NVDA", "net_bps": 6.0, "p_win": 0.62, "weight": 1.5},
        {"session": "2024-02-22", "symbol": "AMD", "net_bps": 2.0, "p_win": 0.57, "weight": 1.0},
    ])
    panel2 = ss.sizing_panel(fr2, ss.SOURCE_DEV)
    assert panel2["T"] == 2
    assert panel2["ci_lo_usd"] <= panel2["mean_usd"] <= panel2["ci_hi_usd"]


# =========================================================================== 14


def test_dev_forward_never_pooled():
    """A frame that mixes dev and forward rows raises (L9-analog); the guard fires from
    both the public entry and the daily-diff path."""
    mixed = pl.concat([
        _weighted_frame([{"session": "2024-02-21", "symbol": "NVDA", "net_bps": 5.0,
                          "p_win": 0.6, "weight": 1.5}], source=ss.SOURCE_DEV),
        _weighted_frame([{"session": "2026-07-20", "symbol": "NVDA", "net_bps": 5.0,
                          "p_win": 0.6, "weight": 1.5}], source=ss.SOURCE_FWD),
    ])
    with pytest.raises(ValueError, match="pooling violation"):
        ss.assert_single_source(mixed)
    with pytest.raises(ValueError, match="pooling violation"):
        ss.daily_paired_diff(mixed)
    # A single-source frame passes.
    ss.assert_single_source(mixed.filter(pl.col("source") == ss.SOURCE_DEV))


# =========================================================================== 15


def test_stream_psr_panel_daily_aggregated():
    """The M10 display panel emits the three streams, each DAILY-aggregated (a 2-reporter
    session collapses to its session mean) with SR0=0. Gate untouched -- display only."""
    led = pl.DataFrame({
        "session": ["2024-02-21", "2024-02-21", "2024-02-22", "2024-02-23"],
        "symbol": ["NVDA", "AMD", "NVDA", "MU"],
        "net_bps": [4.0, 8.0, 6.0, 5.0],
        "taken_classical": [True, True, True, True],
        "taken_meta": [True, False, True, True],
        "selected": [True, False, False, True],
    })
    streams = ss.stream_psr_panel(led)
    by = {s["stream"]: s for s in streams}
    assert set(by) == {"classical", "meta", "portfolio"}
    # classical: 3 distinct sessions (2024-02-21 mean = (4+8)/2 = 6).
    assert by["classical"]["T"] == 3
    # meta: sessions 21 (mean 4), 22 (6), 23 (5) -> T=3.
    assert by["meta"]["T"] == 3
    # portfolio: sessions 21 (4) and 23 (5) -> T=2.
    assert by["portfolio"]["T"] == 2
    # M4: pin the DAILY-AGGREGATED value so a mean->sum mutation fails. The classical
    # 2024-02-21 session mean is (4+8)/2 = 6.0; with sessions [6, 6, 5] the classical
    # SR is mean/std(ddof=1) = (17/3) / std([6,6,5]) -- a sum would give [12,6,5].
    daily_classical = (
        led.filter(pl.col("taken_classical"))
        .group_by("session").agg(pl.col("net_bps").mean().alias("net_bps"))
        .sort("session")
    )
    assert daily_classical["net_bps"].to_list() == [6.0, 6.0, 5.0]  # mean, NOT sum (12)
    # PSR is a probability in [0,1] for every stream (SR0=0; no NaN poisoning).
    for s in streams:
        assert 0.0 <= s["psr_sr0_0"] <= 1.0


# =========================================================================== 16 (M3)


def test_vol_history_skip_neutral_and_counted():
    """A symbol with only 9 prior closes (<21) is a vol-history SKIP: sigma_i is NaN ->
    v = 1.0 NEUTRAL -> weight = tier(p) * 1.0, and the event increments
    n_vol_history_skips. Distinct from a finite tiny sigma (which would hit the HI clip)."""
    short_dates = [f"2024-05-{d:02d}" for d in range(1, 10)]   # 9 closes only -> skip
    full_dates = [f"2024-05-{d:02d}" for d in range(1, 26)]    # 25 closes -> finite sigma
    closes = {s: _flat_closes(full_dates) for s in ss.UNIVERSE}
    closes["NVDA"] = _flat_closes(short_dates)                 # NVDA has too little history

    events = _events_frame([
        {"session": "2024-05-28", "symbol": "NVDA", "p_win": 0.62, "net_bps": 20.0},
    ])
    wf = ss.attach_weights(events, closes)
    # v = 1.0 NEUTRAL (not 2.0 HI) => weight == tier(0.62) == 1.5.
    assert wf["weight"].to_list() == [pytest.approx(1.5)]
    assert wf["vol_skip"].to_list() == [True]

    panel = ss.sizing_panel(wf, ss.SOURCE_DEV)
    assert panel["n_vol_history_skips"] == 1


# =========================================================================== 17 (M1a)


def test_end_to_end_real_path_weight_and_mean():
    """END-TO-END through the REAL wiring: trailing_raw_vol -> champion_sigma_med5 ->
    event_weight -> attach_weights -> sizing_panel, with a hand-computed weight and mean.

    All 5 champions share identical closes => every sigma_i equal => sigma_med5 == sigma_i
    => v == 1.0, so weights reduce to the tier. Session 2024-05-28 has NVDA (p=0.62,
    tier 1.5) and AMD (p=0.57, tier 1.0):
      sum(w)=2.5, n=2, book=10k -> sized = 10k*2*[1.5,1.0]/2.5 = [12000, 8000] (gross 20k
      == 2*book). delta = ((12000-10000)*20 + (8000-10000)*(-8))/1e4
                        = (40000 + 16000)/1e4 = 5.6.
    Session 2024-05-29 is a single NVDA event => renormalizes to equal => delta 0.0.
    panel mean = (5.6 + 0.0)/2 = 2.8."""
    dates = [f"2024-05-{d:02d}" for d in range(1, 26)]  # 25 shared closes
    closes = {s: _flat_closes(dates) for s in ss.UNIVERSE}
    events = _events_frame([
        {"session": "2024-05-28", "symbol": "NVDA", "p_win": 0.62, "net_bps": 20.0},
        {"session": "2024-05-28", "symbol": "AMD", "p_win": 0.57, "net_bps": -8.0},
        {"session": "2024-05-29", "symbol": "NVDA", "p_win": 0.62, "net_bps": 11.0},
    ])
    wf = ss.attach_weights(events, closes)
    nvda0 = wf.filter((pl.col("symbol") == "NVDA") & (pl.col("session") == "2024-05-28"))
    assert nvda0["weight"].to_list() == [pytest.approx(1.5)]  # tier(0.62) * v(1.0)
    assert wf["vol_skip"].to_list() == [False, False, False]  # sufficient history

    daily, counts = ss.daily_paired_diff(wf)
    assert daily["delta_usd"].to_list() == [pytest.approx(5.6), pytest.approx(0.0)]
    assert counts["n_vol_history_skips"] == 0

    panel = ss.sizing_panel(wf, ss.SOURCE_DEV)
    assert panel["T"] == 2
    assert panel["mean_usd"] == pytest.approx(2.8)


# =========================================================================== 18 (M2)


def _global_norm_deltas(fr: pl.DataFrame) -> list[float]:
    """The WRONG global-weight-sum normalization (sizing_overlay-style): the denominator
    is the GLOBAL weight sum over ALL sessions, not the session's own. Used only to prove
    the per-session invariant fails under this mutation."""
    net = fr["net_bps"].to_numpy()
    w = fr["weight"].to_numpy()
    n_total = w.shape[0]
    g = float(w.sum())
    sized_all = ss.BOOK_NOTIONAL * n_total * w / g  # pooled denominator (the bug)
    out = []
    for sess in sorted(fr["session"].unique().to_list()):
        m = (fr["session"] == sess).to_numpy()
        out.append(float(np.sum((sized_all[m] - ss.BOOK_NOTIONAL) * net[m]) / 1e4))
    return out


def test_matched_gross_per_session_not_global():
    """Reviewer differentiating fixture: 2 sessions with DIFFERING weight sums where
    per-session renormalization yields deltas [14.0, 0.0]; a global-weight-sum mutation
    must fail it.

    Session A (2024-01-01): w=[3,1] (sum 4), nets=[20,-8].
      sized = 10k*2*[3,1]/4 = [15000, 5000] (gross 20k == 2*book).
      delta_A = ((15000-10000)*20 + (5000-10000)*(-8))/1e4 = (100000 + 40000)/1e4 = 14.0.
    Session B (2024-01-02): w=[1,1] (sum 2), nets=[10,-6].
      sized = 10k*2*[1,1]/2 = [10000,10000] == equal -> delta_B = 0.0.
    GLOBAL mutation: Sigma_global = 3+1+1+1 = 6, n_total = 4 -> sized_i = 10k*4*w_i/6.
      Session B sized = [6666.67, 6666.67] != equal -> delta_B_global = -1.3333 != 0.0,
      so [14.0, 0.0] is NOT reproduced under the pooled denominator."""
    fr = _weighted_frame([
        {"session": "2024-01-01", "symbol": "NVDA", "net_bps": 20.0, "p_win": 0.62, "weight": 3.0},
        {"session": "2024-01-01", "symbol": "AMD", "net_bps": -8.0, "p_win": 0.62, "weight": 1.0},
        {"session": "2024-01-02", "symbol": "NVDA", "net_bps": 10.0, "p_win": 0.57, "weight": 1.0},
        {"session": "2024-01-02", "symbol": "AMD", "net_bps": -6.0, "p_win": 0.57, "weight": 1.0},
    ])
    daily, _ = ss.daily_paired_diff(fr)
    assert daily["delta_usd"].to_list() == [pytest.approx(14.0), pytest.approx(0.0)]

    # The global-weight-sum mutation does NOT reproduce [14.0, 0.0]:
    mutant = _global_norm_deltas(fr)
    assert mutant[1] == pytest.approx(-1.3333, abs=1e-3)  # session B is no longer 0.0
    assert mutant != pytest.approx([14.0, 0.0])


# =========================================================================== 19 (M1b)


def test_writers_two_sources_separate_and_idempotent(tmp_path):
    """write_source_panel for BOTH sources then the combined doc: dev-reference and
    forward appear as SEPARATE sections, no statistic spans them (each is a
    self-contained panel dict), and refresh_combined is idempotent."""
    import json

    dev_fr = _weighted_frame([
        {"session": "2024-02-21", "symbol": "NVDA", "net_bps": 10.0, "p_win": 0.62, "weight": 1.5},
        {"session": "2024-02-21", "symbol": "AMD", "net_bps": -4.0, "p_win": 0.57, "weight": 1.0},
        {"session": "2024-02-22", "symbol": "NVDA", "net_bps": 6.0, "p_win": 0.62, "weight": 1.5},
        {"session": "2024-02-22", "symbol": "AMD", "net_bps": 2.0, "p_win": 0.57, "weight": 1.0},
    ], source=ss.SOURCE_DEV)
    fwd_fr = _weighted_frame([
        {"session": "2026-07-20", "symbol": "NVDA", "net_bps": 8.0, "p_win": 0.62, "weight": 1.5},
        {"session": "2026-07-20", "symbol": "AMD", "net_bps": -3.0, "p_win": 0.57, "weight": 1.0},
    ], source=ss.SOURCE_FWD)

    dev_panel = ss.sizing_panel(dev_fr, ss.SOURCE_DEV)
    fwd_panel = ss.sizing_panel(fwd_fr, ss.SOURCE_FWD)
    assert dev_panel["T"] == 2 and fwd_panel["T"] == 1  # independent T's

    ss.write_source_panel(dev_panel, ss.SOURCE_DEV, out_dir=tmp_path)
    ss.write_source_panel(fwd_panel, ss.SOURCE_FWD, streams=[], out_dir=tmp_path)

    md = (tmp_path / "panel.md").read_text(encoding="utf-8")
    assert "## Dev reference" in md and "## Forward to date" in md
    assert "source=dev" in md and "source=forward" in md

    combined = json.loads((tmp_path / "panel.json").read_text(encoding="utf-8"))
    # Two self-contained sections; no pooled/merged statistic key exists.
    assert combined["dev"]["panel"]["source"] == "dev"
    assert combined["forward"]["panel"]["source"] == "forward"
    assert combined["dev"]["panel"]["T"] == 2      # not merged with forward's T=1
    assert combined["forward"]["panel"]["T"] == 1
    assert combined["sr0"] == 0.0

    # Idempotent: re-reading the persisted sections yields a byte-identical combined doc.
    before = (tmp_path / "panel.json").read_text(encoding="utf-8")
    ss.refresh_combined(tmp_path)
    after = (tmp_path / "panel.json").read_text(encoding="utf-8")
    assert before == after


# =========================================================================== 20 (J3a)


def test_adia_helpers_are_the_stats_kernel_by_identity():
    """The ADIA helpers MOVED to ``enginev51.stats.adia`` (code review 2026-08-01 J3a)
    and are re-imported here -- they are the SAME objects, not copies.

    Identity, not equality: every historical importer (live/engine, gap_day, open_fade,
    the m28/m29 battery scripts, rfd_live) reaches them through ``sizing_shadow``, and
    two independently-defined-but-equal implementations would silently drift. If this
    ever fails, someone re-implemented the math instead of re-exporting it."""
    from enginev51.stats import adia

    assert ss.psr is adia.psr
    assert ss.min_trl is adia.min_trl
    assert ss.sr_native is adia.sr_native
    # The rest of the same kernel block moved together (psr needs sigma_sr, min_trl
    # needs _bracket, sample_moments needs lag1_autocorr -- a partial move would be a
    # circular import), and downstream screens import them by identity too.
    assert ss.sigma_sr is adia.sigma_sr
    assert ss.sample_moments is adia.sample_moments
    assert ss.lag1_autocorr is adia.lag1_autocorr
    assert ss._bracket is adia._bracket

    # sizing_shadow no longer DEFINES them: exactly one definition site exists.
    assert inspect.getsourcefile(ss.psr) == inspect.getsourcefile(adia.psr)
    assert inspect.getsourcefile(ss.psr) != inspect.getsourcefile(ss.tier)
