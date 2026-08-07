"""Live signal engine core (L0/L1) for the champion MOC-basis family.

Implements ``research/LIVE_SIGNAL_ENGINE_L0L1_DESIGN.md`` (orchestrator, frozen 2026-07-23),
phases L0 (ReplayAdapter + signals journal + session clock) and L1 (ManualAdapter +
the ADIA monitor panel). Context: ``research/LIVE_SIGNAL_ENGINE_PROPOSAL.md``.

ENGINEERING, NOT RESEARCH. Every signal kernel is IMPORTED from a registered /
production module and referenced BY IDENTITY -- there is no local reimplementation of
a basis, a score, a tier, a vol-norm, or any ADIA statistic (design section 0; test
6 asserts the identities). The replay path calls the forward clock's OWN functions
(``forward_paper.compute_session_events`` / ``score_events``), so its rows agree with
the forward ledger by construction. The manual path calls ``live_cockpit.decide_one``
verbatim.

SIGNAL-ONLY, BY CONSTRUCTION. No module in ``enginev51.live`` imports a broker or
network client, and no code path can place an order (design section R5 / tests 8,
11). The ONLY write target is ``JOURNAL_PATH`` (+ its ``.tmp`` sibling). Booster load
failure degrades to classical-only, never trains (R2). ``source="feed"`` is refused
until an L2 design exists (R6); half-day close-window emissions are refused with
reason ``early_close`` (R3), rather than silently skipped upstream.
"""

from __future__ import annotations

import subprocess
import time
from datetime import date
from pathlib import Path

import polars as pl

from enginev51.apps import forward_paper as fp
from enginev51.apps import live_cockpit as lc
from enginev51.config import PROJECT_ROOT, Settings
from enginev51.data.noii import et_ns
from enginev51.models import moc_meta
from enginev51.research_screens import sched_window as sw
from enginev51.research_screens import sizing_shadow as ss

# --------------------------------------------------------------------------- kernels
# Registered kernels bound by IDENTITY (design section 0; test 6). These module-level
# names ARE the imported objects -- the engine reuses them and never reimplements the
# arithmetic. The replay/manual entry points invoke ``fp.``/``lc.`` through the module
# so the forward-clock functions remain monkeypatch-swappable in hermetic tests while
# still being the exact same objects the forward ledger was built from.
compute_session_events = fp.compute_session_events
score_events = fp.score_events
decide_one = lc.decide_one
predict_pwin = moc_meta.predict_pwin
tier = ss.tier
vol_norm = ss.vol_norm
trailing_raw_vol = ss.trailing_raw_vol
champion_sigma_med5 = ss.champion_sigma_med5
is_vol_history_skip = ss.is_vol_history_skip
load_raw_closes = ss.load_raw_closes
psr = ss.psr
min_trl = ss.min_trl
sr_native = ss.sr_native
sample_moments = ss.sample_moments

# --------------------------------------------------------------------------- constants
JOURNAL_PATH = PROJECT_ROOT / "research" / "live" / "signals_journal.parquet"  # gitignored
JOURNAL_KEYS = ("session", "symbol", "source", "window")
OPEN_WINDOW_ET = ((9, 25, 0), (9, 30, 0))   # dormant elsewhere -- scope fence (M24 slot)
CLOSE_WINDOW_ET = ((15, 50, 0), (16, 0, 0))
SOURCES = ("replay", "manual")               # "feed" reserved for L2, refused for now

# Champion universe / threshold, sourced from the registered module (never redefined).
UNIVERSE: tuple[str, ...] = moc_meta.UNIVERSE
CANDIDATE_BASIS_BPS: float = moc_meta.CANDIDATE_BASIS_BPS  # 10.0

# Display-lens constants (M23; report-only). BOOK is the $10k research-gate currency,
# DEPLOY is the $1k account lens -- reused, never a comparison statistic.
BOOK_NOTIONAL: float = ss.BOOK_NOTIONAL
DEPLOY_CAPITAL_USD: float = ss.DEPLOY_CAPITAL_USD
ALPHA: float = ss.ALPHA

