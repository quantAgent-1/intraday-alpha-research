"""live_cockpit -- the production decision cockpit for the champion MOC-basis strategy.

SIGNAL-ONLY, BY CONSTRUCTION. This module computes and DISPLAYS a decision plus an
exact MANUAL order ticket that a human reads and keys by hand into their broker UI.
It contains NO order-routing code, imports NO broker/trading API, and has NO path
that can place, modify, or cancel an order. It never writes to the research ledger
or any research/*.md. ``rehearse`` reads only the local owned lake (no network).

The champion rule (registered ``moc_imbalance_v1`` M6-FINAL + M8 meta, M3_REGISTRATION):
  * at 15:55:10 ET: ``basis_bps = 1e4 * (near / mid - 1)`` where ``near`` is the last
    NOII near (indicative clearing) price > 0 at-or-before 15:55:10 and ``mid`` is the
    prevailing market mid ``(bid + ask) / 2``;
  * TRADE iff ``|basis_bps| >= 10``; direction WITH the basis (near > mid -> BUY,
    near < mid -> SELL SHORT); exit AT the 16:00 closing cross;
  * the M8 meta stream ADDITIONALLY requires ``P(win) >= 0.55`` from the FROZEN
    LightGBM classifier (``research/forward/m8_model.txt``, the same model
    ``apps/forward_paper.py`` runs); with the model loaded and P(win) computable a
    meta NO-GO BLOCKS the order ticket (it is not merely displayed); M15 keeps the
    top-3 firing names by ``P(win)``.

Three modes over one shared, pure decision core::

    python -m enginev51.apps.live_cockpit decide    --symbol NVDA --near .. --bid .. --ask ..
    python -m enginev51.apps.live_cockpit rehearse   --session 2026-07-17
    python -m enginev51.apps.live_cockpit checklist

``decide`` is the live path (manual input). ``rehearse`` replays a settled session
from the lake through the EXACT forward_paper feature/scoring path (training +
verification). ``checklist`` prints the pre-close runbook.

Feature/model reuse (NOT reimplemented here): the frozen M8 model is loaded the same
way ``forward_paper`` loads it; the snapshot M8 features are computed by the frozen
``run_basis_trial.basis_pit_features`` path; ``P(win)`` comes from
``moc_meta.predict_pwin`` behind the registered ``moc_meta.gate``; ``rehearse`` calls
``forward_paper.compute_session_events`` + ``score_events`` so its numbers match the
harness by construction. The ONLY behaviour that differs from ``forward_paper`` is
model loading: the cockpit LOADS the frozen model if present and otherwise DEGRADES
to classical-only (it never trains -- training is a research action, out of scope for
a signal tool).
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import click
import lightgbm as lgb
import numpy as np
import polars as pl

from enginev51 import positioning
from enginev51.apps import forward_paper as fp
from enginev51.apps import run_basis_trial as rbt
from enginev51.config import Settings, get_settings
from enginev51.data.noii import NOII_SCHEMA, et_ns
from enginev51.models import moc_meta
from enginev51.models.moc_gbm import symbol_onehot

ET = ZoneInfo("America/New_York")

# Champion constants -- sourced from the registered modules, never redefined loosely.
UNIVERSE: tuple[str, ...] = moc_meta.UNIVERSE  # ("NVDA","TSLA","AMD","MU","GOOGL")
BASIS_THRESHOLD_BPS: float = moc_meta.CANDIDATE_BASIS_BPS  # 10.0
META_GATE_Q: float = fp.META_GATE_Q  # 0.55
MAX_POSITIONS: int = positioning.MAX_POSITIONS  # 3
MODEL_PATH: Path = fp.MODEL_PATH  # research/forward/m8_model.txt

# Deploy defaults (positioning.DEPLOY_CAPITAL_USD). The per-clip cap models
# manual-keying / single-order risk; there is NO registered MOC spread-abort threshold
# in the M3_REGISTRATION MOC spec, so it is PARAMETERIZED here with a 25 bps default.
DEFAULT_CAPITAL_USD: float = 1000.0
DEFAULT_CLIP_CAP_USD: float = 800.0
DEFAULT_SPREAD_ABORT_BPS: float = 25.0

DECISION_HMS: tuple[int, int, int] = (15, 55, 10)
CLOCK_LO_ET: tuple[int, int] = (15, 54)
CLOCK_HI_ET: tuple[int, int] = (15, 59)

EXIT_MODES: tuple[str, ...] = ("late-loc", "marketable", "auto-note")


# ============================================================================= core
# Pure functions -- inputs -> decision. No I/O, no clock, no printing. Fully unit
# tested. The CLI layers I/O + rendering on top.


def market_mid(bid: float, ask: float) -> float:
    """Prevailing market mid ``(bid + ask) / 2``."""
    return (float(bid) + float(ask)) / 2.0


def spread_bps(bid: float, ask: float, mid: float) -> float:
    """Quoted spread in basis points, ``(ask - bid) / mid * 1e4`` (negative if crossed)."""
    return (float(ask) - float(bid)) / mid * 1e4


def size_shares(capital_usd: float, clip_cap_usd: float, price: float | None) -> int:
    """Whole-share clip size: ``floor(min(capital, per-clip cap) / price)``.

    The per-clip cap bounds any single manual order; with the deploy defaults
    (capital $1,000, cap $800) a clip is sized to $800. Returns 0 for a
    non-positive/absent price or when even one whole share exceeds the clip
    notional (the caller renders that as "capital insufficient").
    """
    if price is None or not price > 0.0:
        return 0
    notional = min(float(capital_usd), float(clip_cap_usd))
    if notional <= 0.0:
        return 0
    return int(math.floor(notional / float(price)))


def classify_basis(
    near: float | None,
    bid: float | None,
    ask: float | None,
    *,
    threshold_bps: float = BASIS_THRESHOLD_BPS,
) -> dict:
    """The classical champion verdict from a manual (near, bid, ask) snapshot.

    Returns the mid, quoted spread, ``basis_bps``, direction (+1 BUY / -1 SELL SHORT
    / 0 no-trade), the side word, an ``errors`` list (bad/crossed quotes, invalid
    near), and the classical GO/NO-GO with its reason. Pure and total.
    """
    errors: list[str] = []
    mid: float | None = None
    spr: float | None = None

    if bid is None or ask is None or bid <= 0.0 or ask <= 0.0:
        errors.append("bid/ask invalid (must be > 0)")
    else:
        mid = market_mid(bid, ask)
        spr = spread_bps(bid, ask, mid)
        if bid > ask:
            errors.append(f"crossed quotes: bid {bid:.4f} > ask {ask:.4f}")

    if near is None or near <= 0.0:
        errors.append("near price invalid (must be > 0)")

    basis: float | None = None
    direction = 0
    side_word: str | None = None
    if mid is not None and mid > 0.0 and near is not None and near > 0.0:
        basis = rbt.basis_bps_of(float(near), mid)
        direction = rbt.direction_of(float(near), mid)
        side_word = {1: "BUY", -1: "SELL SHORT", 0: None}[direction]

    if errors:
        reason = "; ".join(errors)
        classical_go = False
    elif direction == 0:
        reason = "near == mid: no tradable basis"
        classical_go = False
    elif abs(basis) >= threshold_bps:  # type: ignore[arg-type]
        reason = f"|{basis:+.1f}| >= {threshold_bps:g}"
        classical_go = True
    else:
        reason = f"|{basis:+.1f}| < {threshold_bps:g}"
        classical_go = False

    return {
        "mid": mid,
        "spread_bps": spr,
        "basis_bps": basis,
        "direction": direction,
        "side_word": side_word,
        "errors": errors,
        "classical_go": classical_go,
        "classical_reason": reason,
    }


def missing_meta_inputs(
    *,
    far: float | None,
    ref: float | None,
    imbalance: float | None,
    paired: float | None,
    adv20: float | None,
    vol20: float | None,
    imb_growth_53: float | None,
    imb_growth_51: float | None,
    msg_count: float | None,
) -> list[str]:
    """Which registered M8 features cannot be built from the supplied manual inputs.

    Each entry names the missing feature and the flag(s) that would supply it, in the
    registered feature order. An empty list means the full ``moc_meta.FEATURE_COLS``
    vector is computable and the meta gate can run.
    """
    missing: list[str] = []
    if far is None:
        missing.append("near_far_bps(--far)")
    if ref is None:
        missing.append("near_ref_bps(--ref)")
    if paired is None or imbalance is None:
        missing.append("paired_ratio(--paired,--imbalance)")
    if imbalance is None or adv20 is None:
        missing.append("norm_imb(--imbalance,--adv20)")
    if imb_growth_53 is None:
        missing.append("imb_growth_53(--imb-growth-53)")
    if imb_growth_51 is None:
        missing.append("imb_growth_51(--imb-growth-51)")
    if msg_count is None:
        missing.append("msg_count(--msg-count)")
    if vol20 is None:
        missing.append("vol20(--vol20)")
    if adv20 is None:
        missing.append("log_adv20(--adv20)")
    return missing


def build_meta_row(
    symbol: str,
    session_iso: str,
    near: float,
    mid: float,
    *,
    far: float,
    ref: float,
    imbalance: float,
    paired: float,
    adv20: float,
    vol20: float,
    imb_growth_53: float,
    imb_growth_51: float,
    msg_count: float,
) -> dict:
    """Assemble the registered ``moc_meta.FEATURE_COLS`` row from manual inputs.

    The snapshot features (basis_bps, norm_imb, paired_ratio, near_ref_bps,
    near_far_bps) are computed by the FROZEN ``run_basis_trial.basis_pit_features``
    path -- a synthetic single-message NOII frame at 15:55:10 is fed through it, so
    the arithmetic is byte-identical to the forward harness (no copy-pasted formula).
    The history features (imb_growth_53/51, msg_count) cannot come from a one-message
    snapshot and are supplied directly by the caller (already validated present).
    ``imbalance`` is signed: buy-side positive, sell-side negative (magnitude in shares).
    """
    ts = et_ns(session_iso, *DECISION_HMS)
    side_char = "B" if imbalance > 0 else ("A" if imbalance < 0 else "N")
    frame = pl.DataFrame(
        {
            "ts": [ts],
            "side": [side_char],
            "imbalance_shares": [abs(float(imbalance))],
            "paired_shares": [float(paired)],
            "near_price": [float(near)],
            "far_price": [float(far)],
            "ref_price": [float(ref)],
        },
        schema=NOII_SCHEMA,
    )
    feats = rbt.basis_pit_features(frame, session_iso, float(adv20), float(near), float(mid))
    row = {
        "basis_bps": feats["basis_bps"],
        "near_far_bps": feats["near_far_bps"],
        "near_ref_bps": feats["near_ref_bps"],
        "paired_ratio": feats["paired_ratio"],
        "norm_imb": feats["norm_imb"],
        "imb_growth_53": float(imb_growth_53),
        "imb_growth_51": float(imb_growth_51),
        "msg_count": float(msg_count),
        "vol20": float(vol20),
        "log_adv20": float(np.log(float(adv20))),
    }
    row.update(symbol_onehot(symbol))
    return row


def predict_pwin_row(booster: lgb.Booster, row: dict) -> float:
    """P(win) for one manual feature row via the frozen model (registered predict path)."""
    df = pl.DataFrame([row])
    moc_meta.assert_features_present(df)
    return float(moc_meta.predict_pwin(booster, df)[0])


def compute_meta(
    booster: lgb.Booster | None,
    symbol: str,
    session_iso: str,
    near: float | None,
    mid: float | None,
    *,
    far: float | None = None,
    ref: float | None = None,
    imbalance: float | None = None,
    paired: float | None = None,
    adv20: float | None = None,
    vol20: float | None = None,
    imb_growth_53: float | None = None,
    imb_growth_51: float | None = None,
    msg_count: float | None = None,
    gate_q: float = META_GATE_Q,
) -> dict:
    """The M8 meta-gate verdict, degrading cleanly when the model or inputs are absent.

    Returns ``{available, p_win, go, missing, reason}``. Unavailable (available=False)
    when: the model file is absent; the market mid/near are invalid; or any registered
    feature cannot be built from the supplied optional inputs (``missing`` lists them).
    """
    if booster is None:
        return {
            "available": False, "p_win": None, "go": None, "missing": [],
            "reason": "model file absent -- classical-only",
        }
    if mid is None or not mid > 0.0 or near is None or not near > 0.0:
        return {
            "available": False, "p_win": None, "go": None, "missing": [],
            "reason": "P(win) unavailable (market mid/near invalid)",
        }
    missing = missing_meta_inputs(
        far=far, ref=ref, imbalance=imbalance, paired=paired, adv20=adv20,
        vol20=vol20, imb_growth_53=imb_growth_53, imb_growth_51=imb_growth_51,
        msg_count=msg_count,
    )
    if missing:
        return {
            "available": False, "p_win": None, "go": None, "missing": missing,
            "reason": "P(win) unavailable (missing: " + ", ".join(missing) + ")",
        }
    row = build_meta_row(
        symbol, session_iso, float(near), float(mid),
        far=float(far), ref=float(ref), imbalance=float(imbalance),  # type: ignore[arg-type]
        paired=float(paired), adv20=float(adv20), vol20=float(vol20),  # type: ignore[arg-type]
        imb_growth_53=float(imb_growth_53), imb_growth_51=float(imb_growth_51),  # type: ignore[arg-type]
        msg_count=float(msg_count),  # type: ignore[arg-type]
    )
    p = predict_pwin_row(booster, row)
    go = bool(moc_meta.gate(p, gate_q))
    return {
        "available": True, "p_win": p, "go": go, "missing": [],
        "reason": f"P(win)={p:.3f} {'>=' if go else '<'} {gate_q:g}",
    }


def top3_note(meta: dict) -> str:
    """The M15 top-3 note for a single-name ``decide`` view (selection is cross-sectional)."""
    if not meta["available"]:
        return f"M15 keeps top-{MAX_POSITIONS} firing names by P(win) -- P(win) unavailable here"
    if not meta["go"]:
        return f"not meta-eligible (P(win) below gate) -- not a top-{MAX_POSITIONS} candidate"
    return (
        f"meta-eligible at P(win)={meta['p_win']:.3f}; M15 keeps the top-{MAX_POSITIONS} "
        "firing names by P(win) -- rank against the other names' P(win) to confirm"
    )


def decide_one(
    symbol: str,
    near: float | None,
    bid: float | None,
    ask: float | None,
    *,
    session_iso: str,
    booster: lgb.Booster | None,
    far: float | None = None,
    ref: float | None = None,
    imbalance: float | None = None,
    paired: float | None = None,
    adv20: float | None = None,
    vol20: float | None = None,
    imb_growth_53: float | None = None,
    imb_growth_51: float | None = None,
    msg_count: float | None = None,
    capital_usd: float = DEFAULT_CAPITAL_USD,
    clip_cap_usd: float = DEFAULT_CLIP_CAP_USD,
    spread_abort_bps: float = DEFAULT_SPREAD_ABORT_BPS,
    gate_q: float = META_GATE_Q,
) -> dict:
    """The full cockpit decision for one symbol -- the single source of truth for render.

    Combines the classical verdict, the meta-gate verdict, the spread-abort check and
    whole-share sizing into one dict, and resolves whether an entry ticket may be
    printed (``ticket_ok``) or why not (``ticket_block``).

    The champion is classical AND meta: when the frozen M8 model is loaded and its
    P(win) is computable, ``meta["go"]`` is REQUIRED for a ticket (module contract +
    checklist: "if the model is loaded also require P(win) >= 0.55"). A meta NO-GO
    blocks the ORDER TICKET exactly like a spread abort. When the meta stream is
    unavailable (model file absent, or a registered feature cannot be built from the
    supplied inputs) the cockpit degrades to classical-only, unchanged -- an
    unavailable gate never blocks, only a computed NO-GO does (code review B2).
    """
    cb = classify_basis(near, bid, ask, threshold_bps=BASIS_THRESHOLD_BPS)
    meta = compute_meta(
        booster, symbol, session_iso, near, cb["mid"],
        far=far, ref=ref, imbalance=imbalance, paired=paired, adv20=adv20,
        vol20=vol20, imb_growth_53=imb_growth_53, imb_growth_51=imb_growth_51,
        msg_count=msg_count, gate_q=gate_q,
    )

    spr = cb["spread_bps"]
    abort = bool(spr is not None and spr > spread_abort_bps)

    size_price: float | None = None
    if cb["direction"] == 1:
        size_price = ask
    elif cb["direction"] == -1:
        size_price = bid
    shares = size_shares(capital_usd, clip_cap_usd, size_price)
    notional = shares * float(size_price) if (size_price and shares) else 0.0

    block: str | None = None
    if cb["errors"]:
        block = "input error"
    elif cb["direction"] == 0:
        block = "no tradable basis (near == mid)"
    elif not cb["classical_go"]:
        block = "classical NO-GO (|basis| below threshold)"
    elif abort:
        # SPREAD ABORT outranks META NO-GO (code review 2026-08-01 FIX 7): when a
        # snapshot fails both, the MECHANICAL block is the one the operator must be
        # told about — a book that wide is untradeable whatever the model thinks,
        # and naming the model first invites "the gate is too tight" rather than
        # "the market is not there". Order is display-only: ticket_ok is False for
        # either, and the full meta/spread state stays in the returned dict.
        block = f"SPREAD ABORT (spread {spr:.1f} > {spread_abort_bps:g} bps)"
    elif meta["available"] and not meta["go"]:
        block = (
            f"META NO-GO (P(win)={meta['p_win']:.3f} < {gate_q:g} gate) -- "
            "the champion requires classical AND meta"
        )
    elif shares < 1:
        clip = min(capital_usd, clip_cap_usd)
        block = f"capital insufficient (0 whole shares at ${size_price:.2f}, clip ${clip:.0f})"

    return {
        "symbol": symbol.upper(),
        "session_iso": session_iso,
        "near": near, "bid": bid, "ask": ask,
        "mid": cb["mid"], "spread_bps": spr,
        "basis_bps": cb["basis_bps"], "direction": cb["direction"], "side_word": cb["side_word"],
        "errors": cb["errors"],
        "classical_go": cb["classical_go"], "classical_reason": cb["classical_reason"],
        "spread_abort": abort, "spread_abort_bps": spread_abort_bps,
        "meta": meta, "top3_note": top3_note(meta),
        "size_price": size_price, "shares": shares, "notional": notional,
        "capital_usd": capital_usd, "clip_cap_usd": clip_cap_usd,
        "ticket_ok": block is None,
        "ticket_block": block,
    }


# ======================================================================= clock / model


def clock_status(now_et: datetime) -> tuple[bool, str]:
    """Whether ``now_et`` is inside the 15:54-15:59 ET decision window, and a message."""
    mod = now_et.hour * 60 + now_et.minute
    lo = CLOCK_LO_ET[0] * 60 + CLOCK_LO_ET[1]
    hi = CLOCK_HI_ET[0] * 60 + CLOCK_HI_ET[1]
    win = f"{CLOCK_LO_ET[0]}:{CLOCK_LO_ET[1]:02d}-{CLOCK_HI_ET[0]}:{CLOCK_HI_ET[1]:02d} ET"
    if lo <= mod <= hi:
        return True, f"[OK] inside decision window {win}"
    return False, f"[WARNING] {now_et:%H:%M} ET is OUTSIDE the {win} decision window"


def load_model(model_path: str | Path = MODEL_PATH) -> tuple[lgb.Booster | None, str]:
    """Load the frozen M8 model if present, else degrade to classical-only (no training).

    Same load mechanism as ``forward_paper.get_or_train_model``'s load branch, minus the
    train-on-absent (a research action the signal tool must not perform).
    """
    p = Path(model_path)
    if not p.exists():
        return None, f"model file ABSENT at {p} -- meta gate disabled (classical-only)"
    return lgb.Booster(model_file=str(p)), f"loaded frozen M8 model: {p}"


# =========================================================================== rehearse


def rehearse_events(
    settings: Settings,
    session_iso: str,
    *,
    seed: int = 7,
    noii_dir: str | Path | None = None,
    bbo_dir: str | Path | None = None,
) -> pl.DataFrame:
    """The frozen M6-FINAL event scan for a settled session, from the local lake only.

    Delegates to ``forward_paper.compute_session_events`` (which reuses
    ``run_basis_trial`` verbatim), so the basis/features/replay match the harness.
    Reads the owned lake; performs no network I/O and no download.
    """
    asof = date.fromisoformat(session_iso)
    return fp.compute_session_events(
        settings, asof, seed=seed, noii_dir=noii_dir, bbo_dir=bbo_dir
    )


def rehearse_scored(events: pl.DataFrame, booster: lgb.Booster | None) -> pl.DataFrame:
    """Attach p_win + taken flags + M15 positioning, exactly as ``forward_paper`` does.

    With a model, this is ``forward_paper.score_events`` (identical p_win/taken_meta);
    without one it degrades to the classical stream (p_win null). Then the frozen M15
    positioning columns are added. Numbers therefore match the harness by construction.
    """
    if events.height == 0:
        return events
    if booster is not None:
        scored = fp.score_events(events, booster)
    else:
        scored = events.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("p_win"),
            (pl.col("basis_bps").abs() >= BASIS_THRESHOLD_BPS).alias("taken_classical"),
            pl.lit(None, dtype=pl.Boolean).alias("taken_meta"),
        )
    return positioning.apply_positioning(scored)


def _rehearse_row_view(row: dict, *, capital_usd: float, clip_cap_usd: float) -> dict:
    """One symbol's cockpit view over a scored+realized rehearse row (pure)."""
    direction = int(row["side"])
    side_word = {1: "BUY", -1: "SELL SHORT", 0: "--"}[direction]
    # The taker price you would have paid: ask to buy, bid to sell (fallback mid).
    size_price = row.get("entry_ask") if direction == 1 else row.get("entry_bid")
    if size_price is None or not size_price > 0:
        size_price = row.get("entry_mid")
    shares = size_shares(capital_usd, clip_cap_usd, size_price)
    notional = shares * float(size_price) if (size_price and shares) else 0.0
    net_bps = row.get("net_bps")
    hypo_usd = (float(net_bps) / 1e4 * notional) if (net_bps is not None and notional) else 0.0
    p_win = row.get("p_win")
    return {
        "symbol": row["symbol"],
        "side_word": side_word,
        "basis_bps": row.get("basis_bps"),
        "p_win": p_win,
        "classical_go": bool(row.get("taken_classical")),
        "meta_available": p_win is not None,
        "meta_go": bool(row.get("taken_meta")) if p_win is not None else None,
        "selected": bool(row.get("selected")) if row.get("selected") is not None else False,
        "sel_rank": row.get("sel_rank"),
        "shares": shares,
        "notional": notional,
        "cross_px": row.get("cross_px"),
        "net_bps": net_bps,
        "hypo_usd": hypo_usd,
    }


