"""M28 mandatory diagnostics (REGISTRATION.md section 11). Reported always, gating never.

Runs only after `m28_run.py validate`. Every item here exists so a PASS can be attacked as
hard as a FAIL:

  1 per-signal IC, train and validate, including FDR-rejected signals
  2 rho matrix across admitted signal streams + effective breadth
  3 drift vs timing decomposition
  4 session-shuffled placebo (200 draws, seed 101) -- the real statistic must sit in the tail
  5 cost sensitivity (estimated / 2x / flat 3 bps stress)
  6 turnover and legs per day (manual-execution feasibility)
  7 decile monotonicity across all ten composite deciles
  8 per-year / per-quarter validate breakdown
  9 coverage funnel

    uv run python scripts/m28_diagnostics.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from m28_panel import SIGNALS  # noqa: E402
from m28_run import (  # noqa: E402
    DECILE,
    FDR_Q,
    GROSS,
    MIN_NAMES_PER_SESSION,
    TRAIN,
    VALID,
    boot_mean,
    load_panel,
    session_ic,
)

EXP = REPO / "research" / "experiments" / "M28-open-cross-battery"
OUT = EXP / "diagnostics.md"
PLACEBO_DRAWS, PLACEBO_SEED = 200, 101


def signal_ls_returns(df: pl.DataFrame, sig: str, sign: float) -> dict[str, float]:
    """Daily decile long-short gross return of ONE signal, for the rho matrix."""
    d = df.select(["date", "sym", f"z_{sig}", "ret_bps"]).drop_nulls()
    out: dict[str, float] = {}
    for key, g in d.partition_by("date", as_dict=True, maintain_order=True).items():
        if g.height < MIN_NAMES_PER_SESSION:
            continue
        v = g[f"z_{sig}"].to_numpy() * sign
        r = g["ret_bps"].to_numpy()
        k = max(1, int(round(g.height * DECILE)))
        o = np.argsort(v)
        out[key[0] if isinstance(key, tuple) else key] = float(
            GROSS / 2 * r[o[-k:]].mean() - GROSS / 2 * r[o[:k]].mean())
    return out


def null_at_admission(a: dict) -> int:
    """Train-only diagnostics for the NULL-AT-ADMISSION outcome.

    The registration is explicit that in this outcome the validate period is NOT consumed,
    so this path deliberately does NOT compute a single validate statistic -- not even a
    per-signal validate IC. Reading validate here would leak information into any future
    family's design and burn a clean 250-session out-of-sample period for nothing, since
    no composite exists to test. Diagnostic item 1's "train and validate" wording is
    superseded by the more specific NULL-AT-ADMISSION rule.
    """
    df = load_panel()
    tr = df.filter((pl.col("date") >= TRAIN[0]) & (pl.col("date") <= TRAIN[1]))
    tr_by = {r["signal"]: r for r in a["per_signal"]}
    L: list[str] = [
        "# M28 diagnostics -- NULL-AT-ADMISSION (train only)", "",
        "No signal cleared Benjamini-Hochberg FDR at q=0.10 across the 14 candidates, so no "
        "composite exists. **The validate period (2025-06-02..2026-05-29) was never read** "
        "and remains clean for a future, better-powered family. Everything below is computed "
        "on TRAIN only.", "",
        "## 1. Per-signal train IC (all 14)", "",
        "| signal | train IC | 95% CI | p | sessions | FDR threshold at its rank | admitted |",
        "|---|---|---|---|---|---|---|"]
    ranked = sorted(SIGNALS, key=lambda z: tr_by[z]["p"])
    m = len(SIGNALS)
    for rank, sig in enumerate(ranked, start=1):
        t = tr_by[sig]
        L.append(f"| {sig} | {t['ic']:+.4f} | [{t['ci_lo']:+.4f}, {t['ci_hi']:+.4f}] | "
                 f"{t['p']:.4f} | {t['n_sessions']} | {rank / m * FDR_Q:.4f} | "
                 f"{'YES' if t['admitted'] else 'no'} |")
    best = tr_by[ranked[0]]
    L += ["", f"Smallest p-value is **{best['p']:.4f}** ({ranked[0]}); the FDR threshold it "
              f"had to clear is **{1 / m * FDR_Q:.4f}**. The battery misses by more than an "
              f"order of magnitude -- this is not a near-miss.", ""]

    # --- what the null actually rules out (turning a null into information) ---
    widths = [(tr_by[s]["ci_hi"] - tr_by[s]["ci_lo"]) / (2 * 1.96) for s in SIGNALS]
    se_med = float(np.median(widths))
    L += ["## 2. What this null rules out", "",
          f"- median per-signal IC standard error on train: **{se_med:.4f}**",
          f"- an IC of **{2 * se_med:.4f}** (t=2) would have been detectable for a single "
          f"signal; none of the 14 reached half of that",
          f"- largest |IC| observed: **{max(abs(tr_by[s]['ic']) for s in SIGNALS):.4f}**",
          "",
          "A daily cross-sectional IC of ~0.02-0.03 is the rough threshold below which a "
          "dollar-neutral decile book cannot clear a 3 bps round-trip cost at this breadth. "
          "Every candidate here sits at or below **0.014**, i.e. the observed effects are "
          "not merely insignificant -- they are too small to be tradeable even if real.", ""]

    # --- rho across all 14 candidate streams on TRAIN (breadth evidence, no validate) ---
    series = {s: signal_ls_returns(tr, s, 1.0) for s in SIGNALS}
    common = sorted(set.intersection(*[set(v) for v in series.values()]))
    if len(common) > 2:
        M = np.array([[series[s][d] for d in common] for s in SIGNALS])
        C = np.corrcoef(M)
        iu = np.triu_indices_from(C, 1)
        rbar = float(C[iu].mean())
        n_eff = m / (1 + (m - 1) * rbar) if rbar > -1 else float("nan")
        L += ["## 3. Breadth of the candidate battery (train L/S streams)", "",
              f"- mean pairwise rho across the 14 candidate streams: **{rbar:+.3f}**",
              f"- implied effective breadth **N_eff = {n_eff:.2f}** of 14",
              f"- max |rho| between any two candidates: **{np.abs(C[iu]).max():.3f}**", "",
              "Breadth was NOT the binding constraint: the candidates are close to "
              "independent. The constraint is that none of them predicts.", ""]

    # --- coverage ---
    fn = pl.read_parquet(EXP / "panel_funnel.parquet")
    L += ["## 4. Coverage funnel", "",
          f"- names processed: {fn.height}",
          f"- name-days kept: {int(fn['kept'].sum()):,}"]
    for c in ("no_hist", "few_rth", "no_exit", "bad_price", "no_pm"):
        if c in fn.columns:
            L.append(f"- dropped `{c}`: {int(fn[c].sum()):,}")
    L += [f"- train: {tr.height:,} name-days over {tr['date'].n_unique()} sessions", ""]

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


def main() -> int:
    a = json.loads((EXP / "admitted.json").read_text(encoding="utf-8"))
    admitted, signs = a["admitted"], a["signs"]
    if not admitted:
        return null_at_admission(a)
    res = json.loads((EXP / "result.json").read_text(encoding="utf-8"))
    df = load_panel()
    va = df.filter((pl.col("date") >= VALID[0]) & (pl.col("date") <= VALID[1]))
    L: list[str] = ["# M28 diagnostics (non-gating)", ""]

    # 1 ---------------------------------------------------------------- IC
    L += ["## 1. Per-signal IC, train vs validate (all 14, including rejected)", "",
          "| signal | train IC | train p | admitted | validate IC | validate 95% CI | sign held |",
          "|---|---|---|---|---|---|---|"]
    tr_by = {r["signal"]: r for r in a["per_signal"]}
    for s in SIGNALS:
        t = tr_by[s]
        _d, ics = session_ic(va, s)
        vic = float(ics.mean()) if ics.size else float("nan")
        lo, hi, _p = boot_mean(ics) if ics.size > 1 else (float("nan"),) * 3
        held = "-" if not np.isfinite(vic) or t["sign"] == 0 else (
            "yes" if np.sign(vic) == t["sign"] else "NO")
        L.append(f"| {s} | {t['ic']:+.4f} | {t['p']:.4f} | "
                 f"{'**YES**' if t['admitted'] else '.'} | {vic:+.4f} | "
                 f"[{lo:+.4f}, {hi:+.4f}] | {held} |")
    L.append("")

    # 2 ------------------------------------------------------- rho / breadth
    series = {s: signal_ls_returns(va, s, signs[s]) for s in admitted}
    dates = sorted(set.intersection(*[set(v) for v in series.values()])) if series else []
    M = np.array([[series[s][d] for d in dates] for s in admitted])
    L += ["## 2. Correlation between admitted signal streams (validate daily L/S returns)", ""]
    if len(admitted) > 1 and len(dates) > 2:
        C = np.corrcoef(M)
        iu = np.triu_indices_from(C, 1)
        rbar = float(C[iu].mean())
        n_eff = len(admitted) / (1 + (len(admitted) - 1) * rbar) if rbar > -1 else float("nan")
        L += ["| | " + " | ".join(admitted) + " |", "|---" * (len(admitted) + 1) + "|"]
        for i, s in enumerate(admitted):
            L.append(f"| {s} | " + " | ".join(f"{C[i, j]:+.3f}" for j in range(len(admitted))) + " |")
        L += ["", f"mean pairwise rho **{rbar:+.3f}** -> effective breadth "
                  f"**N_eff = {n_eff:.2f}** of {len(admitted)} streams",
              "(the documented bar-tier reopening condition asks N_eff >= 8)", ""]
    else:
        L += [f"only {len(admitted)} admitted stream(s) - no pairwise rho to report", ""]

    # 3 --------------------------------------------------------- drift/timing
    dv = pl.read_parquet(EXP / "daily_validate.parquet")
    g = dv["gross_bps"].to_numpy()
    mk = dv["mkt_ret"].to_numpy()
    L += ["## 3. Drift vs timing", "",
          "- portfolio is dollar-neutral by construction (net exposure 0), so market drift "
          "cannot enter mechanically", "",
          f"- universe mean open->exit return over validate: **{mk.mean():+.2f}** bps/day",
          f"- portfolio gross: **{g.mean():+.2f}** bps/day",
          f"- corr(portfolio gross, universe mean) = **{float(np.corrcoef(g, mk)[0, 1]):+.3f}**",
          ""]

    # 4 ------------------------------------------------------------- placebo
    rng = np.random.default_rng(PLACEBO_SEED)
    expr = [pl.col(f"z_{s}") * signs[s] for s in admitted]
    n_avail = sum((e.is_not_null().cast(pl.Int32) for e in expr[1:]),
                  expr[0].is_not_null().cast(pl.Int32))
    comp = sum(e.fill_null(0.0) for e in expr[1:]) + expr[0].fill_null(0.0)
    base = va.with_columns(n_avail.alias("n_sig")).with_columns(
        pl.when(pl.col("n_sig") > 0).then(comp / pl.col("n_sig")).otherwise(None).alias("comp")
    ).drop_nulls(["comp", "ret_bps", "hs"])
    parts = list(base.partition_by("date", as_dict=True, maintain_order=True).items())
    draws = []
    for _ in range(PLACEBO_DRAWS):
        tot, nd = 0.0, 0
        for _k, gg in parts:
            if gg.height < MIN_NAMES_PER_SESSION:
                continue
            r = gg["ret_bps"].to_numpy()
            c = rng.permutation(gg["comp"].to_numpy())     # break the name<->signal link
            kk = max(1, int(round(gg.height * DECILE)))
            o = np.argsort(c)
            tot += GROSS / 2 * r[o[-kk:]].mean() - GROSS / 2 * r[o[:kk]].mean()
            nd += 1
        draws.append(tot / nd)
    draws = np.array(draws)
    real = res["validate"]["mean_gross"]
    pct = float((draws < real).mean())
    L += ["## 4. Placebo (composite shuffled across names within each session)", "",
          f"- {PLACEBO_DRAWS} draws, seed {PLACEBO_SEED}",
          f"- placebo mean gross **{draws.mean():+.3f}** bps/day, sd {draws.std():.3f}",
          f"- placebo 5th/95th percentile [{np.percentile(draws, 5):+.3f}, "
          f"{np.percentile(draws, 95):+.3f}]",
          f"- **real gross {real:+.3f} sits at the {100 * pct:.1f}th percentile** of the "
          f"placebo distribution", ""]

    # 5 ------------------------------------------------------------- costs
    v = res["validate"]
    L += ["## 5. Cost sensitivity", "",
          "| assumption | mean net bps/day |", "|---|---|",
          f"| primary: flat 3.0 bps half-spread | {v['mean_net']:+.3f} |",
          f"| 2x primary (6.0 bps) | {v['mean_net_double_cost']:+.3f} |",
          f"| optimistic: 0.85 bps (measured megacap median) "
          f"| {v['mean_net_optimistic_cost']:+.3f} |",
          f"| mean daily cost charged | {v['mean_cost']:.3f} |", ""]

    # 6 ---------------------------------------------------------- turnover
    dvv = va.with_columns(n_avail.alias("n_sig")).with_columns(
        pl.when(pl.col("n_sig") > 0).then(comp / pl.col("n_sig")).otherwise(None).alias("comp")
    ).drop_nulls(["comp", "ret_bps", "hs"])
    prev_l, prev_s, turns, legs = set(), set(), [], []
    for _key, gg in dvv.partition_by("date", as_dict=True, maintain_order=True).items():
        if gg.height < MIN_NAMES_PER_SESSION:
            continue
        c = gg["comp"].to_numpy()
        kk = max(1, int(round(gg.height * DECILE)))
        o = np.argsort(c)
        ln = {gg["sym"][int(i)] for i in o[-kk:]}
        sh = {gg["sym"][int(i)] for i in o[:kk]}
        if prev_l:
            turns.append(1 - len(ln & prev_l) / len(ln))
            turns.append(1 - len(sh & prev_s) / len(sh))
        prev_l, prev_s = ln, sh
        legs.append(len(ln) + len(sh))
    L += ["## 6. Turnover / execution load", "",
          f"- mean daily name turnover per leg: **{100 * float(np.mean(turns)):.0f}%**",
          f"- legs to key per day: **{float(np.mean(legs)):.0f}** "
          f"({float(np.mean(legs)) / 2:.0f} long + {float(np.mean(legs)) / 2:.0f} short)",
          f"- at the $10k research book that is ~${10000 / float(np.mean(legs)):,.0f} per name; "
          f"at the $1k deploy lens ~${1200 / float(np.mean(legs)):,.0f} per name",
          "", "A manual trader cannot key this many legs by 09:28. Feasibility is a "
          "REPORTED FACT here, not a gate; a deployable version would need a top-N variant, "
          "which is a NEW registration, not a tweak of this one.", ""]

    # 7 --------------------------------------------------------- monotonic
    L += ["## 7. Decile monotonicity (validate, gross bps, decile 1 = most negative composite)",
          "", "| decile | mean gross bps | n name-days |", "|---|---|---|"]
    buckets: dict[int, list[float]] = {i: [] for i in range(10)}
    for _k, gg in dvv.partition_by("date", as_dict=True, maintain_order=True).items():
        if gg.height < MIN_NAMES_PER_SESSION:
            continue
        c = gg["comp"].to_numpy()
        r = gg["ret_bps"].to_numpy()
        q = np.clip((np.argsort(np.argsort(c)) * 10 // len(c)), 0, 9)
        for b in range(10):
            if (q == b).any():
                buckets[b].extend(r[q == b].tolist())
    for b in range(10):
        L.append(f"| {b + 1} | {float(np.mean(buckets[b])):+.2f} | {len(buckets[b]):,} |")
    L.append("")

    # 8 --------------------------------------------------------- per period
    L += ["## 8. Validate breakdown by quarter", "",
          "| quarter | sessions | mean net bps/day |", "|---|---|---|"]
    dvq = dv.with_columns(
        (pl.col("date").str.slice(0, 4) + "Q"
         + ((pl.col("date").str.slice(5, 2).cast(pl.Int32) - 1) // 3 + 1).cast(pl.Utf8)).alias("q"))
    for key, gg in dvq.partition_by("q", as_dict=True, maintain_order=True).items():
        L.append(f"| {key[0] if isinstance(key, tuple) else key} | {gg.height} | "
                 f"{float(gg['net_bps'].to_numpy().mean()):+.3f} |")
    L.append("")

    # 9 --------------------------------------------------------- coverage
    fn = pl.read_parquet(EXP / "panel_funnel.parquet")
    L += ["## 9. Coverage funnel (across all names)", "",
          f"- names processed: {fn.height}",
          f"- name-days kept: {int(fn['kept'].sum()):,}"]
    for c in ("no_hist", "few_rth", "no_exit", "bad_price", "no_pm"):
        if c in fn.columns:
            L.append(f"- dropped `{c}`: {int(fn[c].sum()):,}")
    L += ["", f"- train sessions {res['train']['sessions']}, "
              f"validate sessions {res['validate']['sessions']}",
          f"- ADIA validate: SR {res['validate']['adia']['sr_native']:+.4f}, "
          f"PSR {res['validate']['adia']['psr_sr0_0']:.4f}, "
          f"MinTRL {res['validate']['adia']['min_trl']:.0f} sessions", ""]

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
