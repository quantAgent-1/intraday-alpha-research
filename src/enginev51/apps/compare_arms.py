"""compare_arms — paired A0-vs-A1 (or any two trials) economics on the research book.

Loads two ``results.parquet`` frames written by ``apps/run_trial.py`` and reports,
per PROTOCOL v6 §4 / the M3-A1 promotion rule:

  1. Per-session BOOK net: the sum of taken ``net_bps`` per session (0 for a
     session with no taken plan in a frame). Restricted to the intersection of
     sessions present in BOTH frames; the paired delta series is b - a. Sessions
     ARE the clusters here, so ``stress.clustered_mean_ci(deltas, sessions)`` is
     a plain bootstrap over the paired per-session deltas. Reported split-wise
     (train-period vs validate-period) and pooled.

  2. Plan-level paired subset: results.parquet has no stable shared key across
     arms (plan_seq and fill ts drift), so plans are paired on
     (symbol, session, payer, side, authored-ts-rounded-to-minute). The authored
     ts is recovered from ``plan_id`` (``{payer}-{symbol}-{ts}-{seq}``), which is
     identical across arms for the same detector state — a more honest key than
     the latency-jittered fill ts. The pairing rate is reported. Plans authored
     in A but not B are A's states that B vetoed.

  3. report.md under research/experiments/<out>/ with: both books' headline, the
     delta CI table, take/skip (veto) counts, and the leg-repricing signature
     (A1 vs A0) — exit-reason mix + gross/expected/confidence quantiles. (Authored
     stop/target geometry is not persisted in results.parquet, so the leg
     comparison uses these realized/authored-claim columns as the closest proxy.)

    uv run python -m enginev51.apps.compare_arms \
        --trial-a M3-A0-may --trial-b M3-A1-may --out M3-A1-vs-A0-may
"""

from __future__ import annotations

import click
import numpy as np
import polars as pl

from enginev51.backtest import stress
from enginev51.protocol import experiments_dir, split_of

NS_PER_MIN = 60_000_000_000


# --------------------------------------------------------------------------- io


def load_results(trial_id: str) -> pl.DataFrame:
    path = experiments_dir() / trial_id / "results.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"no results.parquet for trial {trial_id!r} at {path}")
    return pl.read_parquet(path)


# --------------------------------------------------------------------------- books


def per_session_book(df: pl.DataFrame) -> pl.DataFrame:
    """[session, book_net] — summed taken net_bps per session (0 when none taken).

    Every session present in ``df`` (any status) gets a row, so a session that
    authored only vetoed/unfilled plans still books 0 rather than vanishing.
    """
    sessions = df.select("session").unique()
    booked = (
        df.filter(pl.col("taken"))
        .group_by("session")
        .agg(pl.col("net_bps").sum().alias("book_net"))
    )
    return (
        sessions.join(booked, on="session", how="left")
        .with_columns(pl.col("book_net").fill_null(0.0))
        .sort("session")
    )


def _clustered(values: np.ndarray, sessions: np.ndarray) -> tuple[float, float, float, int]:
    if values.shape[0] == 0:
        return float("nan"), float("nan"), float("nan"), 0
    m, lo, hi = stress.clustered_mean_ci(values, sessions)
    return m, lo, hi, values.shape[0]


def book_headline(df: pl.DataFrame, sessions: list[str]) -> dict:
    """Per-arm book headline over the given (intersection) sessions."""
    book = per_session_book(df).filter(pl.col("session").is_in(sessions))
    vals = book["book_net"].to_numpy()
    sess = book["session"].to_numpy()
    m, lo, hi, n = _clustered(vals, sess)
    return {
        "n_sessions": n,
        "total_book_net_bps": round(float(vals.sum()), 3) if n else 0.0,
        "mean_per_session_bps": round(m, 3) if n else None,
        "ci_lo": round(lo, 3) if n else None,
        "ci_hi": round(hi, 3) if n else None,
    }