# Emitted-plan descriptors (PLAYBOOK: entry MARKET, exit late-LOC 15:55-15:58 ELSE
# 15:59 marketable; be flat by 16:00). The journal records the exit mechanism + the
# late-LOC deadline; these are display strings, not a routing instruction.
ORDER_TYPE_CLOSE = "LOC_late_or_MKT1559"
DEADLINE_CLOSE_ET = "15:58:00"

# Half-day calendar -- the ICE/NYSE-verified frozenset from the M20 screen (read-only).
EARLY_CLOSE_DATES: frozenset[str] = sw.EARLY_CLOSE_DATES

# Journal schema -- column ORDER is pinned (test 2). Nullable columns carry M8/M23
# degrade values (p_win/tier/vol_norm null under classical-only or a vol-history skip).
JOURNAL_SCHEMA: dict[str, pl.DataType] = {
    "ts_emit": pl.Int64,                    # emission instant, UTC epoch ns
    "session": pl.Utf8,
    "symbol": pl.Utf8,
    "window": pl.Utf8,                      # "close" | "open"
    "source": pl.Utf8,                      # "replay" | "manual"
    "basis_bps": pl.Float64,
    "p_win": pl.Float64,                    # null under classical-only (no model)
    "side": pl.Int64,
    "taken_classical": pl.Boolean,
    "taken_meta": pl.Boolean,               # null under classical-only
    "tier": pl.Float64,                     # null when p_win null
    "vol_norm": pl.Float64,                 # null on vol-history skip (R4)
    "size_notional_research": pl.Float64,   # $10k book * tier * vol_norm (report-only)
    "size_shares_deploy": pl.Int64,         # clip-capped whole-share deploy lens (both sources)
    "expected_net_bps": pl.Float64,         # replay: REPLAYED REALIZED net; manual: null
    "order_type": pl.Utf8,
    "limit_px": pl.Float64,                 # late-LOC reference limit (~ NOII near)
    "deadline_et": pl.Utf8,
    "spread_abort": pl.Boolean,
    "engine_git_sha": pl.Utf8,
    "note": pl.Utf8,
}


# ---------------------------------------------------------------- journal I/O (copied)
# Atomic tmp+os.replace and append-dedup-by-keys, COPIED (~20 lines) from the private
# ``research_screens.sched_window_forward._write_atomic`` / ``_append_dedup`` pattern
# (design section 0: those are private, so the pattern is reimplemented locally, not
# imported). Idempotent: existing rows are never rewritten; only new key-tuples append.


def _write_atomic(df: pl.DataFrame, path: str | Path) -> None:
    """Write ``df`` to ``path`` atomically via a ``.tmp`` sibling + os.replace."""
    import os

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.write_parquet(tmp)
    os.replace(tmp, path)


def _load_parquet(path: str | Path, schema: dict) -> pl.DataFrame:
    path = Path(path)
    if not path.exists():
        return pl.DataFrame(schema=schema)
    return pl.read_parquet(path)


def _append_dedup(
    new: pl.DataFrame, path: str | Path, schema: dict, keys: list[str]
) -> dict:
    """Append-only, deduped by ``keys``; idempotent (existing rows never rewritten)."""
    existing = _load_parquet(path, schema)
    if new.height == 0:
        return {"appended": 0, "skipped": 0, "total": existing.height}
    if existing.height:
        seen = set(zip(*[existing[k].to_list() for k in keys], strict=True))
        tuples = list(zip(*[new[k].to_list() for k in keys], strict=True))
        mask = [t not in seen for t in tuples]
        add = new.filter(pl.Series(mask))
        out = pl.concat([existing, add.select(existing.columns).cast(existing.schema)])  # type: ignore[arg-type]
    else:
        add = new
        out = new
    _write_atomic(out, path)
    return {"appended": add.height, "skipped": new.height - add.height, "total": out.height}


def load_journal(path: str | Path = JOURNAL_PATH) -> pl.DataFrame:
    """The signals journal, or an empty schema-correct frame when none exists yet."""
    return _load_parquet(path, JOURNAL_SCHEMA)


