"""
Outbound port: IGameArchive.

Defines the contract that GameService relies on for persisting completed games.
Concrete implementations live alongside this interface in the ports/ folder.
"""
from __future__ import annotations

import abc

from domain.game.completed_game import CompletedGame


class IGameArchive(abc.ABC):
    @abc.abstractmethod
    def save(self, game: CompletedGame) -> None:
        """Persist a completed game.  Overwrites if game_id already exists."""

    @abc.abstractmethod
    def get(self, game_id: str) -> CompletedGame | None:
        """Return the completed game for game_id, or None if not found."""

    @abc.abstractmethod
    def list_all(self) -> list[CompletedGame]:
        """Return all archived completed games, oldest first."""
