"""One-off script: assemble the final letf_aum_anchors.csv from three sources:
  1. NPORT-P pulls (scratch/nport_anchors_raw.csv, produced by _letf_fetch_nport.py)
  2. stockanalysis.com current-day snapshots (scratch/sa_pages/sa_summary.csv + Corgi extras)
  3. Hand-verified press/aggregator anchors given in the M12 Cell A task spec (section c)

Dedupes on (ticker, asof_date, source_kind) keeping the first (NPORT-P prioritized).
Not part of the permanent codebase - throwaway data-assembly helper.
"""
import csv
import re

SCRATCH = "scratch"
OUT = "data/external/letf_aum_anchors.csv"

TODAY = "2026-07-17"


def parse_money(s):
    if not s or s.strip().lower() in ("n/a", "none", "-", ""):
        return None
    s = s.strip().replace("$", "").replace(",", "")
    mult = 1
    if s.endswith("B"):
        mult = 1e9
        s = s[:-1]
    elif s.endswith("M"):
        mult = 1e6
        s = s[:-1]
    elif s.endswith("K"):
        mult = 1e3
        s = s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


rows = []
seen = set()


def add(ticker, asof, aum, kind, url, note):
    if aum is None or asof is None:
        return
    key = (ticker, asof, kind, round(aum, 2))
    if key in seen:
        return
    seen.add(key)
    rows.append({"ticker": ticker, "asof_date": asof, "aum_usd": f"{aum:.2f}", "source_kind": kind, "source_url": url, "note": note})


# ---- 1. NPORT-P pulls (v2: seriesId-enumerated, seriesName-validated) ----
# Do NOT read nport_anchors_raw.csv (v1) - it is contaminated with sibling-fund rows.
import html as _html
with open(f"{SCRATCH}/nport_anchors_v2.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        try:
            aum = float(r["aum_usd"])
        except (KeyError, ValueError):
            continue
        note = _html.unescape(r.get("note", ""))
        add(r["ticker"], r["asof_date"], aum, "NPORT-P", r["source_url"], note)

# ---- 1b. Belt-and-suspenders: leftover confirmed NPORT pulls from earlier recon ----
LEFTOVER_NPORT = [
    # ticker, asof_date, aum_usd, accession(for url), cik
    # Note: AVGU $15,636,788.81 @2026-03-31 (task-spec anchor) is intentionally NOT hardcoded
    # here with a guessed accession - the bulk NPORT script's own "AVGU" phrase search
    # (GraniteShares 2x Long AVGO Daily) independently re-discovers the correct accession.
    ("MUU", "2026-04-30", 1419509532.39, "0001193125-26-287370", "1424958"),
    ("MULL", "2025-12-31", 83467778.00, "0001049169-26-000643", "1689873"),
    ("NVD", "2026-03-31", 88736992.10, "0001049169-26-001408", "1689873"),
]
for ticker, asof, aum, accession, cik in LEFTOVER_NPORT:
    acc_nodash = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/primary_doc.xml"
    add(ticker, asof, aum, "NPORT-P", url, "recon-confirmed prior to bulk pull")

# ---- 2. stockanalysis.com current snapshots ----
with open(f"{SCRATCH}/sa_pages/sa_summary.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if not r.get("ticker"):
            continue
        aum = parse_money(r.get("assets", ""))
        url = f"https://stockanalysis.com/etf/{r['ticker'].lower()}/"
        add(r["ticker"], TODAY, aum, "aggregator", url, "stockanalysis.com live snapshot")

# Corgi extras (fetched separately, not in sa_summary.csv)
CORGI_SNAPSHOT = [
    ("NVC", "$433.30K"), ("TESC", "$271.76K"), ("MIC", "$708.07K"),
    ("AMDC", "$1.53M"), ("NFX", "$233.00K"),
    # AVGC, LRCC, GOGL: "n/a"/None at fetch time - intentionally omitted, see provenance
]
for ticker, assets in CORGI_SNAPSHOT:
    aum = parse_money(assets)
    url = f"https://stockanalysis.com/etf/{ticker.lower()}/"
    add(ticker, TODAY, aum, "aggregator", url, "stockanalysis.com live snapshot (Corgi ETF Trust I, new fund)")

# GOU (fetched separately, not in sa_summary.csv)
add("GOU", TODAY, 10.75e6, "aggregator", "https://stockanalysis.com/etf/gou/",
    "stockanalysis.com live snapshot")

# ---- 3. Hand-verified press/aggregator anchors from task spec section (c) ----
SPEC_ANCHORS = [
    ("MUU", "2026-01-01", 516e6, "article", "task-spec refuter-verified", "reported AUM"),
    ("MUU", "2026-01-26", 1.1e9, "article", "task-spec refuter-verified", "reported AUM, approx"),
    ("MUU", "2026-05-27", 3.7e9, "article", "task-spec refuter-verified", "reported AUM"),
    ("MUU", "2026-05-28", 5.4e9, "article", "task-spec refuter-verified", "reported AUM"),
    ("MUU", "2026-07-09", 5.0e9, "article", "task-spec refuter-verified", "reported range $5.0-5.5B over 2026-07-09/17, low end"),
    ("MUU", "2025-04-30", 21.8e6, "article", "task-spec refuter-verified", "reported AUM"),
    ("NVDL", "2025-01-31", 6e9, "article", "task-spec refuter-verified", "reported 'peak ~$6B in January 2025'; month-end placeholder date, day-level precision unavailable"),
    ("TSLL", "2025-09-30", 6.5e9, "article", "task-spec refuter-verified", "reported 'TSLL $6.5B @2025-09'; month-end placeholder date, day-level precision unavailable"),
    ("TSLL", "2026-05-28", 5.7e9, "article", "task-spec refuter-verified", "reported AUM"),
]
for ticker, asof, aum, kind, url, note in SPEC_ANCHORS:
    add(ticker, asof, aum, kind, url, note)

# ---- write output ----
rows.sort(key=lambda r: (r["ticker"], r["asof_date"], r["source_kind"]))
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["ticker", "asof_date", "aum_usd", "source_kind", "source_url", "note"])
    w.writeheader()
    w.writerows(rows)

print("wrote", len(rows), "rows to", OUT)

# summary by ticker
from collections import Counter
c = Counter(r["ticker"] for r in rows)
kinds = Counter(r["source_kind"] for r in rows)
print("tickers covered:", len(c))
print("by source_kind:", dict(kinds))
zero = []