# --------------------------------------------------------------------------- git sha
_GIT_SHA_CACHE: list[str | None] = []


def _engine_git_sha() -> str | None:
    """Short git SHA of the engine build, or None when git is unavailable (cached)."""
    if _GIT_SHA_CACHE:
        return _GIT_SHA_CACHE[0]
    sha: str | None = None
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(PROJECT_ROOT),
            check=False,
        )
        sha = out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - defensive
        sha = None
    _GIT_SHA_CACHE.append(sha)
    return sha


# --------------------------------------------------------------------------- clock


def session_windows(session_iso: str) -> dict:
    """ET/DST-aware OPEN/CLOSE window bounds for ``session_iso`` (zoneinfo via et_ns).

    Returns ``{"session", "early_close", "open", "close"}``. ``open`` and ``close`` are
    each ``{"start_ns", "end_ns", "start_et", "end_et"}`` (UTC epoch ns bounds, DST
    correct because ``et_ns`` resolves America/New_York). On a listed NYSE half-day the
    CLOSE window is ABSENT (``close=None``) and ``early_close=True`` -- the engine is
    EXPLICIT where ``forward_paper``/``auction_replay`` silently no-op (design R3). The
    OPEN window is unaffected by a half-day.
    """
    early = session_iso in EARLY_CLOSE_DATES

    def _win(bounds: tuple[tuple[int, int, int], tuple[int, int, int]]) -> dict:
        (h0, m0, s0), (h1, m1, s1) = bounds
        return {
            "start_ns": et_ns(session_iso, h0, m0, s0),
            "end_ns": et_ns(session_iso, h1, m1, s1),
            "start_et": f"{h0:02d}:{m0:02d}:{s0:02d}",
            "end_et": f"{h1:02d}:{m1:02d}:{s1:02d}",
        }

    return {
        "session": session_iso,
        "early_close": early,
        "open": _win(OPEN_WINDOW_ET),
        "close": None if early else _win(CLOSE_WINDOW_ET),
    }


# --------------------------------------------------------------------------- emit


def _validate_row_dtypes(row: dict) -> None:
    """Reject a wrong-dtype value BEFORE construction (m4).

    Polars' ``strict=True`` still silently coerces e.g. a float 1.7 into an Int64
    column; this guard raises loudly instead so a malformed row can never enter the
    journal. None is always allowed (every column is nullable).
    """
    for c, dt in JOURNAL_SCHEMA.items():
        v = row.get(c)
        if v is None:
            continue
        if dt == pl.Int64:
            if isinstance(v, bool) or not isinstance(v, int):
                raise TypeError(f"journal column {c!r} expects int|null, got {v!r}")
        elif dt == pl.Float64:
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise TypeError(f"journal column {c!r} expects float|null, got {v!r}")
        elif dt == pl.Boolean:
            if not isinstance(v, bool):
                raise TypeError(f"journal column {c!r} expects bool|null, got {v!r}")
        elif dt == pl.Utf8:
            if not isinstance(v, str):
                raise TypeError(f"journal column {c!r} expects str|null, got {v!r}")


def _rows_to_frame(rows: list[dict]) -> pl.DataFrame:
    """Project partial row dicts onto JOURNAL_SCHEMA under STRICT dtypes (absent -> null).

    Each row is dtype-validated (m4: wrong dtype raises, never coerces) then normalized
    to the full pinned column set before a strict-schema construction.
    """
    if not rows:
        return pl.DataFrame(schema=JOURNAL_SCHEMA)
    for r in rows:
        _validate_row_dtypes(r)
    norm = [{c: r.get(c) for c in JOURNAL_SCHEMA} for r in rows]
    return pl.DataFrame(norm, schema=JOURNAL_SCHEMA, strict=True)  # type: ignore[arg-type]


