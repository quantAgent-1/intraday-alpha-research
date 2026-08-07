# AI-agent workflow (detail)

Companion to the [README](../README.md) landing page for **intraday-research-engine**.
This document expands how human judgment and AI agents co-produced the research lab
without diluting protocol control.

---

## Intent

Use agents for **leverage on bounded work**. Keep humans as the **control plane**
for anything that defines scientific truth or irreversible policy.

| Safe to delegate | Keep human-owned |
|---|---|
| Mechanical ports and refactors | Holdout seal / unseal |
| Test scaffolds from a frozen spec | Registration text & promotion rules |
| Boilerplate CLIs | Thresholds after any results exist |
| Literature sweeps with fixed modalities | Family pass/kill/obituary |
| Adversarial “attack this diff” passes | Final ledger verdicts |
| Formatting, typing, repetitive scripts | “What counts as a look” |

---

## Loop (one research change)

1. **Frame** — human writes the problem, constraints, and non-goals.  
2. **Register** (if an experiment) — ledger row *before* economics.  
3. **Spec** — interfaces, acceptance tests, files in/out of scope.  
4. **Implement** — implementer agent(s) produce code + tests.  
5. **Attack** — separate adversarial agent reviews for leakage, seal bypass,
   fill bugs, silent look-ahead, constant drift.  
6. **Audit** — human reads the attack report, checks critical paths, merges.  
7. **Run / look** — only after registration; results append to the ledger.  
8. **Encode lessons** — any incident becomes a guard test + in-file comment.

Skipping 2, 5, or 6 is how agent-assisted work becomes p-hacking with extra steps.

---

## Role cards

### Human orchestrator

- Owns architecture and package boundaries  
- Freezes numbers that define a family (gates, costs model, splits)  
- Interprets results; refuses to “tune after seeing” without a new variant count  
- Decides when a family is closed vs parked  

### Implementer agent

- Receives a complete spec; does not expand scope silently  
- Prefer pure functions and tests next to new logic  
- Must not invent fill semantics or cost constants  

### Research agent

- Structured passes (e.g. academic / primary venue / practitioner / adversarial)  
- Outputs cited notes into `research/deep/…`  
- Default stance for weak claims: treat as unproven until primary evidence  

### Adversarial reviewer agent

- Assumes the implementer is optimistic  
- Looks for: future leakage, seal disable under `-O`, NaN-as-data, adjusted-vs-raw
  price mixes, unregistered threshold drift  
- A “clean” review is suspicious if the change touched fills or labels  

---

## Prompting patterns that worked

**Good implementer brief**

- Goal in one paragraph  
- Files allowed to touch  
- Invariants that must remain true (link to tests)  
- Explicit non-goals (“do not change `HEADLINE_GATE`”)  
- Definition of done (commands that must pass)  

**Good adversarial brief**

- Diff or module list only  
- Ask for *kill shots*, not style nits  
- Require each finding to name the invariant broken  

**Bad pattern**

- “Build me an edge on NVDA” with no registration  
- Same agent implements and then self-reviews  
- Letting agents edit the ledger or unseal paths  

---

## Mapping to repo artifacts

| Workflow step | Artifact |
|---|---|
| Registration | `research/ledger.jsonl`, `research/experiments/**` |
| Protocol enforcement | `src/enginev51/protocol.py`, `tests/test_protocol.py` |
| Fill / replay truth | `src/enginev51/backtest/*`, `tests/test_fills.py` |
| Deep research lanes | `research/deep/` |
| Public map | `README.md`, `ARCHITECTURE.md` |

---

## Takeaway for employers

This is not “AI wrote my project.”  
It is **human-directed multi-agent production** with the same control points a
careful research team needs: registration, separation of build vs attack, and
human ownership of truth.
