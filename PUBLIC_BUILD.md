# Public portfolio build notes

**Public project name:** `intraday-research-engine`  
**Python import package:** `enginev51` (unchanged for code stability)

This tree is a **sanitized export** of a private research repository, intended for
GitHub portfolio / job-application use. The private source tree was **not** renamed
or modified.

## What changed vs the private lab

| Area | Public treatment |
|---|---|
| Market-data lake (`data/`) | **Excluded** — not redistributable / too large |
| API credentials | Project `.env` only; no machine-local secret paths |
| Absolute user paths | Removed; optional secondary lake via env vars |
| Account / capital framing | Research notional $10k; example small-account lens $1k (report-only) |
| Live trading playbooks | Not included |
| Session handoff / private status | Not included; see `ARCHITECTURE.md` instead |
| Research corpus | Included and lightly scrubbed (full lab archive) |

## What recruiters should evaluate

1. **Causal fill / replay engineering** (`src/enginev51/backtest/`)
2. **Research protocol enforcement** (`protocol.py`, tests)
3. **Data integrity controls** (lake completeness, seal, isolation tests)
4. **Honest research process** (ledger, registrations, null results)

## What not to evaluate as “live performance”

Frozen experiment reports document a research process. Many families failed their
gates under honest costs. That is a feature of the methodology, not a product claim.

## How this directory was produced

1. Copy `src/`, `tests/`, `scripts/`, `config/`, `research/` (excluding binaries/parquet)
2. Scrub personal paths and account-scale details
3. Rewrite public docs (`README` landing page, `ARCHITECTURE`, `LICENSE`, `.env.example`, `docs/AI_WORKFLOW.md`)
4. Neutralize config credential defaults

The private repository is **not** modified by this export.

## Verification checklist (re-run before publish)

- [x] No username / absolute home paths in text sources
- [x] No `.env`, `data/`, personal playbooks at repo root
- [x] Deploy lens constants aligned at **$1000** (settings + positioning + cockpit + sizing_shadow)
- [x] Credentials only via project `.env` / env vars
- [x] Core unit tests green (protocol / fills / config / isolation)
- [x] One-off scripts use relative scratch paths (not machine temp dirs)

**Acceptable residual historical language:** research notes may still *mention* predecessor projects (`engineV2`/`engineV5`), `PLAYBOOK`/`HANDOFF` as prior private docs, or experiment family names. Those are research archive references, not live secrets.
