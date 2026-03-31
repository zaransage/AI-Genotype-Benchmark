"""
Outbound port: IGameRepository.

Defines the contract that GameService relies on for persistence.
Concrete implementations live alongside this interface in the ports/ folder.
"""
from __future__ import annotations

import abc

from domain.game.game import GameState


class IGameRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, state: GameState) -> None:
        """Persist or overwrite the given game state."""

    @abc.abstractmethod
    def get(self, game_id: str) -> GameState | None:
        """Return the game state for game_id, or None if not found."""