# ============================================================================ renders


def _banner(title: str) -> list[str]:
    bar = "=" * 80
    return [bar, f" {title}", bar]


def _exit_leg_lines(direction: int, shares: int, symbol: str, near: float, exit_mode: str) -> list[str]:
    """The exit-leg decision tree (honest about the UNRESOLVED cross reachability)."""
    exit_side = "SELL" if direction == 1 else "BUY TO COVER"
    late = [
        "   IF broker passes late LOC (exchange window 15:55-15:58 ET, PRICE-RESTRICTED):",
        f"      -> {exit_side} {shares} {symbol}  LOC  limit ~{near:.2f}",
        "         (reference-consistent: the NOII near/indicative clearing price; the",
        "          limit must sit inside the exchange late-LOC price band)",
    ]
    mkt = [
        "   ELSE (broker cannot pass late LOC) marketable exit at 15:59:30 +/- :",
        f"      -> {exit_side} {shares} {symbol}  MARKET",
        "         economics DEGRADE by the last-15m E/Q (UNKNOWN; stress 0.9-1.5+;",
        "          project shortfall 1.46 bps at 15:55:10) -- see M16 Phase 0 / DR-X3",
    ]
    if exit_mode == "late-loc":
        return ["   EXIT  [mode=late-loc]", *late, "   LOG which exit path actually executed."]
    if exit_mode == "marketable":
        return ["   EXIT  [mode=marketable]", *mkt, "   LOG which exit path actually executed."]
    return [
        "   EXIT  [mode=auto-note: BOTH paths shown -- choose per broker capability, LOG it]",
        *late,
        *mkt,
    ]


