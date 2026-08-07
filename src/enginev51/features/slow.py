"""Slow feature family: per-minute, session-aware, strictly trailing (point-in-time).

Every window is either (a) a session-scoped shift/cumulation, or (b) a global
rolling masked by in-session row count so it can never span sessions, or
(c) a *daily* rolling that is shift(1)-ed so today's value only uses prior
sessions. The lookahead test in tests/test_features.py asserts the invariant:
truncating future data never changes a past feature row.

Normalization: return-like features are divided by vol20 (trailing 20-session
daily vol) scaled to the window length, so features pool across names.
"""

from __future__ import annotations

import polars as pl

RET_WINDOWS = (5, 15, 30, 60, 120)
DAY_MINUTES = 390.0

# final feature column order (model input). Kept explicit: the registry of v1.
FEATURE_COLS: tuple[str, ...] = (
    # own returns (vol-normalized)
    "f_ret_5m_z", "f_ret_15m_z", "f_ret_30m_z", "f_ret_60m_z", "f_ret_120m_z",
    "f_ret_since_open_z", "f_gap_open_z",
    # vol state
    "f_rv_30m_ann", "f_vol_ratio_30m", "f_vol20", "f_vol_trend",
    # location within the day's structure
    "f_vwap_dev_z", "f_dist_high_z", "f_dist_low_z", "f_range_used_z",
    # participation
    "f_rel_volume_cum", "f_dv_5m_ratio", "f_premarket_dv_ratio",
    # order-flow proxies (bar-level signed flow; Lillo–Farmer flow-memory family)
    "f_flow_5m", "f_flow_30m", "f_flow_120m", "f_upvol_30m", "f_close_loc_30m",
    # market (QQQ) context
    "f_mkt_ret_5m_z", "f_mkt_ret_30m_z", "f_mkt_ret_120m_z",
    "f_mkt_ret_1d", "f_mkt_vol20",
    # sector context + idiosyncratic residuals
    "f_sec_ret_30m_z", "f_idio_ret_30m_z", "f_idio_ret_120m_z",
    "f_rs_1d", "f_rs_5d", "f_beta_mkt",
    # time-of-day / calendar
    "f_min_since_open", "f_min_to_close", "f_dow",
)

META_COLS: tuple[str, ...] = (
    "symbol", "session", "ts", "minute_idx", "n_minutes", "is_real",
    "close", "vol20", "dv20",
)


def _row_in_sess() -> pl.Expr:
    return pl.int_range(pl.len()).over("session")


def _masked_rolling_sum(col: str, w: int) -> pl.Expr:
    """Global rolling sum masked so the window always lies inside the session."""
    return (
        pl.when(_row_in_sess() >= w)
        .then(pl.col(col).rolling_sum(window_size=w, min_samples=w))
        .otherwise(None)
    )


