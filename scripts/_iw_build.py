"""DR-X6 recipe steps C/D: combine IVV (SPX) + QQQ NPORT-P (NDX) raw pulls into the final
point-in-time index-weights dataset, resolve NDX tickers via a name/title crosswalk, run the
mandatory QA (sum-of-weights spot checks + per-name coverage for the 33-name universe), and
write the two deliverables.

Ticker resolution for NDX (mechanical, no invented mappings):
  0. Use the filing's own <identifiers><ticker> when present (rare - mostly derivatives).
  1. IVV point-in-time history: normalize(title) or normalize(name) looked up against a
     name -> [(asof_date, ticker), ...] history built from ALL fetched IVV (Ticker,Name)
     equity rows (BlackRock-sourced, official), resolved AS OF the QQQ filing's own
     repPdDate (latest IVV observation with asof_date <= repPdDate; step function, no
     interpolation, same convention as letf_aum_anchors.csv). This is what a static
     singleton map gets wrong for genuine ticker-rename events: e.g. BlackRock updated the
     display name "FACEBOOK CLASS A INC" -> "META PLATFORMS INC CLASS A" on 2021-10-29,
     eight months before the ticker itself changed FB -> META on 2022-06-30, so the SAME
     exact name string is legitimately ambiguous across time but NOT ambiguous as of any
     single date - point-in-time resolution recovers the period-correct ticker instead of
     either (a) refusing to map it (a plain singleton-only map would drop it as ambiguous)
     or (b) silently mapping every historical quarter to today's ticker (what a
     current-snapshot-only source like SEC's company_tickers.json would do, wrongly,
     for FB-era quarters). Confirmed present in this exact form for 8 names via IVV pull
     (FISV->FI, BK->BNY, WLTW->WTW, BLL->BALL, PEAK->DOC, HOLX->'-', FB->META, ECHO->SATS).
  2. Same-date-unaware exact match against SEC's own free bulk reference
     `company_tickers.json` (ticker/title/CIK) for names IVV never carried (e.g. NDX-only
     constituents such as foreign private issuers not in the S&P 500/IVV universe). SEC
     titles get one mechanical cleanup first: EDGAR appends a trailing "/XX" state- or
     country-of-incorporation qualifier to disambiguate same-named registrants (e.g.
     "APPLIED MATERIALS INC /DE", confirmed present for 79/10426 SEC entries) - this
     qualifier is stripped before normalizing since it is never part of the traded name and
     otherwise silently blocks an exact match (this was AMAT's entire 0/27 failure: IVV's own
     name for AMAT is itself idiosyncratic, "APPLIED MATERIAL INC" (singular, BlackRock's
     spelling, confirmed consistent across all 78 months), which doesn't match QQQ's correct
     "Applied Materials, Inc." either - only the /DE-stripped SEC entry closes this gap).
     Only used when the (cleaned) title maps to a single distinct ticker (SEC is a single
     current-day snapshot with no history, so no point-in-time resolution is possible here -
     an SEC name collision is left unmapped rather than guessed).
  3. Core-name fallback: strip a trailing " CLASS <letter>" token from both sides and retry
     steps 1-2 (history-aware for IVV, singleton-only for SEC), but ONLY if the stripped core
     name maps to a single distinct ticker (this is a secondary net for any remaining
     class-suffix formatting mismatch; a genuinely ambiguous core name like "ALPHABET INC"
     (GOOG vs GOOGL, both real, both concurrently existing, both class-suffixed on both
     sides already) is correctly left to step 1 exact matching instead of guessed - collapsing
     class off a concurrently-multi-class name is exactly the case this fallback must NOT do).
  Anything still unresolved keeps ticker=null and is counted (not dropped - the row and its
  weight remain in the output so weight-sum QA reflects true total capture).
"""
import bisect
import csv
import json
import re
from collections import defaultdict

import polars as pl