def render_decide(d: dict, *, exit_mode: str, model_note: str, now_utc: datetime | None = None) -> str:
    """Big, unambiguous ASCII decision + manual ticket for one symbol."""
    now_utc = now_utc or datetime.now(UTC)
    now_et = now_utc.astimezone(ET)
    _, clock_msg = clock_status(now_et)

    def _f(x: float | None, nd: int = 4) -> str:
        return f"{x:.{nd}f}" if x is not None else "n/a"

    L: list[str] = []
    L += _banner(f"LIVE COCKPIT :: DECIDE      {d['symbol']:<6}      session {d['session_iso']}")
    L.append(f" CLOCK  UTC {now_utc:%Y-%m-%d %H:%M:%S}Z   ET {now_et:%H:%M:%S}   {clock_msg}")
    L.append(f" MODEL  {model_note}")
    L.append("")
    L.append(
        f" INPUTS near={_f(d['near'])}  bid={_f(d['bid'])}  ask={_f(d['ask'])}  "
        f"mid={_f(d['mid'])}  spread={_f(d['spread_bps'], 1)} bps"
    )
    if d["errors"]:
        L.append(f" !! INPUT ERRORS: {'; '.join(d['errors'])}")
    if d["basis_bps"] is not None:
        arrow = {1: "near > mid -> BUY", -1: "near < mid -> SELL SHORT", 0: "near == mid"}[d["direction"]]
        L.append(f" BASIS  basis_bps = 1e4*(near/mid - 1) = {d['basis_bps']:+.1f} bps   -> {arrow}")
    L.append("")
    L.append(" " + "-" * 78)
    L.append(" STREAM VERDICTS")
    cg = ">>> GO <<<" if d["classical_go"] else "NO-GO"
    L.append(f"   CLASSICAL (|basis|>=10):    {cg:<12} ({d['classical_reason']})")
    meta = d["meta"]
    if not meta["available"]:
        mg = "UNAVAILABLE"
    else:
        mg = ">>> GO <<<" if meta["go"] else "NO-GO"
    L.append(f"   META-GATED (P(win)>=0.55):  {mg:<12} ({meta['reason']})")
    L.append(f"   TOP-{MAX_POSITIONS} (M15):               {d['top3_note']}")
    if d["spread_abort"]:
        L.append(f"   SPREAD ABORT:               spread {d['spread_bps']:.1f} > {d['spread_abort_bps']:g} bps -> SKIP")
    L.append(" " + "-" * 78)

    if d["ticket_ok"]:
        L.append(" >>> ORDER TICKET (key by hand in a broker UI) <<<")
        clip = min(d["capital_usd"], d["clip_cap_usd"])
        L.append(
            f"   ENTRY  {d['side_word']}  {d['shares']} shares  {d['symbol']}  @ MARKET"
        )
        L.append(
            f"          size = floor(min(capital ${d['capital_usd']:.0f}, clip ${d['clip_cap_usd']:.0f})"
            f" / ${d['size_price']:.2f}) = {d['shares']} sh (~${d['notional']:.0f} of ${clip:.0f})"
        )
        L.append(
            "          order type MARKET -- wholesalers fill market better than "
            "marketable-limit (DR-X3 C8 CONFIRMED / Phase-0)"
        )
        L += _exit_leg_lines(d["direction"], d["shares"], d["symbol"], float(d["near"]), exit_mode)
        L.append(
            f"   ABORT  skip if spread > {d['spread_abort_bps']:g} bps (now {_f(d['spread_bps'], 1)});"
            " never ADD to a position;"
        )
        L.append("          skip on crossed/stale quotes; be FLAT at 16:00:00 exactly.")
        L.append(
            "   LOG    record this clip in the Phase-0 blotter "
            "(python -m enginev51.apps.phase0_blotter log ...)"
        )
    else:
        L.append(f" >>> NO TICKET <<<   reason: {d['ticket_block']}")
        if str(d["ticket_block"]).startswith("capital insufficient"):
            L.append("   (classical signal fired, but the clip rounds to 0 whole shares)")
    L.append("=" * 80)
    return "\n".join(L)


