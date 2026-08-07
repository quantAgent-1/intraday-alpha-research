"""Shared statistics kernels (no family owns them).

Created by the 2026-08-01 structural review (J3): pure math that several
families need must not live inside a research screen, or every new family
imports a closed family to get a Sharpe ratio.

- ``enginev51.stats.adia`` — ADIA Lab Research Paper No.19 (Lopez de Prado,
  Lipton & Zoonekynd 2026) Sharpe inference: native-frequency SR, PSR under the
  generalized (non-Normal AR(1)) sampling variance, MinTRL. MOVED verbatim out
  of ``research_screens.sizing_shadow`` (M23 golden anchors still pin them);
  that module re-imports them, so every historical importer keeps working with
  object IDENTITY preserved.
- ``enginev51.stats.report`` — the one report-shaped clustered-CI wrapper for
  FUTURE families. Closed screens keep their frozen local ``_ci`` copies.
"""
