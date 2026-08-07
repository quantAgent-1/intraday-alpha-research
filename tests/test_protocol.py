import ast
from collections.abc import Callable
from datetime import date
from pathlib import Path

import polars as pl
import pytest

import enginev51
from enginev51 import protocol
from enginev51.config import get_research_config


def _frame() -> pl.DataFrame:
    return pl.DataFrame(
        {"session": ["2026-02-27", "2026-05-29", "2026-06-01", "2026-07-10"], "x": [1, 2, 3, 4]}
    )


def test_seal_strips_holdout() -> None:
    out = protocol.apply_seal(_frame())
    assert out["session"].to_list() == ["2026-02-27", "2026-05-29"]


def test_unseal_requires_token(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    # v5.1: apply_seal(unseal=True) also appends a ledger note — redirect LEDGER_PATH
    # to a tmp_path so this test doesn't write into the real research ledger.
    monkeypatch.setattr(protocol, "LEDGER_PATH", tmp_path / "ledger.jsonl")

    monkeypatch.delenv("ENGINEV51_UNSEAL_TOKEN", raising=False)
    with pytest.raises(protocol.SealViolation):
        protocol.apply_seal(_frame(), unseal=True)
    monkeypatch.setenv("ENGINEV51_UNSEAL_TOKEN", "I_UNDERSTAND_ONE_SHOT")
    out = protocol.apply_seal(_frame(), unseal=True)
    assert out.height == 4


def test_split_of() -> None:
    assert protocol.split_of("2026-02-28") == "train"
    assert protocol.split_of("2026-03-02") == "validate"
    assert protocol.split_of("2026-06-01") == "holdout"


def test_split_dates_match_research_config() -> None:
    """The protocol's hard-coded split boundaries must agree with config/settings.toml
    [splits] — the two are meant to be the same protocol-bound constants, expressed
    once in code (for import-time guarantees) and once in config (for inspection)."""
    cfg = get_research_config()
    assert protocol.TRAIN_END.isoformat() == cfg.train_end
    assert protocol.VALIDATE_END.isoformat() == cfg.validate_end
    assert protocol.HOLDOUT_START.isoformat() == cfg.holdout_start


# --------------------------------------------------------------------------- #
# Seal choke point (code review 2026-07-28 B7 / 2026-08-01 J2): every holdout
# guard RAISES SealViolation. A bare `assert` is compiled out by `python -O`,
# which would make the seal disable-able from the environment.
# --------------------------------------------------------------------------- #


def _date_guards() -> dict[str, Callable[[date], None]]:
    """The canonical helper plus every ``end``-date guard that delegates to it.

    Complete as of wave 2: ``sizing_shadow.assert_before_holdout`` was the last
    bare-assert holdout guard in the package and now delegates here too.
    """
    from enginev51.apps import (
        run_basis_trial,
        run_m11,
        run_moc_trial,
        run_open_trial,
        run_trial,
        run_xs_reversal,
    )
    from enginev51.research_screens import earnings_close, gap_day, open_fade, sizing_shadow

    return {
        "protocol.refuse_end_on_or_after_holdout": protocol.refuse_end_on_or_after_holdout,
        "open_fade.assert_before_holdout": open_fade.assert_before_holdout,
        "gap_day.assert_before_holdout": gap_day.assert_before_holdout,
        "earnings_close.assert_before_holdout": earnings_close.assert_before_holdout,
        "sizing_shadow.assert_before_holdout": sizing_shadow.assert_before_holdout,
        "run_basis_trial.assert_before_holdout": run_basis_trial.assert_before_holdout,
        "run_m11.assert_before_holdout": run_m11.assert_before_holdout,
        "run_trial.assert_before_holdout": run_trial.assert_before_holdout,
        "run_moc_trial.assert_before_holdout": run_moc_trial.assert_before_holdout,
        "run_open_trial.assert_before_holdout": run_open_trial.assert_before_holdout,
        "run_xs_reversal.assert_before_holdout": run_xs_reversal.assert_before_holdout,
    }


DATE_GUARDS = _date_guards()


@pytest.mark.parametrize("guard_name", sorted(DATE_GUARDS))
def test_date_guard_raises_seal_violation(guard_name: str) -> None:
    """Each date guard refuses >= the seal with SealViolation and passes below it."""
    guard = DATE_GUARDS[guard_name]
    with pytest.raises(protocol.SealViolation):
        guard(protocol.HOLDOUT_START)  # exactly the boundary
    with pytest.raises(protocol.SealViolation):
        guard(date(2026, 7, 1))  # deep in the holdout
    guard(date(2026, 5, 31))  # the last legal session — must not raise


def test_refuse_end_names_the_boundary() -> None:
    with pytest.raises(protocol.SealViolation) as exc:
        protocol.refuse_end_on_or_after_holdout(date(2026, 6, 1))
    assert protocol.HOLDOUT_START.isoformat() in str(exc.value)


def test_frame_guard_raises_seal_violation() -> None:
    """A frame-shaped guard (moc_meta) also raises SealViolation, not AssertionError."""
    from enginev51.models import moc_meta

    with pytest.raises(protocol.SealViolation):
        moc_meta.build_meta_frame(pl.DataFrame({"session": ["2026-06-01"]}))


# Both scan roots, keyed repo-relative so an allowlist entry is unambiguous.
# ``scripts/`` is in scope from 2026-08-01: the acquisition scripts hold their own
# seal guards (month caps + a FETCH_END ceiling) and were the tripwire's blind spot.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCAN_ROOTS: tuple[tuple[Path, str], ...] = (
    (Path(enginev51.__file__).parent, "src/enginev51"),
    (_REPO_ROOT / "scripts", "scripts"),
)

