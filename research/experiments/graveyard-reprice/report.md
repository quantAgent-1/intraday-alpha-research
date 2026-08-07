# Graveyard re-price — statistical edge only

Generated 2026-07-27 by `scripts/graveyard_reprice.py` + daily-portfolio addendum.
No $1k lens. No new thresholds invented inside dead families.
Criteria: `SUCCESS_CRITERIA.md`.

## Success criteria (binding, experiment phase)

1. N ≥ 250 events **or** T ≥ 150 sessions on the declared evaluation stream  
2. Mean **net** with day-clustered / daily-bootstrap 95% CI-lo **> 0**  
3. Mean gross mid-alpha ≥ **2×** mean modeled RT cost  
4. 2×-cost stress: report; CI-lo ≥ 0 strengthens; soft-fail = PROMO-FRAGILE in experiment phase  
5. **No deploy-book metrics in any gate**

Evaluation stream must be **declared**: event-pooled vs **daily equal-weight portfolio** of that day's fires.

---

## Method

| family | mid object | cost expressions |
|---|---|---|
| **M27** | reconstruct mid ≈ file `gross` + ½ entry spread + ½ exit spread + 1 bp slip | (a) open entry + 15:40 exit surface (b) 09:35 taker both |
| **M24** | print→print `gross_bps` | fee-only; stress continuous 15:40 exit |
| **R2-A** | top-quartile \|OLI\| signed fade (pre-declared gate-b object); open→15:45 mid ret | open entry + late exit from measured half-spreads |

CIs: bootstrap seed=7, 2000 reps. Event-level uses session clusters; daily uses resample of session means.

---

## Headline results

### Event-level (session-clustered) — no full PASS

| family | cell | n | sess | mid mean [CI] | net (best expr) [CI] | mid CI>0 | net CI>0 | ≥2×cost |
|---|---|---:|---:|---|---|:---:|:---:|:---:|
| M27 | t50 pooled | 2292 | 641 | +2.95 [−11.5,+17.5] | +0.50 [−13.9,+15.0] open-late | n | n | n |
| M27 | t50 AMAT only | 473 | 473 | +13.9 [−2.3,+31.3] | +11.4 [−4.8,+28.7] | n | n | Y |
| M24 | t50 all | 324 | 182 | +37.4 [−4.3,+82.9] | +37.2 [−4.5,+82.7] fee | n | n | Y |
| M24 | t25 all | 1392 | 642 | +3.5 [−13.9,+21.1] | +3.3 [−14.1,+20.9] | n | n | Y |
| R2A | topq all | 1095 | 513 | +15.2 [−0.71,+30.5] | +13.1 [−2.8,+28.4] open-late | n | n | **Y** |

R2-A event-level mid misses CI>0 by **0.71 bps** — the closest event-stream miss in the corpus.

### Daily equal-weight portfolio of fires — R2-A PASSES statistical edge

Each session: mean of that session's top-quartile fade (and net) events. T = 513 sessions.

| stream | mean bps | 95% CI | T | ≥2×cost | verdict |
|---|---:|---|---:|:---:|---|
| R2-A topq **mid** (daily) | **+22.42** | **[+4.35, +40.47]** | 513 | Y (cost≈2.1) | **CI-lo > 0** |
| R2-A topq **net open-late** (daily) | **+20.30** | **[+2.16, +38.31]** | 513 | Y | **STAT EDGE PASS** |
| R2-A net **2× cost stress** | +18.19 | [−0.29, +37.52] | 513 | — | PROMO-FRAGILE (soft) |
| M24 t50 daily | +31.1 | [−10.5, +76.3] | 182 | Y | still BETWEEN |
| M27 t50 daily mid | +6.01 | [−7.0, +19.4] | 641 | — | no |

**Year stability (R2-A event means, all positive):**

| year | mean fade | mean net | n |
|---|---:|---:|---:|
| 2024 | +9.6 | +7.5 | 569 |
| 2025 | +19.1 | +17.0 | 382 |
| 2026 (to May) | +26.6 | +24.8 | 144 |

**Name lean (topq fade):** 8/10 positive (TSLA, KLAC negative). Semis slightly stronger than mega.

---

## Interpretation

1. **M27 is not salvageable as a primary.** Reconstructed pooled mid is only ~+3 bps with wide CI — weaker than the narrative “+7–11 mid.” Cheap expression does not invent a CI>0 mid. AMAT alone leans positive but is single-name / not a system.

2. **M24 remains BETWEEN** under fee-only print economics and under daily aggregation. Still the first near-zero-ρ open axis (historical fact). Not a statistical-edge PASS.

3. **R2-A is the working candidate under statistical-edge criteria** when the evaluation unit is the **daily portfolio of top-quartile OLI fades**, expression = **open print entry + late continuous exit** (cost ~2 bps), research-book / bps only.

4. **Aggregation matters.** Event-pooled session-bootstrap CI-lo ≈ −0.7 bps; daily equal-weight CI-lo ≈ +2.2 bps net. The daily unit is the correct object for a **book that fires a basket each day**. It was **not** the pre-declared gate-b statistic (event mean). Therefore:

   - Discovery verdict: **we have a strategy shape that clears statistical edge on historical data.**  
   - Protocol verdict: **this does not silently rewrite R2-A prong-0 to PASS.** Prong-0 event-level remains FAIL as pre-declared.  
   - Next action: **new registration** with frozen daily-portfolio primary metric + open-late costs, judged on **forward sessions only** (holdout already spent by M6-FINAL).

5. Session-demean residual diagnostics in the first script are **not** informative for mean (they zero by construction). Market-beta residualization of the daily fade series also collapses mean toward 0 — the edge co-moves with the day's common return; it is **not** pure CS idio alpha. That is acceptable for a statistical-edge phase (beta is allowed); a later hedged book is a different registration.

---

## Go-forward plan (approved constraints)

**Success = statistical edge. No $1k in gates.**

| step | action |
|---|---|
| 1 | **Freeze criteria** (this folder) — done |
| 2 | **Register** `R2A-daily-portfolio-v1` (or named family): top-q \|OLI\| fade, open entry, exit 15:40–15:45, daily EW portfolio of fires, primary cost open-late surface, PASS = daily net CI-lo>0 + ≥2×cost + T≥150 on **forward only** (≥ 2026-06-01 unused / T+1 accrual) |
| 3 | Build harness: reuse `R2A-prong0` panel builders + cost table; forward clock like M10 |
| 4 | Do **not** iterate thresholds on history; do **not** re-open M27/M24 |
| 5 | System/meta layer only after forward stream banks evidence |

---

## Files

- `SUCCESS_CRITERIA.md` — binding experiment-phase bar  
- `reprice_results.json` — full machine output (event-level cells)  
- `scripts/graveyard_reprice.py` — reproducible runner  
- This report — verdict + daily-portfolio addendum  
