# STUDY SESSION HANDOFF — The Denominator Wall

**Topic (ONE only):** Why edges die: promotion \(\alpha \ge 2c\) and detection \(\alpha \ge 2\sigma/\sqrt{n}\)

**Audience:** Project owner (researcher), building intuition for enginev5.1 continuous-intraday quant work. Not a professional quant by training; wants absolute fluency, not a survey.

**Mode:** Interactive tutoring. Socratic + worked numbers. Do **not** expand into other topics (ML, auctions, Avellaneda, OU, new strategy design) unless the student asks a clarifying bridge, then return to this topic.

**Success criteria (student can do all of these unprompted):**
1. State the two inequalities and what each symbol means in plain English and in bps.
2. Compute half-spread and taker RT cost from bid/ask; distinguish mid-alpha vs net.
3. Explain why M27 can have real +7–11 bps mid-alpha and still be a FAMILY KILL.
4. Compute SE and minimum detectable effect (MDE) for a daily series; explain day-clustering.
5. Explain why directional pooled books are noisy; what dollar-neutral and hedged change.
6. Apply the 2× promotion rule to a toy structure (open-cross entry vs 09:35 taker).
7. Explain false negatives: underpowered look → BETWEEN/KILL does not always mean “no edge.”
8. Connect this to M28’s design choices (neutral book, power pre-declared, flat cost stress).

**Out of scope for this session:** building new strategies, running M28, close-auction revival, deep ML, academic SDEs.

---

## Parent-session context (why this topic was chosen)

In the parent conversation the student:
- Felt the repo is beyond their understanding.
- Rejected close-auction (15:55) strategies; wants smart/dynamic quant + ML eventually.
- Correctly worried that studying OU / Avellaneda-Stoikov is interesting but won’t produce alpha for *their* regime (manual 5–25s, retail, RTH, flat day).
- Asked for the **single highest-ROI** math/fundamentals topic to nail in a dedicated session.

Parent agent’s ranking: this topic beats all others because **every family in this program dies against cost \(c\) or noise \(\sigma\)**, not against missing fancy math. The project’s own diagnosis (`research/BREAKTHROUGH_ANALYSIS_2026-07-26.md`) is the primary textbook.

---

## Project hard bounds (do not violate in explanations)

- Signal-only: no order routing.
- Manual latency 5–25 s; deploy ~$1k; research book $10k.
- RTH only; flat by ~15:45–15:50 for continuous work.
- **Close-auction direction is TERMINATED** (user decision 2026-07-23). Use historical MOC examples only as *cost contrast* (single-print exit), never as “what to trade next.”
- Unit of evidence: bps after honest costs; day-clustered CIs; register before economics.

---

## Core claim (memorize)

**The wall is not an idea wall. It is a denominator wall.**

```
PROMOTION:   alpha_gross  >=  2 × c
DETECTION:   alpha_gross  >=  2 × σ / √n
```

- Twenty-two families varied **alpha** (the numerator).
- Almost none engineered **c** or **σ** (the denominators).
- Both are partly under the researcher’s control: name choice, entry clock, instrument, portfolio shape.

---

## Vocabulary (force precise use)

| Term | Definition |
|------|------------|
| **mid** | midpoint of bid and ask: \((bid+ask)/2\) |
| **bps** | basis points: \(1\,\mathrm{bp} = 0.01\% = 10^{-4}\) relative return. Return in bps \(= 10^4 \times (P_\mathrm{out}/P_\mathrm{in} - 1)\) with side sign |
| **half-spread (bps)** | \(10^4 \times (ask-bid)/(2 \times mid)\) |
| **quoted spread (bps)** | \(10^4 \times (ask-bid)/mid\) = 2 × half-spread |
| **mid-alpha / gross (mid)** | expected return measured mid-to-mid (or open-to-exit mid), **before** paying spread/slip |
| **net** | after costs (spread + slip + fees) |
| **taker** | marketable order; pays the spread (crosses the market) |
| **c (all-in RT floor)** | full round-trip cost of the structure in bps of the same notional basis as alpha |
| **σ** | std of the **portfolio** return series (same units as alpha: often daily bps of gross) |
| **n / n_eff** | number of observations; for session-clustered inference, roughly **sessions**, not raw name-trades |
| **SE** | \(\sigma / \sqrt{n}\) (approx for iid; clustering inflates SE) |
| **MDE @ t=2** | minimum detectable effect ≈ \(2 \times \mathrm{SE}\) (rough 95% CI-lo > 0 threshold) |
| **2× promotion rule** | house rule: need \(\alpha_\mathrm{gross} \ge 2c\) before believing the edge is harvestable |
| **BETWEEN THE BARS** | positive lean, CI includes 0 — look spent, not a pass |

