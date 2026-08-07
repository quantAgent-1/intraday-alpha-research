# DR-X3 — What effective spread does small retail flow actually pay?

**Synthesis date:** 2026-07-18  
**Agents:** 4 modalities (A/B/C/D) + 2 independent refuter waves (6 claims, 0/6 refuted)  
**Protocol:** `research/deep/HARNESS.md` Mode A

### Synthesis
| Lane | Verdict rec | Central E/Q prior (liquid Nasdaq $400–$3k) | Last 15 min |
|------|-------------|--------------------------------------------|-------------|
| A academic | OPEN-TESTABLE MED | 0.50 [0.35–0.70] | 0.55 [0.40–0.80] mild ↑ bias / soft UNKNOWN |
| B primary | OPEN-TESTABLE HIGH | 0.55–0.70 | UNKNOWN (stress 0.80–1.00) |
| C practitioner | OPEN-TESTABLE MED | 0.35–0.55 (central 0.45) | UNKNOWN |
| D adversarial | OPEN-TESTABLE MED–HIGH (skeptic prior) | 0.7–1.0 | 0.9–2.0 (shortfall-implied ~2.0 at 15:55:10) |

**Dissents:** Optimistic lanes (A/C) use volume-weighted / good-broker retail averages. Skeptic (D) weights (i) liquid 1-tick names, (ii) NBBO PI overstatement up to 4× (Adams JBF — **CONFIRMED** by both refuters), (iii) marketable-limit worse than market, (iv) **project-owned** entry shortfall 1.46 bps vs half-spread 0.73 bps at 15:55:10 → implied E/Q ≈ 2.0 once mid-drift is included. B is the mechanics anchor: T1 May-2026 JNST/NITE 605 re-parsed by both refuters (half-eff 0.16–0.41 bps on megacap MKT 100–499; 93–97% PI) — real mid-day wholesaler quality — but 605 has **no TOD slice**.

**Refuter status:** All six load-bearing claims survived both independent refuter waves (Dyhrberg E/Q 0.76; May-26 605 bps; Aug-1-2026 modernization compliance; Alpaca 606 routing/PFOF; Schwarz IBKR-worst; Adams 4× overstatement).

## Verdict recommendation
**OPEN-TESTABLE** (confidence **HIGH** that Phase-0 measurement is the right next step; **MED** on any single numeric E/Q prior)

Use a **two-regime cost prior** for M16 / Phase 0 — do **not** collapse to industry E/Q ~0.45:

| Window | Working prior E/Q | One-sided cost @ 0.73 bps half | Status |
|--------|-------------------|-------------------------------|--------|
| Mid-day RTH uninformed marketable | **0.55–0.70** | **~0.4–0.5 bps** | CONFIRMED class (605 + literature) |
| Last 15 min / NOII-conditioned side | **UNKNOWN → stress 0.9–1.5+** | **≥0.7–1.5 bps; project shortfall 1.46** | Do not credit PI |
| Marketable-limit vs market | MLIM worse | NITE half-eff ~2.3 vs 1.5 bps | CONFIRMED T1 |
| Odd-lot post-mod 605 | Not published until **Aug 1, 2026** | — | CONFIRMED T1 |

**What would flip it:** ≥100 Alpaca fills on champion names with SIP mid at **decision** time showing last-15m median E/Q ≤ 0.70 (kills skeptic) **or** mid-day E/Q ≥ 0.95 (kills “sim overstates mid-day”).

### Mechanism
Wholesalers (Virtu/Citadel/Jane Street on Alpaca 606) internalize small segmented retail vs inventory and rebate part of the spread as PI while remitting PFOF (Alpaca: **12% of spread, cap $0.05** marketable core; **no PFOF rebate on primary close**). That mechanism is real for *average uninformed* retail mid-day. It is **not** a free lunch for signal-timed last-15-min flow: adverse selection and mid-drift can make shortfall ≥ full half-spread (project receipt). Capacity at $400–$3k is unlimited at wholesaler scale.

### Claims (load-bearing, post-refute)
C1 [CONFIRMED] (T2, Dyhrberg/Shkilko/Werner JFE 2025, 2019–2022): Wholesaler liq-demanding E/Q **0.76** vs exchange **0.97**; S&P 500 PI ≈ **47%** of quoted.  
C2 [CONFIRMED] (T1, JNST+NITE May 2026 605, both refuters re-parsed): Megacap MKT 100–499 half-eff **0.16–0.41 bps**, **~93–97%** shares PI.  
C3 [CONFIRMED] (T1, SEC 34-104147): Modernized 605 (odd-lot E/Q etc.) compliance **Aug 1, 2026**.  
C4 [CONFIRMED] (T1, Alpaca 606 Q3 2025): Routes Virtu/Citadel/JNST; marketable PFOF 12% spread cap $0.05; no close PFOF rebate.  
C5 [CONFIRMED] (T2, Schwarz et al. JF 2025): PI 19–47% of NBBO across brokers; IBKR Lite/Pro worst (~19%).  
C6 [CONFIRMED] (T2, Adams/Kasten/Kelley JBF 2024): NBBO PI overstates economic savings up to **4×** in some subsamples.  
C7 [PLAUSIBLE] Last-15-min E/Q **UNKNOWN** from 605 (monthly only); project shortfall implies E/Q≈2.0 at 15:55:10 with mid-drift.  
C8 [CONFIRMED] (T1, NITE 605): Marketable-limit worse than market in same size bucket.

