"""M28 live instrument -- BORN DARK. Refuses every real-data path until M28 PASSES.

This is the "dynamic model that manages the system live" half of the M28 design. It is
built now, deliberately, so that it cannot be written *after* seeing a result and quietly
shaped to flatter it. It follows the M20F precedent (`sched_window_forward`): a hard gate
on the registered verdict, with `selftest` as the sole pre-PASS runnable path.

Gate: `research/experiments/M28-open-cross-battery/result.json` must exist AND carry
`verdict == "PASS"`. BETWEEN, FAIL, NULL-AT-ADMISSION or a missing file all refuse.

Commands
    selftest              synthetic end-to-end check; the only path that runs pre-PASS
    decide  --asof DATE   emit the target book for that session (gated)
    journal --asof DATE   append the emitted book to the append-only signals journal (gated)
    reconcile --asof DATE compare a journaled book against realised open->exit returns (gated)
    monitor               ADIA panel (SR/PSR/MinTRL) over the journalled live track (gated)

Signal-only, per mission: nothing here routes an order. The output is a list of names,
sides and weights for a human to key as market-on-open before 09:28 ET.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import polars as pl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from m28_run import ALPHA, DECILE, GROSS, MIN_NAMES_PER_SESSION, load_panel  # noqa: E402

from enginev51.research_screens.sizing_shadow import (  # noqa: E402
    min_trl,
    psr,
    sample_moments,
    sr_native,
)

EXP = REPO / "research" / "experiments" / "M28-open-cross-battery"
JOURNAL = EXP / "live_journal.parquet"
RESULT = EXP / "result.json"
ADMITTED = EXP / "admitted.json"


class Refused(RuntimeError):
    pass


def gate() -> dict:
    """The hard gate. Any answer other than a registered PASS refuses."""
    if not RESULT.exists():
        if ADMITTED.exists():
            a = json.loads(ADMITTED.read_text(encoding="utf-8"))
            if not a.get("admitted"):
                raise Refused(
                    "M28 outcome is NULL-AT-ADMISSION (0 of 14 signals cleared FDR on train); "
                    "no composite exists and validate was deliberately never read. The "
                    "instrument stays dark permanently for this registration."
                )
        raise Refused("no result.json -- M28 has not been evaluated; instrument stays dark")
    r = json.loads(RESULT.read_text(encoding="utf-8"))
    v = r.get("verdict")
    if v != "PASS":
        raise Refused(
            f"M28 verdict is {v!r}, not 'PASS' -- the instrument stays dark. "
            "Reviving it requires a NEW forward-judged registration, not a flag."
        )
    return r


def book_for(date: str) -> pl.DataFrame:
    """Target book for one session from the FROZEN composite rule (inputs < 09:28)."""
    a = json.loads(ADMITTED.read_text(encoding="utf-8"))
    admitted, signs = a["admitted"], a["signs"]
    df = load_panel().filter(pl.col("date") == date)
    if df.height < MIN_NAMES_PER_SESSION:
        raise Refused(f"{date}: only {df.height} names with complete inputs "
                      f"(min {MIN_NAMES_PER_SESSION}) -- no book emitted")
    expr = [pl.col(f"z_{s}") * signs[s] for s in admitted]
    n_avail = sum((e.is_not_null().cast(pl.Int32) for e in expr[1:]),
                  expr[0].is_not_null().cast(pl.Int32))
    comp = sum(e.fill_null(0.0) for e in expr[1:]) + expr[0].fill_null(0.0)
    d = df.with_columns(n_avail.alias("n_sig")).with_columns(
        pl.when(pl.col("n_sig") > 0).then(comp / pl.col("n_sig")).otherwise(None).alias("comp")
    ).drop_nulls(["comp"])
    c = d["comp"].to_numpy()
    k = max(1, int(round(d.height * DECILE)))
    o = np.argsort(c)
    w = np.zeros(d.height)
    w[o[-k:]] = (GROSS / 2) / k
    w[o[:k]] = -(GROSS / 2) / k
    return d.with_columns(pl.Series("weight", w)).filter(pl.col("weight") != 0).select(
        ["date", "sym", "comp", "weight", "hs"]).sort("weight", descending=True)


def cmd_decide(date: str) -> int:
    gate()
    b = book_for(date)
    print(f"M28 target book {date}  (market-on-open, key before 09:28 ET; exit 15:40-15:45)")
    print(f"{'side':6}{'sym':8}{'weight':>9}{'composite':>11}{'est half-spr':>14}")
    for r in b.iter_rows(named=True):
        print(f"{'LONG' if r['weight'] > 0 else 'SHORT':6}{r['sym']:8}"
              f"{r['weight']:+9.4f}{r['comp']:+11.3f}{r['hs']:14.2f}")
    print(f"gross {float(np.abs(b['weight'].to_numpy()).sum()):.3f}  "
          f"net {float(b['weight'].to_numpy().sum()):+.3f}")
    return 0


def cmd_journal(date: str) -> int:
    gate()
    b = book_for(date).with_columns(
        pl.lit(datetime.now(UTC).isoformat()).alias("emitted_at"))
    if JOURNAL.exists():
        old = pl.read_parquet(JOURNAL)
        if old.filter(pl.col("date") == date).height:
            print(f"REFUSING: {date} already journalled (append-only, never rewritten)")
            return 2
        b = pl.concat([old, b], how="vertical_relaxed")
    tmp = JOURNAL.with_suffix(".tmp")
    b.write_parquet(tmp)
    tmp.replace(JOURNAL)
    print(f"journalled {date}: {b.filter(pl.col('date') == date).height} legs")
    return 0


def cmd_reconcile(date: str) -> int:
    gate()
    if not JOURNAL.exists():
        print("no journal")
        return 2
    j = pl.read_parquet(JOURNAL).filter(pl.col("date") == date)
    if j.height == 0:
        print(f"{date} not journalled")
        return 2
    truth = load_panel().filter(pl.col("date") == date).select(["sym", "ret_bps"])
    m = j.join(truth, on="sym", how="left")
    miss = int(m["ret_bps"].is_null().sum())
    w = m["weight"].to_numpy()
    r = np.nan_to_num(m["ret_bps"].to_numpy(), nan=0.0)
    hs = m["hs"].to_numpy()
    gross = float((w * r).sum())
    cost = float((np.abs(w) * hs).sum() + 0.206 * np.abs(w).sum())
    print(f"{date}: legs {m.height}, unmatched {miss}, "
          f"gross {gross:+.2f} cost {cost:.2f} NET {gross - cost:+.2f} bps")
    return 0 if miss == 0 else 1


def cmd_monitor() -> int:
    gate()
    if not JOURNAL.exists():
        print("no journal")
        return 2
    j = pl.read_parquet(JOURNAL)
    truth = load_panel().select(["sym", "date", "ret_bps"])
    m = j.join(truth, on=["sym", "date"], how="left").drop_nulls("ret_bps")
    daily = m.group_by("date").agg(
        ((pl.col("weight") * pl.col("ret_bps")).sum()
         - (pl.col("weight").abs() * pl.col("hs")).sum()
         - 0.206 * pl.col("weight").abs().sum()).alias("net")
    ).sort("date")
    x = daily["net"].to_numpy()
    if x.size < 2:
        print(f"live sessions: {x.size} -- too few for a panel")
        return 0
    g3, g4, rho = sample_moments(x)
    sr = sr_native(x)
    print(f"live sessions {x.size}  mean {x.mean():+.3f} bps/day")
    print(f"  SR(native) {sr:+.4f}  PSR {psr(sr, 0.0, x.size, rho, g3, g4):.4f}  "
          f"MinTRL {min_trl(sr, 0.0, ALPHA, rho, g3, g4):.0f} sessions")
    return 0


def cmd_selftest() -> int:
    """Synthetic end-to-end check. The ONLY path that runs before a PASS."""
    ok = []
    try:
        gate()
        ok.append(("gate refuses pre-PASS", False, "gate() did NOT refuse"))
    except Refused as e:
        ok.append(("gate refuses pre-PASS", True, str(e)[:60]))

    rng = np.random.default_rng(7)
    n = 60
    comp = rng.normal(size=n)
    k = max(1, int(round(n * DECILE)))
    o = np.argsort(comp)
    w = np.zeros(n)
    w[o[-k:]] = (GROSS / 2) / k
    w[o[:k]] = -(GROSS / 2) / k
    ok.append(("gross == 1.0", abs(np.abs(w).sum() - GROSS) < 1e-12, f"{np.abs(w).sum():.6f}"))
    ok.append(("net == 0.0", abs(w.sum()) < 1e-12, f"{w.sum():.2e}"))
    ok.append(("legs == 2k", int((w != 0).sum()) == 2 * k, f"{int((w != 0).sum())} vs {2 * k}"))
    ok.append(("longs are the top composites",
               bool(comp[w > 0].min() >= comp[w == 0].max()), "ordering"))
    x = rng.normal(0.5, 1.0, 250)
    g3, g4, rho = sample_moments(x)
    sr = sr_native(x)
    ok.append(("ADIA kernels finite",
               all(np.isfinite([sr, psr(sr, 0.0, x.size, rho, g3, g4),
                                min_trl(sr, 0.0, ALPHA, rho, g3, g4)])), "psr/mintrl"))
    for name, passed, detail in ok:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}  ({detail})")
    bad = sum(1 for _n, p, _d in ok if not p)
    print(f"selftest: {len(ok) - bad}/{len(ok)} passed")
    return 0 if bad == 0 else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M28 live instrument (dark until PASS).")
    ap.add_argument("cmd", choices=["selftest", "decide", "journal", "reconcile", "monitor"])
    ap.add_argument("--asof", help="ET session date YYYY-MM-DD")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "selftest":
            return cmd_selftest()
        if a.cmd == "monitor":
            return cmd_monitor()
        if not a.asof:
            print("--asof is required")
            return 2
        return {"decide": cmd_decide, "journal": cmd_journal,
                "reconcile": cmd_reconcile}[a.cmd](a.asof)
    except Refused as e:
        print(f"REFUSED: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
