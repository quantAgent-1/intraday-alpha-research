"""phase0_blotter -- M16 Phase-0 manual execution-quality blotter (LOGGING ONLY).

Serves the FROZEN registered protocol `research/experiments/M16-phase0/PROTOCOL.md`
(E/Q audit: >=250 round-trip clips, two time buckets, market vs marketable-limit
coin-flip arm A) plus the wave-4 amendment in `PROTOCOL-DRAFT.md` ("Wave-4
amendment" section: arm B, touch-resting limits, cancel-after-60s, fill-rate +
1-5s post-fill mid markout).

NON-NEGOTIABLE: this module NEVER routes, places, or suggests routing an order.
Execution is 100% MANUAL -- the human reads their broker screen, keys every order
by hand, and reports back what happened. Every command here is decision support
(``plan``) or record-keeping (``log``, ``status``, ``reconcile``) only. No code
path constructs a broker order request; the only network access anywhere in this
module is READ-ONLY historical market data in ``reconcile`` (SIP quotes for
ground-truthing already-completed fills), via the existing
``enginev51.data.alpaca_hist.AlpacaHist`` client -- no new HTTP client is written.

Windows console note: every table this module prints is plain ASCII (no
box-drawing / unicode glyphs), so no special console codepage is required. If
output still looks garbled in your terminal, set PYTHONIOENCODING=utf-8 first
(PowerShell: ``$env:PYTHONIOENCODING = "utf-8"``).

Subcommands (daily workflow):

    uv run python -m enginev51.apps.phase0_blotter plan
    uv run python -m enginev51.apps.phase0_blotter log --clip-id 1 --symbol NVDA \\
        --side buy --arm A --otype market --bid 118.20 --ask 118.22 \\
        --send-time 13:05:11 --fill-price 118.22 --fill-time 13:05:12 --size 4
    uv run python -m enginev51.apps.phase0_blotter status
    uv run python -m enginev51.apps.phase0_blotter reconcile --date 2026-07-21

``plan`` reads the blotter and prints ONE recommended next clip spec: which
bucket is most under-sampled, which arm, (for arm A) the pre-committed coin-flip
order type, the side, and the frozen risk limits -- or, if a clip is still open
(entered but not yet flattened), a reminder to flatten it now.

``log`` appends exactly one LEG (either the entry or the flatten of a clip) to
`research/experiments/M16-phase0/blotter.csv`, deriving mid/Q_bps/half-spread/
E_bps/E-Q/bucket/champion-window from the decision-time NBBO the user read off
their screen. Nothing is ever rejected outright -- a bad-looking datum (crossed
NBBO, off-band notional, non-positive size, a send-time outside both buckets) is
still logged, flagged with a `warn`/`warn_reasons` column, and printed back to
the user. CSV is the source of truth: `log` only ever APPENDS.

``status`` reports progress against every pre-registered target and threshold:
clip counts per bucket x arm x otype, E/Q medians/p75 (entry-only and pooled),
arm-B fill rate with a Wilson 95% CI against the frozen reopen/close thresholds,
markout mean (once `reconcile` has populated it), sessions covered, a max
concurrent exposure sanity check, and a days-remaining estimate.

``reconcile`` ground-truths already-logged legs against OWNED Alpaca historical
SIP quotes (nearest quote <= send-time), flags screen-vs-SIP mid disagreement
>1 tick or crossed SIP data, computes the pre-registered 1-5s post-fill mid
markout for arm-B fills, writes `research/experiments/M16-phase0/reconcile-
<date>.md`, and updates the blotter's `reconciled`/`markout_bps` columns IN
PLACE (row order and every other column are never touched). If Alpaca creds are
absent it prints one line and exits -- it never raises a raw traceback.
"""

from __future__ import annotations

import csv
import json
import math
import random
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import click
import numpy as np
import structlog

from enginev51.config import PROJECT_ROOT, get_settings
from enginev51.data.alpaca_hist import AlpacaHist

log = structlog.get_logger(__name__)

# --------------------------------------------------------------------------- paths

M16_DIR = PROJECT_ROOT / "research" / "experiments" / "M16-phase0"
BLOTTER_PATH = M16_DIR / "blotter.csv"

# --------------------------------------------------------------------------- frozen protocol constants

ET_ZONE = ZoneInfo("America/New_York")

# Time buckets (PROTOCOL.md "Design (frozen)"), half-open [start, end).
MID_START, MID_END = time(13, 0, 0), time(14, 30, 0)
LAST15_START, LAST15_END = time(15, 45, 0), time(16, 0, 0)
# Champion-window sub-tag (PROTOCOL.md "record the 15:55:10-15:58 sub-window tag").
CHAMPION_START, CHAMPION_END = time(15, 55, 10), time(15, 58, 0)

# Sample-size targets (PROTOCOL.md "Clips" + "Order-type rule").
TARGET_TOTAL_CLIPS = 250
TARGET_PER_BUCKET = 100
MIN_N_PER_OTYPE = 50

# Clip sizing / exposure / abort limits (PROTOCOL.md "Exposure bound").
CLIP_NOTIONAL_LO = 400.0
CLIP_NOTIONAL_HI = 800.0
MAX_EXPOSURE_USD = 800.0
MAX_FLATTEN_MINUTES = 5
ABORT_LOSS_USD = 5.0

# Arm-B frozen thresholds (ledger note M16-phase0-armB-amendment, 2026-07-20).
ARMB_FILL_REOPEN_THRESHOLD = 0.80
ARMB_FILL_CLOSE_THRESHOLD = 0.65
ARMB_MARKOUT_REOPEN_BPS = -0.2
ARMB_MARKOUT_CLOSE_BPS = -0.5

# Coin-flip: deterministic per clip ordinal (== clip_id), pre-committed seed 16
# (PROTOCOL.md "Order-type contrast ... Randomize by coin flip per clip; log
# which."). ``random.Random`` only accepts int/float/str/bytes/None seeds (3.11+),
# so the ordinal is folded into a single int seed rather than hashing a tuple.
COIN_FLIP_SEED = 16
_COIN_FLIP_MULT = 1_000_003

