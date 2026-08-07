# Every-day intraday hypotheses — orchestrator max-effort pass (2026-07-23)

Candidate science, NOT registrations. Written against: ORIENTATION.md (2026-07-22),
EXHAUSTION_MAP.md, HYPOTHESES_INTRADAY_COMBINATION.md (post-withdrawal state), DR-X9
report, M27 registration (`gap_day_reversion_v1`, the standing main-goal family), and the
2026-07-23 user decision (close-auction direction terminated; event windows = side support).
Constraint set honored throughout: manual 5–25 s keying, $10k research book, RTH, flat
≤ 15:45–15:50, no close-auction signal or edge in any disguise, owned data + ≤ ~$2 new.

## 0. The structural narrowing (a claim, not filler)

At this latency and universe, the set of flows that recur EVERY session intraday and have a
price-insensitive payer is enumerable. I enumerated it:

| Payer class | Daily size in our names | Accessible trace at 5–25 s? | Status |
|---|---|---|---|
| Institutional parent-order completion (VWAP/POV/IS algos) | ~30–40% of continuous volume | quote-book footprint (depth persistence) — axis NEVER opened by any dead family | **F1 below** |
| Corporate buyback execution (10b-18 POV algos) | GOOGL ~4–6% of own ADV every session; tier-2 semis ~0.5–1.3% | dose is public (10-Q), regulation shapes intraday state-dependence | **F2 below** |
| Opening-auction unexecuted residue | episodic-large, daily-small | owned NOII open windows; fenced by M6b/M24 lineage | **F3 below (fenced lane)** |
| Options dealer delta/charm/vanna re-hedge | real, daily | no owned options history; GEX forward-only + banned from gated results; OPRA gone | EMPTY-FOR-US (data) |
| Retail marketable flow / internalizer inventory | small at megacap scale | sub-penny print ID needs full trades (owned: 5 names ragged); predictive horizon = days | EMPTY (horizon + data) |
| ETF AP creation/redemption; index tracking | large | machine-speed arb; tracking flow close-benchmarked (banned adjacency) | EMPTY-STRUCTURAL |
| Sec-lending / T+1 settlement mechanics | — | GC megacaps: no recalls, no buy-ins; settlement flow is post-close | EMPTY-STRUCTURAL |

Everything else recurring daily is either killed (sub-15-min fades, reversion, TOD harvest,
lead-lag, macro continuation, maker economics, bar-tier ML) or banned (close auction).
So an every-day book for THIS program can only be built from payer classes 1–2, plus the
open-side residue, stacked with M27 (open-digestion payer). That is the whole space; I
looked for a fourth class and did not find one with a nameable payer (see §5).

Doctrine compliance: every hypothesis below is screen-first (conditional MID-alpha with a
registered bar BEFORE any economics — the M18 corollary), single frozen decision instants,
taker-priced legs per COST_MODEL v1, no maker credit, no auction prints anywhere.

---

## F1 — Institutional completion-footprint continuation (the depth axis)

