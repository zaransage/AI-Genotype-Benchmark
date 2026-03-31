"""
Outbound port: contract for game state persistence.

Implementations live in the same folder; the composition root selects one.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.core.models import GameState


class IGameRepository(ABC):

    @abstractmethod
    def save(self, state: GameState) -> None:
        """Persist *state*, overwriting any previous entry for the same game_id."""

    @abstractmethod
    def get(self, game_id: str) -> GameState:
        """Return the GameState for *game_id*. Raises KeyError if not found."""

    @abstractmethod
    def exists(self, game_id: str) -> bool:
        """Return True if a game with *game_id* has been saved."""