SCRATCH = "scratch"
IVV_RAW = f"{SCRATCH}/iw_ivv_raw.csv"
QQQ_RAW = f"{SCRATCH}/iw_qqq_raw.csv"
SEC_TICKERS = f"{SCRATCH}/company_tickers.json"

OUT_PARQUET = "data/external/index_weights_monthly.parquet"
OUT_PROVENANCE = "data/external/index_weights_provenance.md"

UNIVERSE = ["NVDA", "TSLA", "AMD", "MU", "GOOGL", "AAPL", "MSFT", "AMZN", "META", "AVGO",
            "NFLX", "ADBE", "CSCO", "INTC", "QCOM", "INTU", "TXN", "AMAT", "MRVL", "LRCX",
            "KLAC", "PLTR", "AMGN", "GILD", "VRTX", "REGN", "ISRG", "PEP", "COST", "SBUX",
            "MDLZ", "TMUS", "CMCSA", "HON", "ADP", "BKNG", "ABNB", "PANW", "CDNS", "SNPS"]

# ---------------- name normalization ----------------
def normalize_name(s):
    if not s:
        return ""
    s = s.upper()
    s = s.replace("&", " AND ")
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


CLASS_RE = re.compile(r"\s+CLASS [A-Z]$")


def strip_class(s):
    return CLASS_RE.sub("", s)


SEC_SUFFIX_RE = re.compile(r"\s*/[A-Za-z]{2}\s*$")


def clean_sec_title(t):
    """Strip EDGAR's trailing state/country-of-incorporation qualifier, e.g.
    'APPLIED MATERIALS INC /DE' -> 'APPLIED MATERIALS INC'. Confirmed on 79/10426 entries."""
    return SEC_SUFFIX_RE.sub("", t)


def build_singleton_map(pairs):
    """pairs: iterable of (normalized_name, ticker). Returns dict name -> ticker for
    names with exactly one distinct ticker; also returns the raw multi-map for diagnostics."""
    raw = defaultdict(set)
    for name, ticker in pairs:
        if name and ticker:
            raw[name].add(ticker)
    singleton = {k: next(iter(v)) for k, v in raw.items() if len(v) == 1}
    return singleton, raw


def build_history(triples):
    """triples: iterable of (normalized_name, asof_date_iso, ticker). Returns
    name -> (sorted_dates_list, tickers_list_aligned) for as-of (backward) lookup via bisect."""
    raw = defaultdict(list)
    for name, date, ticker in triples:
        if name and ticker and date:
            raw[name].append((date, ticker))
    hist = {}
    for name, pairs in raw.items():
        pairs.sort(key=lambda p: p[0])
        dates = [p[0] for p in pairs]
        tickers = [p[1] for p in pairs]
        hist[name] = (dates, tickers)
    return hist


def build_core_history(triples):
    """Class-stripped, time-aware history - SAFE variant. A class-suffix filer inconsistency
    (e.g. QQQ's own NPORT-P title drops ', Class A' for exactly one quarter - confirmed for
    Meta Platforms at repPdDate=2021-12-31) must not fall through to a non-time-aware fallback
    just because the class token is momentarily missing on the QQQ side. But stripping class
    must NOT be allowed to merge two concurrently-existing, genuinely-distinct securities
    (GOOG/GOOGL) into one history, where "latest ticker as of date" would be ill-defined/
    order-dependent. Resolution: only build a stripped-key history entry when EVERY
    contributing row across the whole IVV pull shares the same underlying full (unstripped)
    name - i.e. the stripped key never actually needed to disambiguate two different classes,
    it is a single class-A-only security with an inconsistently-present suffix. Names with
    >1 distinct full name behind the same stripped key (Alphabet) are excluded here entirely."""
    full_names_per_stripped = defaultdict(set)
    for name, _date, _ticker in triples:
        full_names_per_stripped[strip_class(name)].add(name)
    safe_stripped = {k for k, v in full_names_per_stripped.items() if len(v) == 1}
    safe_triples = [(strip_class(name), date, ticker) for name, date, ticker in triples
                     if strip_class(name) in safe_stripped]
    return build_history(safe_triples)