def emit(rows: list[dict], *, source: str, journal_path: str | Path = JOURNAL_PATH) -> int:
    """Validate, stamp, and append-dedup signal rows to the journal. Returns n appended.

    ``source`` must be in ``SOURCES``. ``source="feed"`` is refused naming the L2 gate
    (R6). Each row's ``window`` must be a live window for its session: a value outside
    ``{"open","close"}`` is refused as dormant, and a ``close`` on a half-day is refused
    with reason ``early_close`` (R3). Stamps ``ts_emit`` (time.time_ns), ``source``, and
    ``engine_git_sha``, then appends deduped by (session, symbol, source, window) -- so
    a replay row never blocks a manual row for the same key and re-running is idempotent
    (R1).
    """
    if source == "feed":
        raise ValueError(
            "source='feed' refused: the live FeedAdapter is L2 (adoption-gated, "
            "$179/mo Databento) and NO L2 design exists yet (design R6)."
        )
    if source not in SOURCES:
        raise ValueError(f"unknown source {source!r}; allowed sources are {SOURCES}")

    sha = _engine_git_sha()
    ts = time.time_ns()
    stamped: list[dict] = []
    for r in rows:
        session = r["session"]
        window = r["window"]
        wins = session_windows(session)
        if window not in ("open", "close"):
            raise ValueError(
                f"refusing emit for {session} window={window!r}: outside the live "
                "windows ('open', 'close') (dormant by design)."
            )
        if wins.get(window) is None:
            reason = "early_close" if wins["early_close"] else "dormant"
            raise ValueError(
                f"refusing emit for {session} window={window!r}: {reason} -- the close "
                "window is absent on a NYSE half-day (design R3)."
            )
        row = dict(r)
        row["ts_emit"] = ts
        row["source"] = source
        row["engine_git_sha"] = sha
        stamped.append(row)

    # n6: dedup WITHIN the batch (keep-first on the journal keys) before appending, so a
    # single emit carrying two same-key rows never double-writes.
    frame = _rows_to_frame(stamped)
    if frame.height:
        frame = frame.unique(subset=list(JOURNAL_KEYS), keep="first", maintain_order=True)
    res = _append_dedup(frame, journal_path, JOURNAL_SCHEMA, list(JOURNAL_KEYS))
    return res["appended"]


# --------------------------------------------------------------------------- display


def _note(parts: list[str | None]) -> str:
    """Join non-empty note fragments with '; ' (empty -> '')."""
    return "; ".join(p for p in parts if p)


def _attach_display(
    p_win: float | None,
    symbol: str,
    session: str,
    closes_by_symbol: dict[str, list[tuple[str, float]]],
) -> tuple[float | None, float | None, list[str]]:
    """(tier, vol_norm, notes) via the M23 kernels for one (symbol, session).

    ``tier`` is null when p_win is null (classical-only). ``vol_norm`` uses the M23
    trailing raw-vol loader + median-of-5 rule; a vol-history skip (<21 prior closes)
    surfaces as ``vol_norm=null`` + a note, per R4 (the neutral-1.0 M23 ruling is the
    kernel's, but the DISPLAY column is honest-null on a skip).
    """
    notes: list[str] = []
    tier_v = tier(p_win) if p_win is not None else None
    sigma_i = trailing_raw_vol(closes_by_symbol.get(symbol, []), session)
    if is_vol_history_skip(sigma_i):
        vol_v: float | None = None
        notes.append("vol_skip")
    else:
        med5 = champion_sigma_med5(
            [trailing_raw_vol(closes_by_symbol.get(s, []), session) for s in UNIVERSE]
        )
        vol_v = vol_norm(sigma_i, med5)
    return tier_v, vol_v, notes


# --------------------------------------------------------------------------- replay


