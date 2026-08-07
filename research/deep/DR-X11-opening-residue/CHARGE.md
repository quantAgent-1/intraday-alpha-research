# DR-X11 — Opening-cross imbalance residue (quantity axis) — lane charter

Chartered 2026-07-23 (session 8) by the orchestrator, per the F3 fence in
`research/HYPOTHESES_FABLE_MAX.md` ("prior-art wave first") and the session-7 queue.
Mode A lane per `research/deep/HARNESS.md`. In-session wave (DR-X9/DR-X10 pattern).

## The charge

Area: DR-X11 — Nasdaq opening-cross imbalance residue: venue mechanics + prior art +
crowding. Gates any F3 registration (quantity-continuation reframing of Q10).

Questions:
1. **Venue mechanics (T1 required; modality B owns):** Nasdaq Opening Cross (Rule 4752
   lineage), current rules: MOO/LOO/OIO entry cutoffs and late-order handling; what
   happens AT the cross to imbalance interest that is NOT paired — cancel vs convert to
   continuous trading, by order type; NOII dissemination for the open (start time,
   cadence 09:25–09:30); exact semantics of the disseminated `imbalance_shares` /
   `paired_shares` fields; price collars/thresholds. This decides whether the "residue
   completes in continuous trading" payer exists MECHANICALLY or the residue is
   informational only.
2. **Prior art / evidence:** published or named-practitioner evidence that opening-auction
   imbalance QUANTITY predicts post-open drift/continuation at 5–120 min horizons in the
   modern (2016+) US market. Cushing–Madhavan-class results + modern replications or
   failures. Nasdaq economic research on the opening cross. Distinguish quantity-imbalance
   signals from price-dislocation signals (near-vs-ref) — the latter is already tested
   internally (M24, closed).
3. **Crowding/decay (D owns the strongest case):** who consumes opening NOII today;
   evidence the residue is arbed within seconds; capacity/decay post-2016; documented
   prop/HFT opening-cross strategies on this exact feed.
4. **Adjacent:** overnight-gap + first-30-min momentum/reversal literature ONLY where it
   conditions on auction/imbalance quantity. Do not re-derive generic open momentum.

Already known (pre-flight, do not re-derive):
- We OWN historical XNAS.ITCH NOII open windows (33 Nasdaq names; core-5 2020→2026,
  broad set 2023→2026; fields ts/side/imbalance_shares/paired_shares/near/far/ref) and
  1s XNAS TOB for 10 names. $0 to test historically.
- Internal fence: M6b (naive opening-cross imbalance trade) FAILED; M24 (near-vs-ref
  PRICE fade at 09:28:30, open print → close print) BETWEEN THE BARS, family closed —
  the one sanctioned Q10 look is spent. F3 (unpaired-QUANTITY continuation, entry
  ~09:35 continuous, exit ≤11:00) is the reframing under adjudication.
- Constraints: manual 5–25 s latency (a ~09:35 scheduled entry is fine), taker RT floor
  2–5 bps megacaps / up to 16 bps mid-liquidity semis, $10k research book, RTH, no
  sub-minute anything, close-auction direction banned (open side only).
- Macro-window continuation is exhausted (DR-X9) — out of scope here.

## Lane plan

- Modalities: A academic (opus), B primary/venue (opus), C practitioner (sonnet),
  D adversarial/prior-art (opus). E (data-reality) is covered by the parallel F3
  prong-0 diagnostic (`scripts/f3_prong0.py`, pre-declared in the ledger).
- Outputs: `modality-A.md` … `modality-D.md` in this directory.
- Then: ≤8 load-bearing claims extracted; 2 refuters each (default refuted=true);
  synthesis (`report.md`) by the orchestrator; EXHAUSTION_MAP row; lane-verdict ledger
  note. No registration from this lane — the fence ruling (historical-look vs
  forward-only) is made by the orchestrator at registration time with this lane's
  evidence in hand.

Status: modality agents dispatched 2026-07-23. Prong-0 running in parallel.
