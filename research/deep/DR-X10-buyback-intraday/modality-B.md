## DR-X10 — Modality B (primary/venue mechanics) findings

*Lane: buyback intraday execution. Owner of the mechanics claims for F2 (buyback-dosage
afternoon support). Primary sources: SEC/CFR rule text, Fifth-Circuit ruling, broker/
practitioner execution documentation, issuer 10-Q/10-K repurchase disclosures.*

### Verdict recommendation

**OPEN-TESTABLE-BUT-WEAKENED (confidence MED).** The 10b-18 apparatus F2 relies on is
CONFIRMED verbatim from the rule text, but three mechanics facts cut against F2's *specific*
intraday mechanism, and one breaks its flagship dosage assumption outright: (1) the safe
harbor is **voluntary/non-exclusive**, so the price condition binds only because issuers
*elect* it — it is a chosen constraint, not "state-conditioned BY regulation"; (2) on a
penny-tick megacap the price condition almost never binds, so the regulation-forced "buy into
weakness" asymmetry is weak — this is F2's own stated kill-risk #1, and the mechanics confirm
it; (3) standard buyback execution is **VWAP/POV that tracks volume continuously and often
finishes 15–30 min before the cutoff** — there is no structural reason an "unexecuted afternoon
remainder" concentrates in the afternoon; and (4) **GOOGL cut buybacks to $0 in Q1 2026** (first
zero-buyback quarter in a decade) after the dose already fell from ~5% of ADV in 2024 to ~3.3%
in 2025 — so "4–6% every session for six years" is wrong at the recent end and the GOOGL cell
is **dead forward**. The historical screen (2020–2025 GOOGL dose) is still $0-owned-data
runnable, but the mechanism is day-scale opportunism, not the intraday regulatory asymmetry F2
posits. Timing condition = **last 10 minutes** for megacaps: F2's assumption is CORRECT.

**What would flip it:** a cited intraday study (or an own-data probe) showing that on
1-tick megacap books the 10b-18 price condition *does* bind often enough to produce a
measurable conditional afternoon drift after soft mornings, distinct from generic day-scale
"buy-the-dip" opportunism — i.e. the redistribution F2 needs is a real intraday object, not a
daily one. Absent that, the mechanics support a **daily/day-scale** reading, which is Modality
D's kill target.

### Mechanism

**Who pays.** The corporation. Buyback flow is volume-mandated (board-authorized $ program),
executed via broker POV/VWAP, and price-insensitive within the day. Under a 10b5-1 plan it runs
on autopilot through earnings blackouts and MNPI windows. Persistence is structural: programs
run for years and 10b5-1 plans execute mechanically.

**Why the "price-insensitive, buys-into-weakness" claim is only *partly* mechanical.** Two
distinct forces both tilt buyback fills toward weakness, and F2 conflates them:
- *Regulatory (the price condition):* purchases may not exceed max(highest independent bid,
  last independent transaction). On upticks the issuer's passive bid is left behind; on
  downticks it fills. **But on a penny-tick liquid name (NVDA 1c ≈ 0.6 bps; GOOGL/AAPL/MSFT
  similar), the last-transaction/bid is essentially the current price, so a 3–5% POV order can
  almost always fill without violating the condition.** The regulatory asymmetry is therefore
  near-zero on exactly the names F2 targets — confirming F2's kill-risk #1 from the mechanics
  side.
- *Deliberate (execution strategy):* practitioner guides confirm issuers *choose* to "buy more
  on days of price weakness and hold fire on stronger days" (eOMR algorithms; opportunistic
  OMR). This is real, but it is a **day-scale** tilt (buy weak *days*), not an intraday
  soft-morning→afternoon object. It is also discretionary, hence not reliably price-insensitive.

