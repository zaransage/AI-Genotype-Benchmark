"""
Canonical domain model for a completed (terminal) tic-tac-toe game.

CompletedGame is immutable once created: status must be terminal and the
move list is frozen at archive time.  Validation in __post_init__ raises
on bad input; it never silently passes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from domain.game.game import GameStatus


# fmt: off
@dataclass
class CompletedGame:
    TERMINAL_STATUSES: ClassVar[frozenset[str]] = frozenset({
        GameStatus.X_WINS,
        GameStatus.O_WINS,
        GameStatus.DRAW,
    })

    game_id:      str
    board:        list[str]
    moves:        list[int]
    winner:       str | None
    status:       str
    completed_at: str        # ISO-8601 timestamp set at archive time

    def __post_init__(self) -> None:
        if not self.game_id:
            raise ValueError("game_id must not be empty")
        if len(self.board) != 9:
            raise ValueError(f"board must have exactly 9 cells, got {len(self.board)}")
        if self.status not in self.TERMINAL_STATUSES:
            raise ValueError(
                f"CompletedGame status must be terminal, got {self.status!r}"
            )
        if not self.completed_at:
            raise ValueError("completed_at must not be empty")
# fmt: on