CHAMPION_NAMES: tuple[str, ...] = ("NVDA", "TSLA", "AMD", "MU", "GOOGL")

# Reg-NMS sub-penny tick for the champion names (all trade >$1); used only by
# `reconcile`'s screen-vs-SIP tick-diff flag.
TICK_USD = 0.01

ENTRY_SIDES: frozenset[str] = frozenset({"buy", "short"})
EXIT_SIDES: frozenset[str] = frozenset({"sell", "cover"})
SIDE_SIGN: dict[str, float] = {"buy": 1.0, "short": -1.0}

# --------------------------------------------------------------------------- csv schema

COLUMNS: tuple[str, ...] = (
    "leg_id", "clip_id", "session_date", "symbol", "side", "arm", "otype",
    "bid", "ask", "mid", "q_bps", "half_spread_bps",
    "send_time", "bucket", "champion_window",
    "fill_price", "fill_time", "e_bps", "eq_ratio",
    "size", "notional", "unfilled",
    "venue", "note",
    "warn", "warn_reasons",
    "reconciled", "markout_bps",
)

_PRICE_COLS = frozenset({"bid", "ask", "mid", "fill_price", "notional"})
_BOOL_COLS = ("champion_window", "unfilled", "warn")
_FLOAT_COLS = (
    "bid", "ask", "mid", "q_bps", "half_spread_bps", "fill_price",
    "e_bps", "eq_ratio", "notional", "markout_bps",
)
_INT_COLS = ("leg_id", "clip_id", "size")

_STORE_FMT = "%Y-%m-%dT%H:%M:%S"


def fmt_dt(dt: datetime) -> str:
    return dt.strftime(_STORE_FMT)


def parse_stored_dt(s: str) -> datetime:
    return datetime.strptime(s, _STORE_FMT).replace(tzinfo=ET_ZONE)


def _to_float_or_none(s: str) -> float | None:
    return float(s) if s not in (None, "") else None


def serialize_row(row: dict) -> dict[str, str]:
    """Typed leg dict -> CSV string dict (blank string for ``None``)."""
    out: dict[str, str] = {}
    for c in COLUMNS:
        v = row.get(c)
        if v is None:
            out[c] = ""
        elif isinstance(v, bool):
            out[c] = "True" if v else "False"
        elif isinstance(v, float):
            nd = 4 if c in _PRICE_COLS else 6
            out[c] = f"{v:.{nd}f}"
        elif isinstance(v, datetime):
            out[c] = fmt_dt(v)
        else:
            out[c] = str(v)
    return out


def parse_row(raw: dict[str, str]) -> dict:
    """CSV string dict (as read by ``csv.DictReader``) -> typed leg dict."""
    row: dict = dict(raw)
    for c in _INT_COLS:
        row[c] = int(raw[c])
    for c in _FLOAT_COLS:
        row[c] = _to_float_or_none(raw.get(c, ""))
    for c in _BOOL_COLS:
        row[c] = raw.get(c, "False") == "True"
    row["send_time"] = parse_stored_dt(raw["send_time"])
    row["fill_time"] = parse_stored_dt(raw["fill_time"]) if raw.get("fill_time") else None
    return row


# --------------------------------------------------------------------------- csv io


def load_rows(path: str | Path = BLOTTER_PATH) -> list[dict]:
    """Every logged leg, typed, in file order. Empty list if the blotter doesn't
    exist yet (first-ever run)."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return [parse_row(r) for r in csv.DictReader(f)]


def append_leg_row(path: str | Path, leg: dict) -> dict:
    """Append ONE leg to the blotter CSV, writing the header first if the file is
    missing. Pure append -- existing rows are never read back or rewritten."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(serialize_row(leg))
    return leg