**Why the "afternoon remainder" clock is unsupported.** Standard execution is VWAP/schedule/POV
that spreads purchases *proportional to volume through the day* — on a U-shaped volume day that
front- and back-loads, it does not "save" a remainder for the afternoon. Practitioner guidance
adds that many programs **stop 15–30 min before the required cutoff** and some avoid the whole
final stretch. So the afternoon (F2's 11:30→15:30 window) is if anything *under*-weighted by
the algo relative to the open, not a reservoir of pent-up completion demand.

**Capacity/dosage.** Public but coarse: Item 703 gives **monthly** shares + average price per
quarter (see C8). No daily data exists (C7). Quarterly÷days is the only obtainable per-session
proxy — F2's crude-proxy kill-risk is unavoidable given the data reality.

### Claims

C1 [CONFIRMED] (T1, 17 CFR 240.10b-18, current text): 10b-18 is a **voluntary, non-exclusive
safe harbor**; failure to meet a condition forfeits the harbor for that day but is *not* itself
a violation. Preliminary Note: "compliance with §240.10b-18 is voluntary." — eCFR/Cornell LII
240.10b-18; Guzman practitioner guide p.6.

C2 [CONFIRMED] (T1, 240.10b-18(b)(2)): **Timing** — a 10b-18 purchase must not be the opening
(regular-way) transaction, and must not be effected during **the last 10 minutes** before the
scheduled close for a security with **ADTV ≥ $1,000,000 AND public float ≥ $150,000,000**, or
the **last 30 minutes** for all other securities. GOOGL/AAPL/MSFT are all in the 10-minute
bucket by orders of magnitude. **F2's "excludes opening print and last 10 minutes" is exactly
right for megacaps.** (Note: it is *not* "first 30 min"; only the opening print is fenced at the
open for actively-traded names.) — eCFR/Cornell 240.10b-18(b)(2); Guzman p.6/p.14.

C3 [CONFIRMED] (T1, 240.10b-18(b)(3)): **Price** — purchase price must not exceed the **higher
of the highest independent bid or the last independent transaction price** in the consolidated
system. Informally an "uptick rule" for issuers. F2's `≤ max(highest independent bid, last
independent transaction)` is verbatim-correct. — eCFR/Cornell 240.10b-18(b)(3).

C4 [CONFIRMED] (T1, 240.10b-18(b)(4)): **Volume** — total 10b-18 purchases on any single day
must not exceed **25% of the 4-week ADTV**. A once-per-week **block** exception exists (one
block that day, no other 10b-18 purchases that day; block ≥ $200k, or ≥5,000 sh & ≥$50k, or
≥20 round lots & ≥150% of volume). The block exception is intact in current CFR text (a
practitioner guide loosely states blocks now count toward the 25% cap — the CFR text governs;
this is immaterial to megacaps, which execute via continuous POV, not weekly blocks). — eCFR/
Cornell 240.10b-18(a)(1),(b)(4).

C5 [CONFIRMED] (T1, 240.10b-18(b)(1)): **Manner** — one broker/dealer per day for *solicited*
purchases; the single-broker condition does **not** apply to unsolicited transactions. — eCFR/
Cornell 240.10b-18(b)(1).

C6 [CONFIRMED] (T1/T3): **10b5-1 mechanics** — megacap buybacks typically run under a written
Rule 10b5-1 plan (schedule/algorithm set when clean of MNPI) that "operates automatically,"
allowing repurchases to **continue through blackout periods** (e.g. pre-earnings) without
insider-trading exposure. 2023 SEC amendments added an issuer **~30-day cooling-off** before
trades commence and require quarterly disclosure of plan adoption/termination. Implication for
F2's blackout prong: 10b5-1 names *keep buying through earnings blackouts*, so the "attenuated
by construction" caveat F2 pre-states is correct. — Guzman p.6–8; SEC Rule 10b5-1 final rule
(2023).

C7 [CONFIRMED] (T1, court): The SEC's May-2023 **Share Repurchase Disclosure Modernization
Rule** — which would have required a **daily** buyback table (Ex-26 to 10-Q/10-K) per name per
quarter — was **VACATED by the U.S. Fifth Circuit on Dec 19, 2023** (found arbitrary/capricious
under the APA). **No daily per-name buyback data exists.** The pre-2023 regime is restored:
Item 703 gives **monthly** totals only. — *Chamber of Commerce v. SEC*, 5th Cir. Dec 19 2023;
Paul Weiss / Davis Polk / Orrick client memos. (Guzman guide, written ~2025, erroneously
describes the daily regime as in force — it is not.)

C8 [CONFIRMED] (T1): **Available dosage data** = 10-Q/10-K Item 703 monthly table: for each
month of the quarter, total shares repurchased, average price paid, shares under announced
program, remaining authorization. Monthly granularity, quarterly filing. This is the exact
object F2 freezes (PIT-lagged to filing date). Per-**day** dose is not disclosed anywhere. —
Reg S-K Item 703; Guzman p.14.

C9 [CONFIRMED] (T1/T3, FY2024–Q1 2026): **GOOGL dose is large but sharply declining and now
zero.** Alphabet repurchased **$62.2B (2024)** and **$45.7B (2025)**, then **$0 in Q1 2026** —
the first zero-buyback quarter in ~a decade — redirecting cash to AI capex ($175–185B/yr
guided). Implied participation (repurchase ÷ ~252 sessions ÷ ~$4.5–5.5B dollar-ADV): **~5.0–5.5%
(2024) → ~3.3% (2025) → 0% (2026 YTD).** F2's "≈$250–280M/session, 4–6% every session for six
owned-quote years" holds for **2020–2024** but is **wrong for 2025 and dead for 2026**; the
GOOGL cell (C1) cannot be deployed forward. — 24/7 Wall St (2026-07-22); Alphabet Q1-2026 10-Q;
financecharts/macrotrends GOOGL series.

C10 [CONFIRMED] (T1/T3, FY2025): **Placebo/tier context for the dose ladder.** AAPL FY2025
(ended 2025-09-27): **$89.3B** repurchased (402M sh); dollar-ADV ≈ **$11.7B** → ~$354M/session
→ **~3.0% of ADV** (~3.4% in the heavy Dec-2025 $25B quarter). MSFT FY2025: **$18.42B**
buyback; dollar-ADV ≈ $9–10B → ~$73M/session → **~0.7–0.8% of ADV**. So the *dose cross-section*
F2 wants as its identification design exists (GOOGL 2024 ~5% > AAPL ~3% > MSFT ~0.8% > TSLA/MU
~0), but the top of the ladder is time-varying and recently collapsed. Dollar-ADV figures are
approximate (price×volume / vendor 3-mo averages), flagged as estimates. — Apple FY2025 10-K;
Shacknews/MSFT FY25 Q4 8-K; finbox/financecharts dollar-volume.

### Constraint gates

| # | Gate | Verdict | Clause |
|---|---|---|---|
| 1 | Latency | PASS | Decision instant is a scheduled clock (11:30 ET); 5–25 s keying pre-positionable. |
| 2 | Access | PASS | Long GOOGL/AAPL/MSFT at $1k–$10k, plain marketable order; no special order type. |
| 3 | Session | PASS | RTH, exit 15:30; clear of the 10b-18 close fence and the 15:50 flat rule. |
| 4 | Data | PASS | Owned SIP quotes + $0 SEC Item 703 (M21 tooling); daily dose does NOT exist (C7) → proxy only. |
| 5 | Fill realism | PASS | Taker-priced legs, no maker/auction assumption; mechanics don't add fill ambiguity. |
| 6 | Statistics | PASS(historical)/FAIL(forward) | ~513 GOOGL soft-morning events on TRAIN; forward is dead (C9) — historical screen IS the test. |
| 7 | Protocol | PASS | Named payer stated pre-result; C3 placebo-diff is a registered kill; charges the reversion-adjacent family. |

**Survivor-profile score: 2 / 5.**
1. Single-print/auction execution — **0** (continuous-market taker legs, fill ambiguity present).
2. Scheduled decision instant — **1** (11:30 clock; latency pre-positionable).
3. Named price-insensitive payer — **½ → round to 0** (payer is named and real, but the
   price-insensitivity is *day-scale/discretionary*, and the flagship name's dose is now zero;
   not the clean price-insensitive-flow the champion has). Scored **0**.
4. Historically testable on owned/≤$100 data — **1** ($0: owned quotes + SEC XBRL).
5. Effect ≥ 2× cost burden — **0** (prior +4–8 bps gross straddles the 5–6.5 bps floor; mechanics
   push the conditional piece *down*, not up).
Net **2/5** — the brief's threshold for "needs an extraordinary reason to research at all."

### Economics sketch

F2's own numbers: GOOGL 11:30→15:30 σ ≈ 90 bps → se ≈ 4.0 bps → detects ≥ 8 bps; conditional
effect prior +4–8 bps gross; GOOGL round-trip cost floor ≈ 2.5–3.3 bps → 2× ≈ 5–6.5 bps. The
mechanics adjust the *prior* downward: (a) the regulatory asymmetry the +4–8 bps leans on is
near-zero on penny-tick names (C3 + Mechanism), (b) VWAP/POV execution gives no afternoon
concentration, (c) the day-scale opportunism that *is* real is already partly impounded and is
Modality D's "daily-only" kill. Net prior after mechanics: **BETWEEN-leaning, modal NULL**, with
the added structural problem that the strongest-dose name (GOOGL) is now a zero-dose name
forward. Comparison line: **champion = +2.5 bps/event dev / +12.5 bps holdout** on a single-print
auction (survivor 5/5); F2 is a continuous-market 2/5 with a weakened mechanism.

### Proposed next test (historical screen only — forward is dead for GOOGL)

- **Hypothesis:** on soft-morning sessions (own 09:35→11:30 return in TRAIN bottom tercile),
  high-buyback-dose names show a positive conditional 11:30→15:30 mid-drift, monotone in dose
  tier, that survives a placebo-tier difference (GOOGL/AAPL minus TSLA/MU).
- **Named payer:** corporate 10b-18/10b5-1 repurchase flow (day-scale opportunistic tilt into
  weakness) — *not* an intraday regulatory asymmetry (mechanics do not support that).
- **Data:** owned SIP quotes + SEC Item 703 monthly dose (M21 tooling), **$0**. Dose PIT-lagged
  to filing date, ranks frozen outcome-blind. **Restrict the GOOGL high-dose window to
  2020-01→2024-12** (dose real); treat 2025 as declining-tier and 2026 as zero-tier — do NOT
  pool a zero-dose 2026 GOOGL into the high-dose cell.
- **Universe:** GOOGL/AAPL (high/mid dose), MSFT (low dose), TSLA/MU (placebo). Optionally add
  AMAT/LRCX/KLAC if quotes owned.
- **Expected n & power:** ~513 GOOGL soft-morning events (of 1,540) over 2020–2024; per-event σ
  ~90 bps → se ~4 bps → detects ≥ 8 bps. Ladder is a sign/ordering test (se ~6 bps), not a
  levels test. Underpowered forward by construction.
- **A-priori thresholds:** screen PASS = pooled gated mid-mean ≥ 8 bps AND day-clustered CI-lo
  > 0 AND **C3 placebo-tier difference CI-lo > 0** (separates buyback support from generic
  dip-buying). Economics only on screen PASS, at 2× cost floor (≥ 6.5 bps net).
- **Promotion rule:** VALIDATE confirm per house pattern; forward is a bookkeeping ledger only
  (cannot power).
- **Kill criteria:** C3 fails (placebo shows same lift) ⇒ mechanism dead; or dose-monotonicity
  sign test fails ⇒ family closes with a conditioner note (admissible long-side feature), not a
  revival promise.
- **Trial family:** charges the buyback/reversion-adjacent family (M18/DR-X7 lineage); one
  pooled TRAIN look.

### Sources

1. **T1** — 17 CFR 240.10b-18, *Purchases of certain equity securities by the issuer and
   others*, current CFR text (voluntary safe harbor; manner/timing/price/volume conditions;
   ADTV $1M / float $150M / 10-min vs 30-min thresholds; 25% ADTV + block exception). eCFR
   (current) / Cornell LII mirror: law.cornell.edu/cfr/text/17/240.10b-18.
2. **T1** — SEC Rule 10b5-1 final amendments (adopted Dec 2022, eff. 2023): issuer ~30-day
   cooling-off; quarterly disclosure of plan adoption/termination.
3. **T1/court** — *Chamber of Commerce of the USA v. SEC*, 5th Cir., **Dec 19, 2023** — vacatur
   of the Share Repurchase Disclosure Modernization Rule (daily buyback table). Summarized:
   Paul Weiss, Davis Polk, Orrick, Fried Frank, Covington client memos (Dec 2023–Jan 2024).
4. **T1** — Reg S-K **Item 703** (monthly repurchase table in 10-Q/10-K) — the surviving
   disclosure regime.
5. **T1** — Alphabet Inc. Form 10-Q, Q1 2026 (repurchases = $0); Apple Inc. Form 10-K FY2025
   ($89.3B / 402M sh); Microsoft FY2025 Q4 8-K ($18.42B FY2025 buyback).
6. **T3** — Guzman & Company, *Share Buybacks for US Corporations: Practitioner's Guide* (2025):
   execution best practices (VWAP/POV, buy-on-weakness, internal 15–20% ADTV caps, stop 15–30
   min before cutoff, one-broker coordination); eOMR algorithms (~2–3% VWAP-discount claim);
   10b5-1 through blackouts. *Note: its daily-disclosure section is out of date post-vacatur.*
7. **T3** — Mayer Brown, *What's the Deal? Rule 10b-18* (2020); Skadden 10b-18 note (2020) —
   condition summaries.
8. **T3** — 24/7 Wall St (2026-07-22), "Alphabet Just Cut Share Buybacks To $0"; financecharts /
   macrotrends GOOGL & AAPL repurchase series; finbox/financecharts dollar-volume (ADV
   estimates, flagged approximate).

#### Queries used
- `Rule 10b-18 safe harbor conditions price volume time single broker exact text SEC`
- `Rule 10b-18 time condition last 10 minutes 30 minutes close ADTV public float threshold`
- `SEC 2023 share repurchase disclosure rule Fifth Circuit vacated daily buyback data`
- `Alphabet GOOGL 10-Q 2026 stock repurchases quarterly amount buyback`
- `Apple AAPL Microsoft MSFT 2025 2026 quarterly share repurchases 10-Q dollar amount`
- `buyback execution desk VWAP POV algorithm 10b5-1 plan corporate repurchase Goldman Morgan Stanley participation rate`
- `Alphabet 10-Q first quarter 2026 zero share repurchases $0 buyback halt confirmed`
- `Apple annual share repurchases trailing 2025 total; AAPL average daily dollar trading volume 2025`
- `Microsoft fiscal 2025 total share repurchases dollar amount annual buyback`
- WebFetch: eCFR 240.10b-18 (redirected); Cornell LII 240.10b-18; SEC 10b-18 FAQ (403);
  Mayer Brown 10b-18 PDF; Guzman practitioner guide PDF; financecharts GOOGL series;
  Northern Trust 10b5-1 brochure (ECONNRESET).
