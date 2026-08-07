"""M6-GBM cell of the ``moc_imbalance_v1`` family (M3_REGISTRATION.md, section
"M6-GBM cell — registered 2026-07-17"). A LightGBM regression on the realized
closing-auction ``net_bps`` of the registered base MOC events, fit under an
expanding calendar walk-forward, whose fixed a-priori gate (``pred > 0``) selects
a taken stream.

This module is the FEATURE + MODEL layer; ``apps/run_moc_gbm.py`` is the
orchestration + report layer. Nothing here writes a ledger row or a verdict.

Base events (registered): the ``MOC-max-t10-persist`` configuration — threshold
0.001 (0.10% of ADV$), persistence prong ON — with their realized ``net_bps``
from ``research/experiments/MOC-max-t10-persist/results.parquet``. We JOIN the
registered PIT features onto those rows (rather than re-run the auction replayer):
``norm_imb`` and ``adv20_dollars`` recomputed here reproduce the base file's
columns bit-for-bit (verified 2026-07-17), so the join is an exact augmentation of
the already-evaluated events, not a re-derivation of the economics.

Registered feature list — all PIT at 15:50:10 ET, from owned NOII + daily bars:
    norm_imb, side, paired_ratio = paired/(paired+|imb|),
    imbalance growth (norm_imb@15:50 - @15:48 and - @15:46),
    near-ref spread bps, near-far spread bps,
    near-price drift 15:46->15:50 bps, NOII message count so far,
    log ADV20$, trailing-20d realized vol (daily closes), symbol one-hot.
    NO calendar features.

DATA-REALITY NOTE (documented, not a deviation): the Nasdaq closing-cross NOII is
disseminated only from 15:50:00 ET (every 10 s, then every second from 15:55), and
the near/far indicative clearing prices are 0 until ~15:55. Consequently, at the
registered 15:50:10 PIT instant on the real tape:
  * there is no NOII message at or before 15:48 or 15:46, so the two growth
    features degenerate to ``norm_imb`` (prior imbalance treated as 0 — nothing
    disseminated yet), and the near-drift feature is 0;
  * near/far prices are 0, so near-ref / near-far spread bps are 0;
  * exactly two messages precede 15:50:10 (15:50:00 and 15:50:10), so msg_count is
    a near-constant 2.
These features are still computed EXACTLY per the registered formula; on real data
they simply carry little signal (visible in the feature-importance table). The
formulas are fully exercised — with prior messages and non-zero near/far prices —
in ``tests/test_moc_gbm.py`` so the implementation is verified against a
hand-computed vector.
"""

from __future__ import annotations

import calendar as _cal
from dataclasses import dataclass
from datetime import date

import lightgbm as lgb
import numpy as np
import polars as pl

from enginev51.data.noii import et_ns, load_noii_session, signal_at
from enginev51.models import lgbm as lgbm_model

# Registered universe (symbol one-hot columns are in this fixed order).
UNIVERSE: tuple[str, ...] = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")

# Feature columns fed to LightGBM, in a fixed, documented order. The final five
# are the symbol one-hot. ``side`` is kept alongside the signed ``norm_imb`` per
# the registered list.
NUMERIC_FEATURES: tuple[str, ...] = (
    "norm_imb",
    "side",
    "paired_ratio",
    "imb_growth_48",
    "imb_growth_46",
    "near_ref_bps",
    "near_far_bps",
    "near_drift_46_50",
    "msg_count",
    "log_adv20",
    "vol20",
)
ONEHOT_FEATURES: tuple[str, ...] = tuple(f"oh_{s}" for s in UNIVERSE)
FEATURE_COLS: tuple[str, ...] = NUMERIC_FEATURES + ONEHOT_FEATURES

LABEL_COL = "net_bps"

# Registered PIT instants (ET).
SIGNAL_HMS = (15, 50, 10)
T1548_HMS = (15, 48, 0)
T1546_HMS = (15, 46, 0)


# --------------------------------------------------------------------------- features


