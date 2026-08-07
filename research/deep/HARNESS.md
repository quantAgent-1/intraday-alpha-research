# enginev5.1 Deep-Research Harness — v1.0 (2026-07-17)

Orchestrator protocol for running deep research on this project's open questions. **Tool- and
product-agnostic**: the orchestrator may be a human, a Claude Code session, a claude.ai project,
or any other agent harness that can (a) give each research agent a prompt, (b) let it search and
fetch the web, (c) collect a markdown report. Nothing here depends on a specific vendor's
features; where parallelism is unavailable, run lanes sequentially — the contract is identical.

Companion files (same directory):
- `AGENT_BRIEF.md` — the hand-out. Every research agent receives it **verbatim** at the top of
  its prompt. Never summarize or excerpt it; agents share no other context.
- `EXHAUSTION_MAP.md` — the accumulating verdict table (open vs exhausted solution space).
Optional Claude Code launcher: `.claude/skills/engine-deep-research/` — explicit
`/engine-deep-research` invocation only; generic "deep research" requests never route here.
Inputs: `research/OPEN_QUESTIONS.md` (the areas), `research/ledger.jsonl` +
`research/experiments/*/report.md` (what we already falsified ourselves).

## Verdict vocabulary (fixed — never invent new labels)

- `OPEN-TESTABLE` — genuinely open AND testable now on owned/≤~$100 data under our constraints.
  Must ship with a registered-trial sketch.
- `OPEN-BLOCKED(<blocker+$>)` — open, but needs data/access/capital; name the minimal unblock
  and its exact cost.
- `EXHAUSTED-BY-US` — our ledger killed it; cite trial id(s). Re-open only with a NEW mechanism
  or NEW data class.
- `EXHAUSTED-BY-FIELD` — ≥2 independent T1/T2 sources kill it under our constraint profile.
- `NOT-VIABLE-STRUCTURAL` — possibly real for HFT/institutions; fails a brief-§8 gate (latency,
  size, access, session) that no research can fix.
- `UNMAPPED` — map mode only: cell identified, no research pass yet.

## Mode A — area deep-dive (input: an OPEN_QUESTIONS item or a free question)

1. **Resolve the charge.** Map the input to an `OPEN_QUESTIONS.md` item (id `DR-Q<n>`) or draft
   a charge for a free question (`DR-X<next>`). Several areas → independent parallel lanes.
2. **Pre-flight (local, before any web spend).** Search `research/ledger.jsonl`,
   `EXHAUSTION_MAP.md`, and `research/experiments/` for the topic. Already EXHAUSTED-BY-US with
   no new angle → stop, report the receipt, spend nothing. Partially covered → write the known
   facts into the charge so agents don't re-derive them.
