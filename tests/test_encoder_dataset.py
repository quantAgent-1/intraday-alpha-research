"""Tests for the M4 encoder dataset layer (src/enginev51/models/encoder/dataset.py).

Covers: frozen downsample semantics, barrier hand-cases, label session-safety,
norm-stats point-in-time invariance, and dataset item shapes / mask / determinism.
All synthetic — no dependence on the materialized lake.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import polars as pl
import pytest

from enginev51.config import Settings
from enginev51.events.event_bars import EVENT_BARS_COLUMNS
from enginev51.features import slow
from enginev51.models.encoder import dataset as ds

NS_PER_S = 1_000_000_000


# ---------------------------------------------------------------- synthetic bars
def _event_bar_frame(n: int, ts0: int, seed: int = 0) -> pl.DataFrame:
    """A synthetic 1-second event-bar frame with all 28 columns, activity every bar."""
    rng = np.random.default_rng(seed)
    ret = rng.normal(0, 1e-4, n)
    mid = 100.0 * np.exp(np.cumsum(ret))
    cols = {c: np.zeros(n, dtype=np.float64) for c in EVENT_BARS_COLUMNS}
    cols["ts"] = (ts0 + np.arange(n) * NS_PER_S).astype(np.int64)
    for c in ("px_open", "px_high", "px_low", "px_close", "bid", "ask", "mid"):
        cols[c] = mid.copy()
    cols["px_high"] = mid * 1.0001
    cols["px_low"] = mid * 0.9999
    cols["bid"] = mid * 0.9999
    cols["ask"] = mid * 1.0001
    cols["n_trades"] = np.ones(n)
    cols["volume"] = np.full(n, 100.0)
    cols["dollar_vol"] = mid * 100.0
    cols["signed_vol"] = rng.choice([-100.0, 100.0], n)
    cols["signed_dollar"] = cols["signed_vol"] * mid
    cols["at_ask_vol"] = np.full(n, 50.0)
    cols["at_bid_vol"] = np.full(n, 50.0)
    cols["max_trade_size"] = np.full(n, 100.0)
    cols["n_quotes"] = np.full(n, 5.0)
    cols["spread_bps_close"] = np.full(n, 2.0)
    cols["spread_bps_mean"] = np.full(n, 2.0)
    cols["imb_close"] = np.zeros(n)
    cols["imb_mean"] = np.zeros(n)
    cols["micro_dev_bps"] = np.zeros(n)
    return pl.DataFrame({c: cols[c] for c in EVENT_BARS_COLUMNS})


def _write_partition(root, symbol: str, session: str, df: pl.DataFrame) -> None:
    d = root / "sip" / "event_bars1s" / symbol.upper()
    d.mkdir(parents=True, exist_ok=True)
    df.write_parquet(d / f"{session}.parquet")


def _settings(tmp_path) -> Settings:
    return Settings(data_dir=tmp_path, legacy_data_dir=tmp_path / "nolegacy")


# ---------------------------------------------------------------- downsample
def test_downsample_semantics_exact():
    n = 10
    base = {c: np.zeros(n) for c in EVENT_BARS_COLUMNS}
    base["ts"] = np.arange(n, dtype=np.int64)
    base["volume"] = np.arange(1, n + 1, dtype=float)          # sum
    base["px_close"] = np.arange(1, n + 1, dtype=float)         # last
    base["px_open"] = np.arange(1, n + 1, dtype=float)          # first
    base["px_high"] = np.arange(1, n + 1, dtype=float)          # max
    base["px_low"] = np.arange(1, n + 1, dtype=float)           # min
    base["spread_bps_mean"] = np.arange(1, n + 1, dtype=float)  # mean
    df = pl.DataFrame({c: base[c] for c in EVENT_BARS_COLUMNS})

    out = ds.downsample_bars(df, 5)
    assert out.height == 2
    assert out["volume"].to_list() == [15.0, 40.0]        # 1..5, 6..10
    assert out["px_close"].to_list() == [5.0, 10.0]       # last
    assert out["px_open"].to_list() == [1.0, 6.0]         # first
    assert out["px_high"].to_list() == [5.0, 10.0]        # max
    assert out["px_low"].to_list() == [1.0, 6.0]          # min
    assert out["spread_bps_mean"].to_list() == [3.0, 8.0]  # mean


def test_numpy_fastpath_matches_polars():
    """The dataset's numpy reshape aggregation must equal the canonical polars path."""
    df = _event_bar_frame(600, ts0=0, seed=3)
    poly = ds.downsample_bars(df, 5).sort("bucket")
    src = {c: df[c].to_numpy().astype(np.float64) for c in ds._all_source_cols()}
    npagg = ds._agg_window_np(src, 0, 120, 5)
    for col in ds._all_source_cols():
        np.testing.assert_allclose(npagg[col], poly[col].to_numpy(), rtol=1e-9, atol=1e-9)