def replay_session(
    settings: Settings | None,
    asof: date,
    *,
    seed: int = 7,
    journal_path: str | Path = JOURNAL_PATH,
    bars_dir: str | Path = ss.RAW_BARS1D_DIR,
    model_path: str | Path = lc.MODEL_PATH,
) -> pl.DataFrame:
    """ReplayAdapter: owned T+1 data -> full pipeline -> journal (source="replay").

    Runs the forward clock's OWN ``compute_session_events`` then loads-or-degrades the
    frozen M8 model the cockpit way (Booster present -> ``score_events``; absent ->
    classical-only, p_win/taken_meta null, note ``no_model``; NEVER trains, R2). Attaches
    the M23 display fields (tier, vol_norm) from the raw bars1d loader, maps each event
    to a close-window journal row (order type per PLAYBOOK), emits deduped, and returns
    the display frame. Because the signal functions are the forward clock's, the emitted
    ``basis_bps`` / ``p_win`` / ``expected_net_bps`` agree with the forward ledger to
    1e-9 by construction (the reconcile acceptance bar). NOTE (n8): a replay row carries
    the REPLAYED REALIZED net in ``expected_net_bps`` (the schema name is pinned) -- it is
    the settled outcome of the replayed session, which is exactly what the reconcile
    net-relevant field checks against the ledger's ``net_bps``.
    """
    events = compute_session_events(settings, asof, seed=seed)
    booster, model_note = lc.load_model(model_path)
    no_model = booster is None

    if events.height == 0:
        return events
    if not no_model:
        scored = score_events(events, booster)
    else:
        scored = events.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("p_win"),
            (pl.col("basis_bps").abs() >= CANDIDATE_BASIS_BPS).alias("taken_classical"),
            pl.lit(None, dtype=pl.Boolean).alias("taken_meta"),
        )

    closes = {s: load_raw_closes(s, bars_dir=Path(bars_dir)) for s in UNIVERSE}
    session = asof.isoformat()
    rows: list[dict] = []
    for r in scored.iter_rows(named=True):
        p_win = r.get("p_win")
        tier_v, vol_v, notes = _attach_display(p_win, r["symbol"], session, closes)
        if no_model:
            notes = ["no_model", *notes]
        # m3: the deploy-lens whole-share count uses the SAME clip-capped kernel as the
        # manual adapter (live_cockpit.size_shares), so the clip cap applies to both.
        entry_px = r.get("entry_px")
        shares_deploy = lc.size_shares(DEPLOY_CAPITAL_USD, lc.DEFAULT_CLIP_CAP_USD, entry_px)
        size_shares_deploy = shares_deploy if entry_px is not None else None
        size_notional_research = (
            BOOK_NOTIONAL * tier_v * vol_v
            if tier_v is not None and vol_v is not None
            else None
        )
        rows.append(
            {
                "session": session,
                "symbol": r["symbol"],
                "window": "close",
                "basis_bps": r.get("basis_bps"),
                "p_win": p_win,
                "side": r.get("side"),
                "taken_classical": r.get("taken_classical"),
                "taken_meta": r.get("taken_meta"),
                "tier": tier_v,
                "vol_norm": vol_v,
                "size_notional_research": size_notional_research,
                "size_shares_deploy": size_shares_deploy,
                "expected_net_bps": r.get("net_bps"),  # replayed realized net (reconcile)
                "order_type": ORDER_TYPE_CLOSE,
                "limit_px": r.get("near_price"),
                "deadline_et": DEADLINE_CLOSE_ET,
                "spread_abort": None,
                "note": _note([model_note if no_model else None, *notes]),
            }
        )
    emit(rows, source="replay", journal_path=journal_path)
    return scored


# --------------------------------------------------------------------------- manual


