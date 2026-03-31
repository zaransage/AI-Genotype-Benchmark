"""
Canonical domain model for a tic-tac-toe game.

GameState is the primary container passed between adaptors and downstream logic.
Validation occurs in __post_init__ — bad input raises, never silently passes.
Policy constants (VALID_PLAYERS, VALID_CELLS) are baked in as class-level attributes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


# fmt: off
class Player:
    X = "X"
    O = "O"


class GameStatus:
    IN_PROGRESS = "in_progress"
    X_WINS      = "x_wins"
    O_WINS      = "o_wins"
    DRAW        = "draw"


@dataclass
class GameState:
    VALID_PLAYERS: ClassVar[frozenset[str]] = frozenset({Player.X, Player.O})
    VALID_CELLS:   ClassVar[frozenset[str]] = frozenset({"", Player.X, Player.O})
    VALID_STATUSES: ClassVar[frozenset[str]] = frozenset({
        GameStatus.IN_PROGRESS,
        GameStatus.X_WINS,
        GameStatus.O_WINS,
        GameStatus.DRAW,
    })

    game_id:        str
    board:          list[str] = field(default_factory=lambda: [""] * 9)
    current_player: str       = Player.X
    status:         str       = GameStatus.IN_PROGRESS
    winner:         str | None = None

    def __post_init__(self) -> None:
        if not self.game_id:
            raise ValueError("game_id must not be empty")
        if len(self.board) != 9:
            raise ValueError(f"board must have exactly 9 cells, got {len(self.board)}")
        for cell in self.board:
            if cell not in self.VALID_CELLS:
                raise ValueError(f"Invalid cell value: {cell!r}")
        if self.current_player not in self.VALID_PLAYERS:
            raise ValueError(f"Invalid current_player: {self.current_player!r}")
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")
# fmt: on
