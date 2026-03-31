"""
InMemoryGameRepository — dict-backed implementation of IGameRepository.

Suitable for development and test; not safe for concurrent use.
Config requirements: none (stateless beyond the in-process dict).
"""
from __future__ import annotations

from domain.game.game import GameState
from domain.game.ports.i_game_repository import IGameRepository


class InMemoryGameRepository(IGameRepository):
    def __init__(self) -> None:
        self._store: dict[str, GameState] = {}

    def save(self, state: GameState) -> None:
        self._store[state.game_id] = state

    def get(self, game_id: str) -> GameState | None:
        return self._store.get(game_id)