**The gap being exploited in OUR OWN data.** `bbo1s` carries `bid_size`/`ask_size` at 1 s
for 10 names (core-5 2020-01→2026-05+, new-5 2023-08→2026-05). No registered family ever
consumed displayed depth: the v1 feature registry (`features/slow.py FEATURE_COLS`) is 100%
bar-derived (returns/vol/VWAP/volume/bar-proxy flow). The re-skin fence ("estimator swap ≠
new information set") cuts the other way here: this is an information-set expansion with NO
estimator — one frozen sign rule.

**Mechanism / who pays.** A parent order worked by a schedule-constrained algo must complete
regardless of price — the constraint is completion, not level. While working it leaves a
public trace: persistent one-sided displayed depth (child slices + repeated same-side
liquidity consumption) over tens of minutes. Conditional on a morning footprint, the
afternoon still contains the unexecuted remainder → same-direction pressure for hours. The
payer persists because order-splitting IS optimal execution; the footprint is a structural
consequence institutions cannot remove, only dilute (dark/midpoint). They pay impact all
afternoon; we hold WITH the remainder.

**Why it might be zero (stated before any look).** Propagator/transient-impact math says the
conditional drift given PUBLIC information ≈ 0 even when flow memory is real — the price
path can already embed expected future child orders. And on tick-constrained books (NVDA:
1c on ~$170 = 0.6 bps) touch depth is HFT queue skew that decorrelates in seconds. The
design must therefore (a) use PERSISTENCE over 45–90 min (MM skew dies in seconds–minutes,
parent footprints don't), and (b) pre-check mechanism before any return claim.

**Frozen rule sketch (register en bloc, variant budget ~8).**
- State per name at decision: over W, at 1 s: `DI` = mean dollar-depth imbalance
  (bid$−ask$)/(bid$+ask$); `PERS` = share of seconds with sign matching sign(DI).
- Fire iff |DI| ≥ TRAIN-frozen per-name tercile AND PERS ≥ 0.60. Direction = sign(DI).
- Cells: **C1** W=10:30–12:00 → enter 12:00:00+latency, exit 15:30:00 (210 min).
  **C2** = C1 + require mid-drift co-sign over W. **C3** W=12:30–14:30 → 14:30→15:45
  (the completion-hour cell; exit 15:45 keeps clear of last-10-min mechanics).
  **XS arm**: same instants, rank DI across quoted names, long top-2 / short bottom-2
  equal-$ (one decision, 4 tickets; needs a plan-schema ruling: basket-as-one-plan,
  M15 precedent).
- **Anti-re-skin prong (pre-registered):** pooled regression of h-return on
  {sign(r_morning), sign(gap)}; a cell passes ONLY if the footprint adds conditional mean
  BEYOND past-return signs — the killed TOD/return signal is included as a control, so this
  cannot be first→last-HH momentum in disguise (Rosa-kill honored, not dodged).
- **Mechanism pre-check gating the look (prong 0, ~$0):** on the trades-owned subset
  (MU 2024-01+; NVDA/TSLA/AMD/GOOGL 2025-09+), corr(DI/PERS state, realized Lee-Ready
  signed-flow imbalance over W). If ρ < 0.10 pooled, the footprint premise is dead and NO
  return look is spent. This is the cheapest decisive test in this memo.

**Numbers.** n: core-5 ~1,540 TRAIN sessions ×5 + new-5 ~640 ×5 ≈ 10,900 name-days; tercile
× PERS gate → ~2,500 fired, ~1,500 clustered sessions. Per-event σ (12:00→15:30, U-shape
discounted): NVDA ~150, TSLA ~200, GOOGL ~90, new-5 ~110–140 → pooled per-session
mean-of-fires σ ≈ 105 bps → **se ≈ 2.7 bps** → CI>0 detectable iff true mean ≥ ~5.5 bps.
XS book σ ≈ 87 bps/day (ρ≈0.55 within-sector cancels), se ≈ 2.9 — similar screen power,
but halves per-plan σ and removes sector-day exposure (better MinTRL, cleaner forward).
Cost floor (M27 construction): core-5 RT ≈ 2.5–4 bps, new-5 ≈ 4–7 → 2× floor ≈ **5–10 bps**.
So screen bar and economic bar coincide at ~6–8 bps: register screen PASS = pooled gated
mean ≥ 6 bps AND day-clustered CI-lo > 0 AND survives the return-sign control. Forward
arithmetic if it ever gets there: ~300–450 plans/yr under k=2; at true +6 bps net,
(1.96·105/6)² ≈ 1,180 plans ≈ 2.6–3.9 yr single-name, ~1.5–2 yr XS — pre-stated slow burn.
**Effect-size prior, honest:** field analogues (flow-memory continuation at day scale)
suggest +2–8 bps gross — the modal outcome is BETWEEN or a clean NULL that permanently
prices the depth axis. That is still the best information-per-dollar available: $0 data.

**Strongest kill-risk.** Parent flow on megacaps now executes largely dark/midpoint/hidden;
XNAS displayed touch (which is not even the SIP NBBO — L9) may carry no parent trace at
all → prong 0 fails, family closes in a day for free.

**Fence audit.** Not sub-15-min (3.5 h). Not reversion (continuation). Not bar-tier ML (no
estimator; new info set). Not TOD harvest (state-based + killed signal as control). Not
lead-lag (XS arm ranks own-name states; no convergence claim) — kinship to dead M7 (daily
XS reversal) is nil, disclosed anyway.

---

## F2 — Buyback-dosage afternoon support (the 10b-18 asymmetry)

**Mechanism / who pays.** Rule 10b-18's price condition (repurchase ≤ max(highest
independent bid, last independent transaction)) makes the corporate buyback algo
STATE-CONDITIONED BY REGULATION: it cannot lift into strength, so it goes passive on
upticks and accumulates into weakness. The safe harbor also excludes the opening print and
the last 10 minutes — i.e., the one large recurring flow that regulation fences OUT of the
auctions and INTO exactly our continuous window (09:30+–15:50). The payer is the
corporation: volume-mandated (announced $ programs, executed via broker POV), price-capped,
utterly price-insensitive within the day, and it FILES ITS OWN DOSE quarterly. Persistence:
programs run for years; 10b5-1 plans execute mechanically.