def _governing_row(frame: pl.DataFrame, ts: int) -> dict | None:
    """The last NOII message at or before ``ts`` (PIT), or ``None``."""
    prior = frame.filter(pl.col("ts") <= ts)
    if prior.height == 0:
        return None
    return prior.sort("ts").row(-1, named=True)


def _norm_imb_at(frame: pl.DataFrame, ts: int, adv20: float) -> float:
    """``norm_imb`` at ``ts`` via the registered ``signal_at``; 0.0 when no message
    has been disseminated at or before ``ts`` (nothing published yet ⇒ no imbalance)."""
    sig = signal_at(frame, ts, adv20)
    return float(sig["norm_imb"]) if sig is not None else 0.0


def noii_pit_features(
    frame: pl.DataFrame, session_iso: str, adv20: float
) -> dict | None:
    """The registered NOII-derived PIT features at 15:50:10 ET (pure over ``frame``).

    ``frame`` is a ``noii.NOII_SCHEMA`` frame (the loaded 15:45–16:00 window).
    Returns a dict of the NOII features, or ``None`` when there is no governing
    NOII message / usable price at 15:50:10 (no tradable signal ⇒ no feature row).
    A message strictly after 15:50:10 cannot change any value (PIT), which the
    tests assert directly.
    """
    ts_sig = et_ns(session_iso, *SIGNAL_HMS)
    ts_48 = et_ns(session_iso, *T1548_HMS)
    ts_46 = et_ns(session_iso, *T1546_HMS)

    sig = signal_at(frame, ts_sig, adv20)
    if sig is None:
        return None
    norm_imb = float(sig["norm_imb"])
    side = int(sig["side"])

    gov = _governing_row(frame, ts_sig)
    if gov is None:  # unreachable when signal_at succeeded, but keep total
        return None

    imb_shares = float(gov["imbalance_shares"] or 0.0)
    paired = float(gov["paired_shares"] or 0.0)
    denom = paired + abs(imb_shares)
    paired_ratio = (paired / denom) if denom > 0.0 else 0.0

    near = float(gov["near_price"] or 0.0)
    far = float(gov["far_price"] or 0.0)
    ref = float(gov["ref_price"] or 0.0)
    near_ref_bps = ((near - ref) / ref * 1e4) if (near > 0.0 and ref > 0.0) else 0.0
    near_far_bps = ((near - far) / far * 1e4) if (near > 0.0 and far > 0.0) else 0.0

    gov_46 = _governing_row(frame, ts_46)
    near_46 = float(gov_46["near_price"] or 0.0) if gov_46 is not None else 0.0
    near_drift = (
        (near - near_46) / near_46 * 1e4 if (near > 0.0 and near_46 > 0.0) else 0.0
    )

    imb_growth_48 = norm_imb - _norm_imb_at(frame, ts_48, adv20)
    imb_growth_46 = norm_imb - _norm_imb_at(frame, ts_46, adv20)

    msg_count = int(frame.filter(pl.col("ts") <= ts_sig).height)

    return {
        "norm_imb": norm_imb,
        "side": float(side),
        "paired_ratio": paired_ratio,
        "imb_growth_48": imb_growth_48,
        "imb_growth_46": imb_growth_46,
        "near_ref_bps": near_ref_bps,
        "near_far_bps": near_far_bps,
        "near_drift_46_50": near_drift,
        "msg_count": float(msg_count),
    }


def trailing_vol20(
    closes: list[tuple[str, float]], session_iso: str, window: int = 20
) -> float:
    """Trailing 20-session realized vol = sample std of daily log-returns of the
    daily closes STRICTLY before ``session_iso`` (PIT).

    ``closes`` is a list of ``(session_iso, close)`` (any order). Uses the last
    ``window`` returns available (from the last ``window + 1`` prior closes).
    Returns ``nan`` when fewer than 2 prior returns exist (LightGBM handles nan).
    """
    prior_pairs = sorted(
        [(d, float(c)) for d, c in closes if d < session_iso and c is not None and c > 0.0]
    )
    vals = [c for _d, c in prior_pairs][-(window + 1) :]
    if len(vals) < 3:
        return float("nan")
    arr = np.asarray(vals, dtype=float)
    rets = np.diff(np.log(arr))
    if rets.size < 2:
        return float("nan")
    return float(np.std(rets, ddof=1))


