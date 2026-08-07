# DR-X5 — Auction mechanics down the liquidity curve

**Synthesis date:** 2026-07-18  
**Agents:** 4 modalities + 2 refuter waves (B&M / Goyal / Nasdaq parity / M11 unrefuted)  
**Protocol:** HARNESS Mode A

### Synthesis
| Lane | Verdict rec | Key line |
|------|-------------|----------|
| A academic | OPEN-TESTABLE MED | Gross \|dev\| rises small; \|dev\|/half-spread **flat-to-worse** |
| B primary | OPEN-TESTABLE HIGH mech / MED econ | Rules **identical**; degrade by activity not tier |
| C practitioner | OPEN-TESTABLE MED | TM pain = our prior; pilot mid band |
| D adversarial | **NOT-VIABLE-STRUCTURAL HIGH** | Spread eats deviation; M11 already null mid-tier |

**Orchestrator resolution:**  
- Mechanics parity → **CONFIRMED** (T1 Nasdaq; all names same schedule).  
- Smallness thesis as *net* edge → **NOT-VIABLE-STRUCTURAL** for the **B&M bottom-quintile / micro** end (half-spread ≈ \|dev\|; Goyal: auction *worse* only for Nasdaq micro; ~10% zero-auction days).  
- **Optional measurement-only** mid-band pilot (ADV **$50–200M**, not micro) remains **OPEN-TESTABLE** with **negative-to-flat prior** — do **not** promote as deploy family until residual-after-half-spread clears; M11 already failed broad never-fit expansion.

## Verdict recommendation
**NOT-VIABLE-STRUCTURAL** (confidence **HIGH**) for “go down ADV to harvest 20.6 bps” as a deploy edge.

**OPEN-TESTABLE** (confidence **LOW–MED**, optional, measurement-only) for a **mid-liquidity residual-vs-spread kill test** on ADV **$50–200M** Nasdaq-primary never-fit names — prior is that net ≤ 0; registration only if user wants the formal corpse.

**What would flip structural kill:** owned 2020–2026 pilot with residual |near−mid| **net of entry half-spread** ≥ **+4 bps/event**, n≥250, half-spread ≲8 bps, cross almost always fires — in mid band, **not** micro.

### Mechanism
Same indexed/passive MOC payer as champion **exists** across size (auction share of ADV ~flat ~6%). Larger gross |auction−mid| down-curve is mostly **wider half-spread** (B&M: full-sample impact residual only **0.55 bps**; small |dev| **20.6** vs half-spread **~22**). Capacity at $10k is free; **economic** capacity is not. Payer density may even favor large (ITG: large-cap MOC share grew more). Short/locate friction rises exactly where |dev| looks fattest.

### Claims (post-refute)
C1 [CONFIRMED] (T2, B&M 2010–18): |dev| **2.66** large vs **20.6** small; half-spread **7.56** vs impact **0.55**.  
C2 [CONFIRMED] (T2, B&M): **68.5%** auctions at bid/ask; **9.56%** small days zero auction.  
C3 [CONFIRMED] (T2, Goyal et al. JFQA 2026): Auction impact < continuous **except Nasdaq microcaps**.  
C4 [CONFIRMED] (T1, Nasdaq FAQ): Schedule/cutoffs/NOII **identical** all nationally listed names.  
C5 [CONFIRMED] (T1 local, M11): 28 never-fit names net **−3.0 bps**, dir **0.47**.  
C6 [CONFIRMED] (T1, B): No-cross → NOCP = last sale; late LOC needs crossing interest.  
C7 [CONFIRMED] (T1, B): Fees = member tiers not stock liquidity tiers; LULD double last 25 min (Tier rules).  
C8 [PLAUSIBLE] 2020–2026 |dev|×tier = **DECAY-UNKNOWN** (no T2 re-tab).

