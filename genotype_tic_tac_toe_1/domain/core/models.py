"""
Canonical dataclass models for the tic-tac-toe domain.

Validation in __post_init__: bad input raises ValueError — it never silently passes.
Policy constants are class-level, not injected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing    import Optional


# ---------------------------------------------------------------------------
# Policy constants — baked into the model, not injected
# ---------------------------------------------------------------------------

EMPTY    = ""
PLAYER_X = "X"
PLAYER_O = "O"

STATUS_ACTIVE = "active"
STATUS_X_WINS = "x_wins"
STATUS_O_WINS = "o_wins"
STATUS_DRAW   = "draw"

_VALID_CELLS    = {EMPTY, PLAYER_X, PLAYER_O}
_VALID_PLAYERS  = {PLAYER_X, PLAYER_O}
_VALID_STATUSES = {STATUS_ACTIVE, STATUS_X_WINS, STATUS_O_WINS, STATUS_DRAW}
_VALID_WINNERS  = {None, PLAYER_X, PLAYER_O}


# ---------------------------------------------------------------------------
# GameState
# ---------------------------------------------------------------------------

@dataclass
class GameState:
    game_id:        str
    board:          list[list[str]]
    current_player: str
    status:         str
    winner:         Optional[str]

    def __post_init__(self) -> None:
        if not self.game_id:
            raise ValueError("game_id must not be empty")

        if len(self.board) != 3 or any(len(row) != 3 for row in self.board):
            raise ValueError("board must be exactly 3 rows of 3 cells")

        for row in self.board:
            for cell in row:
                if cell not in _VALID_CELLS:
                    raise ValueError(f"Invalid board cell: {cell!r}")

        if self.current_player not in _VALID_PLAYERS:
            raise ValueError(f"current_player must be 'X' or 'O', got {self.current_player!r}")

        if self.status not in _VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")

        if self.winner not in _VALID_WINNERS:
            raise ValueError(f"winner must be 'X', 'O', or None, got {self.winner!r}")


# ---------------------------------------------------------------------------
# Move
# ---------------------------------------------------------------------------

@dataclass
class Move:
    game_id: str
    player:  str
    row:     int
    col:     int

    def __post_init__(self) -> None:
        if not self.game_id:
            raise ValueError("game_id must not be empty")

        if self.player not in _VALID_PLAYERS:
            raise ValueError(f"player must be 'X' or 'O', got {self.player!r}")

        if not (0 <= self.row <= 2):
            raise ValueError(f"row must be 0–2, got {self.row}")

        if not (0 <= self.col <= 2):
            raise ValueError(f"col must be 0–2, got {self.col}")


# ---------------------------------------------------------------------------
# CompletedGameRecord
# ---------------------------------------------------------------------------

@dataclass
class CompletedGameRecord:
    game_id:  str
    outcome:  str              # x_wins | o_wins | draw
    winner:   Optional[str]
    board:    list[list[str]]
    moves:    list[Move]

    def __post_init__(self) -> None:
        if not self.game_id:
            raise ValueError("game_id must not be empty")

        if self.outcome not in _VALID_STATUSES - {STATUS_ACTIVE}:
            raise ValueError(f"outcome must be a terminal status, got {self.outcome!r}")
