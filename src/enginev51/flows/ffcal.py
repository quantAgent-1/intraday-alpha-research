"""
ffcal.py — Forced-Flow Calendar v0.1 (present-state stack tool #2).

Who is forced to trade, when, on both tapes (US + KRX), rendered in KST.
Design spec: wiki/designs/forced-flow-calendar.md. Stdlib-only (Python 3.11+).

v5.1: persistence stripped — pure compute. The original module was a stdlib CLI
(`next`/`brief`/`day`/`ics`/`html`/`selftest`) that read a module-relative
`overrides.toml` and wrote artifacts into `store/`. The `argparse` CLI (`main`),
the `store/` file writes, and the `selftest()` harness are removed; the
acceptance anchors from `selftest()` are ported to `tests/test_flows.py`.
`load_overrides()` now takes an explicit path (no module-relative discovery)
so every generator stays pure given the returned `ov` dict.

Feeds implemented (v0.1): F1 opex/witching, F2 VIX exp, F3 roll week, F4 month-end window,
F5 US macro (FOMC+blackout, CPI, NFP; PCE/QRA via overrides), F6 US sessions, F7 index recon
effective dates, F8/F15 earnings (overrides), F9 blackout transitions + gauge, F11 KRX 만기,
F12 KR macro (exports triplet, TSMC monthly, BOK via overrides), F13 cascade-morning flags
(manual v0), F14 KR sessions. Pending (per design): F7 announcement scrapers, F8 auto-confirm,
F10 lockup scraper, F13 KOFIA join, Exit-Sentry panel export.
"""
from __future__ import annotations

import calendar as _cal
import datetime as dt
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

SIZE_W = {"S": 1, "M": 2, "L": 4, "XL": 8}
PILEUP_2D = 14          # 2-day rolling density that flags a pileup
CONF_GLYPH = {"deterministic": "#", "confirmed": "OK", "estimated": "~"}

# --------------------------------------------------------------------------- date helpers

def nth_weekday(y: int, m: int, weekday: int, n: int) -> dt.date:
    """n-th <weekday> (Mon=0) of month; n>=1."""
    first = dt.date(y, m, 1)
    off = (weekday - first.weekday()) % 7
    return first + dt.timedelta(days=off + 7 * (n - 1))

def last_weekday(y: int, m: int, weekday: int) -> dt.date:
    d = dt.date(y, m, _cal.monthrange(y, m)[1])
    return d - dt.timedelta(days=(d.weekday() - weekday) % 7)

def easter(y: int) -> dt.date:
    """Gregorian computus (Anonymous algorithm)."""
    a = y % 19
    b, c = divmod(y, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return dt.date(y, month, day + 1)

def _observed(d: dt.date) -> dt.date:
    if d.weekday() == 5:
        return d - dt.timedelta(days=1)
    if d.weekday() == 6:
        return d + dt.timedelta(days=1)
    return d

def us_holidays(y: int) -> set[dt.date]:
    h = {
        _observed(dt.date(y, 1, 1)),
        nth_weekday(y, 1, 0, 3),                       # MLK
        nth_weekday(y, 2, 0, 3),                       # Presidents
        easter(y) - dt.timedelta(days=2),              # Good Friday
        last_weekday(y, 5, 0),                         # Memorial
        _observed(dt.date(y, 6, 19)),                  # Juneteenth
        _observed(dt.date(y, 7, 4)),                   # Independence
        nth_weekday(y, 9, 0, 1),                       # Labor
        nth_weekday(y, 11, 3, 4),                      # Thanksgiving
        _observed(dt.date(y, 12, 25)),                 # Christmas
    }
    return h

def us_half_days(y: int) -> set[dt.date]:
    out = {nth_weekday(y, 11, 3, 4) + dt.timedelta(days=1)}   # day after Thanksgiving
    xmas_eve = dt.date(y, 12, 24)
    if xmas_eve.weekday() < 5 and xmas_eve not in us_holidays(y):
        out.add(xmas_eve)
    jul3 = dt.date(y, 7, 3)
    if jul3.weekday() < 5 and jul3 not in us_holidays(y):
        out.add(jul3)
    return out

def us_dst(d: dt.date) -> bool:
    """US DST: 2nd Sunday of March .. 1st Sunday of November."""
    return nth_weekday(d.year, 3, 6, 2) <= d < nth_weekday(d.year, 11, 6, 1)

def et_to_kst(d: dt.date, hhmm: str) -> tuple[dt.date, str]:
    """ET wall time -> (KST date, 'HH:MM'). KST = ET + 13h (DST) / + 14h (winter)."""
    hh, mm = map(int, hhmm.split(":"))
    hh += 13 if us_dst(d) else 14
    days, hh = divmod(hh, 24)
    return d + dt.timedelta(days=days), f"{hh:02d}:{mm:02d}"

def is_bd(d: dt.date, hols: set[dt.date]) -> bool:
    return d.weekday() < 5 and d not in hols

def prev_bd(d: dt.date, hols: set[dt.date]) -> dt.date:
    while not is_bd(d, hols):
        d -= dt.timedelta(days=1)
    return d

def next_bd(d: dt.date, hols: set[dt.date]) -> dt.date:
    while not is_bd(d, hols):
        d += dt.timedelta(days=1)
    return d

def add_bd(d: dt.date, n: int, hols: set[dt.date]) -> dt.date:
    step = 1 if n >= 0 else -1
    left = abs(n)
    while left:
        d += dt.timedelta(days=step)
        if is_bd(d, hols):
            left -= 1
    return d

def trading_days(y: int, m: int, hols: set[dt.date]) -> list[dt.date]:
    n = _cal.monthrange(y, m)[1]
    return [d for i in range(n) if is_bd(d := dt.date(y, m, i + 1), hols)]

def month_range(start: dt.date, end: dt.date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)

# --------------------------------------------------------------------------- event model

@dataclass
class Event:
    feed: str                   # F1..F15
    label: str
    market: str                 # US | KR | EU | TW | BOTH
    date: dt.date               # KST display date (band: start)
    time: str = ""              # "HH:MM" KST, "" = all-day/band
    end: dt.date | None = None  # band end (KST)
    size: str = "M"             # S M L XL
    direction: str = "two_way"  # buy|sell|two_way|vol|supply|demand_absent
    confidence: str = "deterministic"   # deterministic|confirmed|estimated
    mechanics: str = ""         # who must do what (one line)
    decayed: bool = False       # famous price effect decayed -> plumbing, not signal
    uses: list[str] = field(default_factory=lambda: ["risk"])
    note: str = ""
    watch: list[str] = field(default_factory=list)   # pre-registered questions for this print

    def covers(self, d: dt.date) -> bool:
        return self.date <= d <= (self.end or self.date)

    def sort_key(self):
        return (self.date, self.time or "99:99", -SIZE_W[self.size])

# --------------------------------------------------------------------------- context

class Ctx:
    def __init__(self, asof: dt.date, start: dt.date, end: dt.date, ov: dict):
        self.asof, self.start, self.end, self.ov = asof, start, end, ov
        years = range(start.year - 1, end.year + 2)
        self.us_hols = set().union(*(us_holidays(y) for y in years))
        self.us_half = set().union(*(us_half_days(y) for y in years))
        self.kr_hols = set()
        kh = ov.get("krx_holidays", {})
        for v in kh.values():
            self.kr_hols.update(v)

def load_overrides(path: Path | None = None) -> dict:
    # v5.1: persistence stripped — no module-relative `overrides.toml` discovery.
    # The caller passes an explicit path (or None → empty dict); every generator
    # is pure given the returned `ov` dict.
    if path is None or not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)