# ---------------------------------------------------------------- barriers
def test_barrier_hand_case():
    vol20 = 0.01
    h = 60
    sigma = vol20 * np.sqrt(h / ds.DAY_MINUTES)
    n_sec = 8000
    # up path: rise linearly to +0.75*sigma by minute 10 (sec 600), then hold there.
    logmid = np.zeros(n_sec)
    up_level = 0.75 * sigma
    logmid[1:601] = np.linspace(up_level / 600, up_level, 600)
    logmid[601:] = up_level
    offsets = np.array([1], dtype=np.int64)  # e = 0, p0 = logmid[0] = 0
    lab = ds._labels_for_session(logmid, n_sec, offsets, vol20)
    # +0.75 hit, -1.25 never -> UP strictly first -> 1
    assert lab["hit_0.75sig_before_1.25sig_60m"][0] == 1.0
    assert lab["hit_0.75sig_before_0.75sig_60m"][0] == 1.0
    # +1.25 never reached (plateau at 0.75) -> those hits are 0
    assert lab["hit_1.25sig_before_1.25sig_60m"][0] == 0.0

    # reversed: falls to -0.75*sigma first, up never -> 0
    logdown = np.zeros(n_sec)
    logdown[1:601] = np.linspace(-up_level / 600, -up_level, 600)
    logdown[601:] = -up_level
    lab2 = ds._labels_for_session(logdown, n_sec, offsets, vol20)
    assert lab2["hit_0.75sig_before_1.25sig_60m"][0] == 0.0
    assert lab2["hit_0.75sig_before_0.75sig_60m"][0] == 0.0


def test_dn_first_barrier_mirror():
    """DOWN-FIRST barriers mirror the up-first ones on a falling-then-flat path."""
    vol20 = 0.01
    h = 60
    sigma = vol20 * np.sqrt(h / ds.DAY_MINUTES)
    n_sec = 8000
    lvl = 0.75 * sigma
    offsets = np.array([1], dtype=np.int64)
    logdown = np.zeros(n_sec)
    logdown[1:601] = np.linspace(-lvl / 600, -lvl, 600)
    logdown[601:] = -lvl
    lab = ds._labels_for_session(logdown, n_sec, offsets, vol20)
    # -0.75 strictly before +0.75(never) -> dn-first hit; up-first is the complement 0
    assert lab["hit_dn_0.75x0.75_60"][0] == 1.0
    assert lab["hit_0.75sig_before_0.75sig_60m"][0] == 0.0
    assert lab["hit_dn_1.25x0.75_60"][0] == 1.0    # +1.25 never -> dn wins
    assert lab["hit_dn_0.75x1.25_60"][0] == 0.0    # -1.25 never touched
    # rv label populated (30m window inside the session)
    assert np.isfinite(lab["l_rv_30m"][0])


