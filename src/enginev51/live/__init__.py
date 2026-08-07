"""Live signal engine package (L0/L1).

See ``research/LIVE_SIGNAL_ENGINE_L0L1_DESIGN.md`` (orchestrator, frozen 2026-07-23) and its
context proposal ``research/LIVE_SIGNAL_ENGINE_PROPOSAL.md``. SIGNAL-ONLY by
construction: nothing in this package imports a broker/network module or routes an
order; its sole write target is ``research/live/signals_journal.parquet``.
"""