# --------------------------------------------------------------------------- generators

def _win(ctx: Ctx, ev: Event) -> bool:
    return ev.date <= ctx.end and (ev.end or ev.date) >= ctx.start

def gen_f1_opex(ctx: Ctx) -> list[Event]:
    out = []
    for y, m in month_range(ctx.start, ctx.end):
        d = prev_bd(nth_weekday(y, m, 4, 3), ctx.us_hols)
        q = m in (3, 6, 9, 12)
        out.append(Event(
            "F1", "US quarterly triple witching" if q else "US monthly options expiry",
            "US", d, size="XL" if q else "L",
            mechanics="Dealer hedges concentrate then expire: pin gravity toward big-OI strikes into the close; "
                      "the week AFTER trades wider (gamma runoff until new OI builds)",
            uses=["risk", "execution", "attribution"]))
    return [e for e in out if _win(ctx, e)]

def gen_f2_vix(ctx: Ctx) -> list[Event]:
    out = []
    for y, m in month_range(ctx.start, ctx.end + dt.timedelta(days=40)):
        nxt_y, nxt_m = (y + 1, 1) if m == 12 else (y, m + 1)
        d = prev_bd(nth_weekday(nxt_y, nxt_m, 4, 3) - dt.timedelta(days=30), ctx.us_hols)
        out.append(Event("F2", "VIX futures/options expiration", "US", d, size="S",
                         mechanics="Vol-complex roll: VIX ETPs and structured products reposition",
                         uses=["attribution"]))
    return [e for e in out if _win(ctx, e)]

def gen_f3_roll(ctx: Ctx) -> list[Event]:
    out = []
    for y, m in month_range(ctx.start, ctx.end):
        if m in (3, 6, 9, 12):
            opex = nth_weekday(y, m, 4, 3)
            out.append(Event("F3", "Index futures roll week (ES/NQ front->next)", "US",
                             opex - dt.timedelta(days=8), end=opex - dt.timedelta(days=4), size="S",
                             mechanics="Volume migrates to the next contract; basis/liquidity noise in index futures",
                             uses=["execution"]))
    return [e for e in out if _win(ctx, e)]

def gen_f4_monthend(ctx: Ctx) -> list[Event]:
    out = []
    est = {e["month"].replace(day=1): e for e in ctx.ov.get("monthend_estimates", [])}
    for y, m in month_range(ctx.start - dt.timedelta(days=7), ctx.end):
        tds = trading_days(y, m, ctx.us_hols)
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        tds2 = trading_days(ny, nm, ctx.us_hols)
        q = m in (3, 6, 9, 12)
        e = est.get(dt.date(y, m, 1), {})
        extra = f" | est: {e['estimate']} ({e['source']})" if e.get("estimate") else ""
        out.append(Event(
            "F4", ("QUARTER-end" if q else "Month-end") + " rebalance window", "BOTH",
            tds[-3], end=tds2[1], size="L" if q else "M",
            mechanics="Pension/target-date/balanced mandates rebalance the stock-bond mix; window dressing "
                      "into the print; concentrated in the last 2-3 sessions" + extra,
            uses=["risk", "attribution"]))
    return [e for e in out if _win(ctx, e)]

# FOMC 2026 (day pairs); confidence: verified only where the wiki pinned it
FOMC_2026 = [((1, 27), (1, 28), "estimated"), ((3, 17), (3, 18), "estimated"),
             ((4, 28), (4, 29), "estimated"), ((6, 16), (6, 17), "confirmed"),
             ((7, 28), (7, 29), "confirmed"), ((9, 15), (9, 16), "estimated"),
             ((10, 27), (10, 28), "estimated"), ((12, 8), (12, 9), "estimated")]
CPI_2026 = {1: (13, "estimated"), 2: (11, "estimated"), 3: (11, "estimated"),
            4: (10, "estimated"), 5: (12, "estimated"), 6: (10, "estimated"),
            7: (14, "confirmed"), 8: (12, "estimated"), 9: (11, "estimated"),
            10: (13, "estimated"), 11: (10, "estimated"), 12: (10, "estimated")}

def gen_f5_us_macro(ctx: Ctx) -> list[Event]:
    out = []
    for (m1, d1), (m2, d2), conf in FOMC_2026:
        day1, day2 = dt.date(2026, m1, d1), dt.date(2026, m2, d2)
        kd, kt = et_to_kst(day2, "14:00")
        out.append(Event("F5", "FOMC decision (+ presser 30min later)", "US", kd, kt, size="XL",
                         direction="vol", confidence=conf,
                         mechanics="The synchronization event: vol positioning unwinds into/out of the print; "
                                   "dots/statement reprice the hike path",
                         uses=["risk", "attribution"]))
        sat = day1 - dt.timedelta(days=(day1.weekday() - 5) % 7 or 7)
        blackout_start = sat - dt.timedelta(days=7)
        thu_after = day2 + dt.timedelta(days=(3 - day2.weekday()) % 7 or 7)
        out.append(Event("F5", "Fed communications blackout", "US", blackout_start, end=thu_after,
                         size="S", confidence=conf, direction="vol",
                         mechanics="No Fedspeak: repricing waits for the decision itself; "
                                   "(pre-FOMC drift window - decayed post-publication)",
                         decayed=True, uses=["attribution"]))
    for y, m in month_range(ctx.start, ctx.end):
        if y == 2026 and m in CPI_2026:
            day, conf = CPI_2026[m]
            kd, kt = et_to_kst(dt.date(y, m, day), "08:30")
            out.append(Event("F5", "US CPI", "US", kd, kt, size="L", direction="vol", confidence=conf,
                             mechanics="Rate-path repricing; implied-move sheet on QQQ/SOXX beforehand",
                             uses=["risk"]))
        nfp = nth_weekday(y, m, 4, 1)
        if nfp in ctx.us_hols:
            nfp = prev_bd(nfp, ctx.us_hols)
        kd, kt = et_to_kst(nfp, "08:30")
        out.append(Event("F5", "US jobs report (NFP)", "US", kd, kt, size="M", direction="vol",
                         confidence="estimated",
                         mechanics="Rate-path repricing; first-Friday rule (shifts on holidays)",
                         uses=["risk"]))
    for e in ctx.ov.get("macro_us", []):
        kd, kt = et_to_kst(e["date"], e.get("time_et", "08:30"))
        out.append(Event("F5", e["label"], "US", kd, kt, size=e.get("size", "M"), direction="vol",
                         confidence="confirmed" if e.get("confirmed") else "estimated",
                         mechanics=e.get("note", ""), uses=["risk"]))
    return [e for e in out if _win(ctx, e)]