# ---------------------------------------------------------------- session safety
def test_label_null_when_window_crosses_close():
    vol20 = 0.01
    n_sec = 4000
    logmid = np.cumsum(np.full(n_sec, 1e-6))  # gentle drift, always finite
    # early point: 60m window (3600s) fits; late point: crosses close -> null
    early = 1        # e=0, e+3600=3600 < 4000  -> finite
    late = 1000      # e=999, e+3600=4599 >= 4000 -> null
    lab = ds._labels_for_session(logmid, n_sec, np.array([early, late]), vol20)
    assert np.isfinite(lab["l_fwd_60m_z"][0])
    assert np.isnan(lab["l_fwd_60m_z"][1])
    assert np.isnan(lab["l_mfe_60m_z"][1])
    assert np.isnan(lab["hit_0.75sig_before_0.75sig_60m"][1])
    # to-close is never null while mid is present
    assert np.isfinite(lab["l_fwd_close_z"][0])
    assert np.isfinite(lab["l_fwd_close_z"][1])


# ---------------------------------------------------------------- norm-stats PIT
def test_norm_stats_pit_future_does_not_change_past(tmp_path):
    settings = _settings(tmp_path)
    root = settings.raw_dir
    sessions = [f"2025-01-{d:02d}" for d in range(2, 17)]  # 15 sessions
    for i, s in enumerate(sessions):
        _write_partition(root, "NVDA", s, _event_bar_frame(200, ts0=i * 10**12, seed=i))

    out1 = tmp_path / "norm1"
    ds.build_norm_stats(settings, ["NVDA"], out_dir=out1, trailing=20, min_priors=12)
    stats1 = pl.read_parquet(out1 / "NVDA.parquet")
    target = sessions[13]  # index 13 -> 13 priors (>= 12)
    t1 = stats1.filter(pl.col("session") == target).sort("channel")
    assert t1.height == len(ds.FINE_DATA_CHANNELS)

    # add a FUTURE session strictly after everything, rebuild
    _write_partition(root, "NVDA", "2025-02-01", _event_bar_frame(200, ts0=99 * 10**12, seed=99))
    out2 = tmp_path / "norm2"
    ds.build_norm_stats(settings, ["NVDA"], out_dir=out2, trailing=20, min_priors=12)
    stats2 = pl.read_parquet(out2 / "NVDA.parquet")
    t2 = stats2.filter(pl.col("session") == target).sort("channel")

    np.testing.assert_allclose(t1["med"].to_numpy(), t2["med"].to_numpy(), rtol=0, atol=0)
    np.testing.assert_allclose(t1["iqr"].to_numpy(), t2["iqr"].to_numpy(), rtol=0, atol=0)


def test_norm_stats_skips_when_too_few_priors(tmp_path):
    settings = _settings(tmp_path)
    root = settings.raw_dir
    sessions = [f"2025-01-{d:02d}" for d in range(2, 8)]  # only 6 sessions
    for i, s in enumerate(sessions):
        _write_partition(root, "NVDA", s, _event_bar_frame(120, ts0=i * 10**12, seed=i))
    out = tmp_path / "norm"
    ds.build_norm_stats(settings, ["NVDA"], out_dir=out, min_priors=12)
    stats = pl.read_parquet(out / "NVDA.parquet")
    assert stats.height == 0  # no session has >= 12 priors


# ---------------------------------------------------------------- dataset
def _full_session_setup(tmp_path, symbol="NVDA", session="2025-09-08"):
    """One full 6.5h session on disk + a matching features parquet. Returns settings."""
    settings = _settings(tmp_path)
    open_ns = int(datetime(2025, 9, 8, 13, 30, tzinfo=UTC).timestamp()) * NS_PER_S  # 9:30 ET (EDT)
    df = _event_bar_frame(23400, ts0=open_ns, seed=7)
    _write_partition(settings.raw_dir, symbol, session, df)

    # features: 5-min grid across the session, vol20 constant, f_* filled
    fts = open_ns + np.arange(0, 23400, 300) * NS_PER_S
    fcols = {c: np.linspace(-1, 1, len(fts)) for c in slow.FEATURE_COLS}
    feat = pl.DataFrame(
        {"session": [session] * len(fts), "ts": fts.astype(np.int64),
         "vol20": np.full(len(fts), 0.02), **fcols}
    )
    fdir = settings.data_dir / "features" / "v1"
    fdir.mkdir(parents=True, exist_ok=True)
    feat.write_parquet(fdir / f"{symbol}.parquet")
    return settings, fdir


