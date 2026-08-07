"""Tests for the M21 earnings-reaction-regime diagnostic
(``research_screens.earnings_regime``). Synthetic daily bars + synthetic calendar in
temp dirs only — no real lake, no network, no estimation on real data. Covers the
registered landmines: PIT (day0 poison), day0 flows from the calendar (no
recomputation), frozen tercile/percentile cuts, PAST-ONLY streak with the <8-priors
exclusion, the imported cluster_ci clustered by event date, the holdout seal,
determinism, score-writes-nothing, the NO-COST-MODEL header, missing-bars
drop-with-reason, and the NVDA(up) vs MU(down) crowded-bucket contrast.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import polars as pl
import pytest

from enginev51.research_screens import earnings_regime as er
from enginev51.research_screens import sched_window as sw

# --------------------------------------------------------------------------- builders


def weekdays(start: str, n: int) -> list[str]:
    d = date.fromisoformat(start)
    out: list[str] = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def make_bars(
    sessions: list[str], closes: list[float], gaps: dict[int, float] | None = None
) -> pl.DataFrame:
    """(session, open, close). open[i] = close[i-1]*(1+gaps[i]) so gap[i] is exact;
    open[0] = close[0]."""
    gaps = gaps or {}
    opens = [closes[0]]
    for i in range(1, len(closes)):
        opens.append(closes[i - 1] * (1.0 + gaps.get(i, 0.0)))
    return pl.DataFrame({"session": sessions, "open": opens, "close": closes})


def flat_bars(sessions: list[str], level: float = 100.0) -> pl.DataFrame:
    return make_bars(sessions, [level] * len(sessions))


def getter_of(mapping: dict[str, pl.DataFrame]):
    def g(sym: str) -> pl.DataFrame | None:
        return mapping.get(sym.upper())

    return g


def calendar_of(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "event_id": r.get("event_id", f"{r['symbol']}-{r['day0_session']}"),
                "symbol": r["symbol"],
                "fiscal_note": r.get("fiscal_note", "Q1"),
                "accept_ts_et": r.get("accept_ts_et", f"{r['day0_session']}T16:05:00"),
                "timing": r.get("timing", "AMC"),
                "day0_session": r["day0_session"],
                "source": "test",
            }
            for r in rows
        ]
    )


# --------------------------------------------------------------------------- 1. PIT poison


def test_pit_prefeatures_ignore_day0_and_later_bars() -> None:
    sess = weekdays("2019-01-01", 400)
    closes = [100.0 * (1.001 ** i) for i in range(len(sess))]
    day0_idx = 300
    day0 = sess[day0_idx]
    smh = er.DailySeries(flat_bars(sess)).close_by_session()

    clean = er.DailySeries(make_bars(sess, closes))
    pre_clean = er.compute_prefeatures(clean, day0, smh)

    # POISON: the day0 bar and everything after -> absurd values.
    poisoned_closes = list(closes)
    for i in range(day0_idx, len(poisoned_closes)):
        poisoned_closes[i] = 1e9
    poisoned = er.DailySeries(make_bars(sess, poisoned_closes))
    pre_poison = er.compute_prefeatures(poisoned, day0, smh)

    assert pre_poison["runup60_rel"] == pytest.approx(pre_clean["runup60_rel"])
    assert pre_poison["mom_12_1"] == pytest.approx(pre_clean["mom_12_1"])
    # The day0 reaction DOES see the poisoned day0 close (proves the poison landed and
    # the pre-features above genuinely ignored it). c2c uses close(day0).
    react = er.compute_reaction_and_outcomes(poisoned, day0)
    assert react["c2c"] > 1e5


def test_runup_is_relative_to_reference_golden() -> None:
    # Name +10% over the 60-day window; reference (SMH) +4% -> runup60_rel = +6%.
    sess = weekdays("2019-01-01", 200)
    i = 100  # day0 index; window is [i-61 .. i-1]
    closes = [100.0] * len(sess)
    closes[i - 61] = 100.0
    closes[i - 1] = 110.0  # name +10% end/start
    name = er.DailySeries(make_bars(sess, closes))
    ref_closes = [100.0] * len(sess)
    ref_closes[i - 61] = 100.0
    ref_closes[i - 1] = 104.0  # ref +4%
    ref = er.DailySeries(make_bars(sess, ref_closes)).close_by_session()
    pre = er.compute_prefeatures(name, sess[i], ref)
    assert pre["runup60_rel"] == pytest.approx(0.10 - 0.04, abs=1e-9)


# --------------------------------------------------------------------------- 2. day0 from calendar


def test_day0_flows_from_calendar_no_recomputation() -> None:
    # Two events, same symbol, DIFFERENT day0_session anchors (BMO vs AMC produce
    # different day0s upstream). The module keys features off day0_session verbatim:
    # each event's gap is measured at ITS OWN anchor, never recomputed here.
    sess = weekdays("2019-01-01", 400)
    closes = [100.0 + i * 0.1 for i in range(len(sess))]
    gaps = {200: 0.05, 250: -0.05}  # +5% gap at idx200, -5% at idx250
    bars = make_bars(sess, closes, gaps)
    cal = calendar_of(
        [
            {"symbol": "NVDA", "day0_session": sess[200], "timing": "BMO"},
            {"symbol": "NVDA", "day0_session": sess[250], "timing": "AMC"},
        ]
    )
    audit, _ = er.assemble_events(cal, getter_of({"NVDA": bars, "SMH": flat_bars(sess)}),
                                  universe=("NVDA",))
    r200 = audit.filter(pl.col("day0_session") == sess[200]).row(0, named=True)
    r250 = audit.filter(pl.col("day0_session") == sess[250]).row(0, named=True)
    assert r200["gap_sign"] == "pos" and r200["gap"] == pytest.approx(0.05, abs=1e-9)
    assert r250["gap_sign"] == "neg" and r250["gap"] == pytest.approx(-0.05, abs=1e-9)
    assert r200["timing"] == "BMO" and r250["timing"] == "AMC"


# --------------------------------------------------------------------------- 3. frozen cuts


def test_score_reuses_frozen_cuts_never_refits(tmp_path) -> None:
    sess = weekdays("2019-01-01", 900)
    smh = flat_bars(sess)
    # spread of run-ups across two names so terciles are non-degenerate
    up = [100.0 * (1.003 ** i) for i in range(len(sess))]
    flat = [100.0 + (i % 5) * 0.02 for i in range(len(sess))]
    bars = {"SMH": smh, "NVDA": make_bars(sess, up, {i: 0.01 for i in range(300, len(sess), 45)}),
            "AMD": make_bars(sess, flat)}
    cal_rows = []
    for sym in ("NVDA", "AMD"):
        s = er.DailySeries(bars[sym])
        for k, idx in enumerate(range(300, len(s.sessions) - 25, 45)):
            cal_rows.append({"event_id": f"{sym}-{k}", "symbol": sym, "day0_session": s.sessions[idx]})
    cal = calendar_of(cal_rows)
    getter = getter_of(bars)

    er.compute_atlas(cal, getter, out_dir=tmp_path, universe=er.UNIVERSE)
    cuts_bytes = er.cuts_path(tmp_path).read_bytes()

    import json

    cuts = json.loads(cuts_bytes)
    ev = cal_rows[-1]
    res = er.score_event(ev["symbol"], ev["day0_session"], getter, cal, out_dir=tmp_path)
    # score used the STORED edges (no refit): its tercile == assign_tercile(value, stored edges)
    e = (cuts["runup_tercile_edges"][0], cuts["runup_tercile_edges"][1])
    assert res["runup_tercile"] == er.assign_tercile(res["runup60_rel"], e)
    # cuts.json is untouched by score.
    assert er.cuts_path(tmp_path).read_bytes() == cuts_bytes


# --------------------------------------------------------------------------- 4. streak past-only


def test_streak_past_only_and_lt8_priors_excluded_from_cells() -> None:
    # 12 events, every prior day0 GAP > 0 (STREAK_BASE='gap', per the frozen ledger).
    # Event with n_priors<8 -> level 'na' (margin only); >=8 -> hi (all priors positive
    # => streak 8 >= 5).
    sess = weekdays("2019-01-01", 900)
    closes = [100.0 * (1.002 ** i) for i in range(len(sess))]
    idxs = list(range(300, 300 + 12 * 40, 40))
    gaps = {i: 0.01 for i in idxs}  # each event opens +1% -> positive day0 gap
    bars = make_bars(sess, closes, gaps)
    cal = calendar_of([{"event_id": f"E{k}", "symbol": "NVDA", "day0_session": sess[i]}
                       for k, i in enumerate(idxs)])
    audit, _ = er.assemble_events(cal, getter_of({"NVDA": bars, "SMH": flat_bars(sess)}),
                                  universe=("NVDA",))
    audit = audit.sort("day0_session")
    levels = audit["streak_level"].to_list()
    npriors = audit["n_priors"].to_list()
    assert npriors[:9] == list(range(9))  # 0..8 priors accumulate PIT
    assert levels[7] == "na"  # 7 priors < 8 -> excluded from streak cells
    assert levels[8] == "hi"  # 8 priors, all positive -> streak 8 >= 5
    assert audit.row(8, named=True)["streak"] == 8

    # cells vs margins: the na event is absent from hi/lo cells but present in the
    # runup x gap margin (streak collapsed).
    scored = er.apply_cuts(audit, er.compute_cuts(audit, "SMH"))
    recs = er.compute_base_rates(scored)
    n_cell = sum(r["N"] for r in recs if r["kind"] == "cell" and r["window"] == "d1_5")
    n_margin = sum(r["N"] for r in recs if r["kind"] == "margin" and r["window"] == "d1_5")
    assert n_margin > n_cell  # na events live only in margins


def test_streak_uses_gap_not_c2c() -> None:
    # Ledger-conformance lock: priors that GAP UP but CLOSE DOWN (gap>0, c2c<0). The
    # streak must follow GAP (registered "positive-gap streak"), so 8 such priors make
    # the 9th event 'hi'. A c2c-based streak would score them negative -> 'lo'.
    assert er.STREAK_BASE == "gap"
    sess = weekdays("2019-01-01", 900)
    idxs = list(range(300, 300 + 10 * 40, 40))
    closes = [100.0] * len(sess)
    for i in idxs:
        closes[i] = 99.0  # close DOWN vs prev 100 -> c2c < 0
    gaps = {i: 0.02 for i in idxs}  # open UP +2% vs prev 100 -> gap > 0
    audit, _ = er.assemble_events(
        calendar_of([{"event_id": f"E{k}", "symbol": "NVDA", "day0_session": sess[i]}
                     for k, i in enumerate(idxs)]),
        getter_of({"NVDA": make_bars(sess, closes, gaps), "SMH": flat_bars(sess)}),
        universe=("NVDA",),
    )
    audit = audit.sort("day0_session")
    r8 = audit.row(8, named=True)  # 8 priors, all gapped UP
    assert r8["gap_sign"] == "pos" and r8["c2c_sign"] == "neg"  # they disagree
    assert r8["streak"] == 8 and r8["streak_level"] == "hi"  # counted by GAP, not c2c


# --------------------------------------------------------------------------- 5. cluster_ci


def test_cluster_ci_is_imported_from_sched_window() -> None:
    assert er.cluster_ci is sw.cluster_ci


def test_cluster_ci_clusters_by_event_date_golden() -> None:
    # Two event-DATES (clusters): A=[1,3] (S=4,n=2), B=[5,7,9] (S=21,n=3), mean=5.
    # ss = (4-10)^2 + (21-15)^2 = 72; se = sqrt(72)/5.
    vals = np.array([1.0, 3.0, 5.0, 7.0, 9.0])
    dates = np.array(["2024-01-10", "2024-01-10", "2024-02-20", "2024-02-20", "2024-02-20"])
    mean, lo, hi, n, ncl = er.cluster_ci(vals, dates)
    se = (72.0 ** 0.5) / 5.0
    assert (n, ncl) == (5, 2)
    assert mean == pytest.approx(5.0)
    assert lo == pytest.approx(5.0 - 1.96 * se) and hi == pytest.approx(5.0 + 1.96 * se)


def test_base_rate_cell_ci_matches_cluster_ci_on_two_dates() -> None:
    # Two symbols reporting the SAME two dates land in one bucket -> the cell CI equals
    # cluster_ci over those two event-date clusters (cross-sectional clustering). Flat
    # closes make every run-up EXACTLY 0.0 so all four share one tercile (no epsilon
    # split); only the day0+5 outcome is overridden per (symbol, date).
    sess = weekdays("2019-01-01", 500)
    i1, i2 = 300, 340
    a = [100.0] * len(sess)
    b = [100.0] * len(sess)
    a[i1 + 5] = 101.0  # NVDA d1_5 = +100 bps on date i1
    a[i2 + 5] = 103.0  # NVDA d1_5 = +300 bps on date i2
    b[i1 + 5] = 102.0  # AMD  d1_5 = +200 bps on date i1
    b[i2 + 5] = 104.0  # AMD  d1_5 = +400 bps on date i2
    bars = {"SMH": flat_bars(sess), "NVDA": make_bars(sess, a), "AMD": make_bars(sess, b)}
    cal = calendar_of(
        [{"symbol": "NVDA", "day0_session": sess[i1]}, {"symbol": "NVDA", "day0_session": sess[i2]},
         {"symbol": "AMD", "day0_session": sess[i1]}, {"symbol": "AMD", "day0_session": sess[i2]}]
    )
    audit, _ = er.assemble_events(cal, getter_of(bars), universe=("NVDA", "AMD"))
    scored = er.apply_cuts(audit, er.compute_cuts(audit, "SMH"))
    kept = scored.filter(pl.col("ret_d1_5").is_not_null())
    # all four share one (tercile, gap_sign) margin; check its clustered CI directly
    recs = er.compute_base_rates(scored)
    marg = [r for r in recs if r["kind"] == "margin" and r["window"] == "d1_5" and r["N"] == kept.height]
    assert marg, "expected a margin holding all four events"
    m = marg[0]
    exp_mean, exp_lo, _, n, ncl = er.cluster_ci(
        kept["ret_d1_5"].to_numpy().astype(float) * 1e4, kept["day0_session"].to_numpy()
    )
    assert m["n_event_dates"] == ncl == 2
    assert m["mean_bps"] == pytest.approx(round(exp_mean, 4))


# --------------------------------------------------------------------------- 6. seal


def test_seal_excludes_holdout_event_but_score_still_works(tmp_path) -> None:
    sess = weekdays("2019-01-01", 2000)  # spans into mid-2026
    closes = [100.0 * (1.0006 ** i) for i in range(len(sess))]
    bars = {"SMH": flat_bars(sess), "NVDA": make_bars(sess, closes, {i: 0.01 for i in range(300, len(sess), 40)})}
    # a train event and a holdout event (day0 >= 2026-06-01)
    train_idx = next(i for i, s in enumerate(sess) if s >= "2020-06-01")
    hold_idx = next(i for i, s in enumerate(sess) if s >= "2026-07-01")
    idxs = list(range(300, hold_idx + 1, 40))
    cal = calendar_of([{"event_id": f"E{k}", "symbol": "NVDA", "day0_session": sess[i]}
                       for k, i in enumerate(idxs)])
    getter = getter_of(bars)
    audit, _ = er.assemble_events(cal, getter, universe=("NVDA",))
    assert audit.filter(pl.col("day0_session") >= "2026-06-01").height == 0  # holdout stripped
    assert set(audit["split"].unique().to_list()) <= {"train", "validate"}

    # the holdout event is still SCOREABLE read-only against the frozen atlas.
    er.compute_atlas(cal, getter, out_dir=tmp_path, universe=("NVDA",))
    hold_sess = sess[hold_idx]
    res = er.score_event("NVDA", hold_sess, getter, cal, out_dir=tmp_path)
    assert res["day0_session"] == hold_sess
    assert res["runup_tercile"] in er.TERCILE_LABELS
    _ = train_idx


# --------------------------------------------------------------------- 6b. outcome containment


def test_outcome_crossing_seal_excluded_but_scoreable(tmp_path) -> None:
    # Literal-seal: an event enters estimation ONLY if day0 + 20 trading sessions <=
    # VALIDATE end (2026-05-31). A late-May-2026 event whose +20d window crosses the
    # boundary is excluded ENTIRELY (both windows nulled), an earlier one is included,
    # and the late one still scores read-only.
    sess = weekdays("2019-01-01", 2000)  # spans past mid-2026
    closes = [100.0 * (1.0005 ** i) for i in range(len(sess))]
    early_idxs = list(range(300, 1500, 40))  # all contained (<= 2024)
    late_idx = next(i for i, s in enumerate(sess) if s >= "2026-05-20")
    assert sess[late_idx] <= "2026-05-31"                       # day0 is pre-holdout
    assert sess[late_idx + er.MAX_OUTCOME_H] > "2026-05-31"     # but +20 crosses the seal
    all_idxs = [*early_idxs, late_idx]
    gaps = {i: 0.01 for i in all_idxs}
    bars = {"SMH": flat_bars(sess), "NVDA": make_bars(sess, closes, gaps)}
    cal = calendar_of([{"event_id": f"E{k}", "symbol": "NVDA", "day0_session": sess[i]}
                       for k, i in enumerate(all_idxs)])
    getter = getter_of(bars)
    audit, _ = er.assemble_events(cal, getter, universe=("NVDA",))

    late = audit.filter(pl.col("day0_session") == sess[late_idx]).row(0, named=True)
    assert late["status"] == "outcome_crosses_seal"
    assert late["ret_d1_5"] is None and late["ret_d1_20"] is None  # both windows excluded
    early = audit.filter(pl.col("day0_session") == sess[early_idxs[-1]]).row(0, named=True)
    assert early["status"] == "ok"

    # both outcome windows share ONE event set (ok events have both outcomes non-null)
    ok = audit.filter(pl.col("status") == "ok")
    assert (ok.filter(pl.col("ret_d1_5").is_not_null()).height
            == ok.filter(pl.col("ret_d1_20").is_not_null()).height == ok.height)
    # the crossed event never enters the frozen tercile distribution
    cuts = er.compute_cuts(audit, "SMH")
    assert cuts["n_estimation_events"] == ok.height

    er.compute_atlas(cal, getter, out_dir=tmp_path, universe=("NVDA",))
    assert "outcome_crosses_seal" in er.atlas_md_path(tmp_path).read_text(encoding="utf-8")

    res = er.score_event("NVDA", sess[late_idx], getter, cal, out_dir=tmp_path)
    assert res["day0_session"] == sess[late_idx] and res["bucket_id"]


# --------------------------------------------------------------------------- 7. determinism + no-write


def test_atlas_deterministic_two_runs(tmp_path) -> None:
    sess = weekdays("2019-01-01", 800)
    up = [100.0 * (1.002 ** i) for i in range(len(sess))]
    flat = [100.0 + (i % 5) * 0.03 for i in range(len(sess))]
    bars = {"SMH": flat_bars(sess), "NVDA": make_bars(sess, up, {i: 0.01 for i in range(300, len(sess), 45)}),
            "AMD": make_bars(sess, flat)}
    cal_rows = []
    for sym in ("NVDA", "AMD"):
        s = er.DailySeries(bars[sym])
        for k, idx in enumerate(range(300, len(s.sessions) - 25, 45)):
            cal_rows.append({"event_id": f"{sym}-{k}", "symbol": sym, "day0_session": s.sessions[idx]})
    cal = calendar_of(cal_rows)
    getter = getter_of(bars)
    d1, d2 = tmp_path / "a", tmp_path / "b"
    er.compute_atlas(cal, getter, out_dir=d1, universe=er.UNIVERSE)
    er.compute_atlas(cal, getter, out_dir=d2, universe=er.UNIVERSE)
    assert pl.read_parquet(er.events_path(d1)).equals(pl.read_parquet(er.events_path(d2)))


def test_score_writes_nothing(tmp_path) -> None:
    sess = weekdays("2019-01-01", 800)
    closes = [100.0 * (1.001 ** i) for i in range(len(sess))]
    bars = {"SMH": flat_bars(sess), "NVDA": make_bars(sess, closes, {i: 0.01 for i in range(300, len(sess), 45)})}
    cal_rows = [{"event_id": f"E{k}", "symbol": "NVDA", "day0_session": sess[i]}
                for k, i in enumerate(range(300, len(sess) - 25, 45))]
    cal = calendar_of(cal_rows)
    getter = getter_of(bars)
    er.compute_atlas(cal, getter, out_dir=tmp_path, universe=("NVDA",))
    before = {p.name: p.stat().st_mtime_ns for p in tmp_path.iterdir()}
    er.score_event("NVDA", cal_rows[-1]["day0_session"], getter, cal, out_dir=tmp_path)
    after = {p.name: p.stat().st_mtime_ns for p in tmp_path.iterdir()}
    assert before == after  # no new files, nothing rewritten


def test_score_refuses_without_atlas(tmp_path) -> None:
    sess = weekdays("2019-01-01", 400)
    bars = {"SMH": flat_bars(sess), "NVDA": make_bars(sess, [100.0 + i * 0.1 for i in range(len(sess))])}
    with pytest.raises(FileNotFoundError, match="atlas artifacts"):
        er.score_event("NVDA", sess[300], getter_of(bars), calendar_of([]), out_dir=tmp_path)


# --------------------------------------------------------------------------- 8. NO-COST-MODEL


def test_no_cost_model_string_in_atlas_and_score(tmp_path) -> None:
    sess = weekdays("2019-01-01", 700)
    closes = [100.0 * (1.001 ** i) for i in range(len(sess))]
    bars = {"SMH": flat_bars(sess), "NVDA": make_bars(sess, closes, {i: 0.01 for i in range(300, len(sess), 45)})}
    cal_rows = [{"event_id": f"E{k}", "symbol": "NVDA", "day0_session": sess[i]}
                for k, i in enumerate(range(300, len(sess) - 25, 45))]
    cal = calendar_of(cal_rows)
    getter = getter_of(bars)
    er.compute_atlas(cal, getter, out_dir=tmp_path, universe=("NVDA",))
    assert er.NO_COST_MODEL in er.atlas_md_path(tmp_path).read_text(encoding="utf-8")
    res = er.score_event("NVDA", cal_rows[-1]["day0_session"], getter, cal, out_dir=tmp_path)
    assert er.NO_COST_MODEL in er.format_score(res)


# --------------------------------------------------------------------------- 9. missing bars


def test_missing_bars_dropped_with_reason_never_silent() -> None:
    sess = weekdays("2019-01-01", 400)
    bars = {"SMH": flat_bars(sess), "NVDA": make_bars(sess, [100.0 + i * 0.1 for i in range(len(sess))])}
    non_trading = "2020-01-04"  # a Saturday: in-range (pre-holdout) but absent from bars
    assert date.fromisoformat(non_trading).weekday() >= 5
    cal = calendar_of(
        [
            {"symbol": "NVDA", "day0_session": sess[300]},   # ok
            {"symbol": "AMD", "day0_session": sess[300]},    # no bars for AMD at all
            {"symbol": "NVDA", "day0_session": non_trading},  # day0 not in NVDA series
        ]
    )
    audit, _ = er.assemble_events(cal, getter_of(bars), universe=("NVDA", "AMD"))
    by = {(r["symbol"], r["day0_session"]): r["status"] for r in audit.iter_rows(named=True)}
    assert by[("AMD", sess[300])] == "no_bars"
    assert by[("NVDA", non_trading)] == "no_day0_bar"
    assert by[("NVDA", sess[300])] == "ok"


def test_short_runup_history_flagged_not_silent() -> None:
    # day0 too early for a 60-day run-up -> excluded from cells with an explicit reason,
    # but its c2c still feeds later streaks.
    sess = weekdays("2019-01-01", 400)
    closes = [100.0 + i * 0.1 for i in range(len(sess))]
    bars = {"SMH": flat_bars(sess), "NVDA": make_bars(sess, closes)}
    cal = calendar_of([{"symbol": "NVDA", "day0_session": sess[10]}])  # only 10 priors
    audit, _ = er.assemble_events(cal, getter_of(bars), universe=("NVDA",))
    r = audit.row(0, named=True)
    assert r["status"] == "short_runup_history"
    assert r["runup_tercile"] is None
    assert r["c2c"] is not None  # reaction still measured


# --------------------------------------------------------------------------- basket fallback


def test_basket_fallback_when_no_smh() -> None:
    sess = weekdays("2019-01-01", 400)
    bars = {sym: make_bars(sess, [100.0 * (1.001 ** i) for i in range(len(sess))])
            for sym in ("NVDA", "AMD", "MU")}  # NO SMH
    cal = calendar_of([{"symbol": "NVDA", "day0_session": sess[300]}])
    audit, ref_source = er.assemble_events(cal, getter_of(bars), universe=("NVDA", "AMD", "MU"))
    assert ref_source == "ew_semi_basket"
    assert audit.row(0, named=True)["ref_source"] == "ew_semi_basket"


# --------------------------------------------------------------------------- contrast: NVDA vs MU


def _crowded_symbol(sess, *, gap: float, forward: float, event_stride: int = 40):
    """A high-run-up (T3) symbol: strong global uptrend for the 60d run-up, with each
    event's day0 gap set to ``gap`` and its forward day+1..+20 window bent by
    ``forward`` (>0 continuation up, <0 regime-break down). Events start at idx 300."""
    n = len(sess)
    closes = [100.0 * (1.004 ** i) for i in range(n)]  # ~T3 vs flat SMH
    gaps: dict[int, float] = {}
    for idx in range(300, n - 30, event_stride):
        gaps[idx] = gap
        base = closes[idx]
        for k in range(1, 21):  # bend the forward window, then it resumes trend
            closes[idx + k] = base * (1.0 + forward) ** (k / 20.0)
    return make_bars(sess, closes, gaps)


def test_crowded_up_vs_down_bucket_contrast(tmp_path) -> None:
    # NVDA-2023/24 class: crowded (T3) + POSITIVE gap -> continuation up.
    # MU-2026 class:      crowded (T3) + NEGATIVE gap -> regime break down.
    sess = weekdays("2019-01-01", 900)
    nvda = _crowded_symbol(sess, gap=0.03, forward=0.06)     # gap+, drift up
    mu = _crowded_symbol(sess, gap=-0.03, forward=-0.06)     # gap-, drift down
    # 6 flat fillers (run-up 0) vs 2 crowded (run-up ~+27%): fillers are 75% of events
    # so the 67th-pct tercile edge sits in filler territory and the crowded names land
    # unambiguously in T3.
    fillers = ("AMD", "QCOM", "TXN", "INTC", "AMAT", "LRCX")
    bars = {"SMH": flat_bars(sess), "NVDA": nvda, "MU": mu}
    for f in fillers:
        bars[f] = flat_bars(sess)
    cal_rows = []
    for sym in ("NVDA", "MU", *fillers):
        s = er.DailySeries(bars[sym])
        for k, idx in enumerate(range(300, len(s.sessions) - 30, 40)):
            cal_rows.append({"event_id": f"{sym}-{k}", "symbol": sym, "day0_session": s.sessions[idx]})
    cal = calendar_of(cal_rows)
    getter = getter_of(bars)
    er.compute_atlas(cal, getter, out_dir=tmp_path, universe=er.UNIVERSE)

    # score an early NVDA event (<8 priors -> na -> margin lookup) and an early MU event
    up_ev = next(r for r in cal_rows if r["symbol"] == "NVDA" and r["event_id"].endswith("-4"))
    dn_ev = next(r for r in cal_rows if r["symbol"] == "MU" and r["event_id"].endswith("-4"))
    up = er.score_event("NVDA", up_ev["day0_session"], getter, cal, out_dir=tmp_path)
    dn = er.score_event("MU", dn_ev["day0_session"], getter, cal, out_dir=tmp_path)

    assert up["runup_tercile"] == "T3" and up["gap_sign"] == "pos"
    assert dn["runup_tercile"] == "T3" and dn["gap_sign"] == "neg"
    assert up["bucket_id"] != dn["bucket_id"]
    # the whole point: crowded+up continues (>0), crowded+down breaks (<0)
    up_d20 = up["base_rates"]["d1_20"]["mean_bps"]
    dn_d20 = dn["base_rates"]["d1_20"]["mean_bps"]
    assert up_d20 > 0 and dn_d20 < 0
    assert up["analogs"] and all(a["symbol"] == "NVDA" for a in up["analogs"])