3. **Compose agent prompts.** Each agent's prompt = `AGENT_BRIEF.md` verbatim + this charge
   block:

       ---
       ## Your charge
       Area: DR-<id> — <title> (OPEN_QUESTIONS.md #<n> / new)
       Question(s): <verbatim from OPEN_QUESTIONS.md + orchestrator refinements>
       Already known (do not re-derive): <pre-flight facts; champion numbers if relevant>
       Your modality: <ONE of A/B/C/D/E below — search only this way; others are covered>
       Depth: ≥8 distinct searches, ≥6 sources fetched AND read; stop early only per brief §10.
       Deliver: brief §9 schema. Your verdict is a RECOMMENDATION; synthesis happens upstream.

4. **Fan out — four standard modalities (+1 optional), one agent each:**
   - **A academic**: SSRN/arXiv q-fin/journals; sample periods and cost treatment mandatory.
   - **B primary/venue**: exchange specs & trader notices, SEC/FINRA rules, broker order-type
     docs, vendor schemas. Owns all mechanics claims (cutoffs, deadlines, fees, eligibility).
   - **C practitioner/vendor**: named-practitioner blogs, fund letters, vendor research (tag
     conflicts), podcasts/talks.
   - **D adversarial/prior-art**: who tried this and failed; decay/crowding/capacity evidence;
     the strongest "this is already arbitraged away" case. D is the lane's built-in skeptic —
     never skip D.
   - **E data-reality (optional, LOCAL not web)**: probe OUR lake/code — do the fields exist,
     what n is reachable, what would the test cost. Run E whenever the verdict could be
     OPEN-TESTABLE. (E requires repo access; if the orchestrating harness has none, the
     orchestrator flags "E pending" in the report instead.)
5. **Verify.** Extract the load-bearing claims (verdict-changing only, ≤8 per area). For each,
   2 independent refuter agents, prompt = `AGENT_BRIEF.md` + "Attempt to REFUTE via primary
   sources: <claim + citation>. Default refuted=true if you cannot locate a primary source.
   Return refuted true/false + reason." Majority refuted → claim dies. CONFIRMED status
   requires that a refuter actually located a T1/T2 source; otherwise best status is PLAUSIBLE.
6. **Synthesize (the orchestrator itself — never delegated).** Write
   `research/deep/DR-<id>-<slug>/report.md` in the brief §9 schema plus a `### Synthesis`
   header (agent count, date, dissents between lanes). Decision rules, applied in order:
   - any brief-§8 gate hard-FAIL → `NOT-VIABLE-STRUCTURAL` (data-cost fail → `OPEN-BLOCKED`);
   - ledger corpse, no new mechanism/data → `EXHAUSTED-BY-US`;
   - ≥2 independent surviving T1/T2 refutations → `EXHAUSTED-BY-FIELD`;
   - testable on owned/≤~$100 data → `OPEN-TESTABLE` + trial sketch;
   - else `OPEN-BLOCKED(<blocker+$>)`.
   Normalize every number into a unit table (bps per-event / per-plan / per-session). Always
   state "what would flip this verdict."
7. **File it.** Update the area's row in `EXHAUSTION_MAP.md` (verdict, date, report path).
   Update the priority section of `OPEN_QUESTIONS.md` if the ranking changed. NEVER write to
   `research/ledger.jsonl` and NEVER register a trial — hand the user a one-line ledger-note
   suggestion and the registration sketch; the user decides.
8. **Report to the user**: verdict + confidence + the 3–5 claims that drove it + next action.
   Not a wall of sources.

## Mode B — map mode ("which solution space is still open?")

Rebuilds `EXHAUSTION_MAP.md`:
1. **Local join first** (no web): sweep ledger, experiment reports, `OPEN_QUESTIONS.md`, prior
   `DR-*` reports → verdict per known cell.
2. **White-space agents** (web, carry the brief): charge = "enumerate mechanisms/venues/event
   types fitting the brief-§3 survivor profile that appear NOWHERE in this map", plus one agent
   per taxonomy slice (auction/single-print regimes; scheduled forced-flow events; anything
   retail-latency-tolerant). Their yield lands as `UNMAPPED` rows — candidates, not verdicts.
3. **Output**: updated map with (a) verdict per cell, (b) `UNMAPPED` candidates with
   survivor-profile scores, (c) ranked next deep-dives (score × cheapness × decision
   relevance). Present the delta to the user.

## Execution notes (any harness)

- Lane budget per area: 4 modality agents + ≤16 refuter calls. Quick check: modalities B+D
  only. Exhaustive: split sub-questions into their own lanes.
- Parallel if the harness supports it; sequential otherwise. Order when sequential: B → D →
  A → C (mechanics and the skeptic first — they kill lanes early and cheaply).
- Capable-but-cheap models are fine for search and refute lanes; the STRONGEST available model
  does synthesis, verdicts, and trial sketches. Never let a search agent write the verdict.
- If the harness supports structured/JSON output, mirror the brief-§9 fields; otherwise the
  markdown schema is the contract.

## Done bar (a lane is not finished until)

- All brief-§9 sections present; every CONFIRMED claim has a refuter-located T1/T2 source.
- Gate table complete (7 gates), survivor-profile score tallied.
- Verdict + confidence + flip condition stated; units normalized (bps per WHAT).
- `EXHAUSTION_MAP.md` row updated; report filed under `research/deep/`.
- No ledger writes, no holdout contact, no auto-registration — sketches go to the user.

## Orchestrator anti-patterns (each has bitten this project)

- Accepting an agent's PLAUSIBLE as CONFIRMED because it is exciting.
- Merging lanes without dedup → double-counted "independent" confirmation from one root source.
- Letting modality C (vendor) numbers set the economics when A/B disagree.
- A verdict that ignores unit mismatch (per-event vs per-session inflation).
- Researching a corpse because nobody checked the ledger first (Mode A step 2 is mandatory).
- Skipping modality D — a lane with no skeptic converges on enthusiasm.