# Files still allowed to guard the seal with a bare assert. EMPTY, and it stays
# empty: the last exemption (research_screens/sizing_shadow.py) was converted in
# wave 2, so every holdout guard in the package now RAISES SealViolation.
BARE_ASSERT_ALLOWLIST: set[str] = set()

# Protocol-frozen no-touch scripts (ruling 2026-08-01 §4.1: ``scripts/r2a_*.py`` and
# ``scripts/rfd_live.py`` are never edited by any agent). If one of them ever carried
# a bare holdout assert it would have to be listed here — a residual hole recorded in
# the ruling rather than silently fixed. Verified 2026-08-01: none of them contains an
# ``assert`` statement that mentions the seal at all, so the set is EMPTY.
NO_TOUCH_SCRIPT_EXEMPTIONS: set[str] = set()

_ALL_EXEMPT = BARE_ASSERT_ALLOWLIST | NO_TOUCH_SCRIPT_EXEMPTIONS

# The seal-guard shapes this tripwire hunts. The first two are the package's
# convention (the constant, or the literal seal date). The bare word ``holdout`` is
# needed for the SCRIPTS, whose guards name the boundary only in the assert message
# (``assert max(mos) <= LAST_MONTH, "holdout guard tripped"``) or via a
# ``datetime(2026, 6, 1)`` ceiling that no token above matches.
_SEAL_TOKENS: tuple[str, ...] = ("HOLDOUT_START", protocol.HOLDOUT_START.isoformat())


def _mentions_seal(text: str) -> bool:
    return any(t in text for t in _SEAL_TOKENS) or "holdout" in text.lower()


def bare_seal_assert_lines(src: str, filename: str = "<memory>") -> list[int]:
    """Line numbers of every ``assert`` statement in ``src`` that guards the seal.

    Factored out of the file walk so the DETECTOR itself is testable against the
    exact shapes it must catch (see ``test_scanner_catches_the_script_guard_shapes``)
    rather than only being exercised by a scan that currently finds nothing.
    """
    if not _mentions_seal(src):
        return []
    out: list[int] = []
    for node in ast.walk(ast.parse(src, filename=filename)):
        if isinstance(node, ast.Assert) and _mentions_seal(ast.get_source_segment(src, node) or ""):
            out.append(node.lineno)
    return sorted(out)


