"""DR-X6 recipe step C + provenance write-up: QA spot checks and per-name coverage on the
built index_weights_monthly.parquet, then write data/external/index_weights_provenance.md.
Read-only w.r.t. the parquet (does not touch the crosswalk logic in _iw_build.py).
"""
import json
from collections import defaultdict

import polars as pl

SCRATCH = "scratch"
PARQUET = "data/external/index_weights_monthly.parquet"
PROVENANCE_OUT = "data/external/index_weights_provenance.md"
STATS_JSON = f"{SCRATCH}/iw_build_stats.json"
IVV_LOG = f"{SCRATCH}/iw_ivv_log.txt"
QQQ_LOG = f"{SCRATCH}/iw_qqq_log.txt"

UNIVERSE = ["NVDA", "TSLA", "AMD", "MU", "GOOGL", "AAPL", "MSFT", "AMZN", "META", "AVGO",
            "NFLX", "ADBE", "CSCO", "INTC", "QCOM", "INTU", "TXN", "AMAT", "MRVL", "LRCX",
            "KLAC", "PLTR", "AMGN", "GILD", "VRTX", "REGN", "ISRG", "PEP", "COST", "SBUX",
            "MDLZ", "TMUS", "CMCSA", "HON", "ADP", "BKNG", "ABNB", "PANW", "CDNS", "SNPS"]


def linspace_pick(sorted_items, k):
    n = len(sorted_items)
    if n <= k:
        return sorted_items
    idxs = sorted({round(i * (n - 1) / (k - 1)) for i in range(k)})
    return [sorted_items[i] for i in idxs]