def render_rehearse(
    scored: pl.DataFrame,
    *,
    session_iso: str,
    capital_usd: float,
    clip_cap_usd: float,
    exit_mode: str,
    model_note: str,
) -> str:
    """Training/verification view: what the cockpit WOULD have shown, vs the realized cross."""
    L: list[str] = []
    L += _banner(f"LIVE COCKPIT :: REHEARSE (training/verification)   session {session_iso}")
    L.append(f" MODEL  {model_note}")
    L.append(
        f" capital ${capital_usd:.0f}   per-clip cap ${clip_cap_usd:.0f}   "
        f"meta gate P(win)>={META_GATE_Q:g}   basis>=|{BASIS_THRESHOLD_BPS:g}|"
    )
    L.append(" numbers reuse forward_paper.compute_session_events + score_events (harness-consistent)")
    L.append("")
    if scored.height == 0:
        L.append(" no events for this session in the owned lake (no valid basis + cross).")
        L.append("=" * 80)
        return "\n".join(L)

    by_sym = {r["symbol"]: r for r in scored.iter_rows(named=True)}
    header = (
        f" {'SYM':<6} {'SIDE':<11} {'BASIS':>8} {'P(win)':>7} {'CLASS':>6} "
        f"{'META':>6} {'TICKET':>13} {'CROSS':>9} {'NET_bps':>8} {'HYPO_$':>8}"
    )
    L.append(header)
    L.append(" " + "-" * (len(header) - 1))

    n_class = n_meta = n_tradable = 0
    net_vals: list[float] = []
    for sym in UNIVERSE:
        row = by_sym.get(sym)
        if row is None:
            L.append(f" {sym:<6} {'(no event -- absent basis/cross in lake)':<63}")
            continue
        v = _rehearse_row_view(row, capital_usd=capital_usd, clip_cap_usd=clip_cap_usd)
        n_class += int(v["classical_go"])
        n_meta += int(bool(v["meta_go"]))
        if v["net_bps"] is not None:
            net_vals.append(float(v["net_bps"]))
        pw = f"{v['p_win']:.3f}" if v["p_win"] is not None else "n/a"
        cls = "GO" if v["classical_go"] else "no"
        if not v["meta_available"]:
            mta = "n/a"
        else:
            mta = "GO" if v["meta_go"] else "no"
        if v["classical_go"] and v["shares"] >= 1:
            n_tradable += 1
            tk = f"{v['side_word'].split()[0]} {v['shares']} MKT"
        elif v["classical_go"]:
            tk = "0sh(insuf)"
        else:
            tk = "--"
        L.append(
            f" {sym:<6} {v['side_word']:<11} {v['basis_bps']:>8.1f} {pw:>7} {cls:>6} "
            f"{mta:>6} {tk:>13} {v['cross_px']:>9.2f} {v['net_bps']:>+8.2f} {v['hypo_usd']:>+8.2f}"
        )

    L.append(" " + "-" * (len(header) - 1))
    mean_net = (sum(net_vals) / len(net_vals)) if net_vals else float("nan")
    L.append(
        f" SUMMARY  classical GO={n_class}   meta GO={n_meta}   cockpit-tradable(>=1sh)="
        f"{n_tradable}   mean net_bps(all events)={mean_net:+.2f}"
    )
    L.append(
        f" EXIT     entry MARKET; exit per the {exit_mode} decision tree "
        "(late-LOC 15:55-15:58 price-restricted ELSE 15:59:30 marketable) -- see `checklist`"
    )
    L.append(" NOTE     hypo_$ = realized net_bps applied to the cockpit clip notional at this capital")
    L.append("=" * 80)
    return "\n".join(L)