def compute_base(grid: pl.DataFrame) -> pl.DataFrame:
    """Per-symbol trailing features that don't need another symbol."""
    df = grid.sort("ts").with_columns(
        (pl.col("close") / pl.col("close").shift(1)).log().over("session").alias("r1"),
    )
    df = df.with_columns((pl.col("r1") ** 2).alias("r1sq"))

    # within-session returns over multiple windows
    df = df.with_columns(
        [
            (pl.col("close") / pl.col("close").shift(w)).log().over("session").alias(f"ret_{w}m")
            for w in RET_WINDOWS
        ]
    )

    # realized vol over 30m/120m (session-safe via mask)
    df = df.with_columns(
        _masked_rolling_sum("r1sq", 30).sqrt().alias("rv_30m"),
        _masked_rolling_sum("r1sq", 120).sqrt().alias("rv_120m"),
        _masked_rolling_sum("dollar_vol", 5).alias("dv_5m"),
    )

    # bar-level signed flow: direction from the bar's own move (tick-rule proxy)
    df = df.with_columns(
        (
            pl.when(pl.col("r1") > 0)
            .then(pl.col("dollar_vol"))
            .when(pl.col("r1") < 0)
            .then(-pl.col("dollar_vol"))
            .otherwise(0.0)
        ).alias("signed_dv"),
        pl.when(pl.col("r1") > 0).then(pl.col("dollar_vol")).otherwise(0.0).alias("up_dv"),
    )
    df = df.with_columns(
        _masked_rolling_sum("signed_dv", 5).alias("flow_5m"),
        _masked_rolling_sum("signed_dv", 30).alias("flow_30m"),
        _masked_rolling_sum("signed_dv", 120).alias("flow_120m"),
        _masked_rolling_sum("up_dv", 30).alias("up_dv_30m"),
        _masked_rolling_sum("dollar_vol", 30).alias("dv_30m"),
        pl.when(_row_in_sess() >= 30)
        .then(pl.col("high").rolling_max(window_size=30, min_samples=30))
        .otherwise(None)
        .alias("hi_30m"),
        pl.when(_row_in_sess() >= 30)
        .then(pl.col("low").rolling_min(window_size=30, min_samples=30))
        .otherwise(None)
        .alias("lo_30m"),
    )

    # session-cumulative structures
    df = df.with_columns(
        pl.col("dollar_vol").cum_sum().over("session").alias("cum_dv"),
        pl.col("volume").cum_sum().over("session").alias("cum_v"),
        (pl.col("dollar_vol")).cum_sum().over("session").alias("_cum_pv"),
        pl.col("high").cum_max().over("session").alias("day_high"),
        pl.col("low").cum_min().over("session").alias("day_low"),
        pl.col("close").first().over("session").alias("sess_first_close"),
        _row_in_sess().alias("row_in_sess"),
    )
    df = df.with_columns(
        pl.when(pl.col("cum_v") > 0)
        .then(pl.col("_cum_pv") / pl.col("cum_v"))
        .otherwise(pl.col("close"))
        .alias("vwap_sess"),
    ).drop("_cum_pv")

    df = df.with_columns(
        (pl.col("close") / pl.col("vwap_sess")).log().alias("vwap_dev"),
        (pl.col("close") / pl.col("day_high")).log().alias("dist_high"),
        (pl.col("close") / pl.col("day_low")).log().alias("dist_low"),
        (pl.col("day_high") / pl.col("day_low")).log().alias("range_used"),
        (pl.col("close") / pl.col("sess_first_close")).log().alias("ret_since_open"),
    )

    # ---- daily frame: everything shift(1)ed so it is known before today's open
    daily = (
        df.group_by("session")
        .agg(
            pl.col("close").last().alias("sess_close"),
            pl.col("prev_close").first().alias("sess_prev_close"),
            pl.col("r1sq").sum().alias("rv_d_sq"),
            pl.col("dollar_vol").sum().alias("total_dv"),
            pl.col("premarket_dv").first().alias("pm_dv"),
        )
        .sort("session")
        .with_columns(
            (pl.col("sess_close") / pl.col("sess_prev_close")).log().alias("sess_ret"),
        )
        .with_columns(
            pl.col("rv_d_sq")
            .rolling_mean(window_size=20, min_samples=10)
            .shift(1)
            .sqrt()
            .alias("vol20"),
            pl.col("total_dv").rolling_mean(window_size=20, min_samples=10).shift(1).alias("dv20"),
            pl.col("sess_ret").shift(1).alias("ret_1d_prev"),
            pl.col("sess_ret").rolling_sum(window_size=5, min_samples=5).shift(1).alias("ret_5d_prev"),
            pl.col("rv_d_sq")
            .rolling_mean(window_size=60, min_samples=30)
            .shift(1)
            .sqrt()
            .alias("vol60"),
        )
        .select(
            "session", "sess_ret", "vol20", "vol60", "dv20", "ret_1d_prev", "ret_5d_prev"
        )
    )
    return df.join(daily, on="session", how="left")


def _z(col: str, minutes: float) -> pl.Expr:
    """Normalize a `minutes`-window log-return by vol20 scaled to that window."""
    scale = pl.col("vol20") * (minutes / DAY_MINUTES) ** 0.5
    return (
        pl.when(pl.col("vol20") > 0).then(pl.col(col) / scale).otherwise(None)
    )


