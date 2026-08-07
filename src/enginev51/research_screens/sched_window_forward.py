"""M20-FORWARD revival screen for the SPENT ``sched_window_v1`` family.

The M20 TRAIN screen passed exactly two cells (``cluster_1000|C2|h30``,
``cluster_1000|C2|h60``); the single VALIDATE look confirmed at ~zero power, so per
the frozen registration rules the family is SPENT and closed. The one revival path
allowed by protocol is a NEW registration that judges the SAME frozen cells purely
on genuinely FORWARD sessions (>= 2026-07-17), M10-forward-paper style, alongside a
PLACEBO control arm. This module is that instrument. It measures forward sessions
through the FROZEN M20 Stage-1 mechanics (imported verbatim from
``research_screens.sched_window`` — never copied, never tuned) and keeps a running
forward tally against a gate that is FROZEN AT REGISTRATION.

ABSOLUTE ACTIVATION GATE. This module is INCAPABLE of producing any real-lake
statistic until ``research/experiments/M20F-forward/registration.json`` exists,
carries ``registered: true``, and has non-null ``trial_id``/``family``/
``gate.min_sessions``/``gate.min_events``. Every entry point that reads the real
lake or writes any ledger/state calls :func:`load_registration` first and raises
:class:`RegistrationMissing` otherwise, naming the DR-X9 wave gate. The family it
serves is NOT yet registered — that config is written by the orchestrator only
after the DR-X9 wave verdict. The ONLY pre-registration invocation is ``selftest``
(synthetic fixtures, temp dir, no lake, no real writes) in the CLI app.

Two arms, one set of frozen mechanics:

* REAL — calendar rows with ``class == "cluster_1000"`` on the asof session (all six
  10:00-ET subtypes), measured via the imported ``measure_event_symbol``.
* PLACEBO — every trading session with NO calendar event of ANY class gets ONE
  synthetic 10:00-ET anchor (``release_id = "PLACEBO-<date>"``, ``class =
  "placebo_1000"``). Deterministic: no sampling, no RNG. Measured through the
  IDENTICAL path and the IDENTICAL C2 gate, but with its OWN prior pool — the frozen
  ``c2_membership`` keys priors by ``(class, symbol)``, so ``placebo_1000`` priors
  can never cross ``cluster_1000`` priors by construction.

C2 prior continuity. ``sched_window_forward_state.parquet`` is an append-only
per-(release_id, symbol) pool of anchor_ts + reaction. On the FIRST activated run
the real pool is SEEDED by measuring every historical ``cluster_1000`` event with
``session < HOLDOUT_START`` (train+validate ONLY) through the same imported path;
forward events then accumulate into the pool as they are measured post-activation.
The placebo pool starts empty and warms forward (placebo cells report "warming"
until >= C2_MIN_PRIORS priors).

SEAL NOTE (orchestrator ruling 2026-07-22 — the seal is LITERAL). Holdout-window
data (>= 2026-06-01, < 2026-07-17) feeds NOTHING here, not even conditioning state:
the real pool seeds ONLY from train+validate (sessions < HOLDOUT_START), and forward
sessions (>= FORWARD_START) accumulate as they are measured. The holdout window is
permanently excluded, leaving a ~6-week gap in the expanding median over ~450 priors
— an accepted, negligible cost for ZERO seal ambiguity. Seeding never needs
``apply_seal``: it already stops strictly before the seal boundary by construction.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import structlog

from enginev51.config import PROJECT_ROOT
from enginev51.data.noii import et_ns
from enginev51.protocol import HOLDOUT_START, experiments_dir
from enginev51.research_screens import sched_window as sw

log = structlog.get_logger(__name__)

# Go-live: first forward session this instrument may collect (matches the M10
# forward-paper go-live; strictly after the sealed holdout boundary 2026-06-01).
FORWARD_START = date(2026, 7, 17)

# Seed boundary — the real prior pool seeds from train+validate ONLY. The seal is
# LITERAL (orchestrator ruling 2026-07-22): holdout-window data (>= HOLDOUT_START,
# < FORWARD_START) feeds NOTHING, not even C2 gate state, so it is excluded from the
# seed. Canonical boundary imported from protocol (never hardcoded). Forward events
# (>= FORWARD_START) accumulate into state post-activation via ``run_asof``.
SEED_END = HOLDOUT_START

# Placebo arm — a deterministic 10:00-ET null anchor on every no-event trading day.
PLACEBO_CLASS = "placebo_1000"
PLACEBO_ANCHOR_ET = (10, 0, 0)

# This module reports ONLY h30/h60 (the two frozen cells); the imported measurement
# still computes all HORIZONS, we simply select these two.
REPORT_HORIZONS: tuple[str, ...] = ("h30", "h60")

DEFAULT_CALENDAR = "data/external/macro_calendar.parquet"

REG_SUBDIR = "M20F-forward"
M20_SUBDIR = "M20-sched-window"

FORWARD_DIR = PROJECT_ROOT / "research" / "forward"
LEDGER_PATH = FORWARD_DIR / "sched_window_forward_ledger.parquet"
STATE_PATH = FORWARD_DIR / "sched_window_forward_state.parquet"

SIZING_CLIP = (0.0, 2.0)
SIZING_CLIP_USD = 10_000.0

LEDGER_SCHEMA: dict[str, pl.DataType] = {
    "asof": pl.Utf8,
    "session": pl.Utf8,
    "arm": pl.Utf8,            # "real" | "placebo"
    "class": pl.Utf8,          # "cluster_1000" | "placebo_1000"
    "subtype": pl.Utf8,
    "release_id": pl.Utf8,
    "symbol": pl.Utf8,
    "horizon": pl.Utf8,        # "h30" | "h60"
    "anchor_ts": pl.Int64,
    "reaction": pl.Float64,
    "signed_ret_bps": pl.Float64,  # non-null ONLY when status == "kept"
    "in_c2": pl.Boolean,
    "n_priors": pl.Int64,
    "status": pl.Utf8,         # "kept" | event/horizon drop reason | c2 exclusion
    "anchor_mid": pl.Float64,
    "entry_mid": pl.Float64,
    "exit_mid": pl.Float64,
}

STATE_SCHEMA: dict[str, pl.DataType] = {
    "release_id": pl.Utf8,
    "symbol": pl.Utf8,
    "class": pl.Utf8,
    "session": pl.Utf8,
    "anchor_ts": pl.Int64,
    "reaction": pl.Float64,
}


# --------------------------------------------------------------------------- errors


class RegistrationMissing(RuntimeError):
    """Raised whenever the activation gate is not satisfied (the default state)."""


class BboMissing(RuntimeError):
    """Raised when an asof session has no bbo-1s partitions (never downloads here)."""


class CalendarExceeded(RuntimeError):
    """Raised when asof runs past the calendar's last known session."""