**Dosage (to be verified from XBRL in the probe; ranks are what get frozen, PIT-lagged to
filing dates per landmine L5):** GOOGL ≈ $250–280M/session vs ~$5–6bn ADV → **4–6%
participation, every session, for six owned-quote years** — the largest known-dose
recurring intraday flow in the universe, and GOOGL is precisely the name M12 showed has NO
close-rebalance complex (its flow is intraday, consistent with its close-deadness). Tier-2:
AMAT/LRCX/KLAC ≈ 0.6–1.0%, NVDA ≈ 0.3–0.7%, TXN trough-then-ramp (≈0.2% 2023-24 → ≈1%
2025-26: a within-name dose step inside owned quotes). Placebo tier: TSLA = 0, MU ≈ 0.
The dose cross-section is a built-in identification design no other flow offers.

**Frozen rule sketch (en bloc, budget ~8).**
- Event: name's 09:35→11:30 return in its own TRAIN bottom tercile ("soft morning" — the
  state where the price condition binds least and the algo is most present).
- **C1 (GOOGL cell):** long GOOGL 11:30:00+latency → 15:30:00 taker, ex-blackout sessions.
- **C2 (dose ladder):** same rule all 10 names; registered prediction = afternoon mean
  MONOTONE in dose tier (GOOGL > tier-2 > placebo), sign test on the ordering.
- **C3 (placebo-diff gate):** GOOGL-minus-placebo-tier afternoon mean > 0 with CI. This is
  the prong that separates "buyback support" from the dead generic buy-the-dip: if TSLA/MU
  show the same lift, the mechanism claim dies regardless of C1.