---

## Formula sheet (work every one with numbers)

### F1 — half-spread and taker legs

Given bid \(B\), ask \(A\), mid \(M = (B+A)/2\):

\[
\mathrm{hs\_bps} = 10^4 \times \frac{A-B}{2M}
\]

**Taker buy** pays ~ask; vs mid you lose ~hs on entry.  
**Taker sell** pays ~bid; vs mid you lose ~hs on exit.

**Classic taker RT (enter and exit both taker)** ≈ **one full quoted spread** in bps  
\(= 2 \times \mathrm{hs}\) at entry clock + \(2 \times \mathrm{hs}\) is wrong — careful:

- Entry taker cost vs mid ≈ **hs_entry**
- Exit taker cost vs mid ≈ **hs_exit**
- RT spread cost ≈ **hs_entry + hs_exit**  
  If same clock and flat book, ≈ **quoted spread once** (not twice the full spread).

House also adds: slip (~0.5 bps/taker leg in COST_MODEL), SEC §31 **0.206 bps** on sale notional, tiny TAF.

### F2 — open-cross special case (M28 structure)

- Entry at **opening cross** = single print → **0 spread** by construction (fees may still apply on short sale).
- Exit taker 15:40–15:45 → pay **hs_exit** + sale fees.
- So \(c\) can be ~**0.5–3 bps** class instead of **16–38 bps** (M27-style 09:35 taker both legs on illiquid names).

### F3 — promotion inequality

\[
\alpha_\mathrm{gross} \;\ge\; 2c
\]

Example (M27-shaped): \(\alpha = 9\) bps, \(c = 16\) bps → \(2c = 32\) → **fails** hard.  
Same \(\alpha = 9\), \(c = 1.0\) (liquid name, good clocks) → \(2c = 2\) → **clears** easily.

### F4 — detection inequality

\[
\mathrm{SE} \approx \frac{\sigma}{\sqrt{n}}, \qquad
\mathrm{MDE}_{t=2} \approx 2 \cdot \mathrm{SE}
\]

Need true \(\alpha\) roughly **above MDE** or CI-lo will often span 0 even when edge is real.

Breakthrough table (gross=1.0, 603 sessions, same signal proxy):

| design | daily σ | SE | MDE@t=2 |
|--------|---------|-----|---------|
| directional pooled (old house shape) | 144.3 | 5.88 | **11.75 bps** |
| dollar-neutral XS | 85.4 | 3.48 | 6.96 bps |
| directional + index hedge | 45.1 | 1.84 | **3.68 bps** |

Hedged SE cut **~3.2×** ≈ like **~10× more data**.

### F5 — t-stat intuition

\[
t \approx \frac{\bar x}{\mathrm{SE}}
\]

Pass-ish when \(|t| \gtrsim 2\) for CI-lo > 0 (rough). Project graveyard is full of \(t \in [0.86, 1.86]\) — **~1.1–2× more data** from significance, median ~1.5×.

### F6 — power failure probability (qualitative)

With SE ≈ 8 bps and true effect 5–15 bps, one-look CI-lo>0 passes a *real* edge only with modest probability (~0.15–0.35 in the memo’s sketch). So **EXHAUSTION_MAP can contain false negatives**. Discipline is still right (no p-hacking); fix is **power before registration**, not looser bars.

---

## Canonical evidence from this repo (use as worked examples)

### E1 — Cost is a surface, not a constant

Median quoted spread bps from `bbo1s` (2025-06→2026-05), breakthrough memo:

