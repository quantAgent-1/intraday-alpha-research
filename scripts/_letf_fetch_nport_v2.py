"""One-off script v2: precise NPORT-P AUM anchors per fund via EDGAR seriesId enumeration.

Fixes the v1 (_letf_fetch_nport.py) contamination problem: EFTS full-text hits from
multi-series trusts include sibling funds' filings, so v1's unvalidated even-spread
sampling pulled wrong-fund docs. v2:
  1. Resolves each fund's EDGAR seriesId from ONE validated primary_doc.xml
     (seeded from v1's validated rows where available, else relevance-ordered EFTS).
  2. Enumerates exactly that series' NPORT-P filings via
     browse-edgar?action=getcompany&CIK=<seriesId>&type=NPORT-P&output=atom.
  3. Fetches each accession's primary_doc.xml, re-validates seriesName, extracts
     repPdDate + netAssets.
Dedupes (ticker, repPdDate) keeping the latest filing (amendments win).
Resumable: state file lists completed tickers; deadline-bounded clean exit.
"""
import csv
import json
import os
import re
import sys
import time

import requests

UA = {"User-Agent": "enginev51-research/1.0 research-contact@example.com"}
SLEEP = 0.22
DEADLINE_S = 480
SCRATCH = "scratch"
RAW_V1 = f"{SCRATCH}/nport_anchors_raw.csv"
OUT = f"{SCRATCH}/nport_anchors_v2.csv"
STATE = f"{SCRATCH}/nport_v2_state.json"

T0 = time.time()


def norm(s):
    import html
    return re.sub(r"[^a-z0-9]", "", html.unescape(s or "").lower())


