"""
domain/game/core/ports/i_game_archive.py

Outbound port interface: persist completed games and their move history.
Implementations live alongside this interface (AI_CONTRACT §8).
"""

from abc import ABC, abstractmethod
from typing import Optional


class IGameArchive(ABC):
    """Contract for archiving completed tic-tac-toe games."""

    @abstractmethod
    def record_move(
        self,
        game_id: str,
        player:  str,
        row:     int,
        col:     int,
    ) -> None:
        """Append one move to the move log for *game_id*."""

    @abstractmethod
    def close_game(
        self,
        game_id: str,
        outcome: str,
        winner:  Optional[str],
    ) -> None:
        """Mark a game as complete and record its outcome."""

    @abstractmethod
    def find_completed_games(self) -> list[dict]:
        """Return all closed game records, ordered by archived_at ascending."""