def render_checklist(
    *,
    capital_usd: float,
    clip_cap_usd: float,
    spread_abort_bps: float,
    exit_mode: str,
) -> str:
    """The pre-close runbook (static, parameterized by the deploy knobs)."""
    clip = min(capital_usd, clip_cap_usd)
    L: list[str] = []
    L += _banner("LIVE COCKPIT :: CHECKLIST -- champion MOC-basis pre-close runbook")
    L.append(" SIGNAL-ONLY: you key every order by hand. Universe: " + ", ".join(UNIVERSE))
    L.append("")
    L.append(" T-MINUS TIMELINE (ET)")
    L.append("   15:50  data screen up: NOII near/far/ref + NBBO bid/ask for all 5 names.")
    L.append(f"          capital check: account >= intended clips; per-clip cap ${clip_cap_usd:.0f}.")
    L.append("          clock sync: trust an NTP clock, NOT the broker UI; the signal is a")
    L.append("          10-second instant -- a skewed clock reads the wrong bar.")
    L.append("   15:54  final quotes stable; pull up the cockpit `decide` for each name.")
    L.append("   15:55:10  DECISION INSTANT: run decide per name; basis_bps = 1e4*(near/mid-1).")
    L.append(f"          TRADE iff |basis| >= {BASIS_THRESHOLD_BPS:g}; direction WITH the basis;")
    L.append(f"          if the model is loaded also require P(win) >= {META_GATE_Q:g}; M15 keeps top-{MAX_POSITIONS}.")
    L.append(f"          size = floor(min(capital ${capital_usd:.0f}, clip ${clip_cap_usd:.0f}) / price) = whole shares (~${clip:.0f}).")
    L.append("   15:55-15:58  ENTER as MARKET orders (DR-X3 C8: market fills better than")
    L.append("          marketable-limit); then place the exit leg.")
    L.append("   16:00:00  be FLAT (exit fills at the closing cross).")
    L.append("")
    L.append(f" EXIT LEG (UNRESOLVED at retail -- state BOTH; mode={exit_mode})")
    L.append("   A) exchange late LOC, 15:55-15:58 ET, PRICE-RESTRICTED (limit must sit in the")
    L.append("      LOC price band): LOC opposite the entry, limit ~ NOII near price.")
    L.append("      (Alpaca rejects on-close after 15:50; broker LOC support varies.)")
    L.append("   B) if a broker CANNOT pass late LOC: 15:59:30 marketable (MARKET) exit --")
    L.append("      economics degrade by the last-15m E/Q (UNKNOWN; stress 0.9-1.5+; project")
    L.append("      shortfall 1.46 bps at 15:55:10). See M16 Phase 0.")
    L.append("   Whichever path a broker supports, LOG which one actually executed.")
    L.append("")
    L.append(" STANDING ABORT RULES")
    L.append(f"   - SKIP the name if quoted spread > {spread_abort_bps:g} bps (no registered MOC threshold;")
    L.append("     parameterized default 25 bps).")
    L.append("   - SKIP on crossed/locked or stale quotes, or if near price has not populated (>0).")
    L.append("   - NEVER add to a position; one clip per name; no averaging.")
    L.append("   - Be FLAT at 16:00:00 exactly (MOC exit is flat-by-close by construction).")
    L.append("   - LOG every clip in the Phase-0 blotter (python -m enginev51.apps.phase0_blotter log ...).")
    L.append("=" * 80)
    return "\n".join(L)


