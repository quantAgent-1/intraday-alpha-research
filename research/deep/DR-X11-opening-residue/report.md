# DR-X11 — Opening-cross imbalance residue (quantity axis) — SYNTHESIS

### Synthesis

Orchestrator synthesis, 2026-07-23 (session 8). Inputs: 4 modality agents (A academic,
B primary/venue, C practitioner, D adversarial — reports in this directory) + 2 refuter
agents (`refute-mechanics.md`, `refute-academic.md`; default refuted=true, primary-source
mandatory) + the local data-reality leg run as the pre-declared **F3 prong-0** diagnostic
(`scripts/f3_prong0.py`, `research/experiments/F3-prong0/`, gates frozen in ledger row
`F3-prong0-predeclaration` BEFORE computation).

Dissents/corrections that shaped the verdict (the refuter layer earned its keep):
- B/D's decisive "unexecuted imbalance is CANCEL-ONLY at the cross" was **partially
  overturned**: pure on-open types (MOO, LOO-on-open, OIO) do cancel (FAQ Q18 verbatim),
  but Rule 4752(a)(2)'s Imbalance definition also sweeps in Early-Market-Hours
  continuing-TIF interest, which persists post-cross **as resting limit liquidity**
  (Rule 4702(b)(9)(B)). Neither component produces post-open taker pressure.
- A/C's "field established no post-open predictability (Challet–Gourianov)" was corrected
  to **"the field never tested it"** — which makes our prong-0 the first direct test of
  this exact cell that we can find anywhere.
- D's application of the ~110% auction reversion (Bogousslavsky–Muravyev) to the OPENING
  auction was refuted — that result is closing-auction-only.
- Modality B cited SEC release 34-91480 throughout; the correct number is **34-91461**
  (substance — dates, cadence, semantics — verified independently at T1).

### Verdict recommendation

**EXHAUSTED-BY-US (confidence HIGH).** The opening-cross unpaired-imbalance QUANTITY
axis is closed in BOTH directions at post-open horizons. The pre-declared prong-0 gates
both failed on 11,487 name-days / 1,608 sessions / 10 names (2020-01→2026-05):
pooled winsorized ρ(residue, 09:35→11:00) = **−0.0004** [−0.0219, +0.0213]; top-quartile
mean signed drift **+2.86 bps** [−3.66, +10.01] vs the ≥+6.0 bar. Reversal is not
rescued (final-pre-cross variant ρ −0.017 n.s.; top-q −5.04 CI-spanning). The
information is consumed at/before the print: contemporaneous ρ(residue, open→09:35
return) = −0.031, consistent with per-second dissemination being arbed into the cross
and with the mechanics below. With no payer and a precisely-measured zero, this cell
does not support a registration in either direction.

What would flip it: a Nasdaq rule change converting unexecuted on-open interest into
marketable continuous-session orders (it is cancelled today), or a post-2016
cost-realistic study showing residue-quantity continuation net of ≥5 bps in liquid
names (21+ searches across four agents found none).

### Mechanism

No payer exists for continuation. The disseminated imbalance decomposes into (i) pure
on-open interest (MOO/LOO-on-open/OIO) — **cancelled and returned at the 09:30 cross**,
it never becomes post-open flow; and (ii) Early-Market-Hours continuing-TIF interest —
persists, but **as resting LIMIT liquidity** (it cushions moves toward it; it does not
chase). The adjacent documented open-side inefficiency is a *reversal* of retail
auction flow (Brown), captured at the auction print itself, not post-open continuation.
Whatever directional information the 09:28:30 residue carries is impounded by the
per-second NOII arb before/at the print — our contemporaneous ρ and the flat post-open
ρ measure exactly that.

### Claims (refuter-adjudicated; full quotes/URLs in the modality and refute files)

- C1 CONFIRMED (T1): Unexecuted MOO/LOO-on-open/OIO orders are cancelled at the opening
  cross; a cancellation message is returned post-cross (Nasdaq Crosses FAQ Q18; Rule
  4702). — refute-mechanics.md
- C2 CONFIRMED-CORRECTED (T1): The disseminated Imbalance ALSO includes Early-Market-
  Hours continuing-TIF interest that persists post-cross as resting limit liquidity
  (Rules 4752(a)(2), 4702(b)(9)(B)); "cancel-only" as stated by B/D is false. —
  refute-mechanics.md
