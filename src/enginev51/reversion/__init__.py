"""M18 reversion_system_v1 harness (BUILD-SPEC + REGISTRATION in
research/experiments/M18-reversion-system/).

A byte-faithful port of engineV2's CPU-backtest OU-reversion semantics onto the
enginev5.1 event_bars1s (1-second) substrate. Harness only: no economics
interpretation lives here.

Port target = engineV2 ``backtest/cpu`` kernels (reversion_nb / event_loop_nb /
ou_mle_nb / riskgate_nb); where the live hot path and the backtest differ, the
backtest wins (it is the anchor's engine). Exact expressions are transcribed
from the cited engineV2 file:line locations in each module's docstring.
"""

from __future__ import annotations