# ================================================================================ cli


@click.group()
def main() -> None:
    """Champion decision cockpit -- SIGNAL-ONLY (computes + shows a manual ticket)."""
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows console safety


@main.command("decide")
@click.option("--symbol", required=True, type=click.Choice(list(UNIVERSE), case_sensitive=False))
@click.option("--near", required=True, type=float, help="NOII near (indicative clearing) price.")
@click.option("--bid", required=True, type=float, help="Prevailing NBBO bid.")
@click.option("--ask", required=True, type=float, help="Prevailing NBBO ask.")
@click.option("--far", type=float, default=None, help="NOII far price (-> near_far_bps).")
@click.option("--ref", type=float, default=None, help="NOII reference price (-> near_ref_bps).")
@click.option("--imbalance", type=float, default=None,
              help="SIGNED imbalance shares: buy-side +, sell-side - (-> norm_imb, paired_ratio).")
@click.option("--paired", type=float, default=None, help="Paired shares (-> paired_ratio).")
@click.option("--adv20", type=float, default=None, help="ADV20 dollars (-> log_adv20, norm_imb).")
@click.option("--vol20", type=float, default=None, help="Trailing 20d realized vol (-> vol20).")
@click.option("--imb-growth-53", type=float, default=None, help="norm_imb(15:55) - norm_imb(15:53).")
@click.option("--imb-growth-51", type=float, default=None, help="norm_imb(15:55) - norm_imb(15:51).")
@click.option("--msg-count", type=float, default=None, help="NOII messages seen by 15:55:10.")
@click.option("--capital", type=float, default=DEFAULT_CAPITAL_USD, show_default=True)
@click.option("--clip-cap", type=float, default=DEFAULT_CLIP_CAP_USD, show_default=True)
@click.option("--spread-abort-bps", type=float, default=DEFAULT_SPREAD_ABORT_BPS, show_default=True)
@click.option("--exit-mode", type=click.Choice(EXIT_MODES), default="auto-note", show_default=True)
@click.option("--session", default=None, help="Session ISO date (default: today ET).")
@click.option("--model", "model_path", default=str(MODEL_PATH), show_default=True)
def decide_cmd(
    symbol: str, near: float, bid: float, ask: float,
    far: float | None, ref: float | None, imbalance: float | None, paired: float | None,
    adv20: float | None, vol20: float | None, imb_growth_53: float | None,
    imb_growth_51: float | None, msg_count: float | None,
    capital: float, clip_cap: float, spread_abort_bps: float, exit_mode: str,
    session: str | None, model_path: str,
) -> None:
    """Live path: type the screen values, get a decision + exact manual ticket."""
    session_iso = session or datetime.now(ET).date().isoformat()
    booster, model_note = load_model(model_path)
    d = decide_one(
        symbol, near, bid, ask, session_iso=session_iso, booster=booster,
        far=far, ref=ref, imbalance=imbalance, paired=paired, adv20=adv20, vol20=vol20,
        imb_growth_53=imb_growth_53, imb_growth_51=imb_growth_51, msg_count=msg_count,
        capital_usd=capital, clip_cap_usd=clip_cap, spread_abort_bps=spread_abort_bps,
    )
    click.echo(render_decide(d, exit_mode=exit_mode, model_note=model_note))