### Constraint gates
| Gate | Bottom-quintile / micro | Mid $50–200M measurement |
|------|-------------------------|---------------------------|
| 1 Latency | PASS weak (moves more) | PASS |
| 2 Access | FAIL short+no-cross | PASS long / COND short |
| 3 Session | PASS if cross fires | PASS |
| 4 Data | PASS ~$15–55 NOII | PASS |
| 5 Fill realism | **FAIL** (cost≈gross) | OPEN measure |
| 6 Statistics | FAIL sparse | PASS designable |
| 7 Protocol | **FAIL** (negative prior) | PASS diagnostic only |

Survivor: micro **1/5**; mid pilot structure **3–4/5** with gate 5 pending.

### Economics sketch (unit table)
| Tier | \|dev\| prior | Half-spread entry | \|dev\|/HS | Net residual prior |
|------|--------------|-------------------|-----------|-------------------|
| Mega (champion) | ~2–5 bps | ~1–4 bps | >1 sometimes | Known +2.5 filtered / +12.5 holdout |
| ADV ~$200M | ~5–10 | ~3–8 | ~1 | **flat / M11-like null** |
| ADV ~$50M | ~10–18 | ~8–20 | ≤1 | **≤0 after entry** |
| B&M small / micro | **20.6** | **~22** | **≲1** | **≤0; toxic** |

Champion compare: **+2.5 / +12.5** — habitat is **liquid narrow names**, not down-curve.

### Pilot-universe recipe (if user still wants measurement corpse)
1. Nasdaq primary common; exclude champion+M11.  
2. PIT seed: IJH/IJR `asOfDate` ∩ ADV **[$50M, $200M]** (optional satellite $20–50M flagged).  
3. Price **[$10, $150]**; auction_rate ≥ 0.9 trailing 60d; reselect annually PIT.  
4. n≈20; NOII ~**$15–55**; report **net after half-spread**, not gross |dev|.  
5. **Kill immediately** if net≤0 or edge only below Goyal micro line.

### Proposed next test
**Default recommendation: do not register a deploy liquidity-down family.**  
Optional: diagnostic “residual-vs-HS by ADV band” on owned+cheap NOII mid band — UNDERPOWERED-BY-DESIGN OK as map cell kill. No ledger write this wave.

### Sources
modality-A/B/C/D.md; refute-1/2.md; B&M JFM 2023; Goyal JFQA 2026; Nasdaq openclose FAQ; M11 report/ledger.

---

## Addendum — wave-3 verification pass (2026-07-21, 4 Opus re-verify agents + 2 refuters)

All four modality files independently re-verified; the 2026-07-18 split verdict STANDS (structural kill for deploy liquidity-down; optional measurement-only mid-band pilot). Deltas:

1. **New tier evidence, CONFIRMED 2/2** (`refute-3-tier-spread-r1/r2.md`, both read the primaries):
   - NYSE Data Insights (Choey Li, Aug 2023, T1): non-R1000 immediate closing-auction move **<0.3×** daily-avg spread vs **0.34–0.40×** for R1000 — dislocation-per-unit-spread DECLINES down-curve on standard days. Strengthens the kill.
   - B&M decomposition re-confirmed verbatim: small-cap |dev| **20.60** bps vs half-spread **22.19** (impact ≈ **−1.6** bps); tick binding **41.8%**; Tick Size Pilot causally RAISED deviations.
2. **Conditioning caveat (new, load-bearing for M14/M12, not for this lane's kill):** the same NYSE piece shows the tier pattern **inverts on index-rebalance days** — non-R1000 **1.77×** spread vs R1000 **0.72×**. Unconditional liquidity-down harvesting stays dead; scheduled-flow-conditioned small-cap auction events (rebalance/month-end) are a distinct, still-open cell consistent with M14 MONTH_END (+5.55) and the M12 flow mechanism. Any future registration must be event-conditioned, not tier-conditioned.
3. Additional degradation facts (T1, modality-A/B this pass): halted-at-16:00 names run NO closing cross (MOC/LOC/IO cancelled, NOCP = last sale) — single-print exit fails in exactly the thin tail; near/far fields blank where no on-close interest exists.
4. Universe-construction unblock (T3, unverified tooling — QA before use): free PIT Russell reconstruction via GitHub `pyndex` / `fja05680/sp500`; iShares IJH/IJR remains the primary free PIT seed.