def test_dataset_item_shapes_mask_determinism(tmp_path):
    settings, fdir = _full_session_setup(tmp_path)
    ndir = tmp_path / "norm"
    idir = tmp_path / "index"
    ds.build_norm_stats(settings, ["NVDA"], out_dir=ndir)
    rows = ds.build_decision_index(settings, ["NVDA"], out_dir=idir)
    assert rows["NVDA"] == 271  # 11:00..15:30 every 60s inclusive

    data = ds.EncoderDataset(settings, ["NVDA"], index_dir=idir, norm_dir=ndir, features_dir=fdir)
    assert len(data) == 271

    it = data[0]
    assert tuple(it["fine"].shape) == (ds.FINE_STEPS, len(ds.FINE_CHANNELS))
    assert tuple(it["sess"].shape) == (ds.SESS_STEPS, len(ds.SESS_CHANNELS))
    assert tuple(it["static"].shape) == (len(slow.FEATURE_COLS) + 2 + 1,)
    assert len(it["labels"]) == len(ds.LABEL_COLS)
    assert it["fine"].dtype.is_floating_point

    # first decision point is 11:00 ET = 90 min into the session
    assert it["meta"]["session"] == "2025-09-08"
    # fine window (90 min ending just before ts) is fully populated -> mask all 1
    assert float(it["fine"][:, -1].sum()) == ds.FINE_STEPS
    # sess mask = minutes since open available so far = 90
    assert float(it["sess"][:, -1].sum()) == 90.0
    # padded sess rows beyond minute 90 are zero
    assert float(it["sess"][90:].abs().sum()) == 0.0

    # determinism: a second build is bit-identical
    import torch

    data2 = ds.EncoderDataset(settings, ["NVDA"], index_dir=idir, norm_dir=ndir, features_dir=fdir)
    it2 = data2[0]
    assert torch.equal(it["fine"], it2["fine"])
    assert torch.equal(it["sess"], it2["sess"])
    assert torch.equal(it["static"], it2["static"])


def test_dataset_static_symbol_onehot_and_time(tmp_path):
    settings, fdir = _full_session_setup(tmp_path)
    ndir = tmp_path / "norm"
    idir = tmp_path / "index"
    ds.build_norm_stats(settings, ["NVDA"], out_dir=ndir)
    ds.build_decision_index(settings, ["NVDA"], out_dir=idir)
    data = ds.EncoderDataset(settings, ["NVDA", "TSLA"], index_dir=idir, norm_dir=ndir, features_dir=fdir)
    it = data[0]
    static = it["static"].numpy()
    # last two entries are the NVDA/TSLA one-hot -> NVDA active
    assert static[-2] == 1.0 and static[-1] == 0.0
    # minute-of-session at 11:00 = 90/390
    mos = static[len(slow.FEATURE_COLS)]
    assert mos == pytest.approx(90 / 390.0)