def gen_f6_us_sessions(ctx: Ctx) -> list[Event]:
    out = []
    d = ctx.start
    while d <= ctx.end:
        if d in ctx.us_hols and d.weekday() < 5:
            out.append(Event("F6", "US market holiday", "US", d, size="S",
                             mechanics="No US session; overnight gaps accumulate into the reopen",
                             uses=["execution"]))
        if d in ctx.us_half:
            out.append(Event("F6", "US half day (early close 13:00 ET)", "US", d, size="S",
                             mechanics="Thin tape, early MOC cutoff; avoid naive market orders",
                             uses=["execution"]))
        d += dt.timedelta(days=1)
    return out

def gen_f7_recon(ctx: Ctx) -> list[Event]:
    out = []
    for y, m in month_range(ctx.start, ctx.end):
        if m in (3, 6, 9, 12):
            qx = prev_bd(nth_weekday(y, m, 4, 3), ctx.us_hols)
            out.append(Event("F7", "S&P quarterly rebalance EFFECTIVE (at the close)", "US",
                             qx, "close", size="L",
                             decayed=True,
                             mechanics="Index funds MUST trade this close (tracking mandate). Add-day price pop "
                                       "is ~0 now (Greenwood-Sammon) - a liquidity event, not direction",
                             uses=["execution", "attribution"]))
            out.append(Event("F7", "Semis ETF index rebalances effective (SOXX/SOXL + SMH)", "US",
                             qx, "close", size="M", decayed=True, confidence="estimated",
                             mechanics="ICE Semiconductor + MarketVector quarterly reviews land at the "
                                       "third-Friday close - sector-specific passive flow, with SOXL's daily "
                                       "leverage reset stacked on top",
                             uses=["execution", "attribution"]))
        if m in (2, 5, 8, 11):
            out.append(Event("F7", "MSCI review EFFECTIVE at month-end close (KR weights leg incl.)", "BOTH",
                             prev_bd(dt.date(y, m, _cal.monthrange(y, m)[1]), ctx.us_hols), "close",
                             size="L", decayed=True,
                             mechanics="Passive trackers trade the close; Samsung/SKH weight changes flow through "
                                       "the KRX close the same day",
                             uses=["execution", "attribution"]))
        if m == 6:
            out.append(Event("F7", "Russell reconstitution EFFECTIVE (biggest MOC print of the year)", "US",
                             last_weekday(y, 6, 4), "close", size="L", decayed=True,
                             mechanics="The deepest closing liquidity of the year - execution window, not signal",
                             uses=["execution"]))
        if m == 12:
            out.append(Event("F7", "Nasdaq-100 annual reconstitution effective", "US",
                             prev_bd(nth_weekday(y, 12, 4, 3), ctx.us_hols), "close", size="M", decayed=True,
                             mechanics="NDX trackers rebalance at the close", uses=["execution", "attribution"]))
    return [e for e in out if _win(ctx, e)]

def _earnings_kst(e: dict) -> tuple[dt.date, str]:
    if e.get("market") == "US":
        et_time = "16:05" if e.get("session", "AMC") == "AMC" else "07:00"
        return et_to_kst(e["date"], et_time)
    return e["date"], e.get("time_kst", "")

def _watch(ctx: Ctx, *keys: str) -> list[str]:
    wf = ctx.ov.get("watch_for", {})
    for k in keys:
        if k in wf:
            return list(wf[k])
    return []

def gen_f8_earnings(ctx: Ctx) -> list[Event]:
    out = []
    for e in ctx.ov.get("earnings", []):
        kd, kt = _earnings_kst(e)
        out.append(Event("F8", f"{e['label']} [{e['ticker']}]", e.get("market", "US"), kd, kt,
                         size=e.get("size", "M"), direction="vol",
                         confidence="confirmed" if e.get("confirmed") else "estimated",
                         mechanics=e.get("note", ""), uses=["risk"],
                         watch=_watch(ctx, f"{e['ticker']}@{e['date']}", e["ticker"])))
    return [e for e in out if _win(ctx, e)]

def _blackout_windows(ctx: Ctx) -> dict[str, list[tuple[dt.date, dt.date, str]]]:
    """name -> merged [(start, end, conf)] using [E-35d, E+2 trading days] on the name's market
    calendar. Overlapping windows (e.g. Samsung prelim + full report) merge, so enter/exit
    transitions fire only on true boundaries."""
    wl = set(ctx.ov.get("meta", {}).get("blackout_watchlist", []))
    raw: dict[str, list] = {}
    for e in ctx.ov.get("earnings", []):
        t = e["ticker"]
        if t not in wl:
            continue
        hols = ctx.kr_hols if e.get("market") == "KR" else ctx.us_hols
        ed = e["date"]
        raw.setdefault(t, []).append(
            (ed - dt.timedelta(days=35), add_bd(ed, 2, hols),
             "confirmed" if e.get("confirmed") else "estimated"))
    wins: dict[str, list] = {}
    for t, spans in raw.items():
        merged: list[tuple[dt.date, dt.date, str]] = []
        for s, e, c in sorted(spans):
            if merged and s <= merged[-1][1]:
                ps, pe, pc = merged[-1]
                merged[-1] = (ps, max(pe, e), "estimated" if "estimated" in (pc, c) else "confirmed")
            else:
                merged.append((s, e, c))
        wins[t] = merged
    return wins