### Constraint gates
| Gate | Result | Note |
|------|--------|------|
| 1 Latency | PASS | Cost measurement, not sub-5s edge |
| 2 Access | PASS | Alpaca marketable today |
| 3 Session | PASS | Continuous cost prior; MOC is separate (no auction PFOF) |
| 4 Data | PASS | Phase 0 = blotter + owned SIP, $0 |
| 5 Fill realism | PASS as measurement; FAIL if M16 assumes E/Q≪1 near close | |
| 6 Statistics | PASS | n≥250 clips easy |
| 7 Protocol | PASS | Cost-model family, not alpha |

Survivor-profile score (as cost recalibration, not edge): **3/5**.

### Economics sketch
- Sim today: full half-spread + 0.5–1 bp slip → shortfall median **1.46 bps** @ 15:55:10 vs half **0.73**.  
- Mid-day literature/605 prior: one-sided **~0.3–0.7 bps** on liquid names → sim **overstates mid-day by ~1–2 bps**.  
- Last 15 min: **do not cut cost** until Phase 0; stress ≥ full half-spread / shortfall.  
- Champion compare: **+2.5 bps/event dev / +12.5 holdout** — continuous entry still eats most of modal +2.5 if shortfall stays ~1.5 bps.  
- Does **not** resurrect maker / sub-15-min / bar-tier kills.

### Proposed next test (Phase 0 — user decides registration)
- **Hypothesis:** Alpaca $400–$3k marketable on {NVDA,TSLA,AMD,MU,GOOGL}: mid-day median E/Q ∈ [0.40, 0.75]; 15:45–16:00 median E/Q ∈ [0.50, 1.20] vs SIP mid at **decision** time.  
- **Data:** blotter + owned SIP; $0.  
- **n:** ≥250 clips, 2 TOD buckets.  
- **Promote:** two-bucket E/Q into sim (`0.5 × quoted_spread × E/Q_bucket` + 0.3 bp residual).  
- **Kill optimistic M16 pad:** if last-15m E/Q ≥ 0.95.  
- **Family:** cost-model / fill-kernel (not alpha). No ledger write this wave.

### Sources
See modality-A/B/C/D.md and refute-1/2.md (Jane Street/Virtu 605, SEC 34-104147, Alpaca 606, Dyhrberg JFE, Schwarz JF, Adams JBF, Brown WP, Huang FEDS).

---

## Addendum — wave-3 verification pass (2026-07-21, 4 Opus re-verify agents + 4 refuters)

All four modality files independently re-verified; the 2026-07-18 verdict and the **two-regime cost prior STAND unchanged**. Refuter adjudications (`refute-3-modernization-r1/r2.md`, `refute-4-overstatement-r1/r2.md`):

1. **Rule 605 modernization timeline — CONFIRMED 2/2 verbatim** (T1, SEC Release 34-104147 / Fed. Reg. 2025-19316): compliance Dec 14 2025 → **Aug 1 2026**; first modernized round-lot reports public ~end-Sept 2026; **odd-lot E/Q stats only by Nov 2026**. No public post-mod odd-lot data exists today → the regulatory substitute for Phase 0 is ≥4 months away; C3 upgraded with the Nov-2026 detail. Phase 0 remains the only near-term resolver.
2. **Today's modality-B JNST NVDA figures — STRUCK (2/2 refuted as stated).** The two refuters' own independent parses of the May-2026 Jane Street 605 file DISAGREE with each other ($0.0083/$0.0062 vs $0.0031/$0.0044 — column/aggregation ambiguity), and the 53.6%/68.2% PI-rate pair traces to a **1997 SEC fractional-pricing study** (sourcing conflation). Do not cite any single-parse JNST number without an agreed parse spec. The **direction** (marketable-limit worse than market) survives — both parses and the Jul-18 NITE C8 agree — so "Phase 0 sends MARKET orders" stands.
3. **PI-overstatement thesis — phenomenon CONFIRMED 2/2, attribution corrected**: sources are Adams-Kasten-Kelley (SSRN 3975667; "factor of four or more in *some subsamples*") and **Bradford Lynch Levy** (SSRN 4189658, "400%"; typical ≈2×) — NOT "Ernst" (misattribution, struck). Whether overstatement is megacap-broad or small-cap-driven: UNRESOLVED (paywalls). C6 wording already correct ("up to 4× in some subsamples").
4. **Skeptic numeric range 0.70–1.00 / 0.90–2.0 — REFUTED 2/2 as an empirical claim**: it is inference-stacking anchored on our own sim shortfall, with no primary source; likewise "~0.48 liquid names" is only weakly sourced. It remains valid ONLY as the project's self-labeled stress prior — exactly how the Jul-18 report files it. No numeric change to the prior table.
5. Alpaca 606 re-confirmed on the fresh Q4-2025 filing (same Virtu/Citadel/JNST set, 12%-of-spread cap 5¢, no close rebate).

**Net effect on the Phase-0 sketch: unchanged, urgency up** (no public data until Nov 2026; broker unmeasured; refuters killed both attempts to sharpen the last-15-min number from public sources — only the live audit can).