# ----------------------------------------------- B1: static-feature availability lag
def test_static_vector_respects_availability_lag(tmp_path):
    """A feature row stamped at a bar OPEN is NOT visible at that stamp (it carries
    that bar's CLOSE); it becomes visible one bar later (features/grid.py contract,
    PRED_STAMP_TO_AVAILABILITY_NS). Pre-fix the asof was `<= ts` -> ~60s look-ahead.
    """
    settings, fdir = _full_session_setup(tmp_path)
    ndir, idir = tmp_path / "norm", tmp_path / "index"
    ds.build_norm_stats(settings, ["NVDA"], out_dir=ndir)
    ds.build_decision_index(settings, ["NVDA"], out_dir=idir)
    data = ds.EncoderDataset(settings, ["NVDA"], index_dir=idir, norm_dir=ndir, features_dir=fdir)

    nf = len(slow.FEATURE_COLS)
    lag = ds.PRED_STAMP_TO_AVAILABILITY_NS
    t0 = 10_000 * NS_PER_S
    day = {  # two rows, one bar apart, with distinct all-channel values
        "feat_ts": np.array([t0, t0 + lag], dtype=np.int64),
        "feat_mat": np.array([np.full(nf, 3.0), np.full(nf, 7.0)], dtype=np.float32),
    }

    # decision exactly AT the first row's stamp: nothing is available yet -> zeros
    at_stamp = data._static_vector(day, "NVDA", t0, 0)
    np.testing.assert_array_equal(at_stamp[:nf], np.zeros(nf, dtype=np.float32))

    # one nanosecond before the lag elapses: still not available
    just_before = data._static_vector(day, "NVDA", t0 + lag - 1, 0)
    np.testing.assert_array_equal(just_before[:nf], np.zeros(nf, dtype=np.float32))

    # exactly one bar later the first row is knowable (the second row, stamped at
    # this very instant, is NOT) -> 3.0, never 7.0
    after_lag = data._static_vector(day, "NVDA", t0 + lag, 0)
    np.testing.assert_array_equal(after_lag[:nf], np.full(nf, 3.0, dtype=np.float32))

    # two bars later the second row is knowable too
    after_two = data._static_vector(day, "NVDA", t0 + 2 * lag, 0)
    np.testing.assert_array_equal(after_two[:nf], np.full(nf, 7.0, dtype=np.float32))


def test_dataset_item_static_uses_lagged_feature_row(tmp_path):
    """End-to-end: the 11:00 decision lands exactly on a 5-min feature stamp, so the
    item must carry the PREVIOUS stamp's features (index 17), not that row (18).
    """
    settings, fdir = _full_session_setup(tmp_path)
    ndir, idir = tmp_path / "norm", tmp_path / "index"
    ds.build_norm_stats(settings, ["NVDA"], out_dir=ndir)
    ds.build_decision_index(settings, ["NVDA"], out_dir=idir)
    data = ds.EncoderDataset(settings, ["NVDA"], index_dir=idir, norm_dir=ndir, features_dir=fdir)

    feat = pl.read_parquet(fdir / "NVDA.parquet").sort("ts")
    ts0 = int(data.index["ts"][0])                     # 11:00 ET decision instant
    assert int(feat["ts"][18]) == ts0                  # the stamp the decision lands on
    nf = len(slow.FEATURE_COLS)
    static = data[0]["static"].numpy()[:nf]
    expected = np.float32(feat[slow.FEATURE_COLS[0]][17])   # all f_* share one ramp
    np.testing.assert_allclose(static, np.full(nf, expected), rtol=0, atol=1e-7)
    # and NOT the row stamped at the decision instant (the pre-fix value)
    leaked = np.float32(feat[slow.FEATURE_COLS[0]][18])
    assert not np.allclose(static, np.full(nf, leaked), rtol=0, atol=1e-7)


def test_holdout_excluded_from_builds(tmp_path):
    settings = _settings(tmp_path)
    root = settings.raw_dir
    # one pre-holdout, one holdout session
    _write_partition(root, "NVDA", "2025-05-01", _event_bar_frame(200, ts0=0, seed=1))
    _write_partition(root, "NVDA", "2026-06-15", _event_bar_frame(200, ts0=10**12, seed=2))
    parts = ds._session_partitions(settings, "NVDA")
    assert "2025-05-01" in parts
    assert "2026-06-15" not in parts  # >= HOLDOUT_START is stripped