- Blackout prong report-only (10b5-1 plans continue through blackouts post-2023 — the
  contrast is attenuated by construction; pre-stated so it can't be quietly dropped later).
- Screen = mid-alpha only; economics only on screen PASS (same M20/M27 ordering).

**Numbers.** GOOGL TRAIN: ~513 soft-morning events (tercile of 1,540). σ(11:30→15:30
GOOGL) ≈ 90 bps → **se ≈ 4.0 bps** → detects ≥ 8 bps. Dose-tier diff se ≈ 6 bps → the
ladder is a sign/ordering test, not a levels test — powered as such. Cost floor GOOGL RT
≈ 2.5–3.3 bps → 2× ≈ 5–6.5 bps. Conditional effect prior: the daily clip's square-root-law
level impact ≈ 0.5·σ_d·√0.05 ≈ 20 bps is impounded; the tradable piece is the
state-dependent redistribution, plausibly 20–40% of it on soft afternoons → **+4–8 bps**
— at or just above the economic bar on the ONE name where the dose is 4–6%. n/year
forward: ~85 GOOGL events/yr; per-event σ 90 → at +6 bps true, ~865 events ≈ a decade
single-name — so the historical screen IS the test; forward alone can never power this.
Honest consequence: if the screen returns BETWEEN, the family closes with a conditioner
note (admissible feature for any future long-side plan), not a revival promise.

**Strongest kill-risk.** On a 1-tick book the price condition almost never binds for a 5%
POV algo (it is always inside last-transaction except at fresh highs) → no conditional
asymmetry exists, only impounded level support → C3 fails. Second: quarterly dose ÷ 62 is
a crude daily proxy; execution is lumpy (10b5-1 grids, ASR tranches) and mis-timing dilutes
the event definition toward zero.

**Cheapest decisive test.** $0: SEC XBRL repurchase series (tooling exists from M21; UA
landmine L8 applies) + owned quotes; one pooled screen with C1–C3. Pre-check worth one
agent-day BEFORE registration: a half-day prior-art wave (charge below) — if a competent
intraday buyback-execution study already shows zero conditional footprint, kill free.

**Fence audit.** Adjacent to the reversion graveyard (M18/DR-X7) — differentiators, stated
plainly: named non-close intraday payer with public dosage; placebo-tier gate C3 makes
"generic dip-buying" a registered kill condition rather than an escape hatch; long-only
one-name once-a-day expression is not an OU system. Adjacent to "flow-conditioned
reversion (M19)" — that kill was specifically LETF flow being close-only; buyback flow is
documented intraday-only. Neither fence row names this payer.

---

## F3 — Opening-imbalance residue continuation (quantity, not price) — FENCED LANE

**Mechanism.** MOO/opening-benchmarked submitters whose demand exceeds what the cross
paired (unpaired imbalance at 09:28:30) do not vanish; the residue chases in the continuous
book over the next 30–90 min. Payer: overnight retail sweeps + open-benchmarked passive
flow, price-insensitive by mandate, slow by queue position. Quantity object (imbalance
ratio), NOT the price-dislocation object M24 faded, and NOT an auction entry (M6b): entry
09:35:00+latency WITH the residue sign, exit 11:00:00, quote legs only, gate = top-quartile
|unpaired/paired| frozen on TRAIN.

**Numbers.** 10 quote names × NOII open windows (owned since 2023-01 for the broad set;
core since 2020): ~6,900 name-days 2023-08+, quartile gate → ~1,700 fired, ~600 clustered.
σ(09:35→11:00) ≈ 55–75 bps → se ≈ 2.7–3.3 bps → detects ≥ ~6 bps. Cost 2× floor ≈ 5–10.
Field prior: post-open imbalance continuation exists in older market structures
(Cushing–Madhavan class); modern megacap magnitude unknown.

**The fence, stated without spin.** The exhaustion map's "Opening cross, smarter structure"
row is CLOSED with the M24 look spent, and M24's post-hoc peeks (gap-agreement 2×2) touched
this anchor's neighborhood. A quantity-continuation object is materially different
(quantity vs price; continuation vs fade; continuous exits vs print-to-print), but it
shares the anchor and the family lineage — so this proposal is conditional: (i) prior-art
wave first, (ii) registration charges M6b+M24 debt, (iii) the orchestrator rules
historical-look-vs-forward-only; if forward-only, ~600 fired/yr gives se ≈ 3 bps after
~1 yr of accrual — viable, just slow. I rank it below F1/F2 because the fence ruling, not
the science, is the binding risk.

---

## F4 — Complex-peer earnings digestion (SIDE SUPPORT ONLY, per mandate)

One compact lane, event-class, ~40–100 usable days/yr: after a complex member's AMC print
(M21 verified calendar), index/beta repricing of PEERS is instant, but fundamental
read-through reallocation (WFE/HBM/analog capex chains) executes next-RTH via parent
orders. Rule sketch: day1 peers only, direction = same-sign as announcer's overnight move,
gate |move| ≥ 3%, enter 09:35+latency, exit 14:00. Power: ~320 peer-events/yr but
day-clustered ~40 → per-day basket se over 5 owned years ≈ 6 bps → detects ≥ 12 bps; prior
5–15 → underpowered-to-borderline, and it sits adjacent to TWO fence rows ("event-day
intraday taker" field-kill — announcer-day object, arguably distinct; "cross-name lead-lag"
— structural kill for the continuous book, arguably distinct for a once-a-day event
trigger). Verdict: worth a screen only because $0 and the M27/F1 harness reuses; register
last, expect UNDERPOWERED, say so in the registration.

---

## 5. Sub-directions examined and declared EMPTY (reasons, not shrugs)

1. **Options-hedging clocked flows** (0DTE/weekly charm-vanna unwinds, Friday pins): no
   owned options history, OPRA entitlement gone, GEX collector forward-only AND banned from
   gated results, expiry_pin closed NO-EVIDENCE; the effect class is industrialized
   (SpotGamma et al). EMPTY-FOR-US on data; revisit only if a $0 PIT gamma proxy appears.
2. **T+1 / share-lending / settlement cycles:** our names are general-collateral; no
   recalls, no threshold-list buy-ins; T+1 flows are post-close; PDT abolished. Nothing
   fires intraday in this universe. EMPTY-STRUCTURAL (would require hard-to-borrow small
   caps — different data, different mission).
3. **ETF creation-basket / index-tracking intraday:** AP arb is machine-speed; tracking
   flow is close-benchmarked (banned adjacency); SMH/SOXX NAV-basis state adds nothing at
   5–25 s. EMPTY-STRUCTURAL.
4. **Within-complex idio mean-reversion book:** triple-fenced (M7, M18+DR-X7, DR-X4) and I
   have no new information set to offer it — depth is F1's, and F1 is a continuation
   object. COLONIZED; do not re-enter.
5. **Megacap own-gap digestion:** M24 diagnostic showed champion-5 opens efficient; the
   down-liquidity version is M27's registered territory. COVERED.
6. **Dark-pool share conditioning:** FINRA ATS data is weekly with 2–4 wk lag — wrong
   frequency for daily state. EMPTY-FOR-US.
7. **Premarket structure:** retail-thin, duplicates the gap information M27 already
   conditions on. FOLDED into M27's feature set.

## 6. Self-critique and ranking (P = survives its registered look to CI-lo > 0 on ≥1 cell)

| Rank | Idea | P(mid-alpha screen) | P(clears 2× floor too) | Dominant failure mode |
|---|---|---|---|---|
| 1 | F1 footprint (XS arm) | 0.20 | 0.08–0.12 | depth is HFT skew; parent flow dark |
| 2 | F2 buyback (GOOGL cell) | 0.12 | 0.06–0.10 | price condition never binds; dose proxy too crude |
| 3 | F3 open residue | 0.05–0.08 | 0.04 | fence forces forward-only; modern magnitude ~0 |
| 4 | F4 peer digestion | 0.05 | 0.03 | underpowered by construction |

Joint P(≥1 promotable) ≈ 0.3. The modal outcome of this entire memo is three obituaries
and one BETWEEN — stated now so nobody is surprised later. That is the honest price of an
every-day edge at a 2–15 bps cost floor in names this efficient.

**The single bet: F1, XS arm, C1 (12:00→15:30).** Reasons: (i) the payer class is the
largest recurring flow in equities and cannot exit the market; (ii) the data is 100% owned
with six years of depth nobody in this program has ever read; (iii) se ≈ 2.7–2.9 bps means
a realistic +6 bps effect is actually DETECTABLE inside the owned sample — the first
every-day design in the program where the power arithmetic closes without forward-decade
fantasies; (iv) prong 0 (depth-vs-signed-flow correlation on the trades subset) can kill it
for $0 in a day before any look is spent — maximal information, minimal debt; (v) both
outcomes are permanent: PASS opens the only new axis we own, NULL prices that axis forever
and the map gets a row either way.

## 7. Ready-to-run wave charges (research-gap protocol)

- **DR-X10 (half-day, cheap): buyback intraday execution footprint** — prior art on
  10b-18 price-condition state-dependence, intraday support, 10b5-1 mechanics post-2023,
  ASR share. Kill bar: a competent intraday study showing zero conditional footprint on
  megacaps ⇒ F2 dies pre-registration. Modality D must hunt "buyback anomaly is daily/
  monthly only" evidence.
- **DR-X11 (half-day): opening-imbalance residue** — Nasdaq opening cross unpaired-order
  literature + practitioner evidence of post-open continuation; required by the F3 fence
  before any registration.
- **DR-X12 (optional, 1 lane): TOB depth-imbalance horizon decay** — any published decay
  curve of depth-state predictability beyond minutes on tick-constrained megacaps; expect
  thin literature (that thinness is part of why F1 is worth a look); refuters hunt for
  "displayed depth is uninformative at institutional horizons" results.

## 8. Execution order proposed

1. F1 prong 0 (mechanism pre-check, $0, no look) — one agent-day after TXN/AMAT quotes
   land. If ρ ≥ 0.10: register F1 en bloc (cells C1–C3 + XS + controls + prong bars),
   one pooled TRAIN look, VALIDATE confirm per house pattern.
2. Fire DR-X10; on survival, register F2 (C1–C3) — $0, XBRL probe first (doses frozen
   outcome-blind, PIT-lagged).
3. DR-X11 → orchestrator fence ruling on F3 → register or park.
4. F4 last, explicitly labeled side-support/UNDERPOWERED-expected, only if harness reuse
   makes it ~free.
5. Portfolio thesis for the every-day goal: M27 (open digestion, 09:35) + F1 (completion
   footprint, 12:00/14:30) + F2 (buyback support, 11:30) are three different payers at
   three different clocks — the every-day book the mandate asks for emerges from stacking
   ρ-independent streams, not from forcing one signal to fire daily. Measure pairwise ρ
   from day one (the M24 ρ-lesson).

---
---

# ROUND 2 (2026-07-24) — post-mortem constraints + the R2-A candidate

Round-1 outcome, priced: F1 dead (prong 0 — displayed depth is HFT queue skew), F2 dead
(DR-X10 — dose too diffuse, priced axis), F3 dead (DR-X11 + prong 0 — residue cancels at
the cross; ρ −0.0004 on 11,487 name-days), F4 never worth its power cost, M27 dead
(effect real, taker floor 2×). The §0 enumeration is fully spent AS EXPRESSED. The round-1
modal forecast ("three obituaries and one BETWEEN") was optimistic by one BETWEEN.

## R2 §0 — Constraint update (the four kill classes, now binding on all new ideas)

K1 (M27): if the payer is "gap digestion" priced on price features alone, the taker floor
eats it — any gap-adjacent idea must carry information BEYOND the gap and/or a spread-free
leg. K2 (F1): no displayed-book-state signals; the visible book is queue games. K3 (F2):
payers must be time-concentrated and large relative to ADV — diffuse POV flow ≤1% ADV is
priced. K4 (F3/DR-X9): informational states disseminated to the whole market at machine
cadence (NOII, macro prints) are consumed before manual latency — UNLESS the expression
venue is a single print we can pre-position into.

The K4 exception clause is the round-2 thesis: **the surviving expression class at manual
latency is the pre-positioned single print.** We own one auction door that is not banned
(the open), and the one documented open-print inefficiency with a public signal is Brown's.

## R2-A — Open-print retail-flow fade (Brown-class) — THE CANDIDATE

**Mechanism.** Retail off-exchange odd-lot flow on day t−1 (public in TAQ since 2013)
predicts an overnight run-up and an intraday-day-t REVERSAL: Brown ("The Quote Not Taken",
SSRN 5498938, sample 2013–2022, refuter-verified 2026-07-23): L/S on t−1 imbalance earns
+9.38/+5.65 bps (EW/VW) overnight, then **−12.27/−6.84 bps intraday day t** (t≈−13/−7),
~half inside the first 5 minutes. Payer: yesterday's retail herd (price-insensitive,
attention-driven) whose overnight-queued flow overprices the open; capture is AT the
opening cross (spread-free by construction, <1 bp fee; "profits fall to near zero" at
bid/ask). Outsider-capturable per the paper's own framing; binding constraint is SIZE
(thin at-open books) — a constraint a $10k book does not feel.