def resolve_asof(hist, name, target_date):
    """Latest (date, ticker) with date <= target_date; None if name unseen or target_date
    precedes every IVV observation for that name (no backward extrapolation)."""
    entry = hist.get(name)
    if not entry:
        return None
    dates, tickers = entry
    idx = bisect.bisect_right(dates, target_date) - 1
    if idx < 0:
        return None
    return tickers[idx]


# ---------------- load IVV (SPX) ----------------
def load_ivv():
    rows = []
    ivv_name_triples = []  # (normalized_name, asof_date, ticker) - for PIT history
    with open(IVV_RAW, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            asset_class = r["asset_class"]
            ticker = r["ticker"].strip()
            name = r["name"].strip()
            if asset_class == "Equity" and ticker:
                ivv_name_triples.append((normalize_name(name), r["asof_date"], ticker))
            if asset_class != "Equity":
                continue
            try:
                w = float(r["weight_pct"]) / 100.0
            except (ValueError, TypeError):
                continue
            rows.append({
                "index": "SPX",
                "asof_date": r["asof_date"],
                "ticker": ticker,
                "weight": w,
                "source": "varnish",
                "source_ref": r["source_url"],
            })
    return rows, ivv_name_triples


# ---------------- load SEC company_tickers.json ----------------
def load_sec_ticker_map():
    with open(SEC_TICKERS, encoding="utf-8") as f:
        d = json.load(f)
    pairs = [(normalize_name(clean_sec_title(v["title"])), v["ticker"]) for v in d.values()]
    return pairs


# ---------------- load QQQ (NDX) + resolve tickers ----------------
def load_qqq(ivv_hist, ivv_core_hist, sec_exact, core_map):
    rows = []
    unmapped_samples = []
    n_total = 0
    n_direct = 0
    n_ivv_pit = 0
    n_ivv_core_pit = 0
    n_sec_exact = 0
    n_core = 0
    n_unmapped = 0
    with open(QQQ_RAW, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            n_total += 1
            try:
                w = float(r["pctVal"]) / 100.0
            except (ValueError, TypeError):
                continue
            target_date = r["repPdDate"]
            ticker = (r["ticker_direct"] or "").strip() or None
            if ticker:
                n_direct += 1
            else:
                title_n = normalize_name(r["title"])
                name_n = normalize_name(r["name"])
                title_c, name_c = strip_class(title_n), strip_class(name_n)
                ticker = resolve_asof(ivv_hist, title_n, target_date) or resolve_asof(ivv_hist, name_n, target_date)
                if ticker:
                    n_ivv_pit += 1
                else:
                    # safe time-aware core fallback BEFORE the non-time-aware SEC snapshot -
                    # recovers quarters where QQQ's own title momentarily drops the class
                    # suffix (confirmed: Meta Platforms at repPdDate=2021-12-31) without
                    # risking the GOOG/GOOGL concurrent-collision problem (see
                    # build_core_history docstring).
                    ticker = resolve_asof(ivv_core_hist, title_c, target_date) or resolve_asof(ivv_core_hist, name_c, target_date)
                    if ticker:
                        n_ivv_core_pit += 1
                    else:
                        ticker = sec_exact.get(title_n) or sec_exact.get(name_n)
                        if ticker:
                            n_sec_exact += 1
                        else:
                            # plain (non-time-aware) core fallback, singleton-ticker-only
                            ticker = core_map.get(title_c) or core_map.get(name_c)
                            if ticker:
                                n_core += 1
                            else:
                                n_unmapped += 1
                                if len(unmapped_samples) < 80:
                                    unmapped_samples.append((r["repPdDate"], r["name"], r["title"], r["assetCat"], r["cusip"]))
            rows.append({
                "index": "NDX",
                "asof_date": r["repPdDate"],
                "ticker": ticker,
                "weight": w,
                "source": "nport",
                "source_ref": r["accession"],
            })
    stats = {"n_total": n_total, "n_direct": n_direct, "n_ivv_pit": n_ivv_pit,
              "n_ivv_core_pit": n_ivv_core_pit, "n_sec_exact": n_sec_exact,
              "n_core": n_core, "n_unmapped": n_unmapped}
    return rows, stats, unmapped_samples


def main():
    ivv_rows, ivv_name_triples = load_ivv()
    print(f"IVV equity rows loaded: {len(ivv_rows)}")

    sec_pairs = load_sec_ticker_map()
    print(f"SEC company_tickers.json entries: {len(sec_pairs)}")

    # IVV: point-in-time history (as-of resolution - see module docstring for the FB/META case)
    ivv_hist = build_history(ivv_name_triples)
    ivv_core_hist = build_core_history(ivv_name_triples)
    ivv_name_pairs = [(n, t) for n, _, t in ivv_name_triples]
    _, ivv_raw_multi = build_singleton_map(ivv_name_pairs)  # diagnostics only (ambiguous names)

    # SEC: single current-day snapshot, singleton-only (no date axis to resolve on)
    sec_exact, sec_raw_multi = build_singleton_map(sec_pairs)

    # core map (class-stripped fallback), singleton-only from both sources, IVV wins ties
    ivv_core_pairs = [(strip_class(n), t) for n, t in ivv_name_pairs]
    sec_core_pairs = [(strip_class(n), t) for n, t in sec_pairs]
    ivv_core, _ = build_singleton_map(ivv_core_pairs)
    sec_core, _ = build_singleton_map(sec_core_pairs)
    core_map = dict(sec_core)
    core_map.update(ivv_core)

    print(f"IVV PIT-history distinct names: {len(ivv_hist)} (ambiguous/renamed: {len({k: v for k, v in ivv_raw_multi.items() if len(v) > 1})})")
    print(f"IVV core (class-stripped) PIT-history distinct names: {len(ivv_core_hist)}")
    print(f"SEC exact-name map size: {len(sec_exact)} (raw distinct names: {len(sec_raw_multi)})")

    qqq_rows, qqq_stats, unmapped_samples = load_qqq(ivv_hist, ivv_core_hist, sec_exact, core_map)
    print(f"QQQ rows loaded: {len(qqq_rows)}; stats: {qqq_stats}")

    all_rows = ivv_rows + qqq_rows
    df = pl.DataFrame(all_rows, schema={"index": pl.Utf8, "asof_date": pl.Utf8, "ticker": pl.Utf8,
                                         "weight": pl.Float64, "source": pl.Utf8, "source_ref": pl.Utf8})
    df = df.sort(["index", "asof_date", "ticker"])
    df.write_parquet(OUT_PARQUET)
    print(f"Wrote {OUT_PARQUET}: {df.height} rows")

    # non-singleton IVV names (diagnostic transparency - names where the same normalized
    # string mapped to >1 distinct ticker somewhere across the 78-month pull)
    ivv_ambiguous = {k: sorted(v) for k, v in ivv_raw_multi.items() if len(v) > 1}

    stats = {
        "ivv_equity_rows": len(ivv_rows),
        "sec_ticker_entries": len(sec_pairs),
        "ivv_hist_names": len(ivv_hist),
        "ivv_raw_distinct_names": len(ivv_raw_multi),
        "sec_exact_map_size": len(sec_exact),
        "qqq_stats": qqq_stats,
        "ivv_ambiguous_names": ivv_ambiguous,
        "unmapped_samples": [
            {"repPdDate": a, "name": b, "title": c, "assetCat": d, "cusip": e}
            for (a, b, c, d, e) in unmapped_samples
        ],
    }
    with open(f"{SCRATCH}/iw_build_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"Wrote {SCRATCH}/iw_build_stats.json")

    return df, qqq_stats, unmapped_samples, ivv_rows, qqq_rows


if __name__ == "__main__":
    main()