def symbol_onehot(symbol: str) -> dict[str, float]:
    sym = symbol.upper()
    return {f"oh_{s}": (1.0 if s == sym else 0.0) for s in UNIVERSE}


def build_features(
    symbol: str,
    session: str,
    *,
    settings=None,
    noii_dir=None,
    adv20: float | None = None,
    noii_frame: pl.DataFrame | None = None,
    closes: list[tuple[str, float]] | None = None,
) -> dict | None:
    """Registered PIT feature vector for one (symbol, session) at 15:50:10 ET.

    Self-contained: loads the NOII window, the trailing dollar ADV20, and the
    daily closes itself when those are not injected. Every input is injectable so
    tests exercise the pure path with hand-built literals (no disk, no network).

    Returns a dict of ``FEATURE_COLS`` plus ``symbol``/``session``, or ``None``
    when the event has no governing NOII signal at 15:50:10.
    """
    sym = symbol.upper()

    if noii_frame is None:
        noii_frame = load_noii_session(sym, session, out_dir=noii_dir)
    if noii_frame is None or noii_frame.height == 0:
        return None

    if adv20 is None:
        from enginev51.backtest.auction_replay import adv20_dollars
        from enginev51.config import get_settings

        s = settings if settings is not None else get_settings()
        adv20 = adv20_dollars(s, sym, session)
    if adv20 is None or adv20 <= 0.0:
        return None

    nf = noii_pit_features(noii_frame, session, float(adv20))
    if nf is None:
        return None

    if closes is None:
        closes = _load_daily_closes(sym)
    vol20 = trailing_vol20(closes, session)

    feat: dict = dict(nf)
    feat["log_adv20"] = float(np.log(adv20))
    feat["vol20"] = vol20
    feat.update(symbol_onehot(sym))
    feat["symbol"] = sym
    feat["session"] = session
    return feat


def _load_daily_closes(symbol: str) -> list[tuple[str, float]]:
    """Daily (session_iso, close) pairs from ``data/raw/sip/bars1d`` (UTC date, the
    label date convention used across ``backtest/auction_replay``)."""
    from datetime import UTC, datetime
    from pathlib import Path

    p = Path("data/raw/sip/bars1d") / f"{symbol.upper()}.parquet"
    if not p.exists():
        return []
    df = pl.read_parquet(p)
    out: list[tuple[str, float]] = []
    for r in df.iter_rows(named=True):
        d = datetime.fromtimestamp(r["ts"] / 1e9, tz=UTC).date().isoformat()
        out.append((d, float(r["close"])))
    return out


# --------------------------------------------------------------------------- folds


@dataclass(slots=True, frozen=True)
class Fold:
    train_sessions: tuple[str, ...]
    test_sessions: tuple[str, ...]
    test_start: str
    test_end: str


def _add_months(d: date, months: int) -> date:
    m0 = d.month - 1 + months
    y = d.year + m0 // 12
    m = m0 % 12 + 1
    day = min(d.day, _cal.monthrange(y, m)[1])
    return date(y, m, day)


