"""
domain/game/core/ports/i_game_repository.py

Outbound port interface: how the core reaches persistent storage.
One file per interface (ADR 0008, AI_CONTRACT §8).
"""

from abc      import ABC, abstractmethod
from typing   import Optional

from domain.game.core.models import GameState


class IGameRepository(ABC):
    """Outbound contract for GameState persistence."""

    @abstractmethod
    def save(self, state: GameState) -> None: ...

    @abstractmethod
    def find_by_id(self, game_id: str) -> Optional[GameState]: ...
