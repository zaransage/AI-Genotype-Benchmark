"""
Inbound adaptor implementation: GameService.

Orchestrates repository access and game logic.
Framework exceptions (HTTPException) must not appear here.
"""

from __future__ import annotations

import uuid
from typing import Optional

from domain.core.adaptors.i_game_service  import IGameService
from domain.core.game_logic               import apply_move, empty_board
from domain.core.models                   import (
    CompletedGameRecord,
    GameState,
    Move,
    PLAYER_X,
    STATUS_ACTIVE,
)
from domain.core.ports.i_game_archive     import IGameArchive
from domain.core.ports.i_game_repository  import IGameRepository


class GameService(IGameService):

    def __init__(
        self,
        repository: IGameRepository,
        archive:    Optional[IGameArchive] = None,
    ) -> None:
        self._repository   = repository
        self._archive      = archive
        self._move_history: dict[str, list[Move]] = {}

    def create_game(self) -> GameState:
        state = GameState(
            game_id        = str(uuid.uuid4()),
            board          = empty_board(),
            current_player = PLAYER_X,
            status         = STATUS_ACTIVE,
            winner         = None,
        )
        self._repository.save(state)
        return state

    def get_game(self, game_id: str) -> GameState:
        return self._repository.get(game_id)

    def make_move(self, move: Move) -> GameState:
        state     = self._repository.get(move.game_id)
        new_state = apply_move(state, move)
        self._repository.save(new_state)

        if self._archive is not None:
            self._move_history.setdefault(move.game_id, []).append(move)
            if new_state.status != STATUS_ACTIVE:
                record = CompletedGameRecord(
                    game_id = new_state.game_id,
                    outcome = new_state.status,
                    winner  = new_state.winner,
                    board   = new_state.board,
                    moves   = self._move_history.pop(move.game_id, []),
                )
                self._archive.archive(record)

        return new_state

    def list_completed_games(self) -> list[CompletedGameRecord]:
        if self._archive is None:
            return []
        return self._archive.list_completed()
