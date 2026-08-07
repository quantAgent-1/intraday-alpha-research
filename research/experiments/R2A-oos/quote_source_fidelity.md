# V-QS quote-source fidelity (Alpaca-downsampled vs owned Databento bbo1s)

- [FAIL] V-QS1 KLAC 2025-03-18: mids match (3,017 matched seconds) — median 1.431 bps; within 2 bps 61.15%
- [FAIL] V-QS2 KLAC 2025-03-18: |dOLI| <= 0.05 — own +0.0842 vs alpaca -0.0903 (d=0.1746)
- [FAIL] V-QS3 KLAC 2025-03-18: exit mid |d| <= 1 bps — 2.608 bps
- [PASS] V-QS1 TXN 2024-06-05: mids match (12,942 matched seconds) — median 0.255 bps; within 2 bps 99.87%
- [PASS] V-QS2 TXN 2024-06-05: |dOLI| <= 0.05 — own -0.0014 vs alpaca -0.0417 (d=0.0403)
- [PASS] V-QS3 TXN 2024-06-05: exit mid |d| <= 1 bps — 0.255 bps
- [PASS] V-QS1 MU 2024-06-05: mids match (19,927 matched seconds) — median 0.000 bps; within 2 bps 99.73%
- [PASS] V-QS2 MU 2024-06-05: |dOLI| <= 0.05 — own +0.0318 vs alpaca +0.0158 (d=0.0161)
- [PASS] V-QS3 MU 2024-06-05: exit mid |d| <= 1 bps — 0.000 bps
- [PASS] V-QS1 NVDA 2025-10-15: mids match (23,568 matched seconds) — median 0.000 bps; within 2 bps 99.99%
- [FAIL] V-QS2 NVDA 2025-10-15: OLI computable — own=None alp=None
- [PASS] V-QS3 NVDA 2025-10-15: exit mid |d| <= 1 bps — 0.000 bps
- [FAIL] V-QS1 AMAT 2025-03-18: mids match (11,120 matched seconds) — median 0.325 bps; within 2 bps 98.83%
- [PASS] V-QS2 AMAT 2025-03-18: |dOLI| <= 0.05 — own +0.0012 vs alpaca +0.0000 (d=0.0012)
- [PASS] V-QS3 AMAT 2025-03-18: exit mid |d| <= 1 bps — 0.000 bps

## VERDICT: V-QS FAIL — bulk pull may NOT be consumed
