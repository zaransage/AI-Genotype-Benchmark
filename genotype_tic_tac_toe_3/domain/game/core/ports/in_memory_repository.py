"""
domain/game/core/ports/in_memory_repository.py

Outbound port implementation: in-memory dictionary store.
Swap for a DB-backed implementation without touching any other module.
"""

from typing import Optional

from domain.game.core.models               import GameState
from domain.game.core.ports.i_game_repository import IGameRepository


class InMemoryGameRepository(IGameRepository):
    """Thread-unsafe in-memory store — suitable for single-process dev/test use."""

    def __init__(self) -> None:
        self._store: dict[str, GameState] = {}

    def save(self, state: GameState) -> None:
        self._store[state.game_id] = state

    def find_by_id(self, game_id: str) -> Optional[GameState]:
        return self._store.get(game_id)