def gen_f9_blackouts(ctx: Ctx) -> list[Event]:
    out = []
    for name, wins in _blackout_windows(ctx).items():
        for (s, e, conf) in wins:
            out.append(Event("F9", f"{name} enters buyback blackout (corporate bid steps aside)", "US"
                             if not name.endswith(".KS") else "KR", s, size="S", confidence=conf,
                             direction="demand_absent",
                             mechanics="Discretionary repurchases pause ~5wk pre-earnings (10b5-1 autopilot continues); "
                                       "the steady bid is absent exactly while event risk peaks",
                             uses=["risk", "attribution"]))
            out.append(Event("F9", f"{name} EXITS blackout (corporate bid returns)", "US"
                             if not name.endswith(".KS") else "KR", e, size="S", confidence=conf,
                             direction="buy",
                             mechanics="Repurchase programs resume post-print - a name-by-name flow tailwind",
                             uses=["risk", "attribution"]))
    return [e for e in out if _win(ctx, e)]

def blackout_gauge(ctx: Ctx, d: dt.date) -> tuple[int, int]:
    wins = _blackout_windows(ctx)
    n_in = sum(1 for w in wins.values() if any(s <= d <= e for s, e, _ in w))
    return n_in, len(wins)

def gen_f11_krx_expiry(ctx: Ctx) -> list[Event]:
    out = []
    for y, m in month_range(ctx.start, ctx.end):
        d = prev_bd(nth_weekday(y, m, 3, 2), ctx.kr_hols)   # 2nd Thursday
        q = m in (3, 6, 9, 12)
        out.append(Event(
            "F11", "KRX quadruple witching (dong-si man-gi)" if q else "KOSPI200 monthly options expiry",
            "KR", d, size="XL" if q else "L",
            mechanics="Expiry flow lands in the 15:20-15:30 closing auction; intraday program-trade balance "
                      "disclosures telegraph direction hours ahead (tail case: 2010-11-11)",
            uses=["risk", "execution", "attribution"]))
        if m in (6, 12):
            out.append(Event("F11", "KOSPI200 constituent changes effective (around expiry)", "KR",
                             d, size="S", decayed=True,
                             mechanics="Local trackers rebalance", uses=["attribution"]))
    return [e for e in out if _win(ctx, e)]

def gen_f12_kr_macro(ctx: Ctx) -> list[Event]:
    out = []
    for y, m in month_range(ctx.start, ctx.end + dt.timedelta(days=31)):
        specs = [(1, "Korea FULL-MONTH exports (prior month)", "L"),
                 (11, "Korea 1-10 day exports", "M"),
                 (21, "Korea 1-20 day exports", "M")]
        for day, label, size in specs:
            d = dt.date(y, m, day)
            wknd = "" if is_bd(d, ctx.kr_hols) else " (weekend/holiday release - tape reacts next session)"
            out.append(Event("F12", label, "KR", d, "09:00", size=size, direction="vol",
                             mechanics="The semis line is the global complex's best public leading indicator, "
                                       "published in this timezone" + wknd,
                             uses=["risk"]))
        d10 = dt.date(y, m, 10)
        wknd = "" if is_bd(d10, ctx.kr_hols) else " (weekend - lands next session)"
        out.append(Event("F12", "TSMC monthly revenue (prior month)", "TW", d10, size="M",
                         direction="vol", confidence="estimated",
                         mechanics="AI-capex chain monthly pulse (~10th each month)" + wknd, uses=["risk"]))
    for e in ctx.ov.get("macro_kr", []):
        out.append(Event("F12", e["label"], "KR", e["date"], e.get("time_kst", ""),
                         size=e.get("size", "M"), direction="vol",
                         confidence="confirmed" if e.get("confirmed") else "estimated",
                         mechanics=e.get("note", ""), uses=["risk"],
                         watch=_watch(ctx, e["label"])))
    return [e for e in out if _win(ctx, e)]

def gen_f16_sector(ctx: Ctx) -> list[Event]:
    """Semis/AI monthly sector-data prints (design Sec 1b, items 1-3)."""
    out = []
    def wknote(d: dt.date) -> str:
        return "" if d.weekday() < 5 else " (weekend - lands next session)"
    for y, m in month_range(ctx.start, ctx.end):
        last = dt.date(y, m, _cal.monthrange(y, m)[1])
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        out.append(Event(
            "F16", "TrendForce DRAM/NAND contract-price settlement window", "BOTH",
            last - dt.timedelta(days=3), end=next_bd(dt.date(ny, nm, 1), ctx.us_hols),
            size="L", direction="vol", confidence="estimated",
            mechanics="THE cycle print: fixed/contract m/m publishes around month-end - "
                      "Sentry T2 read due when it lands",
            uses=["risk"],
            watch=["DRAM fixed m/m still positive? NAND?",
                   "Increment vs last month - decelerating? (2nd-derivative rule)"]))
        d5 = dt.date(y, m, 5)
        out.append(Event("F16", "Hon Hai monthly revenue (AI-server assembly)", "TW", d5,
                         size="M", direction="vol", confidence="estimated",
                         mechanics="World's largest AI-server assembler; monthly revenue + server "
                                   "commentary set the AI-demand tone" + wknote(d5),
                         uses=["risk"]))
        d10 = dt.date(y, m, 10)
        out.append(Event("F16", "Aspeed monthly revenue (BMC = AI-server unit count)", "TW", d10,
                         size="M", direction="vol", confidence="estimated",
                         mechanics="A BMC ships in every AI server - the purest public "
                                   "server-unit nowcast" + wknote(d10),
                         uses=["risk"]))
        out.append(Event("F16", "Taiwan monthly-revenue deadline (ODM cluster: Quanta/Wistron/Inventec)",
                         "TW", d10, size="S", direction="vol", confidence="estimated",
                         mechanics="Statutory: all TW-listed companies report prior-month revenue "
                                   "by the 10th" + wknote(d10),
                         uses=["risk"]))
        tds_kr = trading_days(y, m, ctx.kr_hols)
        if tds_kr:
            out.append(Event("F16", "Korea industrial production - semiconductor shipments & inventory",
                             "KR", tds_kr[-1], "08:00", size="M", direction="vol",
                             confidence="estimated",
                             mechanics="Statistics Korea monthly IP: the semis INVENTORY line is the "
                                       "earliest public inventory-cycle tell (T4-adjacent)",
                             uses=["risk"],
                             watch=["Semis inventory index m/m - building or draining?",
                                    "Shipments-vs-inventory gap widening the right way?"]))
    return [e for e in out if _win(ctx, e)]