def walk_forward_folds_calendar(
    sessions: list[str],
    *,
    initial_train_years: int = 2,
    test_block_months: int = 6,
    embargo_sessions: int = 1,
) -> list[Fold]:
    """Expanding calendar walk-forward per the registration: ≥2y initial train,
    6-month test blocks, 1-session embargo.

    The first test block starts at ``first_session_date + initial_train_years``;
    each block spans ``test_block_months`` calendar months. A fold's training set
    is every session strictly before its test-block start, minus the last
    ``embargo_sessions`` unique sessions (the 1-session gap). Blocks tile the span
    so every event beyond the initial-train span receives exactly one OOS
    prediction.
    """
    uniq = sorted(set(sessions))
    if not uniq:
        return []
    first = date.fromisoformat(uniq[0])
    last = date.fromisoformat(uniq[-1])
    block_start = _add_months(first, 12 * initial_train_years)

    folds: list[Fold] = []
    start = block_start
    while start <= last:
        end = _add_months(start, test_block_months)  # exclusive
        s_iso, e_iso = start.isoformat(), end.isoformat()
        test = [d for d in uniq if s_iso <= d < e_iso]
        train_all = [d for d in uniq if d < s_iso]
        train = train_all[: len(train_all) - embargo_sessions] if embargo_sessions else train_all
        if train and test:
            folds.append(Fold(tuple(train), tuple(test), s_iso, e_iso))
        start = end
    return folds


# --------------------------------------------------------------------------- model


def gate(pred: np.ndarray | float) -> np.ndarray | bool:
    """The FIXED registered gate: TAKE iff predicted net > 0. No threshold tuning."""
    if np.isscalar(pred):
        return bool(pred > 0.0)
    return np.asarray(pred, dtype=float) > 0.0


def train_fold(df_train: pl.DataFrame, params: dict | None = None) -> lgb.Booster:
    """Fit one LightGBM regressor on ``net_bps`` with ``lgbm.DEFAULT_PARAMS``."""
    return lgbm_model.train_one(df_train, FEATURE_COLS, LABEL_COL, params=params)


def run_walk_forward(
    feat_df: pl.DataFrame,
    *,
    initial_train_years: int = 2,
    test_block_months: int = 6,
    embargo_sessions: int = 1,
    params: dict | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, list[Fold]]:
    """Expanding walk-forward over ``feat_df`` (one row per base event, carrying
    ``session``/``symbol``/``net_bps`` + ``FEATURE_COLS``).

    Returns ``(oos_df, importances_df, folds)``:
      * ``oos_df`` — every event beyond the initial-train span with an added
        ``pred`` (OOS prediction) and ``fold`` (test-block start) column;
      * ``importances_df`` — mean LightGBM gain per feature across folds;
      * ``folds`` — the fold objects (train/test session tuples).
    """
    sessions = sorted(feat_df["session"].unique().to_list())
    folds = walk_forward_folds_calendar(
        sessions,
        initial_train_years=initial_train_years,
        test_block_months=test_block_months,
        embargo_sessions=embargo_sessions,
    )
    oos_parts: list[pl.DataFrame] = []
    imp_accum: dict[str, list[float]] = {c: [] for c in FEATURE_COLS}
    for fold in folds:
        tr = feat_df.filter(pl.col("session").is_in(list(fold.train_sessions)))
        te = feat_df.filter(pl.col("session").is_in(list(fold.test_sessions)))
        if tr.height == 0 or te.height == 0:
            continue
        booster = train_fold(tr, params=params)
        preds = lgbm_model.predict(booster, te, FEATURE_COLS)
        oos_parts.append(
            te.with_columns(
                pl.Series("pred", preds),
                pl.lit(fold.test_start).alias("fold"),
            )
        )
        gains = booster.feature_importance(importance_type="gain")
        names = booster.feature_name()
        for name, g in zip(names, gains, strict=True):
            if name in imp_accum:
                imp_accum[name].append(float(g))

    oos_df = (
        pl.concat(oos_parts) if oos_parts else feat_df.head(0).with_columns(
            pl.lit(None, dtype=pl.Float64).alias("pred"),
            pl.lit(None, dtype=pl.Utf8).alias("fold"),
        )
    )
    imp_rows = [
        {
            "feature": c,
            "mean_gain": float(np.mean(imp_accum[c])) if imp_accum[c] else 0.0,
            "n_folds": len(imp_accum[c]),
        }
        for c in FEATURE_COLS
    ]
    importances_df = pl.DataFrame(
        imp_rows,
        schema={"feature": pl.Utf8, "mean_gain": pl.Float64, "n_folds": pl.Int64},
    ).sort("mean_gain", descending=True)
    return oos_df, importances_df, folds