def compute_features(
    base: pl.DataFrame,
    market: pl.DataFrame,
    sector: pl.DataFrame | None,
    daily_beta_window: int = 60,
) -> pl.DataFrame:
    """Join anchor bases (already compute_base'd) and emit the final f_* frame."""
    mkt_cols = market.select(
        "ts",
        pl.col("ret_5m").alias("mkt_ret_5m"),
        pl.col("ret_30m").alias("mkt_ret_30m"),
        pl.col("ret_120m").alias("mkt_ret_120m"),
        pl.col("vol20").alias("mkt_vol20"),
        pl.col("ret_1d_prev").alias("mkt_ret_1d_prev"),
        pl.col("ret_5d_prev").alias("mkt_ret_5d_prev"),
        pl.col("sess_ret").alias("mkt_sess_ret"),
    )
    sec_src = sector if sector is not None else market
    sec_cols = sec_src.select(
        "ts",
        pl.col("ret_30m").alias("sec_ret_30m"),
        pl.col("ret_120m").alias("sec_ret_120m"),
        pl.col("vol20").alias("sec_vol20"),
        pl.col("ret_1d_prev").alias("sec_ret_1d_prev"),
        pl.col("ret_5d_prev").alias("sec_ret_5d_prev"),
        pl.col("close").alias("sec_close"),
        pl.col("sess_ret").alias("sec_sess_ret"),
    )
    df = base.join(mkt_cols, on="ts", how="left").join(sec_cols, on="ts", how="left")

    # rolling daily beta vs market, shift(1)ed (known at open)
    daily = (
        df.group_by("session")
        .agg(
            pl.col("sess_ret").first().alias("y"),
            pl.col("mkt_sess_ret").first().alias("x"),
        )
        .sort("session")
        .with_columns(
            (
                pl.rolling_cov("y", "x", window_size=daily_beta_window, min_samples=20)
                / pl.col("x").rolling_var(window_size=daily_beta_window, min_samples=20)
            )
            .shift(1)
            .alias("beta_mkt"),
        )
        .select("session", "beta_mkt")
    )
    df = df.join(daily, on="session", how="left").with_columns(
        pl.col("beta_mkt").clip(-1.0, 4.0).fill_null(1.0)
    )

    df = df.with_columns(
        (pl.col("ret_30m") - pl.col("beta_mkt") * pl.col("mkt_ret_30m")).alias("idio_ret_30m"),
        (pl.col("ret_120m") - pl.col("beta_mkt") * pl.col("mkt_ret_120m")).alias("idio_ret_120m"),
    )

    dow = (
        pl.col("session").str.to_date().dt.weekday().cast(pl.Float64).alias("f_dow")
    )

    out = df.with_columns(
        # own returns, normalized
        _z("ret_5m", 5).alias("f_ret_5m_z"),
        _z("ret_15m", 15).alias("f_ret_15m_z"),
        _z("ret_30m", 30).alias("f_ret_30m_z"),
        _z("ret_60m", 60).alias("f_ret_60m_z"),
        _z("ret_120m", 120).alias("f_ret_120m_z"),
        (pl.col("ret_since_open") / pl.col("vol20")).alias("f_ret_since_open_z"),
        (pl.col("gap_open") / pl.col("vol20")).alias("f_gap_open_z"),
        # vol state
        (pl.col("rv_30m") * (DAY_MINUTES / 30.0) ** 0.5 * 252**0.5).alias("f_rv_30m_ann"),
        (
            pl.when(pl.col("vol20") > 0)
            .then(pl.col("rv_30m") * (DAY_MINUTES / 30.0) ** 0.5 / pl.col("vol20"))
            .otherwise(None)
        ).alias("f_vol_ratio_30m"),
        pl.col("vol20").alias("f_vol20"),
        (
            pl.when(pl.col("vol60") > 0)
            .then((pl.col("vol20") / pl.col("vol60")).log())
            .otherwise(None)
        ).alias("f_vol_trend"),
        # location
        (pl.col("vwap_dev") / pl.col("vol20")).alias("f_vwap_dev_z"),
        (pl.col("dist_high") / pl.col("vol20")).alias("f_dist_high_z"),
        (pl.col("dist_low") / pl.col("vol20")).alias("f_dist_low_z"),
        (pl.col("range_used") / pl.col("vol20")).alias("f_range_used_z"),
        # participation
        (
            pl.when((pl.col("dv20") > 0) & (pl.col("row_in_sess") >= 0))
            .then(
                pl.col("cum_dv")
                / (
                    pl.col("dv20")
                    * ((pl.col("row_in_sess") + 1).cast(pl.Float64) / pl.col("n_minutes"))
                )
            )
            .otherwise(None)
        ).alias("f_rel_volume_cum"),
        (
            pl.when(pl.col("dv20") > 0)
            .then(pl.col("dv_5m") / (pl.col("dv20") * 5.0 / DAY_MINUTES))
            .otherwise(None)
        ).alias("f_dv_5m_ratio"),
        (
            pl.when(pl.col("dv20") > 0)
            .then(pl.col("premarket_dv") / pl.col("dv20"))
            .otherwise(None)
        ).alias("f_premarket_dv_ratio"),
        # order-flow proxies, normalized by the same participation scale
        (
            pl.when(pl.col("dv20") > 0)
            .then(pl.col("flow_5m") / (pl.col("dv20") * 5.0 / DAY_MINUTES))
            .otherwise(None)
        ).alias("f_flow_5m"),
        (
            pl.when(pl.col("dv20") > 0)
            .then(pl.col("flow_30m") / (pl.col("dv20") * 30.0 / DAY_MINUTES))
            .otherwise(None)
        ).alias("f_flow_30m"),
        (
            pl.when(pl.col("dv20") > 0)
            .then(pl.col("flow_120m") / (pl.col("dv20") * 120.0 / DAY_MINUTES))
            .otherwise(None)
        ).alias("f_flow_120m"),
        (
            pl.when(pl.col("dv_30m") > 0)
            .then(pl.col("up_dv_30m") / pl.col("dv_30m") - 0.5)
            .otherwise(None)
        ).alias("f_upvol_30m"),
        (
            pl.when((pl.col("hi_30m") - pl.col("lo_30m")) > 0)
            .then(
                (pl.col("close") - pl.col("lo_30m")) / (pl.col("hi_30m") - pl.col("lo_30m")) - 0.5
            )
            .otherwise(None)
        ).alias("f_close_loc_30m"),
        # market context
        _mkt_z("mkt_ret_5m", 5).alias("f_mkt_ret_5m_z"),
        _mkt_z("mkt_ret_30m", 30).alias("f_mkt_ret_30m_z"),
        _mkt_z("mkt_ret_120m", 120).alias("f_mkt_ret_120m_z"),
        pl.col("mkt_ret_1d_prev").alias("f_mkt_ret_1d"),
        pl.col("mkt_vol20").alias("f_mkt_vol20"),
        # sector + idio
        (
            pl.when(pl.col("sec_vol20") > 0)
            .then(pl.col("sec_ret_30m") / (pl.col("sec_vol20") * (30 / DAY_MINUTES) ** 0.5))
            .otherwise(None)
        ).alias("f_sec_ret_30m_z"),
        _z("idio_ret_30m", 30).alias("f_idio_ret_30m_z"),
        _z("idio_ret_120m", 120).alias("f_idio_ret_120m_z"),
        (pl.col("ret_1d_prev") - pl.col("sec_ret_1d_prev")).alias("f_rs_1d"),
        (pl.col("ret_5d_prev") - pl.col("sec_ret_5d_prev")).alias("f_rs_5d"),
        pl.col("beta_mkt").alias("f_beta_mkt"),
        # time
        pl.col("row_in_sess").cast(pl.Float64).alias("f_min_since_open"),
        (pl.col("n_minutes") - 1 - pl.col("row_in_sess")).cast(pl.Float64).alias("f_min_to_close"),
        dow,
    )
    return out


def _mkt_z(col: str, minutes: float) -> pl.Expr:
    scale = pl.col("mkt_vol20") * (minutes / DAY_MINUTES) ** 0.5
    return pl.when(pl.col("mkt_vol20") > 0).then(pl.col(col) / scale).otherwise(None)