def test_no_bare_assert_holdout_guard_in_source() -> None:
    """Tripwire: nothing may guard the holdout with a bare ``assert`` (B7/J2).

    Parses every ``src/enginev51/**/*.py`` AND every ``scripts/**/*.py`` and flags any
    ``assert`` statement whose source references ``HOLDOUT_START``, the literal seal
    date, or the word ``holdout`` — the copy-paste shape that ``python -O`` silently
    deletes. Convert offenders to ``protocol.refuse_end_on_or_after_holdout`` (date
    guards) or an explicit ``raise SealViolation`` (frame / month-cap guards).

    Keying on ``holdout`` as well as the seal constant is what closed the 2026-08-01
    blind spot: the three acquisition scripts capped the fetch window with
    ``assert max(mos) <= LAST_MONTH, "holdout guard tripped"`` and
    ``assert FETCH_END <= datetime(2026, 6, 1, ...)``, neither of which mentions the
    constant or the ISO date. Other boundary guards that merely mention the holdout in
    prose are unaffected — they are not ``assert`` statements (``assert_forward_only``
    and friends already raise).
    """
    offenders: list[str] = []
    for root, label in _SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            rel = f"{label}/{path.relative_to(root).as_posix()}"
            if rel in _ALL_EXEMPT:
                continue
            for lineno in bare_seal_assert_lines(
                path.read_text(encoding="utf-8"), filename=str(path)
            ):
                offenders.append(f"{rel}:{lineno}")
    assert not offenders, (
        "bare assert holdout guards (stripped under `python -O`) — raise "
        f"SealViolation instead: {offenders}"
    )


def test_scanner_catches_the_script_guard_shapes() -> None:
    """The detector fails on the OLD behaviour, verbatim.

    These three lines are the pre-fix bodies of ``scripts/refetch_bars1m_raw.py``,
    ``scripts/backfill_bars1m_oos.py`` and ``scripts/backfill_bars1m_wide.py``. If any
    of them is reinstated the scan above flags it; if the detector is ever weakened
    back to seal-constant-only keying, this test goes red first."""
    reverted = (
        "FETCH_END = None\n"
        "def fetch():\n"
        '    assert FETCH_END <= datetime(2026, 6, 1, tzinfo=UTC), "fetch would reach the sealed holdout"\n'  # noqa: E501
        '    assert max(mo_set) <= LAST_MONTH, "holdout guard tripped"\n'
        '    assert max(mos) <= LAST_MONTH, "holdout guard tripped"\n'
    )
    assert bare_seal_assert_lines(reverted) == [3, 4, 5]
    # ...and an unrelated assert in a file that merely talks about the holdout is not
    # swept up (the false-positive direction).
    benign = '# the holdout is sealed\ndef f(tr, fold):\n    assert tr < fold, "leakage"\n'
    assert bare_seal_assert_lines(benign) == []


def test_bare_assert_allowlist_files_exist() -> None:
    """An allowlist entry that no longer exists must be deleted, not left rotting."""
    roots = {label: root for root, label in _SCAN_ROOTS}
    for rel in _ALL_EXEMPT:
        label, _, tail = rel.partition("/")
        assert label in roots, f"allowlist entry outside every scan root: {rel}"
        assert (roots[label] / tail).is_file(), f"stale allowlist entry: {rel}"


def test_bare_assert_allowlist_is_empty() -> None:
    """The end state the ruling asked for: nothing is exempt any more.

    Re-opening the allowlist to silence a new offender is the failure mode this
    pins — convert the guard instead (``refuse_end_on_or_after_holdout`` for date
    guards, an explicit ``raise SealViolation`` for frame / month-cap guards). The
    no-touch scripts get their own set so that, if one ever does need exempting, the
    reason ("frozen by the ruling") is visible instead of blending into the rest."""
    assert BARE_ASSERT_ALLOWLIST == set(), (
        "the bare-assert allowlist was re-opened: "
        f"{sorted(BARE_ASSERT_ALLOWLIST)} — convert the guard, don't exempt it"
    )
    assert NO_TOUCH_SCRIPT_EXEMPTIONS == set(), (
        "a protocol-frozen script was exempted: "
        f"{sorted(NO_TOUCH_SCRIPT_EXEMPTIONS)} — record the residual hole in the ruling"
    )


def test_scan_roots_cover_the_scripts_directory() -> None:
    """The blind spot itself: the scan must walk ``scripts/``, and it must be there."""
    labels = {label for _, label in _SCAN_ROOTS}
    assert labels == {"src/enginev51", "scripts"}
    scripts_root = dict((label, root) for root, label in _SCAN_ROOTS)["scripts"]
    assert scripts_root.is_dir()
    # the three converted files are inside the walked tree
    for name in (
        "refetch_bars1m_raw.py",
        "backfill_bars1m_oos.py",
        "backfill_bars1m_wide.py",
    ):
        assert (scripts_root / name).is_file()


