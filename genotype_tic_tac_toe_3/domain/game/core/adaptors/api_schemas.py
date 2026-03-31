"""
domain/game/core/adaptors/api_schemas.py

Pydantic request/response schemas — the API boundary only.
Converts wire JSON ↔ canonical @dataclass models. Never leaks into domain (AI_CONTRACT §4, ADR 0006).
Aligned column formatting is intentional — excluded from auto-formatters via pyproject.toml (ADR 0006).
"""

from __future__ import annotations

from typing  import Optional
from pydantic import BaseModel, field_validator

from domain.game.core.models import GameState, Move


class MoveRequest(BaseModel):
    """Inbound wire format for POST /games/{id}/moves."""

    player : str
    row    : int
    col    : int

    @field_validator("player")
    @classmethod
    def player_must_be_valid(cls, v: str) -> str:
        if v not in ("X", "O"):
            raise ValueError(f"player must be 'X' or 'O', got {v!r}")
        return v

    @field_validator("row", "col")
    @classmethod
    def coordinate_in_range(cls, v: int) -> int:
        if not (0 <= v <= 2):
            raise ValueError(f"row/col must be 0–2, got {v}")
        return v

    def to_canonical(self) -> Move:
        return Move(player=self.player, row=self.row, col=self.col)


class GameStateResponse(BaseModel):
    """Outbound wire format for all game state responses."""

    game_id        : str
    board          : list[list[str]]
    current_player : str
    status         : str
    winner         : Optional[str]

    @classmethod
    def from_canonical(cls, state: GameState) -> "GameStateResponse":
        return cls(
            game_id        = state.game_id,
            board          = state.board,
            current_player = state.current_player,
            status         = state.status,
            winner         = state.winner,
        )