def _write_all(path: Path, rows: list[dict]) -> None:
    """Full rewrite, preserving row order exactly. ONLY `reconcile` calls this
    (to update `reconciled`/`markout_bps` in place); `log` always appends."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow(serialize_row(r))


def next_leg_id(rows: list[dict]) -> int:
    return max((r["leg_id"] for r in rows), default=0) + 1


def next_clip_id(rows: list[dict]) -> int:
    return max((r["clip_id"] for r in rows), default=0) + 1


# --------------------------------------------------------------------------- time helpers


def parse_et_dt(raw: str, session_date: date) -> datetime:
    """Parse a send-time/fill-time as an ET instant.

    Accepts a full ISO datetime (naive is treated as ET; offset-aware is
    converted to ET) or a bare 'HH:MM:SS' ('HH:MM' also works) time-of-day,
    attached to ``session_date`` and treated as ET -- the spec's "accept naive
    HH:MM:SS as ET" rule.
    """
    raw = raw.strip()
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        t = time.fromisoformat(raw)
        return datetime.combine(session_date, t, tzinfo=ET_ZONE)
    return dt.replace(tzinfo=ET_ZONE) if dt.tzinfo is None else dt.astimezone(ET_ZONE)


def bucket_of(t: time) -> str:
    """MID (13:00-14:30 ET) / LAST15 (15:45-16:00 ET) / OTHER, half-open ranges."""
    if MID_START <= t < MID_END:
        return "MID"
    if LAST15_START <= t < LAST15_END:
        return "LAST15"
    return "OTHER"


def is_champion_window(t: time) -> bool:
    return CHAMPION_START <= t < CHAMPION_END


def coin_flip_order_type(clip_id: int) -> str:
    """Deterministic 50/50 market-vs-marketable-limit pick for arm-A clip
    ``clip_id`` (the "clip ordinal"). Seeded on (COIN_FLIP_SEED, clip_id) folded
    into one int, so the same clip_id always yields the same order type
    regardless of call order -- the split is reproducible and pre-committed.
    """
    seed = COIN_FLIP_SEED * _COIN_FLIP_MULT + int(clip_id)
    return "market" if random.Random(seed).random() < 0.5 else "mlim"


# --------------------------------------------------------------------------- spread / E-Q math


def compute_spread_fields(bid: float, ask: float, fill_price: float | None) -> dict:
    """mid, Q_bps, half-spread_bps, E_bps, E/Q -- PROTOCOL.md "Metrics".

    ``E_bps = 2*|fill-mid|/mid*1e4`` and ``Q_bps = (ask-bid)/mid*1e4`` are both
    UNSIGNED magnitudes (no side term). Guarded against non-positive mid / zero
    spread so a bad quote can never raise (a leg with garbage bid/ask is still
    logged, just with these fields left null -- `validate_leg` flags it).
    """
    mid = (bid + ask) / 2.0
    if mid <= 0:
        return {"mid": None, "q_bps": None, "half_spread_bps": None, "e_bps": None, "eq_ratio": None}
    q_bps = (ask - bid) / mid * 1e4
    half_spread_bps = q_bps / 2.0
    e_bps = None
    eq_ratio = None
    if fill_price is not None:
        e_bps = 2.0 * abs(fill_price - mid) / mid * 1e4
        if q_bps:
            eq_ratio = e_bps / q_bps
    return {"mid": mid, "q_bps": q_bps, "half_spread_bps": half_spread_bps, "e_bps": e_bps, "eq_ratio": eq_ratio}


# --------------------------------------------------------------------------- validation (warn-only)


def validate_leg(
    *, bid: float, ask: float, size: int, unfilled: bool, arm: str, otype: str,
    bucket: str, notional: float | None,
) -> list[str]:
    """Sanity checks -- ALL warn-only. A bad-looking datum is still logged; this
    just returns the reasons it looked bad, for the `warn`/`warn_reasons` columns.
    """
    reasons: list[str] = []
    if not (bid > 0 and ask > 0):
        reasons.append("non_positive_quote")
    elif bid >= ask:
        reasons.append("crossed_or_locked_nbbo")
    if size <= 0:
        reasons.append("non_positive_size")
    if notional is not None and not (CLIP_NOTIONAL_LO <= notional <= CLIP_NOTIONAL_HI):
        reasons.append("notional_out_of_400_800_band")
    if bucket == "OTHER":
        reasons.append("bucket_other")
    if unfilled and not (arm == "B" and otype == "rest"):
        reasons.append("unfilled_not_armB_rest")
    return reasons


def check_fill_args(fill_price: float | None, fill_time_raw: str | None, unfilled: bool) -> str | None:
    """Cross-field CLI validation for --fill-price/--fill-time/--unfilled.

    Returns an error message (for the caller to raise as a clean
    ``click.UsageError``) or ``None`` if the combination is valid. Pure, so the
    rule is testable without invoking the CLI.
    """
    has_fill = fill_price is not None or bool(fill_time_raw)
    if unfilled and has_fill:
        return "--unfilled cannot be combined with --fill-price/--fill-time"
    if not unfilled and (fill_price is None or not fill_time_raw):
        return "--fill-price and --fill-time are required unless --unfilled is set"
    return None


def build_leg_row(
    rows_existing: list[dict],
    *,
    clip_id: int,
    symbol: str,
    side: str,
    arm: str,
    otype: str,
    bid: float,
    ask: float,
    send_time: datetime,
    fill_price: float | None,
    fill_time: datetime | None,
    size: int,
    unfilled: bool,
    session_date: date,
    venue: str = "",
    note: str = "",
) -> dict:
    """Construct one fully-derived leg row (pure -- no I/O). ``rows_existing`` is
    only consulted for the next `leg_id`."""
    leg_id = next_leg_id(rows_existing)
    bucket = bucket_of(send_time.time())
    champion = is_champion_window(send_time.time())
    spread = compute_spread_fields(bid, ask, fill_price)
    if fill_price is not None:
        notional = fill_price * size
    elif spread["mid"] is not None:
        notional = spread["mid"] * size
    else:
        notional = None
    reasons = validate_leg(
        bid=bid, ask=ask, size=size, unfilled=unfilled, arm=arm, otype=otype,
        bucket=bucket, notional=notional,
    )
    return {
        "leg_id": leg_id, "clip_id": clip_id, "session_date": session_date.isoformat(),
        "symbol": symbol.upper(), "side": side, "arm": arm, "otype": otype,
        "bid": bid, "ask": ask, **spread,
        "send_time": send_time, "bucket": bucket, "champion_window": champion,
        "fill_price": fill_price, "fill_time": fill_time,
        "size": size, "notional": notional, "unfilled": unfilled,
        "venue": venue, "note": note,
        "warn": bool(reasons), "warn_reasons": ";".join(reasons),
        "reconciled": "", "markout_bps": None,
    }


# --------------------------------------------------------------------------- clip grouping


def _group_by_clip(rows: list[dict]) -> dict[int, dict]:
    by_clip: dict[int, dict] = {}
    for r in rows:
        c = by_clip.setdefault(r["clip_id"], {"entry": None, "exit": None})
        if r["side"] in ENTRY_SIDES:
            c["entry"] = r
        elif r["side"] in EXIT_SIDES:
            c["exit"] = r
    return by_clip


def open_clips(rows: list[dict]) -> list[dict]:
    """Entry legs with no flatten leg logged yet (excludes arm-B posts that were
    never filled -- those never became a round trip)."""
    return [
        c["entry"] for c in _group_by_clip(rows).values()
        if c["entry"] is not None and c["exit"] is None and not c["entry"]["unfilled"]
    ]


def closed_clip_pairs(rows: list[dict]) -> list[dict]:
    """{"entry": .., "exit": ..} for every fully paired round trip -- "a clip =
    paired entry+flatten legs by clip-id"."""
    return [c for c in _group_by_clip(rows).values() if c["entry"] and c["exit"]]


def armB_posts(rows: list[dict]) -> list[dict]:
    """Arm-B resting-limit entry legs (filled or not) -- "post-events", counted
    separately from clips."""
    return [r for r in rows if r["arm"] == "B" and r["side"] in ENTRY_SIDES and r["otype"] == "rest"]


def sessions_covered(rows: list[dict]) -> list[str]:
    return sorted({r["session_date"] for r in rows})


# --------------------------------------------------------------------------- plan


def recommend_bucket(closed: list[dict]) -> str:
    """Most under-sampled bucket; ties -> MID (listed first, PROTOCOL.md)."""
    counts = {"MID": 0, "LAST15": 0}
    for c in closed:
        b = c["entry"]["bucket"]
        if b in counts:
            counts[b] += 1
    return "MID" if counts["MID"] <= counts["LAST15"] else "LAST15"