# ticker -> (efts_queries, cik10, accept) ; accept = list of normalized substrings, any-match.
# For ProShares, 'eq:' prefix means equality after stripping leading 'proshares'.
FUNDS = {
    # --- MU complex ---
    "MUU": (["Direxion Daily MU Bull 2X"], "0001424958", ["dailymubull2x"], False),
    "MUD": (["Direxion Daily MU Bear 1X"], "0001424958", ["dailymubear1x"], False),
    "MULL": (["GraniteShares 2x Long MU Daily"], "0001689873", ["2xlongmudaily"], False),
    "MUZ": (["Defiance Daily Target 2X Short MU"], "0001924868", ["2xshortmu"], False),
    # --- NVDA complex ---
    "NVDL": (["GraniteShares 2x Long NVDA Daily"], "0001689873", ["2xlongnvdadaily", "15xlongnvdadaily"], False),  # 1.5x era pre-2024
    "NVDU": (["Direxion Daily NVDA Bull 2X"], "0001424958", ["dailynvdabull2x", "dailynvdabull15x"], False),  # 1.5X era pre-2024
    "NVDD": (["Direxion Daily NVDA Bear 1X"], "0001424958", ["dailynvdabear1x"], False),
    "NVD": (["GraniteShares 2x Short NVDA Daily"], "0001689873", ["2xshortnvdadaily", "15xshortnvdadaily"], False),  # -1.5x era pre-2024
    "NVDS": (["Tradr 1.5X Short NVDA Daily", "AXS 1.25X NVDA Bear Daily"], "0001587982",
             ["15xshortnvdadaily", "125xnvdabeardaily"], False),
    "NVDX": (["T-Rex 2X Long NVIDIA Daily Target"], "0001771146", ["2xlongnvidiadailytarget"], False),
    "NVDQ": (["T-Rex 2X Inverse NVIDIA Daily Target"], "0001771146", ["2xinversenvidiadailytarget"], False),
    # --- TSLA complex ---
    "TSLL": (["Direxion Daily TSLA Bull 2X"], "0001424958", ["dailytslabull2x", "dailytslabull15x"], False),  # 1.5X era pre-2024
    "TSLS": (["Direxion Daily TSLA Bear 1X"], "0001424958", ["dailytslabear1x"], False),
    "TSLR": (["GraniteShares 2x Long TSLA Daily"], "0001689873", ["2xlongtsladaily", "175xlongtsladaily"], False),  # 1.75x era pre-2024
    "TSLQ": (["Tradr 2X Short TSLA Daily", "AXS TSLA Bear Daily"], "0001587982",
             ["2xshorttsladaily", "axstslabeardaily"], False),
    "TSLT": (["T-Rex 2X Long Tesla Daily Target"], "0001771146", ["2xlongtesladailytarget"], False),
    "TSLZ": (["T-Rex 2X Inverse Tesla Daily Target"], "0001771146", ["2xinversetesladailytarget"], False),
    # --- GOOGL complex ---
    "GGLL": (["Direxion Daily GOOGL Bull 2X"], "0001424958", ["dailygooglbull2x", "dailygooglbull15x"], False),  # 1.5X era pre-2024
    "GGLS": (["Direxion Daily GOOGL Bear 1X"], "0001424958", ["dailygooglbear1x"], False),
    "GOU": (["GraniteShares 2x Long GOOGL Daily"], "0001689873", ["2xlonggoogldaily"], False),
    # --- AMD complex ---
    "AMDL": (["GraniteShares 2x Long AMD Daily"], "0001689873", ["2xlongamddaily"], False),
    "AMUU": (["Direxion Daily AMD Bull 2X"], "0001424958", ["dailyamdbull2x"], False),
    "AMDD": (["Direxion Daily AMD Bear 1X"], "0001424958", ["dailyamdbear1x"], False),
    "AMDU": (["Defiance Leveraged Long + Income AMD"], "0001924868", ["incomeamd"], False),
    # --- AVGO complex ---
    "AVL": (["Direxion Daily AVGO Bull 2X"], "0001424958", ["dailyavgobull2x"], False),
    "AVS": (["Direxion Daily AVGO Bear 1X"], "0001424958", ["dailyavgobear1x"], False),
    "AVGX": (["Defiance Daily Target 2X Long AVGO"], "0001924868", ["2xlongavgo"], False),
    "AVGG": (["Leverage Shares 2X Long AVGO Daily"], "0001976322", ["2xlongavgodaily"], False),
    "AVGU": (["GraniteShares 2x Long AVGO Daily"], "0001689873", ["2xlongavgodaily"], False),
    # --- NFLX complex ---
    "NFXL": (["Direxion Daily NFLX Bull 2X"], "0001424958", ["dailynflxbull2x"], False),
    "NFXS": (["Direxion Daily NFLX Bear 1X"], "0001424958", ["dailynflxbear1x"], False),
    "NFLU": (["T-Rex 2X Long NFLX Daily Target", "T-Rex 2X Long Netflix Daily Target"], "0001771146",
             ["2xlongnflxdailytarget", "2xlongnetflixdailytarget"], False),
    # --- LRCX ---
    "LRCU": (["Tradr 2X Long LRCX Daily"], "0001587982", ["2xlonglrcxdaily"], False),
    # --- Corgi (almost certainly no NPORT yet; cheap to confirm) ---
    "NVC": (["Corgi NVDA 2x Daily"], "0002078265", ["corginvda2xdaily"], False),
    "TESC": (["Corgi TSLA 2x Daily"], "0002078265", ["corgitsla2xdaily"], False),
    "MIC": (["Corgi MU 2x Daily"], "0002078265", ["corgimu2xdaily"], False),
    "GOGL": (["Corgi GOOGL 2x Daily"], "0002078265", ["corgigoogl2xdaily"], False),
    "AMDC": (["Corgi AMD 2x Daily"], "0002078265", ["corgiamd2xdaily"], False),
    "AVGC": (["Corgi AVGO 2x Daily"], "0002078265", ["corgiavgo2xdaily"], False),
    "NFX": (["Corgi NFLX 2x Daily"], "0002078265", ["corginflx2xdaily"], False),
    "LRCC": (["Corgi LRCX 2x Daily"], "0002078265", ["corgilrcx2xdaily"], False),
    # --- index: NDX complex ---
    "TQQQ": (["ProShares UltraPro QQQ"], "0001174610", ["eq:ultraproqqq"], True),
    "SQQQ": (["ProShares UltraPro Short QQQ"], "0001174610", ["eq:ultraproshortqqq"], True),
    "QLD": (["ProShares Ultra QQQ"], "0001174610", ["eq:ultraqqq"], True),
    "QID": (["ProShares UltraShort QQQ"], "0001174610", ["eq:ultrashortqqq"], True),
    "PSQ": (["ProShares Short QQQ"], "0001174610", ["eq:shortqqq"], True),
    # --- index: semis ---
    "SOXL": (["Direxion Daily Semiconductor Bull 3X"], "0001424958", ["semiconductorbull3x"], True),
    "SOXS": (["Direxion Daily Semiconductor Bear 3X"], "0001424958", ["semiconductorbear3x"], True),
    # --- index: SPX complex ---
    "SSO": (["ProShares Ultra S&P 500", "ProShares Ultra S&P500"], "0001174610", ["eq:ultrasp500"], True),
    "SDS": (["ProShares UltraShort S&P 500", "ProShares UltraShort S&P500"], "0001174610", ["eq:ultrashortsp500"], True),
    "UPRO": (["ProShares UltraPro S&P 500", "ProShares UltraPro S&P500"], "0001174610", ["eq:ultraprosp500"], True),
    "SPXU": (["ProShares UltraPro Short S&P 500", "ProShares UltraPro Short S&P500"], "0001174610",
             ["eq:ultraproshortsp500"], True),
    # Registered names carry "(R)": "Direxion Daily S&P 500(R) Bull 3X ETF" — accept both forms,
    # but NOT High Beta variants (hence the negative guard in accepts() below via exact tokens).
    "SPXL": (["Direxion Daily S&P 500 Bull 3X"], "0001424958", ["sp500bull3x", "sp500rbull3x"], True),
    "SPXS": (["Direxion Daily S&P 500 Bear 3X"], "0001424958", ["sp500bear3x", "sp500rbear3x"], True),
    "SH": (["ProShares Short S&P 500", "ProShares Short S&P500"], "0001174610", ["eq:shortsp500"], True),
}

