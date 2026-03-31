"""
domain/game/core/game_service.py

Pure business logic for tic-tac-toe. No framework concerns; no I/O.
HTTPException and logging belong at the route/boundary level only (ADR 0006).
"""

import uuid
from typing import Optional

from domain.game.core.models import (
    GameState,
    Move,
    PLAYER_X,
    PLAYER_O,
    STATUS_IN_PROGRESS,
    STATUS_X_WINS,
    STATUS_O_WINS,
    STATUS_DRAW,
)

_WIN_LINES = [
    # rows
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    # columns
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    # diagonals
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]


class GameService:
    """All tic-tac-toe rules live here. Stateless; takes and returns canonical models."""

    def create_game(self) -> GameState:
        return GameState(
            game_id        = str(uuid.uuid4()),
            board          = [["", "", ""], ["", "", ""], ["", "", ""]],
            current_player = PLAYER_X,
            status         = STATUS_IN_PROGRESS,
            winner         = None,
        )

    def apply_move(self, state: GameState, move: Move) -> GameState:
        if state.status != STATUS_IN_PROGRESS:
            raise ValueError("Cannot move on a finished game.")
        if state.current_player != move.player:
            raise ValueError(f"It is {state.current_player}'s turn, not {move.player}'s.")
        if state.board[move.row][move.col] != "":
            raise ValueError(f"Cell ({move.row}, {move.col}) is already occupied.")

        new_board = [row[:] for row in state.board]
        new_board[move.row][move.col] = move.player

        winner = self._find_winner(new_board)
        if winner:
            return GameState(
                game_id        = state.game_id,
                board          = new_board,
                current_player = move.player,
                status         = STATUS_X_WINS if winner == PLAYER_X else STATUS_O_WINS,
                winner         = winner,
            )

        if self._board_is_full(new_board):
            return GameState(
                game_id        = state.game_id,
                board          = new_board,
                current_player = move.player,
                status         = STATUS_DRAW,
                winner         = None,
            )

        next_player = PLAYER_O if move.player == PLAYER_X else PLAYER_X
        return GameState(
            game_id        = state.game_id,
            board          = new_board,
            current_player = next_player,
            status         = STATUS_IN_PROGRESS,
            winner         = None,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_winner(self, board: list) -> Optional[str]:
        for line in _WIN_LINES:
            values = [board[r][c] for r, c in line]
            if values[0] != "" and values[0] == values[1] == values[2]:
                return values[0]
        return None

    def _board_is_full(self, board: list) -> bool:
        return all(board[r][c] != "" for r in range(3) for c in range(3))