def recommend_arm(closed: list[dict]) -> str:
    """Most under-sampled arm (equal counts target); ties -> A."""
    counts = {"A": 0, "B": 0}
    for c in closed:
        a = c["entry"]["arm"]
        if a in counts:
            counts[a] += 1
    return "A" if counts["A"] <= counts["B"] else "B"


def recommend_symbol(closed: list[dict]) -> str:
    """Least-logged champion name; ties -> the PROTOCOL.md listed order."""
    counts = dict.fromkeys(CHAMPION_NAMES, 0)
    for c in closed:
        sym = c["entry"]["symbol"]
        if sym in counts:
            counts[sym] += 1
    return min(CHAMPION_NAMES, key=lambda s: (counts[s], CHAMPION_NAMES.index(s)))


LIMITS_REMINDER = (
    "LIMITS (frozen): clip $400-800 notional, whole shares | exposure <=$800 at any "
    "instant | flatten <=5 min | abort-and-record any round-trip loss >$5"
)


def build_plan(rows: list[dict]) -> dict:
    """The next recommended action (pure). If any clip is open, recommend
    flattening the OLDEST one first; else recommend a new entry in the most
    under-sampled (bucket, arm), long-side by default (PROTOCOL.md "long-side
    pairs only" default), with the pre-committed coin-flip otype for arm A.
    """
    open_c = open_clips(rows)
    if open_c:
        entry = min(open_c, key=lambda r: r["send_time"])
        flatten_side = "sell" if entry["side"] == "buy" else "cover"
        return {
            "action": "flatten",
            "clip_id": entry["clip_id"],
            "symbol": entry["symbol"],
            "side": flatten_side,
            "arm": entry["arm"],
            "otype": "market",
            "opened_at": entry["send_time"],
            "size": entry["size"],
            "n_open": len(open_c),
        }
    closed = closed_clip_pairs(rows)
    bucket = recommend_bucket(closed)
    arm = recommend_arm(closed)
    symbol = recommend_symbol(closed)
    new_clip_id = next_clip_id(rows)
    otype = coin_flip_order_type(new_clip_id) if arm == "A" else "rest"
    bucket_n = {
        "MID": sum(1 for c in closed if c["entry"]["bucket"] == "MID"),
        "LAST15": sum(1 for c in closed if c["entry"]["bucket"] == "LAST15"),
    }
    arm_n = {
        "A": sum(1 for c in closed if c["entry"]["arm"] == "A"),
        "B": sum(1 for c in closed if c["entry"]["arm"] == "B"),
    }
    return {
        "action": "enter",
        "clip_id": new_clip_id,
        "symbol": symbol,
        "side": "buy",
        "arm": arm,
        "otype": otype,
        "bucket": bucket,
        "bucket_counts": bucket_n,
        "arm_counts": arm_n,
        "total_clips": len(closed),
    }


def format_plan(plan: dict) -> str:
    lines = ["M16 Phase-0 blotter -- next clip"]
    if plan["action"] == "flatten":
        lines.append(
            f"NEXT LEG: FLATTEN clip #{plan['clip_id']}  symbol={plan['symbol']}  "
            f"side={plan['side']}  arm={plan['arm']}  suggested_otype={plan['otype']}"
        )
        lines.append(
            f"  opened {fmt_dt(plan['opened_at'])} ET, size={plan['size']} sh -- flatten now "
            f"(target <= {MAX_FLATTEN_MINUTES} min from entry)"
        )
        if plan["n_open"] > 1:
            lines.append(f"  WARNING: {plan['n_open']} clips are currently open -- flattening the oldest first")
    else:
        lines.append(
            f"NEXT CLIP: #{plan['clip_id']}  symbol={plan['symbol']}  arm={plan['arm']}  "
            f"otype={plan['otype']}  side={plan['side']}  bucket={plan['bucket']}"
        )
        bn, an = plan["bucket_counts"], plan["arm_counts"]
        lines.append(
            f"  reason: bucket MID={bn['MID']} LAST15={bn['LAST15']} (target >={TARGET_PER_BUCKET} each) | "
            f"arm A={an['A']} B={an['B']} (target equal) | total={plan['total_clips']} "
            f"(target >={TARGET_TOTAL_CLIPS})"
        )
        if plan["arm"] == "A":
            lines.append(f"  coin-flip: clip #{plan['clip_id']} -> {plan['otype']} (seed={COIN_FLIP_SEED})")
    lines.append(LIMITS_REMINDER)
    return "\n".join(lines)


# --------------------------------------------------------------------------- status


def wilson_ci(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """95%-default Wilson score interval for a binomial proportion. (nan, nan) if
    n == 0."""
    if n == 0:
        return (float("nan"), float("nan"))
    phat = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = phat + z2 / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z2 / (4 * n)) / n)
    lo = (center - margin) / denom
    hi = (center + margin) / denom
    return (max(0.0, lo), min(1.0, hi))


def _median_p75(values: list[float]) -> tuple[float | None, float | None, int]:
    if not values:
        return None, None, 0
    arr = np.asarray(values, dtype=float)
    return float(np.median(arr)), float(np.percentile(arr, 75)), len(arr)


def eq_table(
    rows: list[dict], *, entry_only: bool, group_keys: tuple[str, ...] = ("bucket", "otype")
) -> list[dict]:
    """Median/p75 E/Q grouped by ``group_keys`` (default bucket x otype), over
    legs with a computed eq_ratio. ``entry_only=True`` restricts to entry legs
    (buy/short); ``False`` pools entry + exit legs."""
    groups: dict[tuple, list[float]] = {}
    for r in rows:
        if r["eq_ratio"] is None:
            continue
        if entry_only and r["side"] not in ENTRY_SIDES:
            continue
        key = tuple(r[k] for k in group_keys)
        groups.setdefault(key, []).append(r["eq_ratio"])
    out = []
    for key, vals in sorted(groups.items()):
        med, p75, n = _median_p75(vals)
        row = dict(zip(group_keys, key, strict=True))
        row.update({"n": n, "median_eq": med, "p75_eq": p75})
        out.append(row)
    return out