# --------------------------------------------------------------------------- #
# Constants drift tripwire (code review 2026-07-28 S5/S10, 2026-08-01 J3c). The
# copies stay where they are; this is the one place that notices they disagree.
# --------------------------------------------------------------------------- #


def test_protocol_consistent_today() -> None:
    """Every registered copy of every pinned constant currently agrees."""
    protocol.assert_protocol_consistent()


def test_constant_registry_groups_are_internally_consistent() -> None:
    """Sanity on the registry itself: no empty group, no self-pin, and the two
    REGISTERED VINTAGES of the SEC/TAF fee stay in separate groups.

    0.25 and 0.3 are the same economic quantity (sell-side SEC/TAF over a round
    trip) frozen at different dates. Both are published, so neither may move —
    pinning them to each other would fail the suite on day one and the only "fix"
    would be editing a closed family's cost basis."""
    groups = protocol._registered_constant_copies()
    assert len(groups) >= 5
    for group, canon_name, canon_value, copies in groups:
        assert copies, f"empty group: {group}"
        assert canon_name not in copies, f"{canon_name} pinned against itself"
        assert canon_value is not None

    by_group = {g[0]: g for g in groups}
    rt = by_group["SEC/TAF round-trip fee, 0.25 vintage (bps)"]
    sec_taf = by_group["SEC/TAF sell-side fee (bps)"]
    assert rt[2] == 0.25 and sec_taf[2] == 0.3
    assert rt[2] != sec_taf[2]  # never pinned to each other


def _registry_rows() -> list[tuple[str, str, object]]:
    """(group, label, value) for every canon AND every pinned copy in the registry."""
    rows: list[tuple[str, str, object]] = []
    for group, canon_name, canon_value, copies in protocol._registered_constant_copies():
        rows.append((group, canon_name, canon_value))
        rows.extend((group, label, value) for label, value in copies.items())
    return rows


def test_no_pinned_copy_is_an_import_alias_of_another() -> None:
    """No registry row may be a TAUTOLOGY (code review 2026-08-01 FIX 3).

    A copy that takes its value by import (``live_cockpit.META_GATE_Q =
    fp.META_GATE_Q``) is the *same object* as the row it is pinned against, so the
    equality can never fail — it inflates the registry's apparent coverage while
    testing nothing. Two independently-declared literals in different modules are
    distinct float objects in CPython, so cross-module object identity IS the
    alias signature. Same-module rows are exempt: a module's own literals share
    one constant object (``moc_meta.HEADLINE_GATE`` vs ``GATES[1]``) even though
    either can be edited independently."""
    rows = _registry_rows()
    aliases = [
        (a_label, b_label)
        for i, (_, a_label, a_val) in enumerate(rows)
        for _, b_label, b_val in rows[i + 1:]
        if a_val is b_val and a_label.rsplit(".", 1)[0] != b_label.rsplit(".", 1)[0]
    ]
    assert not aliases, (
        f"tautological pins (the copy IS the canon, by import): {aliases} — delete "
        "the row and leave a comment saying the module inherits the canon"
    )


def test_registry_pins_the_expected_number_of_independent_copies() -> None:
    """Recount, so the docstring's claim cannot rot (FIX 3): 29 copies, 6 groups."""
    groups = protocol._registered_constant_copies()
    assert len(groups) == 6
    assert sum(len(copies) for *_, copies in groups) == 29
    # the two rows FIX 3 deleted must not come back
    labels = {label for _, label, _ in _registry_rows()}
    assert "apps.live_cockpit.META_GATE_Q" not in labels
    assert "live.engine.DEPLOY_CAPITAL_USD" not in labels


def test_removed_alias_rows_still_inherit_the_canon() -> None:
    """Deleting the rows is only safe because the values are structurally identical.

    This is the property that replaced the pins: both modules take the number by
    import, so there is nothing left that could drift."""
    from enginev51.apps import forward_paper, live_cockpit
    from enginev51.live import engine as live_engine
    from enginev51.research_screens import sizing_shadow

    assert live_cockpit.META_GATE_Q is forward_paper.META_GATE_Q
    assert live_engine.DEPLOY_CAPITAL_USD is sizing_shadow.DEPLOY_CAPITAL_USD


