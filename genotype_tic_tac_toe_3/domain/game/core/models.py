"""
domain/game/core/models.py

Canonical @dataclass models — the primary containers passed between adaptors and core.
Validation in __post_init__; bad input raises, never silently passes (ADR 0002, AI_CONTRACT §3).
Aligned column formatting is intentional — excluded from auto-formatters via pyproject.toml (ADR 0006).
"""

from dataclasses import dataclass
from typing     import Optional


PLAYER_X          = "X"
PLAYER_O          = "O"
STATUS_IN_PROGRESS = "in_progress"
STATUS_X_WINS     = "x_wins"
STATUS_O_WINS     = "o_wins"
STATUS_DRAW       = "draw"

_VALID_PLAYERS  = (PLAYER_X, PLAYER_O)
_VALID_STATUSES = (STATUS_IN_PROGRESS, STATUS_X_WINS, STATUS_O_WINS, STATUS_DRAW)


@dataclass
class Move:
    player : str
    row    : int
    col    : int

    def __post_init__(self) -> None:
        if self.player not in _VALID_PLAYERS:
            raise ValueError(f"Invalid player: {self.player!r}. Must be one of {_VALID_PLAYERS}.")
        if not (0 <= self.row <= 2):
            raise ValueError(f"Invalid row: {self.row}. Must be 0–2.")
        if not (0 <= self.col <= 2):
            raise ValueError(f"Invalid col: {self.col}. Must be 0–2.")


@dataclass
class GameState:
    game_id        : str
    board          : list           # list[list[str]], 3×3 grid of "", "X", or "O"
    current_player : str
    status         : str
    winner         : Optional[str] = None

    def __post_init__(self) -> None:
        if not self.game_id:
            raise ValueError("game_id cannot be empty.")
        if self.current_player not in _VALID_PLAYERS:
            raise ValueError(f"Invalid current_player: {self.current_player!r}.")
        if self.status not in _VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}.")
        if len(self.board) != 3 or any(len(row) != 3 for row in self.board):
            raise ValueError("board must be a 3×3 list.")
