"""
Outbound port implementation: in-process dictionary store.

Suitable for development and testing; swap for a database-backed
implementation in production by replacing the binding in main.py.
"""

from __future__ import annotations

from domain.core.models                  import GameState
from domain.core.ports.i_game_repository import IGameRepository


class InMemoryGameRepository(IGameRepository):

    def __init__(self) -> None:
        self._store: dict[str, GameState] = {}

    def save(self, state: GameState) -> None:
        self._store[state.game_id] = state

    def get(self, game_id: str) -> GameState:
        if game_id not in self._store:
            raise KeyError(f"Game not found: {game_id!r}")
        return self._store[game_id]

    def exists(self, game_id: str) -> bool:
        return game_id in self._store