def delta_table(a: pl.DataFrame, b: pl.DataFrame) -> tuple[pl.DataFrame, list[str], pl.DataFrame]:
    """(delta CI table split-wise+pooled, intersection sessions, paired delta frame).

    delta = b's per-session book - a's per-session book, over the session
    intersection; clustered (== plain, one delta per session) bootstrap CIs.
    """
    inter = sorted(set(a["session"].unique()) & set(b["session"].unique()))
    ba = per_session_book(a).filter(pl.col("session").is_in(inter))
    bb = per_session_book(b).filter(pl.col("session").is_in(inter))
    paired = (
        ba.rename({"book_net": "book_a"})
        .join(bb.rename({"book_net": "book_b"}), on="session", how="inner")
        .with_columns((pl.col("book_b") - pl.col("book_a")).alias("delta"))
        .with_columns(
            pl.col("session").map_elements(split_of, return_dtype=pl.Utf8).alias("split")
        )
        .sort("session")
    )

    rows: list[dict] = []
    for split in ("train", "validate", "__POOLED__"):
        sub = paired if split == "__POOLED__" else paired.filter(pl.col("split") == split)
        m, lo, hi, n = _clustered(sub["delta"].to_numpy(), sub["session"].to_numpy())
        rows.append(
            {
                "split": "pooled" if split == "__POOLED__" else split,
                "n_sessions": n,
                "mean_delta_bps": round(m, 3) if n else None,
                "ci_lo": round(lo, 3) if n else None,
                "ci_hi": round(hi, 3) if n else None,
            }
        )
    tbl = pl.DataFrame(
        rows,
        schema={
            "split": pl.Utf8,
            "n_sessions": pl.Int64,
            "mean_delta_bps": pl.Float64,
            "ci_lo": pl.Float64,
            "ci_hi": pl.Float64,
        },
        orient="row",
    )
    return tbl, inter, paired


# --------------------------------------------------------------------------- pairing