def manual_decide(
    symbol: str,
    near: float | None,
    bid: float | None,
    ask: float | None,
    *,
    session_iso: str,
    model_path: str | Path = lc.MODEL_PATH,
    journal_path: str | Path = JOURNAL_PATH,
    do_emit: bool = True,
    **feature_kwargs: object,
) -> dict:
    """ManualAdapter: ``live_cockpit.decide_one`` verbatim + M23 display + emit.

    Loads-or-degrades the frozen model the cockpit way (never trains, R2), calls
    ``decide_one`` UNCHANGED, enriches the returned ticket dict with ``tier`` (from the
    meta p_win) and ``vol_norm`` (null for a keyed snapshot -- no lake history at the
    decision instant, noted), emits a close-window row (source="manual"), and returns
    the enriched dict for rendering.
    """
    booster, model_note = lc.load_model(model_path)
    d = decide_one(
        symbol, near, bid, ask, session_iso=session_iso, booster=booster, **feature_kwargs
    )
    p_win = d["meta"]["p_win"]
    tier_v = tier(p_win) if p_win is not None else None
    d["tier"] = tier_v
    d["vol_norm"] = None  # no trailing lake window from a single keyed snapshot
    d["model_note"] = model_note

    if do_emit:
        notes = ["manual_vol_na"]
        if booster is None:
            notes = ["no_model", *notes]
        row = {
            "session": session_iso,
            "symbol": d["symbol"],
            "window": "close",
            "basis_bps": d["basis_bps"],
            "p_win": p_win,
            "side": d["direction"],
            "taken_classical": d["classical_go"],
            "taken_meta": d["meta"]["go"],
            "tier": tier_v,
            "vol_norm": None,
            "size_notional_research": None,
            "size_shares_deploy": d.get("shares"),
            "expected_net_bps": None,  # no realized outcome at the decision instant
            "order_type": ORDER_TYPE_CLOSE,
            "limit_px": near,
            "deadline_et": DEADLINE_CLOSE_ET,
            "spread_abort": d["spread_abort"],
            "note": _note(notes),
        }
        emit([row], source="manual", journal_path=journal_path)
    return d


# --------------------------------------------------------------------------- monitor


def monitor_panel(journal: pl.DataFrame, *, ref_sr: float | None = None) -> dict:
    """ADIA-standard display panel over the journal's taken_classical stream.

    Daily-aggregates the ``taken_classical`` rows (session-mean ``expected_net_bps``, the
    $10k research lens), then reports the native-frequency SR, PSR[SR0=0], and -- when
    ``ref_sr`` is given -- the ADIA live-testing probe PSR[SR0=ref_sr] (the dev
    reference), plus MinTRL(alpha=0.05) and T. Pure display: every statistic is a
    ``sizing_shadow`` kernel called by identity; nothing gates. Manual rows (null
    expected_net_bps) drop out of the aggregate.
    """
    empty = {
        "T": 0,
        "n_events": 0,
        "sr_native": None,
        "psr_sr0_0": None,
        "min_trl": None,
        "ref_sr": ref_sr,
        "psr_ref": None,
        "gamma3": None,
        "gamma4": None,
        "rho": None,
        "lens_usd": BOOK_NOTIONAL,
    }
    if journal.height == 0 or "taken_classical" not in journal.columns:
        return empty
    taken = journal.filter(pl.col("taken_classical").fill_null(False)).filter(
        pl.col("expected_net_bps").is_not_null()
    )
    if taken.height == 0:
        return empty
    daily = (
        taken.group_by("session")
        .agg(pl.col("expected_net_bps").mean().alias("net_bps"))
        .sort("session")
    )
    x = daily["net_bps"].to_numpy()
    t = int(x.shape[0])
    g3, g4, rho = sample_moments(x)
    sr = sr_native(x)
    psr0 = psr(sr, 0.0, t, rho, g3, g4)
    mtrl = min_trl(sr, 0.0, ALPHA, rho, g3, g4)
    psr_ref = psr(sr, ref_sr, t, rho, g3, g4) if ref_sr is not None else None
    return {
        "T": t,
        "n_events": int(taken.height),
        "sr_native": round(float(sr), 4),
        "psr_sr0_0": _round_or_none(psr0, 4),
        "min_trl": _round_or_none(mtrl, 2),
        "ref_sr": ref_sr,
        "psr_ref": _round_or_none(psr_ref, 4) if psr_ref is not None else None,
        "gamma3": round(float(g3), 4),
        "gamma4": round(float(g4), 4),
        "rho": round(float(rho), 4),
        "lens_usd": BOOK_NOTIONAL,
    }


def _round_or_none(v: float | None, ndigits: int) -> float | None:
    import numpy as np

    if v is None or not np.isfinite(v):
        return None
    return round(float(v), ndigits)
