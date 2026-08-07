"""One-off script: fetch stockanalysis.com ETF pages for the M12 LETF universe.
Saves raw HTML to scratchpad and prints extracted Assets / Inception Date / Title.
Not part of the permanent codebase - throwaway data-assembly helper.
"""
import re
import sys
import time
import requests

UA = {"User-Agent": "enginev51-research/1.0 research-contact@example.com"}
SCRATCH = "scratch/sa_pages"

TICKERS = [
    "MUU", "MULL", "MUD", "MUZ",
    "NVDL", "NVDU", "NVDX", "NVD", "NVDD", "NVDS", "NVDQ",
    "TSLL", "TSLT", "TSLR", "TSLQ", "TSLZ", "TSLS",
    "GGLL", "GGLS",
    "AMDL", "AMUU", "AMDD", "AMDU",
    "AVL", "AVGX", "AVGG", "AVGU", "AVS",
    "NFXL", "NFLU", "NFXS",
    "LRCU",
    "TQQQ", "SQQQ", "QLD", "QID", "PSQ",
    "SOXL", "SOXS",
    "SSO", "SDS", "UPRO", "SPXU", "SPXL", "SPXS", "SH",
]

results = []
for t in TICKERS:
    url = f"https://stockanalysis.com/etf/{t.lower()}/"
    try:
        r = requests.get(url, headers=UA, timeout=20)
        status = r.status_code
        html = r.text
        with open(f"{SCRATCH}/{t}.html", "w", encoding="utf-8") as f:
            f.write(html)
        title_m = re.search(r"<title>(.*?)</title>", html)
        title = title_m.group(1) if title_m else None
        rows = re.findall(r"<td[^>]*>([^<]+)</td><td[^>]*>([^<]+)</td>", html)
        d = {k: v for k, v in rows}
        assets = d.get("Assets")
        inception = d.get("Inception Date")
        expense = d.get("Expense Ratio")
        results.append((t, status, title, assets, inception, expense))
        print(f"{t}\t{status}\t{title}\t{assets}\t{inception}\t{expense}")
    except Exception as e:
        results.append((t, "ERR", str(e), None, None, None))
        print(f"{t}\tERR\t{e}")
    time.sleep(0.3)

# also dump a small CSV for downstream parsing
import csv
with open(f"{SCRATCH}/sa_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ticker", "status", "title", "assets", "inception_date", "expense_ratio"])
    w.writerows(results)
print("DONE", len(results))
