"""Purged walk-forward folds over session dates.

Expanding-window walk-forward: each fold trains on all sessions up to
(test_start − embargo) and tests on a contiguous block of sessions. Labels are
strictly intraday (they never cross a session boundary), so a 1-session embargo
is already conservative; it guards refactoring accidents more than physics.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


@dataclass(slots=True, frozen=True)
class Fold:
    train_sessions: tuple[str, ...]
    test_sessions: tuple[str, ...]


def walk_forward_folds(
    df: pl.DataFrame,
    test_block_sessions: int = 21,
    min_train_sessions: int = 250,
    embargo_sessions: int = 1,
) -> list[Fold]:
    sessions = sorted(df["session"].unique().to_list())
    folds: list[Fold] = []
    i = min_train_sessions
    while i < len(sessions):
        test = sessions[i : i + test_block_sessions]
        train = sessions[: max(0, i - embargo_sessions)]
        if train and test:
            folds.append(Fold(tuple(train), tuple(test)))
        i += test_block_sessions
    return folds
