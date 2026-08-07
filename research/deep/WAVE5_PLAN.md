# Deep-Research Wave 5 — Plan (2026-07-22)

Orchestrator: Claude Code session (synthesis stays here). Protocol: `HARNESS.md` v1.0 Mode A.
Each agent gets `AGENT_BRIEF.md` **verbatim** + the lane charge + ONE modality focus block.
Collect raw outputs as `research/deep/DR-X9-macro-announcement-drift/modality-<A|B|C|D>.md`;
refuters run on return, orchestrated here.

## Wave goal

| Lane | Area | Unblocks |
|------|------|----------|
| 1 | DR-X9 post-release macro drift in cash equities (minutes–hours) | The M20 Stage-2 gate: `sched_window_v1` (registered 2026-07-22) may NOT graduate from mid-alpha screen to economics without this lane's prior-art/decay/payer verdict. Also feeds the mechanism prong that PROTOCOL demands for any calendar-anchored family. |

Context the lane must respect (do not re-litigate): M20 Stage-1 is a REGISTERED mid-alpha
screen on owned 1s quotes (5 megacaps, 2020–2026); its grid is frozen and it runs regardless
of this wave — the wave gates only Stage-2 (economics/registration). The exhaustion map has
already killed: published TOD pattern harvest (Rosa 2022 OOS kill), event-day single-name
catalyst/earnings intraday taker (frontier 07-16), hourly stat-arb re-skins, intraday
reversion (M18 + DR-X7). This lane is about MARKET-WIDE scheduled macro releases — a
different anchor class none of those covered.

---

# LANE 1 — DR-X9-macro-announcement-drift

## Your charge

Area: DR-X9 — After scheduled macro releases (FOMC statement/minutes 14:00 ET, 10:00 ET
releases: ISM/UMich/JOLTS/CB-confidence, Treasury 10y/30y auction results ~13:01–13:03 ET,
and 8:30 ET releases as of the 09:30 open), does the initial price reaction CONTINUE at
minutes-to-hours horizons in US large-cap cash equities — and who is the slow payer?

Questions:
1. **Post-release continuation evidence (decisive):** Published magnitudes (bps) of
   post-announcement drift/continuation at 15 min – 4 h horizons, per release class, in cash
   equities or index futures, samples and OOS status. Key objects: post-FOMC statement drift
   ("monetary momentum", Neuhierl–Weber and successors), Lucca–Moench pre-FOMC drift AND its
   post-2015 decay literature, 10:00 macro release drift (ISM/confidence), Treasury
   auction-result spillovers into equities, and 8:30-release morning-session drift. For each:
   does the effect survive post-publication samples (McLean–Pontiff-class decay checks)?
2. **The payer:** Direct evidence on WHO trades slowly after releases — vol-target /
   risk-parity re-levering latency (same-day intraday vs close vs multi-day), documented
   institutional rebalance latency after macro news, dealer/vol-desk hedging after
   uncertainty resolution. Magnitudes and timing with primary or measured sources; label
   folklore as folklore.
3. **Adversarial/decay:** Has minutes-to-hours announcement drift been arbitraged away
   post-2015? Any Rosa-2022-style OOS kills specific to announcement drift? Is surviving
   drift concentrated in ES/NQ futures seconds-scale (inaccessible to manual cash-equity
   latency) with nothing left at minutes–hours in cash?
4. **Single-name expression:** For a market-wide effect expressed in NVDA/TSLA/AMD/MU/GOOGL,
   what does the literature say about announcement-day beta vs idiosyncratic noise in single
   megacaps — is the index effect detectable per-name at feasible N, or does idio vol drown
   it (power question)? Any announcement studies done directly on single stocks?
5. **Release mechanics (T1 precision):** Exact publication protocols and timestamps — BLS
   8:30:00 embargo mechanics, ISM 10:00:00 dissemination, UMich distribution (subscriber
   early access history — did two-tier release end, when?), Conference Board 10:00, Treasury
   auction result posting latency (13:01? 13:03? variance), Fed 14:00:00. Anything that
   invalidates a 5-minute reaction window read from quotes (e.g., staggered/leaked releases).

Already known (do not re-derive): M20 registration text (grid, anchors, 5-min reaction
window, 25 s decision lag, 15:45 cap); our owned data (XNAS 1s TOB 2020–2026, 5 names);
Savor–Wilson announcement-day premium is DAY-level — the open question is intraday
resolution; exhaustion-map kills listed above.

The decision this feeds: M20 Stage-2 registration is ALLOWED only with this lane's verdict
in hand. Pre-commitment: if this lane returns EXHAUSTED-BY-FIELD for minutes–hours
cash-equity announcement continuation with >=2 unrefuted OOS kills covering our release
classes, Stage-2 is BANNED regardless of the Stage-1 screen outcome (screen numbers then
stand as coverage documentation only). If it returns a named, timed, slow payer for specific
classes, those classes get priority in Stage-2.

## Modality focus blocks

- **A (academic):** SSRN/JF/JFE/RFS/JME 2013–2026. Monetary momentum, pre-/post-FOMC drift
  and decay, macro announcement premia intraday resolution, auction-result spillovers.
  Extract bps + horizon + sample + OOS columns for every claim.
- **B (primary/venue):** Release-mechanics ground truth from the issuing institutions (BLS,
  ISM, UMich, Conference Board, TreasuryDirect, Federal Reserve) — exact timestamps, embargo
  and dissemination protocol, any two-tier access history with end dates. Owns all
  mechanics claims.
- **C (practitioner):** Vol-target/risk-parity/CTA execution practice — how fast do they
  re-lever after macro events (fund docs, sell-side strategy notes, manager commentary)?
  Any practitioner accounts of trading post-release drift at retail-accessible latency?
- **D (adversarial/prior-art):** The kill case: decay studies, crowding evidence, prop/HFT
  dominance of the first seconds leaving nothing at minutes, failed replications, and any
  practitioner post-mortems of announcement-drift strategies. Default skeptical; refuters
  will hold you to primary sources.

Refuter rule (standing): claims default `refuted=true` without a primary source; majority
refuted kills the claim.