def _authored_ts_min(plan_id: str) -> int | None:
    """Recover the authored-ts (rounded to the minute) from ``{payer}-{sym}-{ts}-{seq}``."""
    parts = plan_id.split("-")
    if len(parts) < 4:
        return None
    try:
        ts = int(parts[-2])
    except ValueError:
        return None
    return (ts // NS_PER_MIN) * NS_PER_MIN


def _pair_key(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col("plan_id")
        .map_elements(_authored_ts_min, return_dtype=pl.Int64)
        .alias("_ats")
    )


def pairing_report(a: pl.DataFrame, b: pl.DataFrame) -> dict:
    """Plan-level pairing on (symbol, session, payer, side, authored-ts-minute).

    Reports counts + pairing rate and the veto count (authored in A, absent in B).
    """
    keys = ["symbol", "session", "payer", "side", "_ats"]
    ka = _pair_key(a).select(keys).unique()
    kb = _pair_key(b).select(keys).unique()
    matched = ka.join(kb, on=keys, how="inner").height
    only_a = ka.join(kb, on=keys, how="anti").height  # authored in A, not B = vetoed by B
    only_b = kb.join(ka, on=keys, how="anti").height
    denom = ka.height
    return {
        "n_authored_a": a.height,
        "n_authored_b": b.height,
        "n_unique_keys_a": ka.height,
        "n_unique_keys_b": kb.height,
        "n_matched": matched,
        "n_only_a_vetoed_by_b": only_a,
        "n_only_b": only_b,
        "pairing_rate": round(matched / denom, 4) if denom else None,
    }


def leg_signature(df: pl.DataFrame, arm_label: str) -> pl.DataFrame:
    """Leg-repricing proxy for the taken stream: exit mix share + column quantiles.

    Authored stop/target px are not persisted in results.parquet; gross_mid_bps
    (realized), expected_net_bps (the plan's own claim, which A1 re-prices) and
    confidence (A1 lifts up to 0.7) are the observable signature of re-pricing.
    """
    t = df.filter(pl.col("taken"))
    n = t.height
    rows: list[dict] = []

    def _q(col: str, q: float) -> float | None:
        return round(float(t[col].quantile(q)), 3) if n else None

    for col in ("gross_mid_bps", "expected_net_bps", "confidence"):
        rows.append(
            {
                "arm": arm_label,
                "metric": col,
                "n": n,
                "p10": _q(col, 0.10),
                "p50": _q(col, 0.50),
                "p90": _q(col, 0.90),
                "mean": round(float(t[col].mean()), 3) if n else None,
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            "arm": pl.Utf8,
            "metric": pl.Utf8,
            "n": pl.Int64,
            "p10": pl.Float64,
            "p50": pl.Float64,
            "p90": pl.Float64,
            "mean": pl.Float64,
        },
        orient="row",
    )


def exit_mix(df: pl.DataFrame, arm_label: str) -> pl.DataFrame:
    t = df.filter(pl.col("taken"))
    if t.height == 0:
        return pl.DataFrame(
            schema={"arm": pl.Utf8, "exit_reason": pl.Utf8, "count": pl.Int64, "share": pl.Float64}
        )
    g = t.group_by("exit_reason").agg(pl.len().alias("count")).sort("count", descending=True)
    return g.with_columns(
        pl.lit(arm_label).alias("arm"),
        (pl.col("count") / t.height).round(4).alias("share"),
    ).select("arm", "exit_reason", "count", "share")


# --------------------------------------------------------------------------- report


def _ascii(df: pl.DataFrame) -> str:
    with pl.Config(
        tbl_formatting="ASCII_MARKDOWN",
        tbl_hide_dataframe_shape=True,
        tbl_hide_column_data_types=True,
        tbl_rows=200,
        tbl_cols=-1,
        tbl_width_chars=200,
    ):
        return str(df)


def build_report_md(trial_a: str, trial_b: str, a: pl.DataFrame, b: pl.DataFrame) -> str:
    tbl, inter, paired = delta_table(a, b)
    ha = book_headline(a, inter)
    hb = book_headline(b, inter)
    pr = pairing_report(a, b)

    head = pl.DataFrame(
        [
            {"arm": f"A = {trial_a}", **ha},
            {"arm": f"B = {trial_b}", **hb},
        ],
        schema={
            "arm": pl.Utf8,
            "n_sessions": pl.Int64,
            "total_book_net_bps": pl.Float64,
            "mean_per_session_bps": pl.Float64,
            "ci_lo": pl.Float64,
            "ci_hi": pl.Float64,
        },
        orient="row",
    )
    pair_tbl = pl.DataFrame([pr], orient="row")

    md: list[str] = [
        f"# compare_arms — B({trial_b}) vs A({trial_a})",
        "",
        f"Intersection sessions: {len(inter)}  "
        f"(A sessions={a['session'].n_unique()}, B sessions={b['session'].n_unique()})",
        "",
        "## 1. Per-session BOOK net headline (intersection sessions)",
        "",
        _ascii(head),
        "",
        "## 2. Paired per-session BOOK delta (B - A), day/session-clustered CI",
        "",
        "delta_j = book_B(session_j) - book_A(session_j); sessions are the bootstrap clusters.",
        "",
        _ascii(tbl),
        "",
        "## 3. Plan-level pairing (symbol, session, payer, side, authored-ts-minute)",
        "",
        "'n_only_a_vetoed_by_b' = detector states authored in A but not B (B's vetoes).",
        "",
        _ascii(pair_tbl),
        "",
        "## 4. Leg-repricing signature (taken stream) — A0 vs A1",
        "",
        "Authored leg px are not persisted in results.parquet; these realized / "
        "authored-claim columns are the observable re-pricing proxy.",
        "",
        _ascii(pl.concat([leg_signature(a, "A"), leg_signature(b, "B")], how="vertical")),
        "",
        "### Exit-reason mix",
        "",
        _ascii(pl.concat([exit_mix(a, "A"), exit_mix(b, "B")], how="vertical_relaxed")),
        "",
    ]
    return "\n".join(md)


# --------------------------------------------------------------------------- cli


@click.command()
@click.option("--trial-a", required=True, help="Baseline trial id (research/experiments/<id>/).")
@click.option("--trial-b", required=True, help="Overlay trial id to compare against A.")
@click.option("--out", required=True, help="Output experiment id for the comparison report.")
def main(trial_a: str, trial_b: str, out: str) -> None:
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")  # Windows cp949 console safety
    a = load_results(trial_a)
    b = load_results(trial_b)

    md = build_report_md(trial_a, trial_b, a, b)
    out_dir = experiments_dir() / out
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "report.md"
    report_path.write_text(md, encoding="utf-8")

    tbl, inter, _ = delta_table(a, b)
    pr = pairing_report(a, b)
    click.echo(f"compare: B={trial_b} vs A={trial_a}  intersection_sessions={len(inter)}")
    click.echo(_ascii(tbl))
    click.echo(
        f"pairing: matched={pr['n_matched']} vetoed_by_b={pr['n_only_a_vetoed_by_b']} "
        f"rate={pr['pairing_rate']}"
    )
    click.echo(f"report: {report_path}")


if __name__ == "__main__":
    main()