INDEX_SAMPLE = 8  # anchors per index fund (registration bar: 3-4 suffice)


def accepts(ticker, series_name):
    sn = norm(series_name)
    for pat in FUNDS[ticker][2]:
        if pat.startswith("eq:"):
            target = pat[3:]
            stripped = sn[len("proshares"):] if sn.startswith("proshares") else sn
            if stripped == target:
                return True
        elif pat in sn:
            return True
    return False


def get(url, **kw):
    r = requests.get(url, headers=UA, timeout=25, **kw)
    time.sleep(SLEEP)
    return r


def efts_search(q, cik10, from_=0):
    r = get("https://efts.sec.gov/LATEST/search-index",
            params={"q": f'"{q}"', "forms": "NPORT-P", "ciks": cik10, "from": from_})
    try:
        return r.json().get("hits", {}).get("hits", [])
    except Exception:
        return []


def fetch_primary(cik, accession):
    acc_nodash = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/primary_doc.xml"
    r = get(url)
    return r.status_code, r.text, url


def parse_nport(xml_text):
    def g(tag):
        m = re.search(rf"<{tag}>([^<]*)</{tag}>", xml_text)
        return m.group(1).strip() if m else None
    sn = g("seriesName")
    sid = g("seriesId")
    rpd = g("repPdDate")
    na = g("netAssets")
    fin = g("isFinalFiling")
    return sn, sid, rpd, (float(na) if na else None), fin


def browse_series_filings(series_id):
    url = ("https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
           f"&CIK={series_id}&type=NPORT-P&dateb=&owner=include&count=100&output=atom")
    r = get(url)
    entries = re.findall(
        r"<accession-number>([\d-]+)</accession-number>.*?<filing-date>([\d-]+)</filing-date>.*?<filing-type>([^<]+)</filing-type>",
        r.text, re.DOTALL)
    return entries  # [(accession, filing_date, type)]