def clip_counts(closed: list[dict]) -> list[dict]:
    """Clip counts grouped by (bucket, arm, otype) of the entry leg."""
    groups: dict[tuple[str, str, str], int] = {}
    for c in closed:
        e = c["entry"]
        key = (e["bucket"], e["arm"], e["otype"])
        groups[key] = groups.get(key, 0) + 1
    return [{"bucket": b, "arm": a, "otype": o, "n": n} for (b, a, o), n in sorted(groups.items())]


def max_concurrent_exposure(rows: list[dict]) -> tuple[float, bool]:
    """Sweep-line peak notional exposure across all (possibly overlapping)
    clips. A still-open clip is conservatively treated as exposed through the
    latest timestamp seen anywhere in the log (we have no evidence it closed
    earlier). Returns (peak_usd, exceeded_800)."""
    by_clip = _group_by_clip(rows)
    all_ts = [r["fill_time"] or r["send_time"] for r in rows]
    if not all_ts:
        return 0.0, False
    global_end = max(all_ts)
    events: list[tuple[datetime, float]] = []
    for c in by_clip.values():
        entry = c["entry"]
        if not entry or entry["unfilled"] or entry["fill_price"] is None:
            continue
        start = entry["fill_time"] or entry["send_time"]
        exit_row = c["exit"]
        end = (exit_row["fill_time"] or exit_row["send_time"]) if exit_row else global_end
        notional = entry["fill_price"] * entry["size"]
        events.append((start, notional))
        events.append((end, -notional))
    events.sort(key=lambda e: e[0])
    running = 0.0
    peak = 0.0
    for _, delta in events:
        running += delta
        peak = max(peak, running)
    return peak, peak > MAX_EXPOSURE_USD


def compute_status(rows: list[dict]) -> dict:
    closed = closed_clip_pairs(rows)
    total_clips = len(closed)
    posts = armB_posts(rows)
    filled_posts = [p for p in posts if not p["unfilled"]]
    fill_rate = (len(filled_posts) / len(posts)) if posts else None
    ci_lo, ci_hi = wilson_ci(len(filled_posts), len(posts)) if posts else (float("nan"), float("nan"))

    bucket_counts = {"MID": 0, "LAST15": 0}
    arm_counts = {"A": 0, "B": 0}
    for c in closed:
        b, a = c["entry"]["bucket"], c["entry"]["arm"]
        if b in bucket_counts:
            bucket_counts[b] += 1
        if a in arm_counts:
            arm_counts[a] += 1

    otype_leg_counts: dict[str, int] = {}
    for r in rows:
        if r["eq_ratio"] is not None:
            otype_leg_counts[r["otype"]] = otype_leg_counts.get(r["otype"], 0) + 1

    sessions = sessions_covered(rows)
    n_sessions = len(sessions)
    clips_per_day = (total_clips / n_sessions) if n_sessions else 0.0
    remaining = max(0, TARGET_TOTAL_CLIPS - total_clips)
    days_remaining = (remaining / clips_per_day) if clips_per_day > 0 else None

    markouts = [r["markout_bps"] for r in rows if r["markout_bps"] is not None]
    peak_exposure, exceeded = max_concurrent_exposure(rows)

    return {
        "total_clips": total_clips,
        "target_total": TARGET_TOTAL_CLIPS,
        "total_ok": total_clips >= TARGET_TOTAL_CLIPS,
        "bucket_counts": bucket_counts,
        "bucket_target": TARGET_PER_BUCKET,
        "bucket_ok": {k: v >= TARGET_PER_BUCKET for k, v in bucket_counts.items()},
        "arm_counts": arm_counts,
        "otype_leg_counts": otype_leg_counts,
        "otype_min_n": MIN_N_PER_OTYPE,
        "otype_ok": {k: v >= MIN_N_PER_OTYPE for k, v in otype_leg_counts.items()},
        "clip_counts_detail": clip_counts(closed),
        "eq_entry_only": eq_table(rows, entry_only=True),
        "eq_pooled": eq_table(rows, entry_only=False),
        "eq_by_otype_pooled": eq_table(rows, entry_only=False, group_keys=("otype",)),
        "armB_n_posts": len(posts),
        "armB_n_filled": len(filled_posts),
        "armB_fill_rate": fill_rate,
        "armB_fill_ci_lo": ci_lo,
        "armB_fill_ci_hi": ci_hi,
        "armB_reopen_candidate": fill_rate is not None and fill_rate >= ARMB_FILL_REOPEN_THRESHOLD,
        "armB_close_candidate": fill_rate is not None and fill_rate <= ARMB_FILL_CLOSE_THRESHOLD,
        "markout_mean_bps": (sum(markouts) / len(markouts)) if markouts else None,
        "markout_n": len(markouts),
        "n_sessions": n_sessions,
        "sessions_span": [sessions[0], sessions[-1]] if sessions else [],
        "clips_per_day": clips_per_day,
        "days_remaining": days_remaining,
        "open_clips": len(open_clips(rows)),
        "max_concurrent_exposure_usd": peak_exposure,
        "exposure_exceeded_800": exceeded,
    }


def _fmt(x: object, nd: int = 3) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, float) and math.isnan(x):
        return "n/a"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def _ascii_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def _line(cells: list[str]) -> str:
        return "  ".join(c.ljust(w) for c, w in zip(cells, widths, strict=True))

    out = [_line(headers), _line(["-" * w for w in widths])]
    out.extend(_line(r) for r in rows)
    return "\n".join(out)