- C3 CONFIRMED (T1): EOII regime break effective **2021-05-17** (SR-NASDAQ-2021-004,
  SEC release **34-91461**): EOII 09:25 ET every 10 s excluding near/far; full NOII
  every 1 s 09:28→cross; pre-2021 dissemination began 09:28. Matches our lake's observed
  cadence exactly. — refute-mechanics.md + F3-prong0 coverage stats
- C4 CONFIRMED (T1, current rules): MOO cutoff 09:28:00; late LOO to 09:29:30 with
  repricing; on-open cancel/modify lock 09:25; collar = benchmark ± max($0.50, 10%)
  plus Price Tests A/B/C; collar failure cancels on-open orders. — refute-mechanics.md
- C5 CORRECTED (T2): Challet & Gourianov (2018, 2010–2016) never tests post-09:30
  returns (never-tested ≠ tested-null); its mean-reversion evidence is strong at the
  CLOSE (H≈0.23, 93% of assets) and weak at the OPEN (H≈0.45, 73%); the "95%" was a
  cross-sectional asset-share statistic. — refute-academic.md
- C6 CORRECTED (T2): Bogousslavsky–Muravyev's ~110% large-cap auction-deviation
  reversion (Table 7) is CLOSING-auction-only; no opening-auction result exists in the
  paper. — refute-academic.md
- C7 CONFIRMED-NUANCED (T2): Brown, "The Quote Not Taken" (sample 2013–2022):
  **prior-day** off-exchange retail flow predicts opening-auction REVERSAL; publicly
  observable and outsider-capturable AT the auction print (gross of spread by
  construction; ~zero if captured at bid/ask); constrained by thin at-open liquidity
  (size), not information exclusivity; the $16bn is cumulative over the sample, not
  annual. DECAY-UNKNOWN post-2022. — refute-academic.md
- C8 CONFIRMED (T2, dated: NYSE 2001–2005): Heston–Korajczyk–Sadka intraday periodicity
  continuation is not explained by order imbalance (explicit covariate test). —
  refute-academic.md

### Constraint gates (for F3 as chartered)

1 Latency PASS (scheduled 09:35 entry) · 2 Access PASS · 3 Session PASS · 4 Data PASS
($0, owned) · 5 Fill realism **FAIL** (continuous double-taker round trip — the inverse
of the champion's single-print exit) · 6 Statistics PASS (n=11,487 — the zero is
precise, not underpowered) · 7 Protocol **FAIL** (no named payer survives the
mechanics). Survivor-profile score: **2/5** (scheduled instant; cheaply testable).

### Economics sketch

Measured effect ≈ 0 (ρ −0.0004; top-quartile +2.86 bps CI-spanning) vs a 2× cost bar of
5–10 bps (megacap RT floor 2–5 bps, semis up to 16). There is nothing to price. The
one exploratory positive cell (15:45 horizon, top-q +13.1 bps) is 1-of-4 non-gated
supporting horizons and is ruled REPORTED-NOT-GATED, non-actionable (ledger
`F3-prong0-result`).

### Proposed next test

None on this axis — closed both directions. Two durable byproducts:

1. **T1 panel-facts bank** for any future opening-window family: the C3/C4 chronology
   (2021-05-17 break; dissemination schedule; cutoffs; collar), plus the prong-0
   coverage facts (side coding {B,A,N}; ~138 opening rows/session; snapshot window
   populated every session 2020→2026).
2. **Successor candidate (UNCHARTERED — routed to ideation round 2 for fence/power
   audit, explicitly NOT registered here):** Brown-class *prior-day off-exchange retail
   flow → opening-print reversal*, expressed as a pre-positioned on-open order (single
   print, scheduled, no spread at entry; size-constrained not information-constrained).
   Distinct information set (prior-day tape, not NOII) and distinct execution (auction
   print, not continuous) from everything this lane killed and from M24/M6b. Known
   headwinds to audit: sample ends 2022 (decay-unknown), our M24 diagnostic leaned
   megacap-opens-efficient, trades-tape coverage for retail-flow construction is ragged
   (MU 2024-01+, others 2025-09+), and the on-open order type door (09:28) must carry
   the signal.

### Sources

The four modality reports and two refute files in this directory carry the full
numbered, tiered, dated source lists and the literal query logs. Local receipts:
`research/experiments/F3-prong0/{result.json,summary.md}`, `scripts/f3_prong0.py`,
ledger rows `F3-prong0-predeclaration` / `F3-prong0-result` / `DR-X11-lane-verdict`.