@main.command("rehearse")
@click.option("--session", required=True, help="Settled session ISO date to replay from the lake.")
@click.option("--capital", type=float, default=DEFAULT_CAPITAL_USD, show_default=True)
@click.option("--clip-cap", type=float, default=DEFAULT_CLIP_CAP_USD, show_default=True)
@click.option("--exit-mode", type=click.Choice(EXIT_MODES), default="auto-note", show_default=True)
@click.option("--seed", type=int, default=7, show_default=True, help="Frozen latency-draw seed.")
@click.option("--noii-dir", default=None, help="NOII lake root (default: data/raw/noii).")
@click.option("--bbo-dir", default=None, help="BBO-1s lake root (default: data/raw/bbo1s).")
@click.option("--model", "model_path", default=str(MODEL_PATH), show_default=True)
def rehearse_cmd(
    session: str, capital: float, clip_cap: float, exit_mode: str, seed: int,
    noii_dir: str | None, bbo_dir: str | None, model_path: str,
) -> None:
    """Training/verification: replay a settled session; show cockpit view vs realized cross."""
    settings = get_settings()
    booster, model_note = load_model(model_path)
    events = rehearse_events(settings, session, seed=seed, noii_dir=noii_dir, bbo_dir=bbo_dir)
    scored = rehearse_scored(events, booster)
    click.echo(
        render_rehearse(
            scored, session_iso=session, capital_usd=capital, clip_cap_usd=clip_cap,
            exit_mode=exit_mode, model_note=model_note,
        )
    )


@main.command("checklist")
@click.option("--capital", type=float, default=DEFAULT_CAPITAL_USD, show_default=True)
@click.option("--clip-cap", type=float, default=DEFAULT_CLIP_CAP_USD, show_default=True)
@click.option("--spread-abort-bps", type=float, default=DEFAULT_SPREAD_ABORT_BPS, show_default=True)
@click.option("--exit-mode", type=click.Choice(EXIT_MODES), default="auto-note", show_default=True)
def checklist_cmd(capital: float, clip_cap: float, spread_abort_bps: float, exit_mode: str) -> None:
    """Print the pre-close runbook (T-minus timeline, exit legs, abort rules)."""
    click.echo(
        render_checklist(
            capital_usd=capital, clip_cap_usd=clip_cap,
            spread_abort_bps=spread_abort_bps, exit_mode=exit_mode,
        )
    )


if __name__ == "__main__":
    main()