def format_status_text(stats: dict) -> str:
    lines = [
        "M16 Phase-0 execution-quality blotter -- status",
        "",
        f"total clips: {stats['total_clips']} / {stats['target_total']}  ok={stats['total_ok']}"
        + (f"   sessions {stats['sessions_span'][0]}..{stats['sessions_span'][1]}" if stats["sessions_span"] else ""),
        f"bucket MID:    {stats['bucket_counts']['MID']:4d} / {stats['bucket_target']}  ok={stats['bucket_ok']['MID']}",
        f"bucket LAST15: {stats['bucket_counts']['LAST15']:4d} / {stats['bucket_target']}  ok={stats['bucket_ok']['LAST15']}",
        f"arm A={stats['arm_counts']['A']}  arm B={stats['arm_counts']['B']}  open_clips={stats['open_clips']}",
        "",
    ]
    if stats["clip_counts_detail"]:
        lines.append("clip counts (bucket x arm x otype):")
        lines.append(_ascii_table(
            ["bucket", "arm", "otype", "n"],
            [[r["bucket"], r["arm"], r["otype"], str(r["n"])] for r in stats["clip_counts_detail"]],
        ))
        lines.append("")

    lines.append(f"order-type rule (n>={stats['otype_min_n']}/type to qualify):")
    if stats["eq_by_otype_pooled"]:
        lines.append(_ascii_table(
            ["otype", "n", "ok", "median_eq", "p75_eq"],
            [[r["otype"], str(r["n"]), str(stats["otype_ok"].get(r["otype"], False)),
              _fmt(r["median_eq"]), _fmt(r["p75_eq"])] for r in stats["eq_by_otype_pooled"]],
        ))
    else:
        lines.append("  n=0 (no filled legs yet)")
    lines.append("")

    for label, key in (("E/Q -- entry legs only", "eq_entry_only"), ("E/Q -- pooled (entry+exit)", "eq_pooled")):
        lines.append(f"{label}:")
        if stats[key]:
            lines.append(_ascii_table(
                ["bucket", "otype", "n", "median_eq", "p75_eq"],
                [[r["bucket"], r["otype"], str(r["n"]), _fmt(r["median_eq"]), _fmt(r["p75_eq"])]
                 for r in stats[key]],
            ))
        else:
            lines.append("  n=0")
        lines.append("")

    lines.append(
        f"arm-B fill rate: {_fmt(stats['armB_fill_rate'], 3)}  "
        f"95%CI=[{_fmt(stats['armB_fill_ci_lo'], 3)}, {_fmt(stats['armB_fill_ci_hi'], 3)}]  "
        f"n_posts={stats['armB_n_posts']}  n_filled={stats['armB_n_filled']}"
    )
    lines.append(
        f"  vs frozen thresholds: reopen>=~{ARMB_FILL_REOPEN_THRESHOLD:.0%} -> "
        f"{stats['armB_reopen_candidate']}  |  close<=~{ARMB_FILL_CLOSE_THRESHOLD:.0%} -> "
        f"{stats['armB_close_candidate']}  (informational only -- registration lives in M3_REGISTRATION.md)"
    )
    lines.append(
        f"markout mean: {_fmt(stats['markout_mean_bps'], 3)} bps  (n={stats['markout_n']}; "
        f"populated by `reconcile`)"
    )
    lines.append("")
    lines.append(
        f"sessions covered: {stats['n_sessions']}  clips/day: {_fmt(stats['clips_per_day'], 2)}  "
        f"days remaining @ observed rate: {_fmt(stats['days_remaining'], 1)}"
    )
    lines.append(
        f"max concurrent exposure (sanity check): ${stats['max_concurrent_exposure_usd']:.2f}"
        f"  exceeded_$800={stats['exposure_exceeded_800']}"
        + ("  *** WARNING: exceeds the frozen $800 exposure bound ***" if stats["exposure_exceeded_800"] else "")
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------- reconcile


def nearest_quote_at_or_before(quotes: list[dict], target: datetime) -> dict | None:
    """The freshest quote with ts <= target, or None if every quote is after it
    (or ``quotes`` is empty). ``quotes``: list of {"ts": datetime, "bid", "ask"}.
    """
    candidates = [q for q in quotes if q["ts"] <= target]
    if not candidates:
        return None
    return max(candidates, key=lambda q: q["ts"])


def sip_ground_truth(quotes: list[dict], send_time: datetime) -> dict | None:
    """SIP bid/ask/mid nearest-at-or-before ``send_time``, plus a crossed flag."""
    q = nearest_quote_at_or_before(quotes, send_time)
    if q is None:
        return None
    sip_bid, sip_ask = float(q["bid"]), float(q["ask"])
    return {
        "sip_bid": sip_bid, "sip_ask": sip_ask, "sip_mid": (sip_bid + sip_ask) / 2.0,
        "sip_ts": q["ts"], "crossed": sip_bid >= sip_ask,
    }


def markout_bps(side: str, fill_price: float, mid_post: float) -> float:
    """Signed post-fill markout for a maker fill: positive = price moved in the
    maker's favor after the fill, negative = adverse selection cost (the wave-4
    priors: -0.5..-1 bp). ``side`` is the ENTRY side (buy -> +1, short -> -1)."""
    sign = SIDE_SIGN.get(side, 1.0)
    return sign * (mid_post - fill_price) / fill_price * 1e4


def compute_markout_for_fill(
    quotes: list[dict], side: str, fill_price: float, fill_time: datetime,
    *, window_lo_s: float = 1.0, window_hi_s: float = 5.0,
) -> float | None:
    """The pre-registered 1-5s post-fill mid markout (wave-4 amendment). Uses the
    freshest quote at-or-before fill_time+window_hi_s; if that quote actually
    predates fill_time+window_lo_s (no quote update happened anywhere inside the
    window), returns None rather than silently using a stale pre-window price.
    """
    target = fill_time + timedelta(seconds=window_hi_s)
    q = nearest_quote_at_or_before(quotes, target)
    if q is None:
        return None
    if q["ts"] < fill_time + timedelta(seconds=window_lo_s):
        return None
    mid_post = (q["bid"] + q["ask"]) / 2.0
    return markout_bps(side, fill_price, mid_post)


def build_reconcile_rows(rows_for_symbol: list[dict], quotes: list[dict]) -> list[dict]:
    """Pure: per-leg SIP ground-truth comparison + arm-B markout, given one
    symbol's already-loaded blotter rows and its already-fetched ET-tagged SIP
    quotes. No I/O -- this is the function the tests exercise directly."""
    out = []
    for r in rows_for_symbol:
        gt = sip_ground_truth(quotes, r["send_time"])
        entry: dict = {
            "leg_id": r["leg_id"], "clip_id": r["clip_id"], "symbol": r["symbol"],
            "side": r["side"], "send_time": r["send_time"],
            "screen_bid": r["bid"], "screen_ask": r["ask"], "screen_mid": r["mid"],
        }
        if gt is None:
            entry.update({"sip_mid": None, "diff_ticks": None, "flag": "no_sip_quote"})
        else:
            screen_mid = r["mid"] if r["mid"] is not None else 0.0
            diff_ticks = abs(screen_mid - gt["sip_mid"]) / TICK_USD
            flags = []
            if diff_ticks > 1.0:
                flags.append("mid_diff>1tick")
            if gt["crossed"]:
                flags.append("sip_crossed")
            entry.update({
                "sip_bid": gt["sip_bid"], "sip_ask": gt["sip_ask"], "sip_mid": gt["sip_mid"],
                "diff_ticks": round(diff_ticks, 2), "flag": ";".join(flags) if flags else "ok",
            })
        markout = None
        if (
            r["arm"] == "B" and r["side"] in ENTRY_SIDES and not r["unfilled"]
            and r["fill_price"] is not None and r["fill_time"] is not None
        ):
            markout = compute_markout_for_fill(quotes, r["side"], r["fill_price"], r["fill_time"])
        entry["markout_bps"] = markout
        out.append(entry)
    return out


def _fmt_opt(x: float | None, nd: int = 4) -> str:
    return "n/a" if x is None else f"{x:.{nd}f}"


def render_reconcile_report(label: str, results: list[dict], *, session_dates: list[str] | None = None) -> str:
    lines = [f"# M16 Phase-0 reconciliation -- {label}", ""]
    lines.append(
        "SIP ground-truthing per PROTOCOL v6.1 case-level fill discipline: owned Alpaca "
        "HISTORICAL SIP quotes vs the screen-logged NBBO at send-time (nearest quote <= "
        "send-time); arm-B fills also get the pre-registered 1-5s post-fill mid markout."
    )
    if session_dates:
        lines.append(f"\nsession dates covered: {', '.join(session_dates)}")
    lines.append(f"\nlegs reconciled: {len(results)}\n")
    n_flagged = sum(1 for r in results if r.get("flag") not in (None, "ok"))
    markout_vals = [r["markout_bps"] for r in results if r.get("markout_bps") is not None]
    mean_markout = (sum(markout_vals) / len(markout_vals)) if markout_vals else None
    lines.append(f"flagged (>1 tick mid diff or crossed SIP): {n_flagged}")
    lines.append(
        f"arm-B markouts computed: {len(markout_vals)}"
        + (f"  mean={mean_markout:+.3f} bps" if mean_markout is not None else "")
    )
    lines.append("")
    lines.append("| leg_id | clip_id | symbol | side | send_time (ET) | screen_mid | sip_mid | diff_ticks | flag | markout_bps |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        lines.append(
            f"| {r['leg_id']} | {r['clip_id']} | {r['symbol']} | {r['side']} | "
            f"{r['send_time'].strftime('%Y-%m-%d %H:%M:%S')} | "
            f"{_fmt_opt(r.get('screen_mid'))} | {_fmt_opt(r.get('sip_mid'))} | "
            f"{_fmt_opt(r.get('diff_ticks'), 2)} | {r.get('flag', 'no_sip_quote')} | "
            f"{_fmt_opt(r.get('markout_bps'))} |"
        )
    return "\n".join(lines) + "\n"


def fetch_symbol_quotes(api: AlpacaHist, symbol: str, start: datetime, end: datetime) -> list[dict]:
    """All SIP quote pages for ``symbol`` in [start, end), flattened + ET-tagged.
    Thin wrapper around the EXISTING ``AlpacaHist.fetch_quotes`` -- no new HTTP
    client. Network I/O; not exercised by tests (see module docstring)."""
    out: list[dict] = []
    for page in api.fetch_quotes(symbol, start, end, feed="sip"):
        for q in page:
            ts = datetime.fromtimestamp(q["ts"] / 1e9, tz=UTC).astimezone(ET_ZONE)
            out.append({"ts": ts, "bid": float(q["bid"]), "ask": float(q["ask"])})
    out.sort(key=lambda r: r["ts"])
    return out


# --------------------------------------------------------------------------- cli


@click.group()
def main() -> None:
    """M16 Phase-0 execution-quality blotter -- LOGGING/ANALYTICS ONLY.

    No command here ever places, routes, or suggests routing an order. The human
    keys every order by hand; this tool tells them what to key next (`plan`),
    records what happened (`log`), reports progress (`status`), and
    ground-truths the log against owned SIP data (`reconcile`).
    """


@main.command("plan")
@click.option("--blotter", "blotter_path", default=str(BLOTTER_PATH), show_default=True, help="Blotter CSV path.")
def plan_cmd(blotter_path: str) -> None:
    rows = load_rows(blotter_path)
    click.echo(format_plan(build_plan(rows)))


@main.command("log")
@click.option("--clip-id", type=int, required=True, help="Round-trip id (same for entry + flatten legs).")
@click.option("--symbol", required=True, help="Ticker (e.g. NVDA).")
@click.option("--side", type=click.Choice(["buy", "sell", "short", "cover"]), required=True)
@click.option("--arm", type=click.Choice(["A", "B"]), required=True)
@click.option("--otype", type=click.Choice(["market", "mlim", "rest"]), required=True)
@click.option("--bid", type=float, required=True, help="Decision-time NBBO bid read from the screen at send.")
@click.option("--ask", type=float, required=True, help="Decision-time NBBO ask read from the screen at send.")
@click.option("--send-time", "send_time_raw", required=True, help="ET, 'HH:MM:SS' or full ISO.")
@click.option("--fill-price", type=float, default=None, help="Required unless --unfilled.")
@click.option("--fill-time", "fill_time_raw", default=None, help="ET, 'HH:MM:SS' or full ISO. Required unless --unfilled.")
@click.option("--size", type=int, required=True, help="Shares.")
@click.option("--unfilled", is_flag=True, default=False, help="Arm-B post cancelled unfilled after 60s.")
@click.option("--date", "date_raw", default=None, help="Session date YYYY-MM-DD (default: today ET).")
@click.option("--venue", default="", help="Fill venue, if the broker shows one.")
@click.option("--note", default="")
@click.option("--blotter", "blotter_path", default=str(BLOTTER_PATH), show_default=True, help="Blotter CSV path.")
def log_cmd(
    clip_id: int, symbol: str, side: str, arm: str, otype: str, bid: float, ask: float,
    send_time_raw: str, fill_price: float | None, fill_time_raw: str | None, size: int,
    unfilled: bool, date_raw: str | None, venue: str, note: str, blotter_path: str,
) -> None:
    err = check_fill_args(fill_price, fill_time_raw, unfilled)
    if err:
        raise click.UsageError(err)
    try:
        session_date = date.fromisoformat(date_raw) if date_raw else datetime.now(ET_ZONE).date()
    except ValueError as exc:
        raise click.UsageError(f"--date must be YYYY-MM-DD: {exc}") from exc
    send_time = parse_et_dt(send_time_raw, session_date)
    fill_time = parse_et_dt(fill_time_raw, session_date) if fill_time_raw else None

    rows = load_rows(blotter_path)
    leg = build_leg_row(
        rows, clip_id=clip_id, symbol=symbol, side=side, arm=arm, otype=otype, bid=bid, ask=ask,
        send_time=send_time, fill_price=fill_price, fill_time=fill_time, size=size,
        unfilled=unfilled, session_date=session_date, venue=venue, note=note,
    )
    append_leg_row(blotter_path, leg)
    log.info(
        "leg_logged", leg_id=leg["leg_id"], clip_id=clip_id, symbol=leg["symbol"], side=side,
        arm=arm, otype=otype, bucket=leg["bucket"], warn=leg["warn"],
    )
    click.echo(
        f"logged leg #{leg['leg_id']} (clip {clip_id} {leg['symbol']} {side} {arm}/{otype})  "
        f"bucket={leg['bucket']} champion_window={leg['champion_window']} "
        f"E/Q={_fmt(leg['eq_ratio'])}"
    )
    if leg["warn"]:
        click.echo(f"WARN: {leg['warn_reasons']}")


@main.command("status")
@click.option("--blotter", "blotter_path", default=str(BLOTTER_PATH), show_default=True, help="Blotter CSV path.")
@click.option("--json", "as_json", is_flag=True, help="Emit the stats dict as JSON.")
def status_cmd(blotter_path: str, as_json: bool) -> None:
    stats = compute_status(load_rows(blotter_path))
    if as_json:
        click.echo(json.dumps(stats, indent=2, default=str))
    else:
        click.echo(format_status_text(stats))


@main.command("reconcile")
@click.option("--date", "date_str", default=None, help="Session date YYYY-MM-DD to reconcile.")
@click.option("--all-unreconciled", is_flag=True, default=False, help="Reconcile every not-yet-reconciled row.")
@click.option("--blotter", "blotter_path", default=str(BLOTTER_PATH), show_default=True, help="Blotter CSV path.")
@click.option("--out-dir", default=str(M16_DIR), show_default=True, help="Where reconcile-<date>.md is written.")
def reconcile_cmd(date_str: str | None, all_unreconciled: bool, blotter_path: str, out_dir: str) -> None:
    if not date_str and not all_unreconciled:
        raise click.UsageError("pass --date YYYY-MM-DD or --all-unreconciled")
    if date_str:
        try:
            date.fromisoformat(date_str)
        except ValueError as exc:
            raise click.UsageError(f"--date must be YYYY-MM-DD: {exc}") from exc

    rows = load_rows(blotter_path)
    if date_str:
        targets = [r for r in rows if r["session_date"] == date_str]
        label = date_str
    else:
        targets = [r for r in rows if not r["reconciled"]]
        label = datetime.now(ET_ZONE).date().isoformat()
    if not targets:
        click.echo(f"reconcile: nothing to do ({'date ' + date_str if date_str else 'no unreconciled rows'})")
        return

    settings = get_settings()
    if not settings.alpaca_api_key or not settings.alpaca_api_secret:
        click.echo("reconcile needs ALPACA_API_KEY / ALPACA_API_SECRET set (.env) -- add them and retry.")
        raise SystemExit(1)
    try:
        api = AlpacaHist(settings)
    except RuntimeError as exc:
        click.echo(f"reconcile: cannot start the SIP client ({exc}) -- add ALPACA_API_KEY/ALPACA_API_SECRET and retry.")
        raise SystemExit(1) from exc

    try:
        by_symbol: dict[str, list[dict]] = {}
        for r in targets:
            by_symbol.setdefault(r["symbol"], []).append(r)
        all_results: list[dict] = []
        for symbol, sym_rows in by_symbol.items():
            stamps = [r["send_time"] for r in sym_rows] + [r["fill_time"] for r in sym_rows if r["fill_time"]]
            start = min(stamps) - timedelta(minutes=2)
            end = max(stamps) + timedelta(seconds=10)
            quotes = fetch_symbol_quotes(api, symbol, start, end)
            all_results.extend(build_reconcile_rows(sym_rows, quotes))
    except RuntimeError as exc:
        click.echo(f"reconcile: SIP fetch failed ({exc}) -- retry later.")
        raise SystemExit(1) from exc
    finally:
        api.close()

    by_leg = {res["leg_id"]: res for res in all_results}
    today_iso = datetime.now(ET_ZONE).date().isoformat()
    for r in rows:
        res = by_leg.get(r["leg_id"])
        if res is None:
            continue
        r["reconciled"] = today_iso
        if res["markout_bps"] is not None:
            r["markout_bps"] = res["markout_bps"]
    _write_all(Path(blotter_path), rows)

    out_path = Path(out_dir) / f"reconcile-{label}.md"
    report = render_reconcile_report(label, all_results, session_dates=sorted({r["session_date"] for r in targets}))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    n_flagged = sum(1 for res in all_results if res.get("flag") not in (None, "ok"))
    log.info("reconcile_done", label=label, n_legs=len(all_results), n_flagged=n_flagged, out=str(out_path))
    click.echo(f"reconcile: {len(all_results)} legs, {n_flagged} flagged -- report -> {out_path}")


if __name__ == "__main__":
    main()