def gen_f18_policy(ctx: Ctx) -> list[Event]:
    out = []
    for e in ctx.ov.get("policy", []):
        out.append(Event("F18", e["label"], e.get("market", "BOTH"), e["date"],
                         e.get("time_kst", ""), size=e.get("size", "M"), direction="vol",
                         confidence="confirmed" if e.get("confirmed") else "estimated",
                         mechanics=e.get("note", ""), uses=["risk"]))
    return [e for e in out if _win(ctx, e)]

def gen_f13_bandaemae(ctx: Ctx) -> list[Event]:
    out = []
    f13 = ctx.ov.get("f13", {})
    z = float(f13.get("margin_z", 0.0))
    for d in f13.get("kospi_down_days", []):
        nb = next_bd(d + dt.timedelta(days=1), ctx.kr_hols)
        out.append(Event("F13", "BANDAEMAE window: forced margin supply into the KR open", "KR",
                         nb, "09:00", size="L" if z >= 1 else "M", direction="sell",
                         mechanics=f"T+2 misu liquidations execute at the open; sinyong margin calls clear "
                                   f"through ~10:00 (margin z={z:+.1f}); the ~10:00 turn checkpoint applies",
                         uses=["risk", "execution"]))
    return [e for e in out if _win(ctx, e)]

def gen_f14_kr_sessions(ctx: Ctx) -> list[Event]:
    out = []
    d = ctx.start
    while d <= ctx.end:
        if d in ctx.kr_hols and d.weekday() < 5:
            out.append(Event("F14", "KRX market holiday", "KR", d, size="S",
                             mechanics="No KR session", uses=["execution"]))
        d += dt.timedelta(days=1)
    return out

def gen_oneoffs(ctx: Ctx) -> list[Event]:
    out = []
    for e in ctx.ov.get("oneoffs", []):
        out.append(Event("F*", e["label"], e.get("market", "US"), e["date"],
                         e.get("time_kst", ""), end=e.get("end_date"),
                         size=e.get("size", "M"), direction=e.get("direction", "two_way"),
                         confidence="confirmed" if e.get("confirmed") else "estimated",
                         mechanics=e.get("mechanics", ""), uses=e.get("uses", ["risk"])))
    for e in ctx.ov.get("lockups", []):
        out.append(Event("F10", f"Lockup expiry: {e.get('ticker','?')}", "US", e["date"], size="M",
                         direction="supply", confidence="estimated",
                         mechanics="Insiders/early holders become able to sell", uses=["risk"]))
    return [e for e in out if _win(ctx, e)]

GENERATORS = [gen_f1_opex, gen_f2_vix, gen_f3_roll, gen_f4_monthend, gen_f5_us_macro,
              gen_f6_us_sessions, gen_f7_recon, gen_f8_earnings, gen_f9_blackouts,
              gen_f11_krx_expiry, gen_f12_kr_macro, gen_f13_bandaemae, gen_f14_kr_sessions,
              gen_f16_sector, gen_f18_policy, gen_oneoffs]

def build(ctx: Ctx) -> list[Event]:
    evs: list[Event] = []
    for g in GENERATORS:
        evs.extend(g(ctx))
    return sorted(evs, key=Event.sort_key)

# --------------------------------------------------------------------------- density

def day_score(events: list[Event], d: dt.date) -> int:
    return sum(SIZE_W[e.size] for e in events if e.covers(d))

def pileup_days(events: list[Event], days: list[dt.date]) -> set[dt.date]:
    out = set()
    for i, d in enumerate(days):
        nxt = days[i + 1] if i + 1 < len(days) else d
        s2 = day_score(events, d) + (day_score(events, nxt) if nxt != d else 0)
        xl2 = sum(1 for e in events if e.size == "XL" and (e.covers(d) or e.covers(nxt)))
        if s2 >= PILEUP_2D or xl2 >= 2:
            out |= {d, nxt}
    return out

# --------------------------------------------------------------------------- renderers

def _fmt_event(e: Event, d: dt.date) -> str:
    t = f"{e.time} " if e.time and e.date == d else ""
    band = ""
    if e.end:
        n_tot = (e.end - e.date).days + 1
        band = f" (day {(d - e.date).days + 1}/{n_tot}, through {e.end:%b %d})"
    conf = CONF_GLYPH[e.confidence]
    plumb = " [plumbing, not signal]" if e.decayed else ""
    mech = f" -- {e.mechanics}" if e.mechanics else ""
    return f"- {t}[{e.size}|{conf}] {e.label}{band}{mech}{plumb} (uses: {','.join(e.uses)})"

def render_brief(ctx: Ctx, days_n: int) -> str:
    d0 = ctx.asof
    days = [d0 + dt.timedelta(days=i) for i in range(days_n)]
    evs = build(ctx)
    piles = pileup_days(evs, days)
    ban = ctx.ov.get("meta", {}).get("short_sale_ban", False)
    lines = [f"## Forced-flow calendar - next {days_n} days (as of {d0}, all times KST)",
             f"_ffcal v0.1 | KR short-sale ban: {'ON' if ban else 'off'} | "
             f"[S/M/L/XL]=size, #=rule OK=confirmed ~=estimated_", ""]
    for d in days:
        todays = [e for e in evs if e.covers(d)]
        if not todays and d.weekday() >= 5:
            continue
        score = day_score(evs, d)
        flag = "  [!] PILEUP" if d in piles and score > 0 else ""
        n_in, n_tot = blackout_gauge(ctx, d)
        bo = f" | corporate bid: {n_tot - n_in}/{n_tot} present" if n_tot else ""
        lines.append(f"### {d:%a %b %d} - density {score}{bo}{flag}")
        for e in todays:
            lines.append(_fmt_event(e, d))
            if e.date == d:
                lines.extend(f"    ? {q}" for q in e.watch)
        lines.append("")
    return "\n".join(lines)

