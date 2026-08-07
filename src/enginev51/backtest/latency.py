"""Manual-execution latency model: seeded, per-(plan, leg) uniform draws.

The human takes 5-25 s to act on ANY leg (entry, stop trigger, target arm,
chase, curfew-flat). Draws are deterministic functions of (seed, plan_id, leg)
via sha256 — stable across processes and runs (python's builtin hash() is
salted per process and must never be used here). PROTOCOL v6 §3.
"""

from __future__ import annotations

import hashlib

NS_PER_S = 1_000_000_000

# Canonical leg names — replayer uses these; new legs get new names, never reuse.
LEG_ENTRY = "entry"
LEG_CHASE = "chase"
LEG_STOP = "stop"
LEG_TARGET = "target"  # suffixed with index: target0, target1
LEG_CURFEW = "curfew"
LEG_HOLD = "hold"  # hold-expiry market-out


def latency_ns(
    seed: int, plan_id: str, leg: str, lo_s: float = 5.0, hi_s: float = 25.0
) -> int:
    """Uniform [lo_s, hi_s) seconds in ns, deterministic in (seed, plan_id, leg)."""
    if hi_s < lo_s:
        raise ValueError("hi_s < lo_s")
    h = hashlib.sha256(f"{seed}:{plan_id}:{leg}".encode()).digest()
    u = int.from_bytes(h[:8], "big") / 2**64  # [0, 1)
    return int((lo_s + u * (hi_s - lo_s)) * NS_PER_S)
