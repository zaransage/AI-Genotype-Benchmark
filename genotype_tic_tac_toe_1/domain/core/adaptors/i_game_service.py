"""
Inbound adaptor interface: contract for the game application service.

Implementations live in this folder; the composition root selects one.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.core.models import CompletedGameRecord, GameState, Move


class IGameService(ABC):

    @abstractmethod
    def create_game(self) -> GameState:
        """Create and persist a new game; return its initial state."""

    @abstractmethod
    def get_game(self, game_id: str) -> GameState:
        """Return the current state for *game_id*. Raises KeyError if not found."""

    @abstractmethod
    def make_move(self, move: Move) -> GameState:
        """
        Apply *move* and persist the result; return the new state.

        Raises KeyError if the game does not exist.
        Raises ValueError for illegal moves (wrong player, occupied cell, game over).
        """

    @abstractmethod
    def list_completed_games(self) -> list[CompletedGameRecord]:
        """Return all archived completed games, oldest first.

        Returns an empty list when no archive is configured.
        """