T_TMPL = {
    "krx_expiry": [
        ("08:00", "Pre-open: overnight US close read; check any F13 bandaemae flag + KOFIA margin delta"),
        ("08:30", "KR prints if scheduled (Samsung/SKH windows); opening auction orders build"),
        ("09:00", "Open. Post-down-day: misu T+2 forced supply hits at/near the open"),
        ("09:00-10:00", "Margin-call (sinyong) liquidation window - the ~10:00 turn checkpoint (V-day checklist)"),
        ("14:00-15:00", "Program-trade balance read: expiry imbalance direction forms"),
        ("15:20-15:30", "CLOSING CALL AUCTION - the expiry flow print. No market orders into it"),
        ("15:30", "Post-close: log auction imbalance vs the day's direction (attribution line)"),
    ],
    "us_opex": [
        ("22:30*", "US open (23:30 winter). Opex day: pin gravity toward big-OI strikes"),
        ("04:00*", "MOC imbalances publish; leveraged-ETF close-rebalance pressure window"),
        ("04:45-05:00*", "Closing cross: expiry prints land"),
        ("note", "Post-opex week: ranges typically widen as dealer gamma rolls off"),
    ],
    "fomc": [
        ("03:00", "FOMC decision + statement (dots if SEP meeting)"),
        ("03:30", "Press conference - the second reaction leg often exceeds the first"),
        ("05:00", "US close read; write the post-mortem line before sleep (nap protocol)"),
    ],
    "month_end": [
        ("note", "Month-end window: mix-rebalance flow concentrated in the last 2-3 sessions; "
                 "moves here carry a plumbing prior (attribution before narrative)"),
    ],
}

def render_day(ctx: Ctx, d: dt.date) -> str:
    evs = [e for e in build(ctx) if e.covers(d)]
    kinds = []
    for e in evs:
        if e.feed == "F11" and e.size in ("L", "XL") and e.date == d:
            kinds.append("krx_expiry")
        if e.feed == "F1" and e.date == d:
            kinds.append("us_opex")
        if e.feed == "F5" and e.label.startswith("FOMC decision") and e.date == d:
            kinds.append("fomc")
        if e.feed == "F4":
            kinds.append("month_end")
    lines = [f"## T-schedule {d:%a %b %d %Y} (KST)", ""]
    for k in dict.fromkeys(kinds):
        lines.append(f"**[{k}]**")
        for t, txt in T_TMPL[k]:
            lines.append(f"- {t} - {txt}")
        lines.append("")
    lines.append("**Events this day:**")
    if not evs:
        lines.append("- (none)")
    for e in evs:
        lines.append(_fmt_event(e, d))
        if e.date == d:
            lines.extend(f"    ? {q}" for q in e.watch)
    if any("*" in t for k in dict.fromkeys(kinds) if k == "us_opex" for t, _ in T_TMPL[k]):
        lines.append("\n_* = DST times (Mar-Nov); add 1h in winter._")
    return "\n".join(lines)

def render_ics(ctx: Ctx, days_n: int) -> str:
    evs = [e for e in build(ctx) if e.size in ("L", "XL")
           and e.date <= ctx.asof + dt.timedelta(days=days_n)]
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ffcal//v0.1//EN"]
    for e in evs:
        uid = f"{e.feed}-{e.date}-{abs(hash(e.label)) % 99999}@ffcal"
        out += ["BEGIN:VEVENT", f"UID:{uid}"]
        if len(e.time) == 5 and e.time[2] == ":":
            hh, mm = e.time.split(":")
            out.append(f"DTSTART:{e.date:%Y%m%d}T{hh}{mm}00")
        else:
            out.append(f"DTSTART;VALUE=DATE:{e.date:%Y%m%d}")
        summ = e.label.replace(",", r"\,")
        out += [f"SUMMARY:[{e.size}] {summ}",
                f"DESCRIPTION:{e.mechanics.replace(',', r'\,')}", "END:VEVENT"]
    out.append("END:VCALENDAR")
    return "\n".join(out)

# --------------------------------------------------------------------------- html dashboard

def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

