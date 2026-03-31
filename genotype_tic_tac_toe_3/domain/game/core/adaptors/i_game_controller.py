"""
domain/game/core/adaptors/i_game_controller.py

Inbound adaptor interface: how external callers (REST, CLI, etc.) drive the core.
One file per interface (ADR 0008, AI_CONTRACT §8).
"""

from abc    import ABC, abstractmethod

from domain.game.core.models import GameState, Move


class IGameController(ABC):
    """Inbound contract for driving tic-tac-toe use cases."""

    @abstractmethod
    def create_game(self) -> GameState: ...

    @abstractmethod
    def make_move(self, game_id: str, move: Move) -> GameState: ...

    @abstractmethod
    def get_game(self, game_id: str) -> GameState: ...
