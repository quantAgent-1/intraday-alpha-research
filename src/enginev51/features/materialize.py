"""Materialize the training feature+label matrix, one parquet per signal symbol.

Output: data/features/{version}/{SYMBOL}.parquet with META + f_* + l_* columns,
sampled every `sample_every` minutes, warmed rows only. `_meta.json` records
the registry (feature list, horizons, source feed, build time) for provenance.

The same feature code (grid → compute_base → compute_features) is what the live
loop will call on streaming bars — single-sourced by construction.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl
import structlog

from enginev51.config import Settings, get_research_config
from enginev51.data import store
from enginev51.features import slow
from enginev51.features.grid import build_session_grid
from enginev51.labels import forward

log = structlog.get_logger(__name__)

SECTOR_ANCHOR: dict[str, str] = {
    "NVDA": "SMH", "AMD": "SMH", "MU": "SMH", "AVGO": "SMH", "SMCI": "SMH",
    # others default to market (QQQ)
}

MARKET_ANCHOR = "QQQ"
WARMUP_MINUTES = 30


def _base_for(settings: Settings, feed: str, symbol: str) -> pl.DataFrame | None:
    # v5.1: reads union the new lake and engineV5's legacy lake (read-only).
    bars = store.load_bars(settings.read_roots, feed, symbol)
    if bars.height == 0:
        log.warning("no_bars", symbol=symbol)
        return None
    grid = build_session_grid(bars, symbol)
    return slow.compute_base(grid)


def materialize(
    settings: Settings,
    version: str = "v1",
    symbols: list[str] | None = None,
    feed: str = "sip",
    sample_every: int = 5,
) -> None:
    # v5.1: config field enginev5_data_dir renamed to data_dir
    out_dir = settings.data_dir / "features" / version
    out_dir.mkdir(parents=True, exist_ok=True)
    # v5.1: universe binding moved to research config (protocol-bound), not Settings.
    syms = [s.upper() for s in (symbols or get_research_config().universe_bar_signal)]

    anchors: dict[str, pl.DataFrame] = {}
    for a in {MARKET_ANCHOR, *SECTOR_ANCHOR.values()}:
        base = _base_for(settings, feed, a)
        if base is None:
            raise RuntimeError(f"anchor {a} has no bars — backfill first")
        anchors[a] = base
        log.info("anchor_ready", anchor=a, rows=base.height)

    # v5.1: anchors/kalman removed (engineV5 ledger: dead ends)
    feature_cols = list(slow.FEATURE_COLS)

    built: list[str] = []
    for s in syms:
        base = _base_for(settings, feed, s)
        if base is None:
            continue
        sector = anchors.get(SECTOR_ANCHOR.get(s, MARKET_ANCHOR))
        feats = slow.compute_features(base, anchors[MARKET_ANCHOR], sector)
        # v5.1: anchors/kalman removed (engineV5 ledger: dead ends)
        feats = forward.add_labels(feats)
        feats = (
            feats.filter(
                (pl.col("row_in_sess") >= WARMUP_MINUTES)
                & (pl.col("row_in_sess") % sample_every == 0)
                & pl.col("vol20").is_not_null()
            )
            .select(list(slow.META_COLS) + feature_cols + list(forward.LABEL_COLS))
            .sort("ts")
        )
        feats.write_parquet(out_dir / f"{s}.parquet", compression="zstd")
        built.append(s)
        log.info("features_written", symbol=s, rows=feats.height)

    meta = {
        "version": version,
        "built_at": datetime.now(UTC).isoformat(),
        "source_feed": feed,
        "sample_every_min": sample_every,
        "warmup_minutes": WARMUP_MINUTES,
        "symbols": built,
        "feature_cols": feature_cols,
        "label_cols": list(forward.LABEL_COLS),
        "sector_anchor": SECTOR_ANCHOR,
        "market_anchor": MARKET_ANCHOR,
    }
    (out_dir / "_meta.json").write_text(json.dumps(meta, indent=2))
    log.info("materialize_complete", symbols=len(built), out=str(out_dir))