HTML_CSS = """
:root{
  --bg:#F5F6F8; --surface:#FFFFFF; --ink:#1C2128; --muted:#5B6472; --line:#E3E6EB;
  --accent:#4263EB; --accent-ink:#FFFFFF; --pileup:#C92A2A; --pin:#B54708;
  --d0:transparent; --d1:#E7ECFF; --d2:#B3C1FF; --d3:#7C93F7; --d4:#4263EB; --d5:#2B3FA8;
  --chip-xl:#1C2128; --chip-xl-ink:#FFFFFF;
}
@media (prefers-color-scheme: dark){:root{
  --bg:#14171C; --surface:#1D2127; --ink:#E8EAEE; --muted:#9AA3B0; --line:#2A3038;
  --accent:#7C93F7; --accent-ink:#0F1320; --pileup:#FF6B6B; --pin:#F0A75A;
  --d1:#232A45; --d2:#33406E; --d3:#4C63C4; --d4:#7C93F7; --d5:#A9B8FF;
  --chip-xl:#E8EAEE; --chip-xl-ink:#14171C;
}}
:root[data-theme="dark"]{
  --bg:#14171C; --surface:#1D2127; --ink:#E8EAEE; --muted:#9AA3B0; --line:#2A3038;
  --accent:#7C93F7; --accent-ink:#0F1320; --pileup:#FF6B6B; --pin:#F0A75A;
  --d1:#232A45; --d2:#33406E; --d3:#4C63C4; --d4:#7C93F7; --d5:#A9B8FF;
  --chip-xl:#E8EAEE; --chip-xl-ink:#14171C;
}
:root[data-theme="light"]{
  --bg:#F5F6F8; --surface:#FFFFFF; --ink:#1C2128; --muted:#5B6472; --line:#E3E6EB;
  --accent:#4263EB; --accent-ink:#FFFFFF; --pileup:#C92A2A; --pin:#B54708;
  --d1:#E7ECFF; --d2:#B3C1FF; --d3:#7C93F7; --d4:#4263EB; --d5:#2B3FA8;
  --chip-xl:#1C2128; --chip-xl-ink:#FFFFFF;
}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);margin:0;
  font:14px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:20px;font-weight:700;margin:0}
h2{font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);margin:28px 0 10px}
.sub{color:var(--muted);font-size:13px;margin-top:2px}
.mono{font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;
  font-variant-numeric:tabular-nums}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:10px;font-size:12px;color:var(--muted)}
.stripbox{overflow-x:auto;border:1px solid var(--line);border-radius:8px;
  background:var(--surface);padding:12px;margin-top:8px}
.grid{display:grid;gap:2px;min-width:640px}
.cell{border-radius:4px;padding:4px 2px 3px;text-align:center;cursor:pointer;border:0;
  background:var(--d0);color:var(--ink);font:inherit}
.cell .dw{font-size:10px;color:var(--muted);display:block}
.cell .dn{font-size:12px;font-weight:600;display:block}
.cell .ds{font-size:11px;display:block;margin-top:2px}
.cell.h3x,.cell.h4x,.cell.h5x{color:#fff}
:root[data-theme="dark"] .cell.h4x,:root[data-theme="dark"] .cell.h5x{color:#0F1320}
@media (prefers-color-scheme: dark){.cell.h4x,.cell.h5x{color:#0F1320}
  :root[data-theme="light"] .cell.h4x,:root[data-theme="light"] .cell.h5x{color:#fff}}
.h1x{background:var(--d1)}.h2x{background:var(--d2)}.h3x{background:var(--d3)}
.h4x{background:var(--d4)}.h5x{background:var(--d5)}
.cell.off{opacity:.45}
.cell.pile{outline:2px solid var(--pileup);outline-offset:-2px}
.cell.today{box-shadow:0 0 0 2px var(--accent) inset}
.bar{align-self:end;width:100%;border-radius:3px 3px 0 0;background:var(--accent);opacity:.85}
.barcell{height:34px;display:flex;align-items:flex-end}
.rowlab{font-size:11px;color:var(--muted);margin:8px 0 2px}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 4px}
.fbtn{border:1px solid var(--line);background:var(--surface);color:var(--ink);
  border-radius:16px;padding:4px 12px;font:inherit;font-size:12px;cursor:pointer}
.fbtn[aria-pressed="true"]{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.day{background:var(--surface);border:1px solid var(--line);border-radius:8px;
  padding:12px 14px;margin-top:10px}
.day.pile{border-left:3px solid var(--pileup)}
.dayhead{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px}
.dayhead .date{font-size:15px;font-weight:700}
.dayhead .meta{font-size:12px;color:var(--muted)}
.badge{font-size:11px;font-weight:700;color:var(--pileup);border:1px solid var(--pileup);
  border-radius:4px;padding:1px 6px}
.ev{display:flex;gap:8px;padding:7px 0;border-top:1px solid var(--line);align-items:baseline}
.ev:first-of-type{border-top:0;margin-top:6px}
.ev .t{min-width:44px;font-size:12px;color:var(--muted)}
.chip{font-size:10.5px;font-weight:600;border-radius:4px;padding:1px 5px;
  border:1px solid var(--line);color:var(--muted);white-space:nowrap}
.chip.sS{}
.chip.sM{background:var(--d1);border-color:var(--d2);color:var(--ink)}
.chip.sL{background:var(--d2);border-color:var(--d3);color:var(--ink)}
.chip.sXL{background:var(--chip-xl);border-color:var(--chip-xl);color:var(--chip-xl-ink)}
.chip.est{border-style:dashed;color:var(--pin)}
.chip.mkt{}
.evbody{flex:1;min-width:220px}
.evbody .lbl{font-weight:600}
.evbody .mech{color:var(--muted);font-size:12.5px}
.evbody .plumb{font-size:11px;color:var(--muted);border:1px dashed var(--line);
  border-radius:4px;padding:0 4px;white-space:nowrap}
.wf{font-size:12px;color:var(--muted);margin-top:3px;padding-left:2px}
.wf b{color:var(--pin);font-weight:700}
.uses{font-size:11px;color:var(--muted);white-space:nowrap}
details.ts{margin-top:8px;font-size:12.5px}
details.ts summary{cursor:pointer;color:var(--accent);font-weight:600}
details.ts ol{margin:6px 0 2px;padding-left:0;list-style:none}
details.ts li{padding:3px 0;border-top:1px dashed var(--line)}
details.ts .tt{display:inline-block;min-width:96px;color:var(--muted)}
.pins{background:var(--surface);border:1px dashed var(--pin);border-radius:8px;
  padding:10px 14px;margin-top:8px;font-size:13px}
.pins li{margin:3px 0}
.foot{margin-top:26px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);
  padding-top:10px}
@media (prefers-reduced-motion: no-preference){html{scroll-behavior:smooth}}
"""

HTML_JS = """
(function(){
  var st={mkt:'all',big:false,plumb:true};
  function apply(){
    document.querySelectorAll('.ev').forEach(function(r){
      var okM = st.mkt==='all' || (st.mkt==='KR' ? r.dataset.mkt==='KR' : r.dataset.mkt!=='KR');
      var okS = !st.big || r.dataset.size==='L' || r.dataset.size==='XL';
      var okP = st.plumb || r.dataset.decayed!=='1';
      r.style.display = (okM&&okS&&okP)?'':'none';
    });
    document.querySelectorAll('.day').forEach(function(d){
      var any=[].slice.call(d.querySelectorAll('.ev')).some(function(r){return r.style.display!=='none';});
      d.style.display = any||d.dataset.keep==='1' ? '' : 'none';
    });
  }
  function press(id,on){var b=document.getElementById(id);if(b)b.setAttribute('aria-pressed',on?'true':'false');}
  window.ffSet=function(k,v,btn){
    if(k==='mkt'){st.mkt=v;['f-all','f-kr','f-us'].forEach(function(i){press(i,false);});press(btn,true);}
    if(k==='big'){st.big=!st.big;press(btn,st.big);}
    if(k==='plumb'){st.plumb=!st.plumb;press(btn,!st.plumb);}
    apply();
  };
  window.ffGo=function(id){var el=document.getElementById(id);if(el)el.scrollIntoView();};
})();
"""

def _heat_class(score: int) -> str:
    if score <= 0: return ""
    if score <= 3: return "h1x"
    if score <= 7: return "h2x"
    if score <= 11: return "h3x"
    if score <= 15: return "h4x"
    return "h5x"

def _day_kinds(evs_day: list[Event], d: dt.date) -> list[str]:
    kinds = []
    for e in evs_day:
        if e.feed == "F11" and e.size in ("L", "XL") and e.date == d: kinds.append("krx_expiry")
        if e.feed == "F1" and e.date == d: kinds.append("us_opex")
        if e.feed == "F5" and e.label.startswith("FOMC decision") and e.date == d: kinds.append("fomc")
        if e.feed == "F4": kinds.append("month_end")
    return list(dict.fromkeys(kinds))

