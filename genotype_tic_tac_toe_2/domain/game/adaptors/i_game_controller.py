"""
Inbound adaptor interface: IGameController.

Defines the contract for any inbound driving mechanism (REST, CLI, etc.).
Implementations live alongside this interface in the adaptors/ folder.
"""
from __future__ import annotations

import abc


class IGameController(abc.ABC):
    @abc.abstractmethod
    def create_game(self):
        """Create a new game and return its initial state representation."""

    @abc.abstractmethod
    def make_move(self, game_id: str, position: int):
        """Apply a move to the specified game and return the updated state."""

    @abc.abstractmethod
    def get_game(self, game_id: str):
        """Return the current state of the specified game."""
