"""Tests for the LETF close-rebalance estimator (pure math + config table).

Hand-computed cases for the (L² − L)·AUM·r demand law, the bull/inverse sign
semantics, complex aggregation across an index, and the staleness warning.
"""

from __future__ import annotations

import math
from datetime import date

import structlog
from structlog.testing import capture_logs

from enginev51.flows import letf


def test_soxl_bull_buys_on_rally():
    # SOXL L=3, AUM=$10B, index +2% -> (9-3)*10e9*0.02 = +$1.2B (buy).
    d = letf.rebalance_demand_usd(3.0, 10e9, 0.02)
    assert math.isclose(d, 1.2e9, rel_tol=0, abs_tol=1.0)
    assert d > 0  # positive = must BUY into the close


def test_soxs_inverse_also_buys_on_rally():
    # SOXS L=-3, AUM=$1B, index +2% -> (L^2-L) with L=-3 -> 9+3 = 12;
    # 12 * 1e9 * 0.02 = +$240M (inverse fund ALSO buys when the index rises).
    assert (-3.0) ** 2 - (-3.0) == 12.0
    d = letf.rebalance_demand_usd(-3.0, 1e9, 0.02)
    assert math.isclose(d, 240e6, rel_tol=0, abs_tol=1.0)
    assert d > 0


def test_bull_sells_on_selloff():
    # SOXL on a -2% day must SELL: (9-3)*10e9*(-0.02) = -$1.2B.
    d = letf.rebalance_demand_usd(3.0, 10e9, -0.02)
    assert math.isclose(d, -1.2e9, rel_tol=0, abs_tol=1.0)
    assert d < 0


def test_complex_demand_aggregation_mixed():
    # Synthetic two-index complex; SOXX bull+bear both buy on a rally and add.
    table = {
        "AAAL": {"leverage": 3.0, "aum_usd": 10e9, "index": "SOXX", "as_of": "2999-01-01"},
        "AAAS": {"leverage": -3.0, "aum_usd": 1e9, "index": "SOXX", "as_of": "2999-01-01"},
        "BBBL": {"leverage": 3.0, "aum_usd": 20e9, "index": "QQQ", "as_of": "2999-01-01"},
    }
    tmp = _write_table(table)
    out = letf.complex_demand(str(tmp), {"SOXX": 0.02, "QQQ": -0.01})

    soxx = out["SOXX"]
    # 1.2e9 (bull) + 0.24e9 (bear) = 1.44e9
    assert math.isclose(soxx["demand_usd"], 1.44e9, abs_tol=1.0)
    assert math.isclose(soxx["per_etf"]["AAAL"], 1.2e9, abs_tol=1.0)
    assert math.isclose(soxx["per_etf"]["AAAS"], 0.24e9, abs_tol=1.0)

    qqq = out["QQQ"]
    # (9-3)*20e9*(-0.01) = -1.2e9
    assert math.isclose(qqq["demand_usd"], -1.2e9, abs_tol=1.0)


def test_complex_demand_skips_index_without_return():
    table = {
        "BBBL": {"leverage": 3.0, "aum_usd": 20e9, "index": "QQQ", "as_of": "2999-01-01"},
    }
    tmp = _write_table(table)
    out = letf.complex_demand(str(tmp), {"SOXX": 0.02})
    assert out == {}


def test_staleness_warning_fires():
    table = {
        "OLD": {"leverage": 3.0, "aum_usd": 1e9, "index": "SOXX", "as_of": "2020-01-01"},
        "NEW": {"leverage": 3.0, "aum_usd": 1e9, "index": "SOXX", "as_of": "2026-07-14"},
    }
    with capture_logs() as logs:
        stale = letf.staleness_check(table, today=date(2026, 7, 15))
    names = {t[0] for t in stale}
    assert names == {"OLD"}
    events = [e for e in logs if e.get("event") == "letf_aum_stale"]
    assert len(events) == 1 and events[0]["ticker"] == "OLD"


def test_staleness_no_warning_when_fresh():
    table = {
        "NEW": {"leverage": 3.0, "aum_usd": 1e9, "index": "SOXX", "as_of": "2026-07-14"},
    }
    stale = letf.staleness_check(table, today=date(2026, 7, 15))
    assert stale == []


def test_shipped_table_loads_and_has_expected_etfs():
    # The real config/letf_aum.toml parses and groups SOXX + QQQ complexes.
    table = letf.load_aum_table()
    assert set(table) == {"SOXL", "SOXS", "TQQQ", "SQQQ"}
    assert table["SOXL"]["index"] == "SOXX" and table["SOXL"]["leverage"] == 3.0
    assert table["SOXS"]["leverage"] == -3.0
    assert table["TQQQ"]["index"] == "QQQ"
    for row in table.values():
        assert row["aum_usd"] > 0
        assert str(row["source"]).startswith("http")


# --------------------------------------------------------------------------- helpers

_TMP_COUNTER = [0]


def _write_table(etf: dict) -> object:
    """Write a minimal letf_aum.toml to a temp file and return its path."""
    import tempfile

    import tomli_w

    _TMP_COUNTER[0] += 1
    import pathlib

    d = pathlib.Path(tempfile.gettempdir()) / f"letf_aum_test_{_TMP_COUNTER[0]}.toml"
    d.write_bytes(tomli_w.dumps({"etf": etf}).encode("utf-8"))
    return d


# quiet structlog during tests (no configured handler needed for capture_logs)
structlog.configure(processors=[structlog.processors.KeyValueRenderer()])
