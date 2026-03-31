"""
domain/game/core/adaptors/rest_controller.py

Inbound adaptor implementation: wires GameService + IGameRepository for REST use.
KeyError for missing game IDs is caught at the route level where HTTPException belongs (ADR 0006).
An optional IGameArchive records each move and closes completed games for persistence.
"""

from typing import Optional

from domain.game.core.adaptors.i_game_controller  import IGameController
from domain.game.core.game_service                import GameService
from domain.game.core.models                      import GameState, Move, STATUS_IN_PROGRESS
from domain.game.core.ports.i_game_archive        import IGameArchive
from domain.game.core.ports.i_game_repository     import IGameRepository


class RestGameController(IGameController):
    """Drives GameService; raises KeyError for not-found games (route layer converts to 404)."""

    def __init__(
        self,
        service:    GameService,
        repository: IGameRepository,
        archive:    Optional[IGameArchive] = None,
    ) -> None:
        self._service    = service
        self._repository = repository
        self._archive    = archive

    def create_game(self) -> GameState:
        state = self._service.create_game()
        self._repository.save(state)
        return state

    def make_move(self, game_id: str, move: Move) -> GameState:
        state = self._repository.find_by_id(game_id)
        if state is None:
            raise KeyError(f"Game not found: {game_id!r}")
        new_state = self._service.apply_move(state, move)
        self._repository.save(new_state)
        if self._archive is not None:
            self._archive.record_move(game_id, move.player, move.row, move.col)
            if new_state.status != STATUS_IN_PROGRESS:
                self._archive.close_game(game_id, new_state.status, new_state.winner)
        return new_state

    def get_game(self, game_id: str) -> GameState:
        state = self._repository.find_by_id(game_id)
        if state is None:
            raise KeyError(f"Game not found: {game_id!r}")
        return state