**Why it clears the kill classes.** K1: the signal is FLOW, claimed to discriminate
flow-driven gaps (revert) from news-driven gaps (don't) — information beyond price, and
the prong-0 gate ENFORCES incrementality by residualizing on the gap. K2: tape prints,
not displayed book. K3: retail flow on these names is large and the expression is
time-concentrated at one print. K4: expression = pre-positioned on-open order (keyed any
time before 09:28; zero latency pressure — the friendliest execution shape this program
has ever evaluated).

**Fence audit (all clear, with receipts):** NOT M6b/M24/F3 (those consumed NOII-feed
state; this consumes the prior-day tape — a data class no registered family ever used).
NOT M7/grok-daily-swing (price-based XS reversal at daily horizons; this is
flow-conditioned, intraday-only, flat by 15:45–15:50). NOT M27 (price-only gap fade on
semis — and R2-A must PROVE incrementality to it at prong 0 or die as redundant). The
round-1 "retail flow — EMPTY (horizon+data)" row is legitimately reopened: named paper,
new venue expression (open print), new data class (own-tape retail proxy). Close-auction
ban untouched (open side; exits ≤15:45 taker — no MOC/LOC leg anywhere).

**Honest headwinds, stated before the data speaks:** (i) Brown's VW intraday number is
−6.84 L/S ⇒ ~3 bps/leg on megacap-tier names — our M24 diagnostic (champion-5 opens
efficient) agrees; the live tier is the semis, where we must backfill trades ($0, Alpaca).
(ii) Sample ends 2022; the paper went public 2025-09 as a job-market paper — decay risk is
real and unmeasurable until we look. (iii) Odd-lot flow ≠ all retail (round-lot retail
exists); proxy noise dilutes. (iv) Our panel is 10 names × ~2.3 yrs max — power is
marginal for effects under ~10 bps; the prong-0 pre-declares a PARK-UNDERPOWERED outcome
to keep us honest rather than letting a spanning CI masquerade as a kill or a pass.

**Economics sketch (pre-data):** entry at cross = 0 spread + ~0 fee; exit taker ≤15:45 ≈
1–2.5 bps megacaps / ~8 bps semis (COST_MODEL v1). Needed conditional gross ≥ 2× exit leg:
~4–6 bps megacaps, ~16 bps semis... megacap bar is REACHABLE if the conditional (top-|OLI|)
effect exceeds Brown's unconditional VW ~3 bps/leg; semis bar needs the M24-style
liquidity amplification to be real. Both are exactly what prong 0 measures.

## R2 §2 — EMPTY-cell re-scan for auction-print expressions (the Brown translation test)

Applied the same "re-express at a single print" translation to every round-1 EMPTY cell:
options dealer re-hedge (no owned options history; GEX banned from gated results — still
EMPTY-FOR-US on data); ETF AP/index tracking (close-benchmarked; no open concentration —
EMPTY-STRUCTURAL); sec-lending/settlement (post-close — EMPTY-STRUCTURAL); dark-pool ATS
shares (weekly, 2–4 wk lag — wrong frequency); internalizer inventory unwind (same payer
as R2-A viewed from the other side — folded into R2-A); pension/month-end (MOC-benchmarked,
banned side); NDX/VIX settlement SOQ opens (monthly at best + options-data-blocked —
UNMAPPED, low prior, side-support frequency only). **Yield: R2-A is the only auction-print
expression with owned/cheap data, a named payer, and daily frequency.** This was the whole
re-scan; no agents were spent on it.

## R2 §3 — Execution order

1. Backfill semis-5 trades 2024-01→2026-05 (Alpaca historical, $0, ~2–3 h background).
2. R2-A prong 0 (pre-declared in ledger BEFORE computation — gates below), one run on the
   full 10-name panel AFTER the backfill lands. Outcomes: PASS → register M28
   `open_print_retail_fade_v1` (registration charges the M6b/M24-lineage debt and the
   daily-swing adjacency; one pooled TRAIN look + VALIDATE confirm per house pattern);
   KILL → obituary row, axis priced; PARK-UNDERPOWERED → no family, revisit only with a
   materially wider panel (more names/years of trades backfill — cost it then).
3. Nothing else from round 2 — the re-scan yielded no second candidate. If R2-A dies, the
   program's honest state is: no open every-day intraday candidate on owned data; next
   moves are M26 (side support, parked) and/or a data-class expansion decision (options
   PIT history or broad-name tick backfill) which goes to the user as a WAVE/$ decision.

## R2-A prong-0 spec (frozen; ledger row `R2A-prong0-predeclaration` is authoritative)

State (per name-day t, per name): OLI_{t−1} = (buy_vol − sell_vol)/(buy_vol + sell_vol)
over day t−1 prints with exchange=='D' AND size<100 AND price>0, RTH 09:30–16:00 ET,
signed by quote rule vs prevailing bbo1s mid (searchsorted-guarded, completed buckets
only; tick-rule fallback on mid-equal; carry-last on further tie — f1_prong0 machinery
verbatim). Require ≥30 signed odd-lot prints on t−1 else drop day (counted). Outcome:
ret_t = (exit_mid/open_t − 1)×1e4 with open_t = bars1d RAW open (the cross print; L2
convention as M24) and exit_mid = last bbo1s mid ≤ 15:45 (require ≥15:40). Controls:
gap_t = (open_t/close_{t−1} − 1)×1e4 (raw bars1d), ret_{t−1} = close-to-close t−1 (raw).
Panel: 10 names (core-5 + semis-5), trades-coverage-limited (MU 2024-01+, NVDA ragged
2024+, TSLA/AMD/GOOGL 2025-09+, semis 2024-01+ post-backfill), sessions < 2026-06-01,
early-close days dropped.

Gate (a) INCREMENTAL INFO (reversal sign): within-name OLS-residualize BOTH OLI_{t−1} and
ret_t on [gap_t, ret_{t−1}] (per-name intercepts); pooled Pearson ρ of the residuals,
winsorized 1%/99%; PASS iff ρ ≤ −0.03 AND session-clustered bootstrap 95% CI-hi < 0
(seed 7, 2000 draws, session resampling).
Gate (b) MAGNITUDE: per-name top-quartile |OLI_{t−1}| days; signed_fade = −sign(OLI)×ret_t
raw; PASS iff mean ≥ +6.0 bps AND session-clustered 95% CI-lo > 0.
Adjudication (pre-declared): PASS = both gates → M28 registration path. KILL = residual ρ
point ≥ 0 OR top-quartile mean ≤ 0 (wrong sign anywhere decisive). PARK-UNDERPOWERED =
right signs, gates unmet. Supporting (non-gating): raw (unresidualized) ρ; horizons
open→10:00 / open→11:00; tier split (megacap vs semi); gap-quartile × OLI-quartile 4×4
mean table (the flow-vs-news discrimination picture); overnight leg ρ(OLI, gap) (Brown's
first stage, sanity); per-name rows; coverage/sparsity panel.