# --------------------------------------------------------------------------- paths


def reg_dir(root: str | Path | None = None) -> Path:
    p = Path(root) if root is not None else (experiments_dir() / REG_SUBDIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def registration_path(root: str | Path | None = None) -> Path:
    return reg_dir(root) / "registration.json"


def template_path(root: str | Path | None = None) -> Path:
    return reg_dir(root) / "registration.TEMPLATE.json"


def m20_dir() -> Path:
    return experiments_dir() / M20_SUBDIR


def default_pass_list_path() -> Path:
    return m20_dir() / "train_pass_list.json"


def default_floors_path() -> Path:
    return m20_dir() / "cost_floors.json"


# --------------------------------------------------------------------------- gate


def load_registration(root: str | Path | None = None) -> dict:
    """Load + validate the activation config, or REFUSE (naming the DR-X9 gate).

    The forward screen is inert by default: it refuses unless ``registration.json``
    exists, ``registered`` is exactly ``True``, and every gate primitive
    (``trial_id``, ``family``, ``gate.min_sessions``, ``gate.min_events``) is
    non-null. The orchestrator writes that config only AFTER the DR-X9 wave verdict;
    until then this raises and nothing touches the real lake or any ledger/state.
    """
    path = registration_path(root)
    refusal = (
        f"forward-screen NOT activated: {path} is missing or incomplete. The "
        "sched_window_v1 family is SPENT; this instrument stays inert until the "
        "orchestrator writes a registered config AFTER the DR-X9 wave verdict "
        "(research/deep/WAVE5_PLAN.md). selftest is the only pre-registration run."
    )
    if not path.exists():
        raise RegistrationMissing(refusal)
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:  # pragma: no cover - defensive
        raise RegistrationMissing(f"{refusal}\n(unreadable registration.json: {exc})") from exc
    if cfg.get("registered") is not True:
        raise RegistrationMissing(refusal + "  [registered is not true]")
    gate = cfg.get("gate") or {}
    missing = [
        k
        for k, v in (
            ("trial_id", cfg.get("trial_id")),
            ("family", cfg.get("family")),
            ("gate.min_sessions", gate.get("min_sessions")),
            ("gate.min_events", gate.get("min_events")),
        )
        if v is None
    ]
    if missing:
        raise RegistrationMissing(refusal + f"  [null gate fields: {missing}]")
    return cfg


def resolve_cells(reg: dict, pass_list_path: str | Path | None = None) -> dict:
    """Frozen cells = ``train_pass_list.json`` cells INTERSECT the registration cells.

    Returns ``{"cells", "real_classes", "horizons"}``. The intersection is the
    source of truth: neither the pass list nor the registration alone can widen the
    tested surface. Real classes/horizons are parsed from the surviving cell ids
    (config-driven, no hardcoded class list).
    """
    pp = Path(pass_list_path) if pass_list_path is not None else default_pass_list_path()
    train_cells = set(json.loads(pp.read_text(encoding="utf-8")).get("cells", []))
    reg_cells = set(reg.get("cells", []))
    cells = sorted(train_cells & reg_cells)
    if not cells:
        raise RegistrationMissing(
            "no frozen cells survive train_pass_list INTERSECT registration.cells "
            f"(train={sorted(train_cells)}, reg={sorted(reg_cells)}) — refusing."
        )
    real_classes = {c.split("|")[0] for c in cells}
    horizons = [h for h in REPORT_HORIZONS if any(c.split("|")[2] == h for c in cells)]
    return {"cells": cells, "real_classes": real_classes, "horizons": horizons}


# --------------------------------------------------------------------------- artifacts


def load_train_means(pass_list_path: str | Path | None = None) -> dict:
    pp = Path(pass_list_path) if pass_list_path is not None else default_pass_list_path()
    return json.loads(pp.read_text(encoding="utf-8")).get("train_means", {})


def load_class_floors(floors_path: str | Path | None = None) -> dict:
    fp = Path(floors_path) if floors_path is not None else default_floors_path()
    return json.loads(fp.read_text(encoding="utf-8")).get("class_floor_bps", {})


def sizing_usd(train_mean: float | None, floor: float | None) -> float | None:
    """REPORT-ONLY sizing = ``clip(train_mean / floor, 0, 2) * 10_000`` USD.

    The registered sizing FORM (M20 §"Sizing pre-commitment"); constants come from
    the frozen atlas artifacts only. Never routes an order — a display column.
    """
    if train_mean is None or floor is None or floor == 0:
        return None
    ratio = float(np.clip(train_mean / floor, *SIZING_CLIP))
    return round(ratio * SIZING_CLIP_USD, 2)


# --------------------------------------------------------------------------- calendar


def load_calendar(path: str | Path) -> pl.DataFrame:
    """Read the macro calendar and attach a normalized ISO ``_session`` column."""
    cal = sw.load_macro_calendar(path)
    return cal.with_columns(
        pl.col("session_date").cast(pl.Date).cast(pl.Utf8).alias("_session")
    )


def calendar_max_session(cal: pl.DataFrame) -> str:
    return str(cal["_session"].max())


def is_placebo_session(cal: pl.DataFrame, session: str) -> bool:
    """A trading session with NO calendar event of ANY class is a placebo session."""
    return cal.filter(pl.col("_session") == session).height == 0


def real_events_on(cal: pl.DataFrame, session: str, classes: set[str]) -> list[dict]:
    """Real-arm anchors on ``session`` (calendar rows whose class is in ``classes``)."""
    sub = cal.filter((pl.col("_session") == session) & pl.col("class").is_in(list(classes)))
    out: list[dict] = []
    for row in sub.iter_rows(named=True):
        out.append(
            {
                "release_id": str(row["release_id"]),
                "class": str(row["class"]),
                "subtype": "" if row.get("subtype") is None else str(row["subtype"]),
                "anchor_ts": sw._anchor_utc_ns(row["anchor_ts_et"], session),
            }
        )
    return out


def placebo_event(session: str) -> dict:
    """The single deterministic placebo anchor for a no-event session."""
    return {
        "release_id": f"PLACEBO-{session}",
        "class": PLACEBO_CLASS,
        "subtype": "",
        "anchor_ts": et_ns(session, *PLACEBO_ANCHOR_ET),
    }


# --------------------------------------------------------------------------- measure


def measure_events(
    events: list[dict],
    get_bbo: sw.BbboGetter,
    session: str,
    universe: tuple[str, ...],
    *,
    fail_on_missing: bool,
) -> list[dict]:
    """Measure every (event x symbol) on ``session`` via the imported M20 path.

    ``fail_on_missing`` is TRUE for the asof session (an absent bbo partition raises
    :class:`BboMissing` — this module NEVER downloads; the operator runs the daily
    forward_paper collector first) and FALSE while seeding history (an absent old
    partition simply yields no reaction and contributes no prior).
    """
    if fail_on_missing and events:
        for sym in universe:
            if get_bbo(sym, session) is None:
                raise BboMissing(
                    f"bbo-1s partition absent for {sym} {session}. This module never "
                    "downloads; run the daily collector first:\n  uv run python -m "
                    f"enginev51.apps.forward_paper run --asof {session}"
                )
    out: list[dict] = []
    for ev in events:
        for sym in universe:
            m = sw.measure_event_symbol(get_bbo(sym, session), anchor_ts=ev["anchor_ts"],
                                        session=session)
            m["release_id"] = ev["release_id"]
            m["class"] = ev["class"]
            m["subtype"] = ev["subtype"]
            m["symbol"] = sym
            m["session"] = session
            out.append(m)
    return out


def _state_rows(measured: list[dict]) -> pl.DataFrame:
    """Non-null-reaction measured events projected onto the prior-pool schema."""
    rows = [
        {
            "release_id": m["release_id"],
            "symbol": m["symbol"],
            "class": m["class"],
            "session": m["session"],
            "anchor_ts": int(m["anchor_ts"]),
            "reaction": float(m["reaction"]),
        }
        for m in measured
        if m.get("reaction") is not None
    ]
    return pl.DataFrame(rows, schema=STATE_SCHEMA) if rows else pl.DataFrame(schema=STATE_SCHEMA)


# --------------------------------------------------------------------------- C2 gate


def attach_c2(frame: pl.DataFrame) -> pl.DataFrame:
    """The FROZEN C2 magnitude gate (imported ``sw.c2_membership``).

    Groups priors by ``(class, symbol)`` — so real (``cluster_1000``) and placebo
    (``placebo_1000``) prior pools are separated BY CONSTRUCTION and can never cross.
    """
    if frame.height == 0:
        return frame
    return sw.c2_membership(frame)


def c2_decisions(state_path: str | Path, measured: list[dict]) -> dict:
    """PIT C2 decision per (release_id, symbol) for the freshly measured events.

    Builds the union of the PRIOR pool (state minus the current batch's keys) and
    the current batch's non-null reactions, then runs the frozen expanding-median
    gate. ``sw.c2_membership`` ranks priors STRICTLY earlier by anchor_ts, so the
    result is PIT and run-order independent (a later session already in state never
    becomes a prior for an earlier one). Returns ``{(rid, sym): {in_c2, n_priors,
    c2_reason}}``.
    """
    asof_state = _state_rows(measured)
    keys = set(zip(asof_state["release_id"].to_list(), asof_state["symbol"].to_list(),
                   strict=True))
    prior = load_state(state_path)
    if prior.height and keys:
        mask = [
            (r, s) not in keys
            for r, s in zip(prior["release_id"].to_list(), prior["symbol"].to_list(),
                            strict=True)
        ]
        prior = prior.filter(pl.Series(mask))
    frames = [f for f in (prior.select(list(STATE_SCHEMA)), asof_state) if f.height]
    if not frames:
        return {}
    gated = attach_c2(pl.concat(frames))
    dec: dict = {}
    for r in gated.iter_rows(named=True):
        dec[(r["release_id"], r["symbol"])] = {
            "in_c2": bool(r["in_c2"]),
            "n_priors": int(r["n_priors"]),
            "c2_reason": r["c2_reason"],
        }
    return dec


# --------------------------------------------------------------------------- ledger rows


def _ledger_rows(measured: list[dict], dec: dict, asof: date, horizons: list[str]) -> pl.DataFrame:
    """Flatten measured events x report-horizons into LEDGER_SCHEMA rows.

    Status precedence mirrors the frozen atlas ``_audit_row`` (form fixed to C2):
    event drop -> horizon drop -> C2 in -> C2 exclusion reason. ``signed_ret_bps``
    is populated ONLY for ``kept`` rows (measured, resolved horizon, C2 member).
    """
    rows: list[dict] = []
    for m in measured:
        rid, sym = m["release_id"], m["symbol"]
        cm = dec.get((rid, sym), {"in_c2": False, "n_priors": 0, "c2_reason": None})
        arm = "placebo" if m["class"] == PLACEBO_CLASS else "real"
        ev_drop = m["event_drop"]
        for hz in horizons:
            hr = m["hz"].get(hz)
            exit_mid = None
            signed = None
            if ev_drop is not None:
                status = ev_drop
            elif hr is None:  # pragma: no cover - h30/h60 always present in HORIZONS
                status = "no_horizon"
            elif hr["drop"] is not None:
                status = hr["drop"]
                exit_mid = hr["exit_mid"]
            elif cm["in_c2"]:
                status = "kept"
                exit_mid = hr["exit_mid"]
                signed = hr["signed_ret_bps"]
            else:
                status = cm["c2_reason"] or (
                    "c2_priors" if cm["n_priors"] < sw.C2_MIN_PRIORS else "c2_magnitude"
                )
                exit_mid = hr["exit_mid"]
            rows.append(
                {
                    "asof": asof.isoformat(),
                    "session": m["session"],
                    "arm": arm,
                    "class": m["class"],
                    "subtype": m["subtype"],
                    "release_id": rid,
                    "symbol": sym,
                    "horizon": hz,
                    "anchor_ts": int(m["anchor_ts"]),
                    "reaction": m["reaction"],
                    "signed_ret_bps": signed,
                    "in_c2": bool(cm["in_c2"]),
                    "n_priors": int(cm["n_priors"]),
                    "status": status,
                    "anchor_mid": m["anchor_mid"],
                    "entry_mid": m["entry_mid"],
                    "exit_mid": exit_mid,
                }
            )
    return pl.DataFrame(rows, schema=LEDGER_SCHEMA) if rows else pl.DataFrame(schema=LEDGER_SCHEMA)


# --------------------------------------------------------------------------- parquet I/O


def _write_atomic(df: pl.DataFrame, path: str | Path) -> None:
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


def _append_dedup(new: pl.DataFrame, path: str | Path, schema: dict, keys: list[str]) -> dict:
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


def load_ledger(path: str | Path = LEDGER_PATH) -> pl.DataFrame:
    return _load_parquet(path, LEDGER_SCHEMA)


def append_ledger(new: pl.DataFrame, path: str | Path = LEDGER_PATH) -> dict:
    return _append_dedup(new, path, LEDGER_SCHEMA, ["release_id", "symbol", "horizon"])


def load_state(path: str | Path = STATE_PATH) -> pl.DataFrame:
    return _load_parquet(path, STATE_SCHEMA)


def append_state(new: pl.DataFrame, path: str | Path = STATE_PATH) -> dict:
    return _append_dedup(new, path, STATE_SCHEMA, ["release_id", "symbol"])


# --------------------------------------------------------------------------- seeding


def seed_state(
    cal: pl.DataFrame,
    get_bbo: sw.BbboGetter,
    real_classes: set[str],
    universe: tuple[str, ...],
    state_path: str | Path,
) -> dict:
    """Seed the real prior pool from train+validate ONLY (``session < SEED_END``).

    Behind the activation gate ONLY (never at import, never in real-lake tests). The
    seal is LITERAL (module SEAL NOTE): the holdout window feeds NOTHING, not even
    C2 gate state, so it is excluded here; forward events accumulate later via
    ``run_asof``. The seed stops strictly before the seal boundary, so ``apply_seal``
    is unnecessary.
    """
    hist = cal.filter(
        (pl.col("_session") < SEED_END.isoformat())
        & pl.col("class").is_in(list(real_classes))
    )
    measured: list[dict] = []
    for session, grp in _group_by_session(hist):
        events = [
            {
                "release_id": str(row["release_id"]),
                "class": str(row["class"]),
                "subtype": "" if row.get("subtype") is None else str(row["subtype"]),
                "anchor_ts": sw._anchor_utc_ns(row["anchor_ts_et"], session),
            }
            for row in grp
        ]
        measured.extend(
            measure_events(events, get_bbo, session, universe, fail_on_missing=False)
        )
    rows = _state_rows(measured)
    _write_atomic(rows, state_path)
    log.info("m20f_seed_state", sessions=hist["_session"].n_unique(), priors=rows.height,
             classes=sorted(real_classes))
    return {"seed_sessions": int(hist["_session"].n_unique()), "seed_priors": rows.height}


def _group_by_session(cal: pl.DataFrame) -> list[tuple[str, list[dict]]]:
    out: list[tuple[str, list[dict]]] = []
    for session in sorted(cal["_session"].unique().to_list()):
        grp = cal.filter(pl.col("_session") == session).iter_rows(named=True)
        out.append((session, list(grp)))
    return out


# --------------------------------------------------------------------------- run


def assert_forward_only(asof: date) -> None:
    if asof < FORWARD_START:
        raise ValueError(
            f"--asof {asof} is before the forward go-live {FORWARD_START.isoformat()}; "
            "this instrument collects only genuinely forward sessions."
        )


def run_asof(
    asof: date,
    *,
    calendar_path: str | Path = DEFAULT_CALENDAR,
    bbo_dir: str | Path | None = None,
    ledger_path: str | Path = LEDGER_PATH,
    state_path: str | Path = STATE_PATH,
    reg_root: str | Path | None = None,
    pass_list_path: str | Path | None = None,
    universe: tuple[str, ...] = sw.UNIVERSE,
    get_bbo: sw.BbboGetter | None = None,
    do_seed: bool = True,
) -> dict:
    """Collect one forward session end-to-end (GATED). Idempotent by construction.

    Order: activation gate -> forward-only guard -> calendar-bound guard -> seed (if
    the state pool is absent) -> measure real + placebo for ``asof`` (lake read-only)
    -> PIT C2 -> append ledger (dedup release_id/symbol/horizon) -> append state
    (dedup release_id/symbol).
    """
    reg = load_registration(reg_root)
    assert_forward_only(asof)
    resolved = resolve_cells(reg, pass_list_path)
    real_classes, horizons = resolved["real_classes"], resolved["horizons"]

    cal = load_calendar(calendar_path)
    max_session = calendar_max_session(cal)
    if asof.isoformat() > max_session:
        raise CalendarExceeded(
            f"--asof {asof.isoformat()} is past the calendar's last session "
            f"{max_session}. Refresh the embedded-table calendar first:\n  uv run "
            "python scripts/build_macro_calendar.py"
        )

    if get_bbo is None:
        get_bbo = sw.make_bbo_getter(out_dir=bbo_dir)

    seed_note: dict = {}
    if do_seed and not Path(state_path).exists():
        seed_note = seed_state(cal, get_bbo, real_classes, universe, state_path)

    session = asof.isoformat()
    events = real_events_on(cal, session, real_classes)
    placebo = is_placebo_session(cal, session)
    if placebo:
        events = events + [placebo_event(session)]

    measured = measure_events(events, get_bbo, session, universe, fail_on_missing=True)
    dec = c2_decisions(state_path, measured)
    rows = _ledger_rows(measured, dec, asof, horizons)
    ledger_res = append_ledger(rows, ledger_path)
    state_res = append_state(_state_rows(measured), state_path)

    return {
        "asof": session,
        "placebo_session": placebo,
        "n_real_events": len([e for e in events if e["class"] != PLACEBO_CLASS]),
        "n_measured": len(measured),
        "seed": seed_note,
        "ledger": ledger_res,
        "state": state_res,
    }


# --------------------------------------------------------------------------- status


def _arm_hz_stat(kept: pl.DataFrame, arm: str, hz: str, z: float) -> dict:
    sub = (
        kept.filter((pl.col("arm") == arm) & (pl.col("horizon") == hz))
        if kept.height
        else kept
    )
    if sub.height == 0:
        return {"N": 0, "sessions": 0, "mean_bps": None, "ci_lo": None, "ci_hi": None}
    mean, lo, hi, n, ns = sw.cluster_ci(
        sub["signed_ret_bps"].to_numpy(), sub["session"].to_numpy(), z=z
    )
    return {
        "N": n,
        "sessions": ns,
        "mean_bps": round(mean, 4) if n else None,
        "ci_lo": round(lo, 4) if (n and not np.isnan(lo)) else None,
        "ci_hi": round(hi, 4) if (n and not np.isnan(hi)) else None,
    }


def _placebo_warming(ledger: pl.DataFrame, hz: str) -> bool:
    """Placebo cell is 'warming' until some placebo (symbol) reaches C2_MIN_PRIORS."""
    if ledger.height == 0:
        return True
    sub = ledger.filter((pl.col("arm") == "placebo") & (pl.col("horizon") == hz))
    if sub.height == 0:
        return True
    return int(sub.filter(pl.col("status") == "kept").height) == 0


def status_stats(
    ledger: pl.DataFrame,
    reg: dict,
    *,
    train_means: dict,
    floors: dict,
    z: float = 1.96,
) -> dict:
    """Per-arm x horizon forward tally, gate progress, and the placebo comparison.

    C2-gated only (``status == "kept"``). The pass/fail RULE freezes at registration
    (``gate.rule`` / ``placebo_kill.rule``) — this reports PROGRESS and the numbers
    the frozen rule will read, never a fabricated verdict. ``sizing_$`` is
    REPORT-ONLY (registered form; frozen train mean / class floor).
    """
    kept = ledger.filter(pl.col("status") == "kept") if ledger.height else ledger
    cells_out: list[dict] = []
    placebo_cmp: list[dict] = []

    real_cells = sorted(set(reg.get("cells", [])) & set(train_means))
    for cell_id in real_cells:
        cls, form, hz = cell_id.split("|")
        floor = floors.get(cls)
        tmean = train_means.get(cell_id)
        real = _arm_hz_stat(kept, "real", hz, z)
        real_cell = {
            "cell_id": cell_id,
            "arm": "real",
            "horizon": hz,
            **real,
            "train_mean_bps": tmean,
            "class_floor_bps": floor,
            "sizing_usd_REPORT_ONLY": sizing_usd(tmean, floor),
        }
        placebo = _arm_hz_stat(kept, "placebo", hz, z)
        placebo_cell = {
            "cell_id": f"{PLACEBO_CLASS}|{form}|{hz}",
            "arm": "placebo",
            "horizon": hz,
            **placebo,
            "warming": _placebo_warming(ledger, hz),
        }
        cells_out.extend([real_cell, placebo_cell])
        placebo_cmp.append(
            {
                "horizon": hz,
                "real_mean_bps": real["mean_bps"],
                "placebo_mean_bps": placebo["mean_bps"],
                "real_minus_placebo_bps": (
                    round(real["mean_bps"] - placebo["mean_bps"], 4)
                    if real["mean_bps"] is not None and placebo["mean_bps"] is not None
                    else None
                ),
            }
        )

    real_kept = kept.filter(pl.col("arm") == "real") if kept.height else kept
    ref_hz = REPORT_HORIZONS[0]
    events = (
        int(real_kept.filter(pl.col("horizon") == ref_hz).height) if real_kept.height else 0
    )
    sessions = int(real_kept["session"].n_unique()) if real_kept.height else 0
    gate_cfg = reg.get("gate") or {}
    min_sessions = gate_cfg.get("min_sessions")
    min_events = gate_cfg.get("min_events")
    gate = {
        "min_sessions": min_sessions,
        "min_events": min_events,
        "sessions": sessions,
        "events": events,
        "sessions_met": bool(min_sessions is not None and sessions >= min_sessions),
        "events_met": bool(min_events is not None and events >= min_events),
        "rule": gate_cfg.get("rule"),
        "placebo_kill_rule": (reg.get("placebo_kill") or {}).get("rule"),
        "note": "pass/fail RULE freezes at registration; figures are PROGRESS only.",
    }

    return {
        "trial_id": reg.get("trial_id"),
        "family": reg.get("family"),
        "n_sessions": int(ledger["session"].n_unique()) if ledger.height else 0,
        "asof_span": (
            [ledger["session"].min(), ledger["session"].max()] if ledger.height else []
        ),
        "cells": cells_out,
        "placebo_comparison": placebo_cmp,
        "gate": gate,
    }


def format_status(stats: dict) -> str:
    """Human-readable status block (the daily console view)."""
    lines = [
        f"M20-FORWARD revival screen — {stats.get('family')} "
        f"(trial {stats.get('trial_id')}); C2-gated, forward-only",
        "",
        f"sessions collected: {stats['n_sessions']}"
        + (f"   span {stats['asof_span'][0]}..{stats['asof_span'][1]}" if stats["asof_span"] else ""),
        "",
    ]
    for c in stats["cells"]:
        if c["N"] == 0:
            body = (
                "n=0 (warming)"
                if c["arm"] == "placebo" and c.get("warming")
                else "n=0 (no C2 events yet)"
            )
        else:
            body = (
                f"mean={c['mean_bps']:+.3f}  95%CI=["
                f"{'nan' if c['ci_lo'] is None else format(c['ci_lo'], '+.3f')}, "
                f"{'nan' if c['ci_hi'] is None else format(c['ci_hi'], '+.3f')}]  "
                f"n={c['N']}  sessions={c['sessions']}"
            )
        extra = ""
        if c["arm"] == "real":
            sz = c.get("sizing_usd_REPORT_ONLY")
            extra = f"   sizing=${sz:.0f} [REPORT-ONLY]" if sz is not None else ""
        lines.append(f"  {c['cell_id']:<26} {body}{extra}")

    lines += ["", "placebo comparison (real - placebo, C2 mean):"]
    for p in stats["placebo_comparison"]:
        d = p["real_minus_placebo_bps"]
        lines.append(
            f"  {p['horizon']}: real={_fmt(p['real_mean_bps'])}  "
            f"placebo={_fmt(p['placebo_mean_bps'])}  delta={_fmt(d)}"
        )

    g = stats["gate"]
    lines += [
        "",
        "registered forward gate (progress; RULE frozen at registration):",
        f"  sessions >= {g['min_sessions']}: {g['sessions_met']}  ({g['sessions']} collected)",
        f"  events   >= {g['min_events']}: {g['events_met']}  ({g['events']} C2 real events)",
        f"  gate.rule:        {g['rule']}",
        f"  placebo_kill.rule: {g['placebo_kill_rule']}",
    ]
    return "\n".join(lines)


def _fmt(v: float | None) -> str:
    return "n/a" if v is None else format(v, "+.3f")
