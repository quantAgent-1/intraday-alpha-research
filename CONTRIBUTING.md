# Contributing

**intraday-research-engine** is published as a **research portfolio**. It is not a
multi-contributor product with a feature roadmap. That said, if you fork or open issues:

## Rules that protect scientific integrity

1. **Register before economics.** New experiment families should document hypothesis,
   mechanism, features, thresholds, and promotion rule *before* results exist.
2. **Respect the holdout seal.** Do not unseal or re-cut splits to salvage a narrative.
3. **Economics come from the fill kernel / replayer.** Do not invent `net_bps` by hand
   unless the screen is explicitly labeled mid-alpha-only.
4. **No order routing.** Do not add broker order-submit paths.
5. **No secrets.** Never commit `.env`, API keys, account numbers, or personal paths.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check src tests
```

## Scope of PRs

Welcome: bug fixes in pure kernels, clearer docs, test hardening, dependency pins.

Out of scope for this public mirror: private data backfills, personal trading ops,
and reopening closed research families without a new registered design.