def render_html_fragment(ctx: Ctx, days_n: int) -> str:
    days = [ctx.asof + dt.timedelta(days=i) for i in range(days_n)]
    evs = build(ctx)
    piles = pileup_days(evs, days)
    ban = ctx.ov.get("meta", {}).get("short_sale_ban", False)
    h = []
    a = h.append
    a(f"<style>{HTML_CSS}</style>")
    a('<div class="wrap">')
    a('<h1>Forced-Flow Calendar</h1>')
    a(f'<div class="sub">Who is forced to trade, when — US + KRX, all times KST. '
      f'As of <span class="mono">{ctx.asof}</span> · next {days_n} days · '
      f'KR short-sale ban: {"ON" if ban else "off"} · ffcal v0.1</div>')
    a('<div class="legend"><span><b>Size</b> S M L XL = density weight 1/2/4/8</span>'
      '<span><b>Conf</b> # rule · OK confirmed · ~ estimated (dashed)</span>'
      '<span><b>[!]</b> PILEUP = stacked window (2-day density &ge; 14 or 2 XL)</span>'
      '<span><b>plumbing</b> = price effect decayed; risk/execution/attribution only</span>'
      '<span><b>?</b> = pre-registered questions for the print (answer them on the call sheet)</span></div>')

    # --- density + corporate-bid strips (shared day columns) ---
    a('<h2>Density — the shape of the next weeks</h2>')
    a('<div class="stripbox">')
    a(f'<div class="grid" style="grid-template-columns:repeat({len(days)},minmax(34px,1fr))">')
    for d in days:
        s = day_score(evs, d)
        cls = ["cell", _heat_class(s)]
        off = d.weekday() >= 5
        if off: cls.append("off")
        if d in piles and s > 0: cls.append("pile")
        if d == ctx.asof: cls.append("today")
        mon = f"{d:%b} " if (d == days[0] or d.day == 1) else ""
        a(f'<button class="{" ".join(c for c in cls if c)}" onclick="ffGo(\'d{d}\')" '
          f'title="{d:%a %b %d} - density {s}{" [PILEUP]" if d in piles and s>0 else ""}">'
          f'<span class="dw">{d:%a}</span><span class="dn">{mon}{d.day}</span>'
          f'<span class="ds mono">{s if s else "&middot;"}</span></button>')
    a('</div>')
    wins_n = blackout_gauge(ctx, days[0])[1]
    a(f'<div class="rowlab">Corporate bid present (buyback watchlist, of {wins_n}) '
      f'— bars = names NOT in blackout</div>')
    a(f'<div class="grid" style="grid-template-columns:repeat({len(days)},minmax(34px,1fr))">')
    for d in days:
        n_in, n_tot = blackout_gauge(ctx, d)
        present = n_tot - n_in
        pct = 0 if not n_tot else round(100 * present / n_tot)
        a(f'<div class="barcell" title="{d:%a %b %d}: {present}/{n_tot} present">'
          f'<div class="bar" style="height:{max(6, pct) if n_tot else 0}%"></div></div>')
    a('</div></div>')

    # --- pins needed ---
    pins = [e for e in evs if e.confidence == "estimated" and e.size in ("M", "L", "XL")
            and any(e.covers(d) for d in days)]
    if pins:
        a('<h2>Pins needed — estimated dates, confirm on IR/schedule</h2><div class="pins"><ul>')
        seen = set()
        for e in pins:
            key = e.label
            if key in seen: continue
            seen.add(key)
            a(f'<li><span class="mono">{e.date:%b %d}</span> — {_esc(e.label)}</li>')
        a('</ul></div>')

    # --- filters + day cards ---
    a('<h2>Day by day</h2>')
    a('<div class="filters">'
      '<button class="fbtn" id="f-all" aria-pressed="true" onclick="ffSet(\'mkt\',\'all\',\'f-all\')">All markets</button>'
      '<button class="fbtn" id="f-kr" aria-pressed="false" onclick="ffSet(\'mkt\',\'KR\',\'f-kr\')">KR only</button>'
      '<button class="fbtn" id="f-us" aria-pressed="false" onclick="ffSet(\'mkt\',\'US\',\'f-us\')">US &amp; global</button>'
      '<button class="fbtn" id="f-big" aria-pressed="false" onclick="ffSet(\'big\',null,\'f-big\')">L + XL only</button>'
      '<button class="fbtn" id="f-plumb" aria-pressed="false" onclick="ffSet(\'plumb\',null,\'f-plumb\')">Hide plumbing</button>'
      '</div>')
    for d in days:
        todays = [e for e in evs if e.covers(d)]
        if not todays and d.weekday() >= 5: continue
        s = day_score(evs, d)
        n_in, n_tot = blackout_gauge(ctx, d)
        pile = d in piles and s > 0
        a(f'<section class="day{" pile" if pile else ""}" id="d{d}" data-keep="{1 if d==ctx.asof else 0}">')
        a(f'<div class="dayhead"><span class="date">{d:%a %b %d}</span>'
          f'<span class="meta mono">density {s}</span>'
          f'<span class="meta">bid {n_tot-n_in}/{n_tot}</span>'
          f'{"<span class=badge>[!] PILEUP</span>" if pile else ""}'
          f'{"<span class=meta>&larr; today</span>" if d==ctx.asof else ""}</div>')
        for e in todays:
            t = e.time if (e.time and e.date == d) else ""
            band = ""
            if e.end:
                band = f' <span class="mech">(day {(d-e.date).days+1}/{(e.end-e.date).days+1}, through {e.end:%b %d})</span>'
            conf = CONF_GLYPH[e.confidence]
            a(f'<div class="ev" data-mkt="{e.market}" data-size="{e.size}" data-decayed="{1 if e.decayed else 0}">'
              f'<span class="t mono">{t}</span>'
              f'<span class="chip s{e.size}">{e.size}</span>'
              f'<span class="chip{" est" if e.confidence=="estimated" else ""}">{conf}</span>'
              f'<span class="chip mkt">{e.market}</span>'
              f'<span class="evbody"><span class="lbl">{_esc(e.label)}</span>{band}'
              f'{" <span class=plumb>plumbing</span>" if e.decayed else ""}'
              f'<br><span class="mech">{_esc(e.mechanics)}</span>'
              + "".join(f'<div class="wf"><b>?</b> {_esc(q)}</div>'
                        for q in (e.watch if e.date == d else []))
              + f'</span><span class="uses">{",".join(e.uses)}</span></div>')
        for k in _day_kinds(todays, d):
            a(f'<details class="ts"><summary>T-schedule: {k}</summary><ol>')
            for tt, txt in T_TMPL[k]:
                a(f'<li><span class="tt mono">{tt}</span>{_esc(txt)}</li>')
            a('</ol></details>')
        a('</section>')
    a('<div class="foot">Generated by <span class="mono">tools/calendar/ffcal.py html</span> · '
      'design spec: wiki/designs/forced-flow-calendar.md · sizes weight the density score; '
      'estimated dates are dashed — pin them before relying. Rule-zero: the Jul-9 KRX expiry and '
      'Jul-17 US opex T-schedules must be cited in a call sheet before the fact.</div>')
    a('</div>')
    a(f"<script>{HTML_JS}</script>")
    return "\n".join(h)

def render_html(ctx: Ctx, days_n: int) -> str:
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Forced-Flow Calendar</title></head><body>'
            + render_html_fragment(ctx, days_n) + "</body></html>")
