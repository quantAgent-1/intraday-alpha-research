"""DR-X6 recipe step B: NDX quarterly proxy via SEC Form NPORT-P for Invesco QQQ Trust.

Mechanical data assembly only. Lists all NPORT-P filings for CIK 0001067839 (QQQ) from the
submissions API, fetches each accession's primary_doc.xml from EDGAR Archives, and parses
every <invstOrSec> entry: name, title, cusip, isin, direct ticker (rare - most equity rows
carry only isin), pctVal, assetCat, plus the filing's repPdDate. No ticker resolution here
(that is a name/isin -> ticker crosswalk problem handled in _iw_build.py); this script is a
faithful raw capture of what SEC publishes.

Declared User-Agent WITHOUT "naver" substring (SEC WAF blocks that token) per project note.
Rate limit: <=5 req/s (well under SEC's 10 req/s fair-access ceiling).
"""
import csv
import re
import sys
import time

import requests

UA = {"User-Agent": "enginev51 research contact@example.com"}
CIK = "0001067839"  # Invesco QQQ Trust, Series 1
SCRATCH = "scratch"
OUT_RAW = f"{SCRATCH}/iw_qqq_raw.csv"
LOG = f"{SCRATCH}/iw_qqq_log.txt"
SLEEP_S = 0.25  # ~4 req/s

FIELDNAMES = ["accession", "filing_date", "repPdDate", "name", "title", "cusip", "isin",
              "ticker_direct", "assetCat", "pctVal", "valUSD", "source_url"]


def get(url, **kw):
    r = requests.get(url, headers=UA, timeout=25, **kw)
    time.sleep(SLEEP_S)
    return r


def list_nport_p_filings():
    url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    r = get(url)
    r.raise_for_status()
    d = r.json()
    recent = d["filings"]["recent"]
    forms = recent["form"]
    out = []
    for i in range(len(forms)):
        if forms[i] == "NPORT-P":
            out.append({
                "accession": recent["accessionNumber"][i],
                "filing_date": recent["filingDate"][i],
                "report_date": recent["reportDate"][i],
                "primary_doc": recent["primaryDocument"][i],
            })
    # older filings (if any) live in filings.files - check and warn if present
    extra_files = d["filings"].get("files", [])
    return out, extra_files, d.get("name")


def fetch_primary_doc(accession):
    acc_nodash = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{acc_nodash}/primary_doc.xml"
    r = get(url)
    return r.status_code, r.text, url


def g1(pattern, text):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None


def parse_filing(text):
    rep_pd_date = g1(r"<repPdDate>([^<]*)</repPdDate>", text)
    blocks = re.findall(r"<invstOrSec>.*?</invstOrSec>", text, re.DOTALL)
    rows = []
    for b in blocks:
        name = g1(r"<name>([^<]*)</name>", b)
        title = g1(r"<title>([^<]*)</title>", b)
        cusip = g1(r"<cusip>([^<]*)</cusip>", b)
        isin = g1(r'<isin value="([^"]*)"', b)
        ticker = g1(r'<ticker value="([^"]*)"', b)
        asset_cat = g1(r"<assetCat>([^<]*)</assetCat>", b)
        pct_val = g1(r"<pctVal>([^<]*)</pctVal>", b)
        val_usd = g1(r"<valUSD>([^<]*)</valUSD>", b)
        rows.append({
            "repPdDate": rep_pd_date, "name": name, "title": title, "cusip": cusip,
            "isin": isin, "ticker_direct": ticker, "assetCat": asset_cat,
            "pctVal": pct_val, "valUSD": val_usd,
        })
    return rep_pd_date, rows


def main():
    filings, extra_files, entity_name = list_nport_p_filings()
    print(f"entity: {entity_name}; NPORT-P filings found: {len(filings)}", flush=True)
    if extra_files:
        print(f"WARNING: submissions JSON has paginated 'files' entries not fetched: {extra_files}", flush=True)

    out_f = open(OUT_RAW, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES)
    writer.writeheader()
    log_f = open(LOG, "w", encoding="utf-8")
    log_f.write(f"entity: {entity_name}\nNPORT-P filings found: {len(filings)}\nextra_files: {extra_files}\n")

    n_ok, n_fail = 0, 0
    for f in sorted(filings, key=lambda x: x["report_date"]):
        acc = f["accession"]
        status, text, url = fetch_primary_doc(acc)
        if status != 200:
            n_fail += 1
            log_f.write(f"{acc}\treport={f['report_date']}\tHTTP{status}\n")
            log_f.flush()
            print(f"{acc} report={f['report_date']}: HTTP{status} FAIL", flush=True)
            continue
        rep_pd_date, rows = parse_filing(text)
        if rep_pd_date is None or len(rows) < 10:
            n_fail += 1
            log_f.write(f"{acc}\treport={f['report_date']}\tPARSE_FAIL rows={len(rows)} repPdDate={rep_pd_date}\n")
            log_f.flush()
            print(f"{acc} report={f['report_date']}: PARSE_FAIL rows={len(rows)}", flush=True)
            continue
        for rec in rows:
            rec["accession"] = acc
            rec["filing_date"] = f["filing_date"]
            rec["source_url"] = url
            writer.writerow(rec)
        out_f.flush()
        n_ok += 1
        log_f.write(f"{acc}\treport={f['report_date']}\tOK rows={len(rows)} repPdDate={rep_pd_date}\n")
        log_f.flush()
        print(f"{acc} report={f['report_date']}: OK rows={len(rows)} repPdDate={rep_pd_date}", flush=True)

    out_f.close()
    log_f.close()
    print(f"DONE. filings_ok={n_ok} filings_fail={n_fail} total={len(filings)}")


if __name__ == "__main__":
    sys.exit(main())