# ---- v1 seed accessions: first validated row per ticker from the old raw pull ----
def load_seeds():
    seeds = {}
    if not os.path.exists(RAW_V1):
        return seeds
    with open(RAW_V1, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            t = r["ticker"]
            if t in seeds or t not in FUNDS:
                continue
            sn = r["note"].replace("seriesName=", "").split(";")[0]
            if accepts(t, sn):
                m = re.search(r"/data/(\d+)/(\d+)/primary_doc\.xml", r["source_url"])
                if m:
                    cik, acc_nodash = m.group(1), m.group(2)
                    acc = f"{acc_nodash[:10]}-{acc_nodash[10:12]}-{acc_nodash[12:]}"
                    seeds[t] = (cik, acc)
    return seeds


def resolve_series_id(ticker, seeds, log):
    queries, cik10, _, _ = FUNDS[ticker]
    # via seed accession
    if ticker in seeds:
        cik, acc = seeds[ticker]
        status, text, url = fetch_primary(cik, acc)
        if status == 200:
            sn, sid, rpd, na, fin = parse_nport(text)
            if sn and sid and accepts(ticker, sn):
                return sid
        log.append(f"{ticker}\tseed-resolution-failed")
    # via relevance-ordered EFTS
    for q in queries:
        hits = efts_search(q, cik10)
        tried = 0
        for hh in hits:
            if tried >= 8:
                break
            acc = hh["_id"].split(":")[0]
            cik = (hh["_source"].get("ciks") or [cik10])[0]
            status, text, url = fetch_primary(cik, acc)
            tried += 1
            if status != 200:
                continue
            sn, sid, rpd, na, fin = parse_nport(text)
            if sn and sid and accepts(ticker, sn):
                return sid
        log.append(f"{ticker}\tquery-exhausted:{q} (hits={len(hits)}, tried={tried})")
    return None


def main():
    state = {"done": [], "series_ids": {}}
    if os.path.exists(STATE):
        state = json.load(open(STATE, encoding="utf-8"))
    seeds = load_seeds()
    log = []

    # collect rows keyed (ticker, repPdDate) -> (filing_date, row)
    best = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                fd = re.search(r"filed=([\d-]+)", r["note"])
                best[(r["ticker"], r["asof_date"])] = (fd.group(1) if fd else "", r)

    def save():
        rows = [v[1] for v in best.values()]
        rows.sort(key=lambda r: (r["ticker"], r["asof_date"]))
        with open(OUT, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["ticker", "asof_date", "aum_usd", "source_kind", "source_url", "note"])
            w.writeheader()
            w.writerows(rows)
        json.dump(state, open(STATE, "w", encoding="utf-8"))
        with open(f"{SCRATCH}/nport_v2_log.txt", "a", encoding="utf-8") as f:
            f.write("\n".join(log) + "\n")

    order = [t for t in FUNDS if not FUNDS[t][3]] + [t for t in FUNDS if FUNDS[t][3]]
    for ticker in order:
        if ticker in state["done"]:
            continue
        if time.time() - T0 > DEADLINE_S:
            print("DEADLINE — remaining:", [t for t in order if t not in state["done"]])
            save()
            return

        sid = state["series_ids"].get(ticker) or resolve_series_id(ticker, seeds, log)
        if not sid:
            print(f"{ticker}: UNRESOLVED (no NPORT-P located)")
            log.append(f"{ticker}\tUNRESOLVED")
            state["done"].append(ticker)
            continue
        state["series_ids"][ticker] = sid

        entries = [(a, d, ty) for (a, d, ty) in browse_series_filings(sid) if d >= "2022-01-01"]
        entries.sort(key=lambda e: e[1])
        if FUNDS[ticker][3] and len(entries) > INDEX_SAMPLE:
            idx = sorted(set(int(i * (len(entries) - 1) / (INDEX_SAMPLE - 1)) for i in range(INDEX_SAMPLE)))
            entries = [entries[i] for i in idx]

        n_ok = 0
        for acc, fdate, ftype in entries:
            if time.time() - T0 > DEADLINE_S + 60:  # finish current fund with grace period
                break
            cik = FUNDS[ticker][1].lstrip("0")
            status, text, url = fetch_primary(cik, acc)
            if status != 200:
                log.append(f"{ticker}\t{acc}\tHTTP{status}")
                continue
            sn, sid2, rpd, na, fin = parse_nport(text)
            if not sn or na is None or not accepts(ticker, sn):
                log.append(f"{ticker}\t{acc}\tREJECT seriesName={sn}")
                continue
            key = (ticker, rpd)
            row = {"ticker": ticker, "asof_date": rpd, "aum_usd": f"{na:.2f}",
                   "source_kind": "NPORT-P", "source_url": url,
                   "note": f"seriesName={sn};seriesId={sid};form={ftype};filed={fdate}"}
            if key not in best or best[key][0] <= fdate:
                best[key] = (fdate, row)
            n_ok += 1
        print(f"{ticker}: seriesId={sid} filings={len(entries)} ok={n_ok}")
        state["done"].append(ticker)
        save()

    save()
    print("ALL DONE. rows=", len(best))


if __name__ == "__main__":
    main()