@pytest.mark.parametrize(
    ("module_path", "attr", "drifted"),
    [
        ("enginev51.apps.forward_paper", "META_GATE_Q", 0.60),
        ("enginev51.apps.run_m11", "SEC_TAF_SELL_BPS", 0.5),
        ("enginev51.research_screens.sizing_shadow", "DEPLOY_CAPITAL_USD", 5000.0),
        ("enginev51.research_screens.gap_day", "BOOK_NOTIONAL", 25_000.0),
    ],
)
def test_constant_drift_is_caught_and_named(
    monkeypatch: pytest.MonkeyPatch, module_path: str, attr: str, drifted: float
) -> None:
    """Drift ANY registered copy and the suite fails, naming the drifted module.

    This is the test that fails on the old behaviour: before the tripwire existed,
    a stray edit to any of these literals was silent."""
    import importlib

    mod = importlib.import_module(module_path)
    monkeypatch.setattr(mod, attr, drifted)
    with pytest.raises(protocol.SealViolation) as exc:
        protocol.assert_protocol_consistent()
    msg = str(exc.value)
    assert module_path.removeprefix("enginev51.") in msg
    assert attr in msg


def test_headline_gate_is_the_middle_registered_gate() -> None:
    """moc_meta owns the canon and it must stay inside the registered ladder."""
    from enginev51.models import moc_meta

    assert moc_meta.HEADLINE_GATE == 0.55
    assert moc_meta.HEADLINE_GATE in moc_meta.GATES


# --------------------------------------------------------------------------- #
# In-house family count (code review 2026-07-28 S9): INHERITED_TRIAL_FAMILIES
# alone undercounts the looks taken.
# --------------------------------------------------------------------------- #


def test_in_house_families_cover_ledger() -> None:
    """The static list must not fall behind the append-only ledger.

    Registering a family without adding it here fails the suite — that is the
    whole point (a silently stale count is a dishonest PSR/DSR denominator). The
    ledger is READ, never written."""
    registered = protocol.registered_families_in_ledger()
    assert registered, "no registered families found — ledger read is broken"
    missing = registered - set(protocol.IN_HOUSE_TRIAL_FAMILIES)
    assert not missing, (
        f"families registered in research/ledger.jsonl but missing from "
        f"protocol.IN_HOUSE_TRIAL_FAMILIES: {sorted(missing)}"
    )


def test_in_house_family_list_has_no_duplicates() -> None:
    assert len(protocol.IN_HOUSE_TRIAL_FAMILIES) == len(set(protocol.IN_HOUSE_TRIAL_FAMILIES))
    assert list(protocol.IN_HOUSE_TRIAL_FAMILIES) == sorted(protocol.IN_HOUSE_TRIAL_FAMILIES)


def test_trial_family_counts_expose_inherited_and_in_house() -> None:
    """The multiple-testing denominator is inherited + in-house, never one alone."""
    counts = protocol.trial_family_counts()
    assert counts["inherited"] == sum(protocol.INHERITED_TRIAL_FAMILIES.values())
    assert counts["in_house"] == len(protocol.IN_HOUSE_TRIAL_FAMILIES)
    assert counts["total"] == counts["inherited"] + counts["in_house"]
    assert counts["in_house"] > len(protocol.INHERITED_TRIAL_FAMILIES)


def test_registered_families_reader_is_read_only(tmp_path) -> None:
    """The reader never creates or mutates a ledger; a missing one is an empty set."""
    missing = tmp_path / "nope.jsonl"
    assert protocol.registered_families_in_ledger(missing) == set()
    assert not missing.exists()

    fake = tmp_path / "ledger.jsonl"
    fake.write_text(
        '{"kind": "registered", "family": "a_v1"}\n'
        "\n"
        '{"kind": "result", "family": "b_v1"}\n'
        '{"kind": "registered", "family": "a_v1"}\n',
        encoding="utf-8",
    )
    before = fake.read_bytes()
    assert protocol.registered_families_in_ledger(fake) == {"a_v1"}
    assert fake.read_bytes() == before
