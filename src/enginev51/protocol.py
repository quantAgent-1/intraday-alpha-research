"""PROTOCOL.md, enforced in code: split boundaries, the holdout seal, the ledger.

Ported from engineV5 (same seal, same dates — the holdout is INHERITED, not re-cut).
Any code path that assembles research datasets must go through `apply_seal`.
The holdout (≥ 2026-06-01) is stripped unless `unseal=True`, which additionally
requires ENGINEV51_UNSEAL_TOKEN=I_UNDERSTAND_ONE_SHOT in the environment — the
mechanical speed bump that keeps the one-shot rule honest.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import polars as pl

from enginev51.config import PROJECT_ROOT

TRAIN_END = date(2026, 2, 28)  # inclusive
VALIDATE_START = date(2026, 3, 1)
VALIDATE_END = date(2026, 5, 31)  # inclusive
HOLDOUT_START = date(2026, 6, 1)  # sealed; inherited from engineV5 PROTOCOL v5

LEDGER_PATH = PROJECT_ROOT / "research" / "ledger.jsonl"

_UNSEAL_ENV = "ENGINEV51_UNSEAL_TOKEN"
_UNSEAL_TOKEN = "I_UNDERSTAND_ONE_SHOT"

# Honest multiple-testing accounting: trial families this project inherits.
# DSR/PBO computations must use at least these counts for overlapping families.
INHERITED_TRIAL_FAMILIES: dict[str, int] = {
    "single_name_subhour_microstructure": 160,  # engineV2 record
    "bar_tier_intraday_30m_4h": 33,  # engineV5 (18) + engineV_grok (~15)
    "daily_swing_1d_5d": 9,  # engineV_grok E5 cells
}

# ...and the families THIS project has registered itself (code review 2026-07-28 S9:
# INHERITED_TRIAL_FAMILIES alone undercounts, because it stops at pre-v5.1 history).
# Every entry is a distinct `family` value on a kind="registered" row of
# `research/ledger.jsonl`; the ledger is the append-only record and this list is the
# AUDITABLE mirror of it — `tests/test_protocol.py::test_in_house_families_cover_ledger`
# re-reads the ledger and fails the suite if a registration lands without landing here.
# Read alongside the inherited counts whenever a PSR/DSR/PBO number is reported: the
# multiple-testing denominator is inherited + in-house, never one of them.
IN_HOUSE_TRIAL_FAMILIES: tuple[str, ...] = (
    "calendar_overlay_v1",
    "cost_model",
    "daily_swing_1d_5d",
    "daily_xs_reversal_v1",
    "earnings_close_v1",
    "earnings_reaction_regime_v1",
    "gap_day_reversion_v1",
    "m16_flow_book",
    "m4_encoder_v1",
    "moc_diagnostic_v1",
    "moc_imbalance_v1",
    "moc_mechanism_v1",
    "moc_meta_v1",
    "moc_method_v1",
    "open_auction_fade_v1",
    "open_cross_battery_v1",
    "open_imbalance_v1",
    "payer_detectors_v1",
    "retail_fade_daily_v1",
    "reversion_system_v1",
    "sched_window_v1",
    "short_ratio_battery_v1",
    "sizing_shadow_v1",
    "tsy_results_forward_v1",
    "xsect_factor_momentum_v1",
)


def trial_family_counts() -> dict[str, int]:
    """The honest multiple-testing denominator: inherited + in-house.

    ``inherited`` is the pre-v5.1 CELL count (engineV2/V5/grok, weighted per family);
    ``in_house`` is the number of families this project has registered. They are
    different units on purpose — the inherited record survives only as per-family
    trial counts, while v5.1 registers whole families — so `total` is the honest
    lower bound on the number of looks taken, not a precise cell count.

    NOTE ``daily_swing_1d_5d`` appears in BOTH dicts: engineV_grok's 9 cells were
    inherited, and M3 re-registered the family here. The overlap is left visible
    rather than netted out; over-counting looks is the conservative direction.
    """
    inherited = sum(INHERITED_TRIAL_FAMILIES.values())
    in_house = len(IN_HOUSE_TRIAL_FAMILIES)
    return {"inherited": inherited, "in_house": in_house, "total": inherited + in_house}


def registered_families_in_ledger(path: Path | None = None) -> set[str]:
    """Distinct ``family`` values on kind="registered" ledger rows (READ-ONLY).

    The ledger is append-only and is never written by this reader. Used by the
    suite to prove ``IN_HOUSE_TRIAL_FAMILIES`` has not fallen behind reality.
    """
    p = path or LEDGER_PATH
    if not p.exists():
        return set()
    out: set[str] = set()
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("kind") == "registered" and row.get("family"):
                out.add(str(row["family"]))
    return out


class SealViolation(RuntimeError):
    pass


def refuse_end_on_or_after_holdout(end: date) -> None:
    """Refuse any run whose ``end`` date reaches the sealed holdout.

    The canonical date guard for CLIs and builders (code review 2026-08-01 J2 /
    2026-07-28 B7). It RAISES — a bare ``assert end < HOLDOUT_START`` is compiled
    out under ``python -O`` / PYTHONOPTIMIZE, which would make the seal
    disable-able by an env var. Dependency-free on purpose: no config read, no
    ledger write, so every module can call it at import-time cost of nothing.
    """
    if end >= HOLDOUT_START:
        raise SealViolation(
            f"end {end.isoformat()} is on/after the sealed holdout "
            f"{HOLDOUT_START.isoformat()} — research code never touches the holdout "
            "(PROTOCOL v6 §1)"
        )


_splits_checked = False


def assert_splits_consistent() -> None:
    """Fail loudly if settings.toml's split dates drift from these constants.

    The dates exist in two places (here, enforced; research config, displayed) —
    code review 2026-07-17 F11: drift would make the toml look authoritative
    while this module silently enforces something else. Checked once per
    process, at the seal choke point.
    """
    global _splits_checked
    if _splits_checked:
        return
    from enginev51.config import get_research_config

    rc = get_research_config()
    pairs = {
        "train_end": (rc.train_end, TRAIN_END.isoformat()),
        "validate_end": (rc.validate_end, VALIDATE_END.isoformat()),
        "holdout_start": (rc.holdout_start, HOLDOUT_START.isoformat()),
    }
    drifted = {k: v for k, v in pairs.items() if v[0] != v[1]}
    if drifted:
        raise SealViolation(
            f"settings.toml splits drifted from protocol.py constants: {drifted} "
            "(protocol.py is the enforced source of truth — reconcile the toml)"
        )
    _splits_checked = True


def _registered_constant_copies() -> list[tuple[str, str, object, dict[str, object]]]:
    """(group, canonical home, canonical value, {module label: its copy}).

    The drift registry behind `assert_protocol_consistent`. Imports live inside the
    function: `protocol` sits UNDER every module named here, so a module-level import
    would be a cycle.

    SEMANTIC RULE (binding): a row belongs here only if the copy is the SAME QUANTITY
    as the canon, not merely the same float. Near-misses deliberately excluded:
      * `gap_day.FEES_RT_BPS = 0.25` / `sched_window.FEES_BPS_RT = 0.25` ARE the same
        economic quantity as the 0.3 canon — SEC/TAF sell-side fees over a round trip
        (gap_day's own comment says so: "SEC/TAF sell side at the $10k clip (round
        trip)"). They are two REGISTERED VINTAGES of that number: 0.25 was frozen into
        the M20/M27 cost floors and the sched_window screen, 0.3 into M11/M24 and
        `config.sec_taf_sell_bps`. Both vintages are frozen — a registered number does
        not move after results exist — so they are pinned to EACH OTHER (the 0.25 pair
        below) and DELIBERATELY not to the 0.3 canon. Pinning across the vintages would
        fail the suite on day one and the only "fix" would be editing a published
        screen's cost basis, which the ruling forbids. The split is a dated-vintage
        fact, not a claim that the two measure different things.
      * `reversion.meta.META_THRESHOLD = 0.55` is the reversion system's own pooled
        meta veto — a different model on a different signal family that happens to
        share the number. Not the M8 MOC gate; not pinned.
      * `reversion.ou` "1200 s" (a ring-buffer eviction age) and
        `reversion.fills.PRICE_SCALE = 10_000` (fixed-point price scale) are not money.
      * `events.detectors.cascade["stop_amp_frac"] = 0.3` is a stop fraction.
      * Inline call-site kwargs (`sec_taf_sell_bps=0.3` inside run_basis_trial /
        run_moc_trial / run_open_trial CLI bodies) are literals in expressions, not
        named constants; only NAMED module constants and NAMED signature defaults are
        addressable here.
    """
    import inspect

    from enginev51 import positioning
    from enginev51.apps import (
        forward_paper,
        live_cockpit,
        run_m9,
        run_m11,
        run_meta_trial,
        run_open_trial,
        run_xs_reversal,
    )
    from enginev51.backtest.auction_replay import replay_moc_event
    from enginev51.backtest.replay import ReplayConfig
    from enginev51.config import get_research_config
    from enginev51.models import m8v2_run, moc_meta, sizing
    from enginev51.research_screens import (
        gap_day,
        open_fade,
        sched_window,
        sched_window_forward,
        sizing_shadow,
    )
    from enginev51.scoreboard import research_book

    rc = get_research_config()

    def _default(fn: object, name: str) -> object:
        return inspect.signature(fn).parameters[name].default  # type: ignore[arg-type]

    return [
        (
            "meta gate P(win)",
            "models.moc_meta.HEADLINE_GATE",
            moc_meta.HEADLINE_GATE,
            {
                "models.moc_meta.GATES[1]": moc_meta.GATES[1],
                "apps.forward_paper.META_GATE_Q": forward_paper.META_GATE_Q,
                # NOT pinned: apps.live_cockpit.META_GATE_Q is `fp.META_GATE_Q` by
                # import — it inherits the canon, so drift is structurally impossible
                # and a row here would only assert a float equals itself.
                "apps.run_m11.META_GATE": run_m11.META_GATE,
                "apps.run_m9.COMPARE_GATE": run_m9.COMPARE_GATE,
                "models.m8v2_run.COMPARE_GATE": m8v2_run.COMPARE_GATE,
                "models.sizing.GATE_Q": sizing.GATE_Q,
                "research_screens.sizing_shadow.P_CUT_LO": sizing_shadow.P_CUT_LO,
            },
        ),
        (
            "registered gate ladder",
            "models.moc_meta.GATES",
            moc_meta.GATES,
            {
                "apps.run_m9.GATES": run_m9.GATES,
                "models.m8v2_run.CONTEXT_GATES": m8v2_run.CONTEXT_GATES,
            },
        ),
        (
            "research book notional (USD)",
            "config.ResearchConfig.notional_research_usd",
            rc.notional_research_usd,
            {
                "positioning.CAPITAL_USD": positioning.CAPITAL_USD,
                "apps.run_m9.BOOK_NOTIONAL": run_m9.BOOK_NOTIONAL,
                "apps.run_meta_trial.BOOK_NOTIONAL": run_meta_trial.BOOK_NOTIONAL,
                "apps.run_xs_reversal.NOTIONAL": run_xs_reversal.NOTIONAL,
                "models.sizing.BOOK_NOTIONAL": sizing.BOOK_NOTIONAL,
                "research_screens.gap_day.BOOK_NOTIONAL": gap_day.BOOK_NOTIONAL,
                "research_screens.open_fade.BOOK_NOTIONAL": open_fade.BOOK_NOTIONAL,
                "research_screens.sizing_shadow.BOOK_NOTIONAL": sizing_shadow.BOOK_NOTIONAL,
                "research_screens.sched_window_forward.SIZING_CLIP_USD": (
                    sched_window_forward.SIZING_CLIP_USD
                ),
                "scoreboard.research_book.results_frame(notional_usd=)": _default(
                    research_book.results_frame, "notional_usd"
                ),
            },
        ),
        (
            "deploy-lens capital (USD)",
            "config.ResearchConfig.deploy_equity_usd",
            rc.deploy_equity_usd,
            {
                "positioning.DEPLOY_CAPITAL_USD": positioning.DEPLOY_CAPITAL_USD,
                "apps.live_cockpit.DEFAULT_CAPITAL_USD": live_cockpit.DEFAULT_CAPITAL_USD,
                "research_screens.sizing_shadow.DEPLOY_CAPITAL_USD": (
                    sizing_shadow.DEPLOY_CAPITAL_USD
                ),
                # NOT pinned: live.engine.DEPLOY_CAPITAL_USD is
                # `ss.DEPLOY_CAPITAL_USD` by import — it inherits the pinned canon,
                # so drift is structurally impossible and a row here would be a
                # tautology (the same float object compared with itself).
            },
        ),
        (
            "SEC/TAF sell-side fee (bps)",
            "config.ResearchConfig.sec_taf_sell_bps",
            rc.sec_taf_sell_bps,
            {
                "apps.run_m11.SEC_TAF_SELL_BPS": run_m11.SEC_TAF_SELL_BPS,
                "apps.run_xs_reversal.SEC_TAF_SELL_BPS": run_xs_reversal.SEC_TAF_SELL_BPS,
                "research_screens.open_fade.SEC_TAF_SELL_BPS": open_fade.SEC_TAF_SELL_BPS,
                "backtest.auction_replay.replay_moc_event(sec_taf_sell_bps=)": _default(
                    replay_moc_event, "sec_taf_sell_bps"
                ),
                "backtest.replay.ReplayConfig(sec_taf_sell_bps=)": _default(
                    ReplayConfig, "sec_taf_sell_bps"
                ),
                "apps.run_open_trial.replay_open_event(sec_taf_sell_bps=)": _default(
                    run_open_trial.replay_open_event, "sec_taf_sell_bps"
                ),
            },
        ),
        (
            # Same quantity as the 0.3 canon (SEC/TAF sell-side over a round trip) at
            # an EARLIER registered vintage; both frozen, so the vintages are pinned
            # separately and never to each other — see the docstring.
            "SEC/TAF round-trip fee, 0.25 vintage (bps)",
            "research_screens.gap_day.FEES_RT_BPS",
            gap_day.FEES_RT_BPS,
            {"research_screens.sched_window.FEES_BPS_RT": sched_window.FEES_BPS_RT},
        ),
    ]


def assert_protocol_consistent() -> None:
    """Fail loudly if any registered COPY of a protocol constant has drifted.

    The splits check (`assert_splits_consistent`) generalized to the rest of the
    protocol-bound numbers (code review 2026-07-28 S5/S10, 2026-08-01 J3c). Ruled as
    **assert-equality, not rewiring**: the meta gate, the research book, the deploy
    lens and the sell-side fee are each redeclared as a frozen literal inside a dozen
    registered screens, and rewriting a published family to import a canon would
    touch numeric paths for zero scientific gain. So the literals STAY and are pinned
    HERE — one place that fails the suite the moment two copies disagree.

    Only INDEPENDENT declarations are pinned. A module that takes the number by
    import (`live_cockpit.META_GATE_Q = fp.META_GATE_Q`, `live.engine.
    DEPLOY_CAPITAL_USD = ss.DEPLOY_CAPITAL_USD`) cannot drift, so pinning it would
    assert a float equals itself and inflate the registry's apparent coverage
    (code review 2026-08-01). 29 copies are pinned across 6 groups; the tautology
    tripwire lives in `tests/test_protocol.py`.

    Not called from `apply_seal`: it imports half the package (a dozen modules,
    LightGBM included) and is an audit, not a hot path. The suite calls it.
    """
    assert_splits_consistent()
    for group, canon_name, canon_value, copies in _registered_constant_copies():
        drifted = {k: v for k, v in copies.items() if v != canon_value}
        if drifted:
            raise SealViolation(
                f"protocol constant drift in [{group}]: canon {canon_name}="
                f"{canon_value!r}, but {drifted!r} — these are the SAME quantity "
                "declared in several registered modules; reconcile the drifted copy "
                "(protocol._registered_constant_copies is the registry)"
            )


def apply_seal(df: pl.DataFrame, *, unseal: bool = False) -> pl.DataFrame:
    """Strip holdout rows (session >= HOLDOUT_START) from a research frame."""
    assert_splits_consistent()
    if unseal:
        if os.environ.get(_UNSEAL_ENV) != _UNSEAL_TOKEN:
            raise SealViolation(
                f"unseal requested without {_UNSEAL_ENV}={_UNSEAL_TOKEN} — see PROTOCOL.md"
            )
        ledger_append("note", {"event": "HOLDOUT_UNSEALED", "rows": df.height})
        return df
    return df.filter(pl.col("session") < HOLDOUT_START.isoformat())


def split_of(session: str) -> str:
    d = date.fromisoformat(session)
    if d <= TRAIN_END:
        return "train"
    if d <= VALIDATE_END:
        return "validate"
    return "holdout"


def ledger_append(kind: str, payload: dict[str, Any]) -> None:
    """Append one row to the append-only ledger (kind: registered | result | note)."""
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(UTC).isoformat(),
        "kind": kind,
        **payload,
    }
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def experiments_dir() -> Path:
    p = PROJECT_ROOT / "research" / "experiments"
    p.mkdir(parents=True, exist_ok=True)
    return p
