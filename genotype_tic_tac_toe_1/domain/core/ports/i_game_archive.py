"""
Outbound port: contract for archiving completed games.

Implementations live in the same folder; the composition root selects one.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.core.models import CompletedGameRecord


class IGameArchive(ABC):

    @abstractmethod
    def archive(self, record: CompletedGameRecord) -> None:
        """Persist a completed game record."""

    @abstractmethod
    def list_completed(self) -> list[CompletedGameRecord]:
        """Return all archived completed game records, oldest first."""

    @abstractmethod
    def get_record(self, game_id: str) -> CompletedGameRecord:
        """Return the record for *game_id*. Raises KeyError if not found."""