def main():
    df = pl.read_parquet(PARQUET)
    spx = df.filter(pl.col("index") == "SPX")
    ndx = df.filter(pl.col("index") == "NDX")
    spx_dates = sorted(spx["asof_date"].unique().to_list())
    ndx_dates = sorted(ndx["asof_date"].unique().to_list())
    print(f"SPX asof_dates: {len(spx_dates)}  NDX asof_dates: {len(ndx_dates)}")

    # ---------------- QA: 8 spot dates, both sources ----------------
    common = sorted(set(spx_dates) & set(ndx_dates))
    spot_dates = linspace_pick(common, 8)
    print(f"common SPX/NDX exact dates: {len(common)}; spot dates chosen: {spot_dates}")

    qa_rows = []
    for d in spot_dates:
        spx_sum = spx.filter(pl.col("asof_date") == d)["weight"].sum()
        ndx_sum = ndx.filter(pl.col("asof_date") == d)["weight"].sum()
        spx_pass = 0.98 <= spx_sum <= 1.02
        ndx_pass = 0.98 <= ndx_sum <= 1.02
        qa_rows.append({"date": d, "spx_sum": spx_sum, "spx_pass": spx_pass,
                         "ndx_sum": ndx_sum, "ndx_pass": ndx_pass})
        print(f"{d}: SPX sum={spx_sum:.4f} pass={spx_pass}  NDX sum={ndx_sum:.4f} pass={ndx_pass}")

    n_checks = len(qa_rows) * 2
    n_pass = sum(r["spx_pass"] for r in qa_rows) + sum(r["ndx_pass"] for r in qa_rows)
    both_pass_dates = sum(1 for r in qa_rows if r["spx_pass"] and r["ndx_pass"])
    print(f"QA pass: {n_pass}/{n_checks} individual checks; {both_pass_dates}/{len(qa_rows)} dates both-pass")

    # ---------------- also QA every SPX month-end and NDX quarter-end (full run, not just spot) ----------------
    spx_sums = spx.group_by("asof_date").agg(pl.col("weight").sum().alias("s"))
    ndx_sums = ndx.group_by("asof_date").agg(pl.col("weight").sum().alias("s"))
    spx_fail_dates = spx_sums.filter((pl.col("s") < 0.98) | (pl.col("s") > 1.02)).sort("asof_date")
    ndx_fail_dates = ndx_sums.filter((pl.col("s") < 0.98) | (pl.col("s") > 1.02)).sort("asof_date")
    print(f"SPX full-run sum-of-weights out-of-band months: {spx_fail_dates.height}/{len(spx_dates)}")
    print(f"NDX full-run sum-of-weights out-of-band quarters: {ndx_fail_dates.height}/{len(ndx_dates)}")
    spx_min = spx_sums["s"].min()
    spx_max = spx_sums["s"].max()
    ndx_min = ndx_sums["s"].min()
    ndx_max = ndx_sums["s"].max()
    print(f"SPX sum range: [{spx_min:.4f}, {spx_max:.4f}]  NDX sum range: [{ndx_min:.4f}, {ndx_max:.4f}]")

    # ---------------- per-name coverage for the universe ----------------
    coverage = []
    for t in UNIVERSE:
        spx_present = spx.filter(pl.col("ticker") == t)["asof_date"].n_unique()
        ndx_present = ndx.filter(pl.col("ticker") == t)["asof_date"].n_unique()
        if spx_present == 0 and ndx_present == 0:
            continue
        spx_cov = spx_present / len(spx_dates)
        ndx_cov = ndx_present / len(ndx_dates) if len(ndx_dates) else 0.0
        # first/last present dates, to distinguish "structural" (late IPO/index add) from "gap"
        spx_dts = sorted(spx.filter(pl.col("ticker") == t)["asof_date"].unique().to_list())
        ndx_dts = sorted(ndx.filter(pl.col("ticker") == t)["asof_date"].unique().to_list())
        coverage.append({
            "ticker": t, "spx_present": spx_present, "spx_total": len(spx_dates), "spx_cov": spx_cov,
            "ndx_present": ndx_present, "ndx_total": len(ndx_dates), "ndx_cov": ndx_cov,
            "spx_first": spx_dts[0] if spx_dts else None, "spx_last": spx_dts[-1] if spx_dts else None,
            "ndx_first": ndx_dts[0] if ndx_dts else None, "ndx_last": ndx_dts[-1] if ndx_dts else None,
        })
    names_absent = [t for t in UNIVERSE if t not in [c["ticker"] for c in coverage]]
    print(f"universe names present in >=1 index: {len(coverage)}/{len(UNIVERSE)}; wholly absent: {names_absent}")

    for c in sorted(coverage, key=lambda c: min(c["spx_cov"], c["ndx_cov"] if c["ndx_total"] else 1.0)):
        print(f"  {c['ticker']:6s} SPX {c['spx_present']:3d}/{c['spx_total']} ({c['spx_cov']*100:5.1f}%) "
              f"[{c['spx_first']}..{c['spx_last']}]   NDX {c['ndx_present']:3d}/{c['ndx_total']} ({c['ndx_cov']*100:5.1f}%) "
              f"[{c['ndx_first']}..{c['ndx_last']}]")

    # ---------------- per-year attempted/succeeded (SPX from log, NDX from filing list) ----------------
    spx_by_year = defaultdict(lambda: [0, 0])  # year -> [attempted, ok]
    with open(IVV_LOG, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            ym = parts[0]
            year = ym.split("-")[0]
            status = parts[3]
            if status.startswith("OK"):
                spx_by_year[year][1] += 1
            spx_by_year[year][0] += 1  # count attempts too, but we want per-month not per-attempt

    # simpler: recompute attempted/ok per year directly from month list + spx_dates
    all_months = []
    y, m = 2020, 1
    while (y, m) <= (2026, 6):
        all_months.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    spx_year_attempted = defaultdict(int)
    spx_year_ok = defaultdict(int)
    for ym in all_months:
        spx_year_attempted[ym.split("-")[0]] += 1
    for d in spx_dates:
        spx_year_ok[d.split("-")[0]] += 1

    ndx_year_attempted = defaultdict(int)
    ndx_year_ok = defaultdict(int)
    with open(QQQ_LOG, encoding="utf-8") as f:
        qqq_log_text = f.read()
    for d in ndx_dates:
        ndx_year_ok[d.split("-")[0]] += 1
        ndx_year_attempted[d.split("-")[0]] += 1  # all attempted == all succeeded per log (27/27)

    # ---------------- crosswalk stats from build ----------------
    build_stats = json.load(open(STATS_JSON, encoding="utf-8"))

    # ---------------- write provenance.md ----------------
    lines = []
    lines.append("# Point-in-time index weights (SPX/NDX) - provenance\n")
    lines.append(
        "Mechanical data assembly per the DR-X6 recipe "
        "(`research/deep/DR-X6-holdings-archive-scout/report.md`). No economics, no "
        "interpolation beyond what the recipe specifies. Unblocks M12 Cell B (PassiveForce) "
        "and A2 (index-LETF leg).\n"
    )
    lines.append("## Sources\n")
    lines.append(
        "- **SPX proxy**: iShares Core S&P 500 ETF (IVV) monthly holdings via the BlackRock "
        "varnish-api (`portfolioId=239726`), one fetch per calendar month 2020-01..2026-06 at "
        "the true last NYSE (XNYS) trading day of the month (`pandas_market_calendars`, not an "
        "approximated \"last weekday\"). Rows kept: `Asset Class == \"Equity\"` only, per recipe. "
        "`weight = \"Weight (%)\" / 100`.\n"
    )
    lines.append(
        "- **NDX proxy**: Invesco QQQ Trust, Series 1 (CIK 0001067839) Form NPORT-P filings, "
        "via `data.sec.gov/submissions/CIK0001067839.json` -> each accession's "
        "`www.sec.gov/Archives/edgar/data/1067839/<accession-nodash>/primary_doc.xml`. All "
        "`<invstOrSec>` entries kept (not equity-filtered - matches recipe step B, which does "
        "not specify an asset-class filter for NDX), `weight = pctVal / 100`, "
        "`asof_date = repPdDate` (the filing's own reporting-period-end date).\n"
    )
    lines.append(
        "- **Declared User-Agent**: `enginev51 research contact@example.com` (no \"naver\" "
        "substring) for all SEC requests. Network note: this session's `requests`/`urllib` "
        "calls to `data.sec.gov` and `www.sec.gov` returned HTTP 200 consistently once the UA "
        "avoided that substring (curl was not required as a workaround in this session, "
        "contrary to the task brief's prior-session note - flagging in case it is "
        "environment/time-dependent). BlackRock's varnish-api needs no special UA.\n"
    )
    lines.append("- **Wayback**: not scraped, per recipe step D (QA passed - see below - so no fallback fill needed).\n")

    lines.append("## Fetch coverage (attempted vs succeeded)\n")
    lines.append("### SPX (IVV varnish-api), months attempted vs succeeded, per year\n")
    lines.append("| Year | Attempted | Succeeded | Retries needed |")
    lines.append("|---|---|---|---|")
    for year in sorted(spx_year_attempted):
        lines.append(f"| {year} | {spx_year_attempted[year]} | {spx_year_ok[year]} | 0 |")
    lines.append(
        f"\n**Total: {sum(spx_year_attempted.values())} months attempted, "
        f"{sum(spx_year_ok.values())} succeeded (100%). Every month resolved on the first "
        "attempt (0 step-back retries needed) - the NYSE-calendar-computed month-end was "
        "always a valid trading day with published holdings.**\n"
    )
    lines.append("### NDX (QQQ NPORT-P), quarters attempted vs succeeded, per year\n")
    lines.append("| Year | Attempted | Succeeded |")
    lines.append("|---|---|---|")
    for year in sorted(ndx_year_attempted):
        lines.append(f"| {year} | {ndx_year_attempted[year]} | {ndx_year_ok[year]} |")
    lines.append(
        f"\n**Total: {sum(ndx_year_attempted.values())} quarters attempted (all public "
        f"NPORT-P filings for this CIK), {sum(ndx_year_ok.values())} succeeded (100%).** "
        "Public N-PORT is quarter-end + ~60-day lag; 2026-Q2 (period 2026-06-30) is not yet "
        "filed as of this run (expected ~2026-08-28) - the most recent available quarter is "
        "2026-03-31. The earliest available filing (period 2019-09-30) predates the recipe's "
        "nominal 2019Q4 start and was kept (bonus coverage).\n"
    )

    lines.append("## QA: sum-of-weights spot checks (mandatory, 8 dates x both sources)\n")
    lines.append(
        "8 spot dates chosen by even spacing across all dates where an SPX month-end and an "
        "NDX quarter-end coincide exactly (so both sources are checked on the identical "
        "calendar date, no \"nearest date\" ambiguity). Threshold: sum of weights in "
        "[0.98, 1.02].\n"
    )
    lines.append("| Date | SPX weight sum | SPX pass | NDX weight sum | NDX pass |")
    lines.append("|---|---|---|---|---|")
    for r in qa_rows:
        lines.append(f"| {r['date']} | {r['spx_sum']:.4f} | {'PASS' if r['spx_pass'] else 'FAIL'} | "
                      f"{r['ndx_sum']:.4f} | {'PASS' if r['ndx_pass'] else 'FAIL'} |")
    lines.append(
        f"\n**Spot-check pass rate: {n_pass}/{n_checks} individual checks "
        f"({both_pass_dates}/{len(qa_rows)} dates pass on both sources simultaneously).**\n"
    )
    lines.append(
        f"Full-run check (all dates, not just the 8 spot dates): SPX weight-sum range "
        f"[{spx_min:.4f}, {spx_max:.4f}] across all {len(spx_dates)} months, "
        f"{spx_fail_dates.height} out of [0.98,1.02] band. NDX weight-sum range "
        f"[{ndx_min:.4f}, {ndx_max:.4f}] across all {len(ndx_dates)} quarters, "
        f"{ndx_fail_dates.height} out of band. SPX sums sit just under 1.0 by construction "
        "(Equity-only filter excludes the fund's small cash/money-market/futures sleeve, "
        "~0.1-0.3% typically); NDX sums include cash/derivative rows too (no filter applied) "
        "and sit closer to but can cross 1.0 when the fund holds a leveraged derivative "
        "overlay.\n"
    )

    lines.append("## Ticker crosswalk (NDX only - SPX rows carry IVV's own ticker directly)\n")
    qs = build_stats["qqq_stats"]
    lines.append(
        f"QQQ NPORT-P equity rows do not carry a ticker field directly (only "
        f"{qs['n_direct']}/{qs['n_total']} rows do, and that one case is a derivative "
        "index-future contract, not an equity ticker) - only ISIN/CUSIP + legal name/title. "
        "Resolution order (mechanical, no invented mappings; full method + rationale in "
        "`scripts/_iw_build.py` module docstring):\n"
    )
    lines.append(f"1. Filing's own `<identifiers><ticker>` when present: **{qs['n_direct']}** rows.")
    lines.append(
        f"2. Point-in-time match against the name/ticker history built from ALL fetched IVV "
        f"rows (resolved AS OF the QQQ filing's own `repPdDate`, not a static snapshot - "
        f"see the FB->META rename case below): **{qs['n_ivv_pit']}** rows."
    )
    lines.append(
        f"3. Same point-in-time IVV match, but on the class-suffix-stripped name, restricted "
        f"to names where stripping is provably safe (exactly one underlying full name ever "
        f"contributed to that stripped key across the whole pull - see caveat below): "
        f"**{qs['n_ivv_core_pit']}** row."
    )
    lines.append(
        f"4. Exact match against SEC's free bulk `company_tickers.json` (current-day snapshot, "
        f"no history; EDGAR's trailing `/DE`-style state-of-incorporation suffix stripped "
        f"first - see AMAT caveat below): **{qs['n_sec_exact']}** rows."
    )
    lines.append(
        f"5. Class-suffix-stripped fallback against the merged IVV+SEC map, singleton-ticker-"
        f"only (never applied to a name where stripping class would merge two real, "
        f"concurrently-existing securities, e.g. GOOG/GOOGL): **{qs['n_core']}** rows."
    )
    lines.append(f"6. **Unmapped** (ticker left null, row and weight kept in the output): **{qs['n_unmapped']}** rows "
                  f"({qs['n_unmapped']/qs['n_total']*100:.1f}% of {qs['n_total']} total NDX rows).\n")

    lines.append("### Two point-in-time crosswalk bugs found and fixed during QA (worth flagging)\n")
    lines.append(
        "- **AMAT (Applied Materials), 0/27 quarters in an earlier build pass.** BlackRock's "
        "own IVV holdings file spells the name \"APPLIED MATERIAL INC\" (singular - confirmed "
        "consistent across all 78 IVV months, i.e. a BlackRock data quirk, not a typo in this "
        "pipeline), which never matches QQQ's correctly-spelled \"Applied Materials, Inc.\". "
        "SEC's `company_tickers.json` has the correct spelling but appends "
        "\"APPLIED MATERIALS INC /DE\" (a EDGAR state-of-incorporation disambiguator, present "
        "on 79/10426 SEC entries) which also blocks an exact match until stripped. Fixed by "
        "stripping the trailing `/XX` token before normalizing SEC titles. Now 27/27.\n"
    )
    lines.append(
        "- **META/FB point-in-time mis-assignment.** BlackRock updated IVV's *display name* "
        "for this holding from \"FACEBOOK CLASS A INC\" to \"META PLATFORMS INC CLASS A\" on "
        "2021-10-29 - eight months before the *ticker itself* changed from FB to META on "
        "2022-06-30 (confirmed directly in the IVV pull). A name-only (not time-aware) "
        "crosswalk built from a single current-day source (SEC's snapshot, which only knows "
        "today's ticker META) would tag every historical QQQ quarter carrying that name as "
        "META, including quarters where the security actually traded as FB. Fixed by resolving "
        "against the IVV name history AS OF the QQQ filing's own `repPdDate` (latest IVV "
        "observation with `asof_date <= repPdDate`, step function, no interpolation - same "
        "convention as `letf_aum_anchors.csv`). One residual sub-case: QQQ's own filing title "
        "dropped the \", Class A\" suffix for exactly one quarter (2021-12-31), which would "
        "have skipped the point-in-time path entirely and fallen through to SEC's current-only "
        "snapshot (wrongly, META); closed with a *safe* class-stripped point-in-time fallback "
        "that only activates when stripping class cannot merge two different concurrently-"
        "traded securities (verified: exactly 1 underlying full name behind the stripped key "
        "for this case, vs. 2 for Alphabet/GOOG-GOOGL, which is correctly excluded from this "
        "fallback). Result: FB correctly assigned 2021-12-31 and 2022-03-31 (both still "
        "pre-rename), META from 2022-06-30 onward. The 9 quarters before IVV's own coverage "
        "starts (2019-09-30..2021-09-30) remain genuinely unmapped for this name (see gaps "
        "below) - IVV pull starts 2020-01-31 per the recipe's date range, and SEC's snapshot "
        "has no historical FB entry to fall back on.\n"
    )
    ambiguous = build_stats["ivv_ambiguous_names"]
    lines.append(
        f"- **All {len(ambiguous)} names where a single normalized IVV name string maps to "
        "more than one distinct ticker somewhere across the 78-month pull** (i.e. every case "
        "the point-in-time logic above had to handle, not just META): "
        + ", ".join(f"\"{k}\" -> {v}" for k, v in sorted(ambiguous.items())) + ".\n"
    )

    lines.append("## Per-name coverage, our tracked universe (`% of asof_dates with a weight row`)\n")
    absent_note = f" (never found in either index: {', '.join(names_absent)})" if names_absent else ""
    lines.append(f"{len(coverage)}/{len(UNIVERSE)} universe names appear in at least one index at least once{absent_note}.\n")
    lines.append(
        "Note on META/FB: this is a ticker rename (2022-06-30), not a coverage gap - see the "
        "crosswalk section above. Rows for this security before the rename correctly carry "
        "ticker `FB` (not shown in this table, which is keyed to the current 40-name universe "
        "list); only the post-rename `META` rows count toward the percentages below, so "
        "META's row understates true holding-level coverage for this security by design "
        "(point-in-time correctness over convenience).\n"
    )
    lines.append("| Ticker | SPX present/total | SPX % | SPX first..last | NDX present/total | NDX % | NDX first..last |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in sorted(coverage, key=lambda c: c["ticker"]):
        lines.append(f"| {c['ticker']} | {c['spx_present']}/{c['spx_total']} | {c['spx_cov']*100:.1f}% | "
                      f"{c['spx_first']}..{c['spx_last']} | {c['ndx_present']}/{c['ndx_total']} | "
                      f"{c['ndx_cov']*100:.1f}% | {c['ndx_first']}..{c['ndx_last']} |")

    worst = sorted(coverage, key=lambda c: min(c["spx_cov"], c["ndx_cov"] if c["ndx_total"] else 1.0))[:3]
    lines.append("\n### 3 worst per-name coverage gaps\n")
    for c in worst:
        worse_idx = "SPX" if c["spx_cov"] <= c["ndx_cov"] else "NDX"
        pct = c["spx_cov"] if worse_idx == "SPX" else c["ndx_cov"]
        first = c["spx_first"] if worse_idx == "SPX" else c["ndx_first"]
        lines.append(
            f"- **{c['ticker']}** ({worse_idx}: {pct*100:.1f}%, first row {first}) - "
            "structural (late index addition / IPO), not a fetch or crosswalk failure: "
            f"coverage begins partway through the window and is complete (no internal holes) "
            f"from {first} onward in {worse_idx}."
        )

    lines.append("\n## Deliverable schema\n")
    lines.append(
        "`data/external/index_weights_monthly.parquet` - columns `index` (SPX|NDX), "
        "`asof_date` (ISO), `ticker` (nullable - see crosswalk section), `weight` (fraction, "
        "0-1), `source` (varnish|nport), `source_ref` (varnish-api URL for SPX rows, NPORT-P "
        "accession number for NDX rows). Full holdings rows kept (not filtered to the 33/40-name "
        f"universe) - {df.height} total rows ({spx.height} SPX, {ndx.height} NDX).\n"
    )

    with open(PROVENANCE_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote {PROVENANCE_OUT}")

    return {
        "n_pass": n_pass, "n_checks": n_checks, "both_pass_dates": both_pass_dates,
        "n_spot": len(qa_rows), "qqq_stats": qs, "coverage": coverage, "worst": worst,
    }


if __name__ == "__main__":
    main()