| name | 09:35 | 12:00 | 15:40 |
|------|-------|-------|-------|
| NVDA | 0.8 | 0.6 | 0.6 |
| GOOGL | 1.6 | 0.7 | 0.6 |
| TSLA | 2.8 | 1.3 | 1.0 |
| AMD | 5.4 | 2.4 | 1.5 |
| MU | 6.9 | 3.4 | 2.4 |
| … | | | |
| KLAC | **30.0** | 11.9 | 7.5 |

Taker RT ~ hs_in + hs_out ≈ half of those if one-way is “spread,” carefully: quoted spread ≈ 2·hs, RT two taker legs ≈ quoted_spread_in/2 + quoted_spread_out/2 = average quoted/2…  
**Simpler teaching rule used in memo:** taker RT ≈ **one full quoted spread** when both legs at similar width (hs+hs = quoted).  
Range ~**0.7 bps (NVDA good clocks)** to **~19–30+ bps (KLAC bad clocks)**.

M27 froze pooled RT floor **16.0 bps**, KLAC **38.5** — same story, different path.

### E2 — M27 kill (promotion failure)

- Mid-alpha real: ~**+7 to +11 bps** gross  
- Cost floor ~**16 bps** (universe = least liquid of broad panel — worst cost tier by design)  
- Net expectation negative; family **KILL**  
- Lesson: **effect-size vs liquidity mirror** — thinner names may have more mid-alpha (M24 ~2–3×) but costs 20–40× worse. Alpha-per-unit-cost ranking was never done until breakthrough memo.

### E3 — Detection failures (graveyard)

| family | point | SE (impl.) | t | data multiple for CI-lo>0 |
|--------|-------|------------|---|---------------------------|
| R2-A gate (b) | +14.87 | 8.00 | 1.86 | 1.11× |
| M24 t50 | +37.1 | 22.24 | 1.67 | 1.38× |
| M22 Cell A | +3.70 | 2.39 | 1.55 | 1.60× |
| M16-A | +1.69 | 1.25 | 1.35 | 2.09× |

### E4 — M28 design as *application* of this topic

- Open-cross entry → slash **c**  
- Exit 15:40–15:45 → cheapest continuous hour  
- Dollar-neutral L/S → slash **σ** vs directional  
- Pre-declared se ≈ 5.7 bps/day, needs ~**+11 bps/day** for CI-lo>0 — honest: 3–5 bps true effect may print **BETWEEN**, not “refuted”  
- Cost amendment: bar-range is **anti**-informative for spread (corr −0.5); primary **flat 3.0 bps** hs stress  
- PASS = CI-lo>0 **and** gross ≥ 2× mean daily cost  

---

## Cost model house facts (`research/COST_MODEL.md`)

- Alpaca commission $0 through 2026-12-31  
- SEC §31 **0.206 bps** on sale notional  
- Taker slip model **0.5 bps**/marketable leg  
- **Never** credit maker half-spread or rebates at retail (until Phase-0 measures)  
- Promotion: gross ≥ **2×** all-in floor  

---

## Teaching plan for the tutor agent

### Phase 0 — Contract (2 min)
Restate topic, success criteria, out of scope. Ask student current comfort (1–5) with: bps, spread, SE, CI.

### Phase 1 — Units and mid vs net (until solid)
- Convert price moves to bps by hand.
- Bid/ask → mid, hs_bps, quoted spread.
- Toy trade: mid-alpha +8 bps, both legs taker with hs=4 each → net?
- Quiz until 3/3 correct without hints.

### Phase 2 — Promotion inequality + M27
- Derive \(c\) for NVDA 09:35→15:40 vs KLAC same.
- Walk M27 numbers; student explains kill in one sentence.
- Counterfactual: same alpha on NVDA clocks — does 2× clear?
- Discuss liquidity mirror trap (more alpha where cost explodes).

### Phase 3 — Detection inequality + power
- From daily σ and n, compute SE and MDE.
- Reproduce breakthrough table intuition (directional vs neutral vs hedged).
- Why “n = number of trades” is usually a lie (session clustering).
- R2-A / M24 as near-misses: underpowered ≠ proven zero.

### Phase 4 — Portfolio shape is an engineering choice
- Net market exposure ~0.58 per unit gross on old house design (memo).
- Neutral book removes a bet you didn’t intend.
- Hedge fork: if alpha *is* the factor, hedged mean → 0 (honest, not a bug).

### Phase 5 — Integration: M28 + student’s future ML dream
- Map each M28 choice to \(c\) or \(\sigma\).
- Where ML belongs later: **after** structure clears denominators (meta on system days), not instead of this math.
- Student writes 5-bullet “denominator checklist” for any future registration.

### Phase 6 — Mastery exam (must pass)
10 short questions + 2 numeric problems. If any fail, remediate that slice only.

### End of session
Write a short `STUDY_NOTES_DENOMINATOR_WALL.md` in `research/study/` with: student-owned summary, mistakes corrected, remaining fuzzy spots. Tell student to return to parent session with that file.

---

## Files the tutor may read (prefer these; don’t roam the repo)

| Priority | Path |
|----------|------|
| Primary textbook | `research/BREAKTHROUGH_ANALYSIS_2026-07-26.md` |
| Cost rules | `research/COST_MODEL.md` |
| Worked kill | `research/experiments/M27-gap-day/report.md` (if present; else ledger summary below) |
| Application | `research/experiments/M28-open-cross-battery/REGISTRATION.md` |
| Cost amendment | `research/experiments/M28-open-cross-battery/AMENDMENT_1_COST.md` |
| Map only | `ORIENTATION.md` landmines L1–L3 if fill/cost confusion arises |

**Do not** send the student to ORIENTATION’s champion/close sections as “what we trade.” Close is banned.

### M27 ledger one-liner (if report skim is enough)
`FAMILY KILL` — t50 −8.71 [−23.1,+5.7] n=2292; mid-alpha real ~+7–11 bps gross; taker floor ~16 bps pooled (KLAC 38.5); 09:35 spreads 60–90 bps quotes on that panel.

---

## Pedagogy rules

1. **Numbers before nouns.** Every concept gets a 30-second hand calculation.
2. **One idea per message** when possible; check understanding before advancing.
3. **Correct imprecise language immediately** (“profit” → net bps; “significant” → CI-lo / t / pre-registered bar).
4. **No strategy shopping.** If student invents a trade idea, run it through the two inequalities only, then return to curriculum.
5. **No auction revival.** Historical single-print = cost contrast only.
6. **If student is lost:** drop to Phase 1 price→bps for 5 minutes; rebuild.
7. **If student is bored / already strong:** jump to Phase 5–6 and stress-test with adversarial questions.

---

## Starter questions (tutor opens with these)

1. “In one sentence, what is a basis point?”  
2. “If NVDA bid=100.00 ask=100.02, what is mid and half-spread in bps?”  
3. “What is the difference between mid-alpha and net?”  

Then proceed Phase 1 → … → mastery exam.

---

## Mastery exam bank (use subset; shuffle)

**Conceptual**
1. State both inequalities from memory.
2. Why can a strategy with positive mid-alpha still be a kill?
3. Why is SE for 2000 name-events not \(\sigma/\sqrt{2000}\) if they share 50 days?
4. What does dollar-neutral buy you in the detection inequality?
5. Why might hedging destroy measured alpha (not just noise)?
6. What is BETWEEN THE BARS?
7. Why is “try more signals until CI>0” invalid under this project’s protocol?
8. Open-cross entry changes which symbol in the inequalities, primarily?
9. What does the 2× rule protect you from?
10. Why did M27’s universe rule make promotion harder by construction?

**Numeric**
A. Bid 250, ask 250.50. hs_bps? Quoted spread bps?  
B. Mid-alpha +10 bps/day, daily σ=90, n=250 sessions. SE? MDE@t=2? Does t≈10/SE clear 2?  
C. hs_entry=5, hs_exit=1, slip 0.5×2, fees 0.2. Approx c? Need gross ≥ ? for 2× rule.  
D. True α=6, SE=5. Roughly what t? Is CI-lo>0 likely?

---

## Return protocol for the student

When done, student returns to parent enginev5.1 conversation and says something like:  
“Denominator wall study done — notes in `research/study/STUDY_NOTES_DENOMINATOR_WALL.md`.”  
Parent session can then pick the **next** single topic or apply this to M28.

---

## One-line topic title for the new session UI

**Study: denominator wall (α≥2c and α≥2σ/√n) — enginev5.1**
