"""
Pure business logic for tic-tac-toe.

No I/O, no framework concerns — only deterministic transformations
of canonical model types.
"""

from __future__ import annotations

from domain.core.models import (
    GameState,
    Move,
    EMPTY,
    PLAYER_X,
    PLAYER_O,
    STATUS_ACTIVE,
    STATUS_X_WINS,
    STATUS_O_WINS,
    STATUS_DRAW,
)


def empty_board() -> list[list[str]]:
    """Return a blank 3×3 board."""
    return [[EMPTY, EMPTY, EMPTY] for _ in range(3)]


def check_winner(board: list[list[str]]) -> str | None:
    """Return the winning player symbol, or None if there is no winner yet."""
    lines = [
        # rows
        [board[0][0], board[0][1], board[0][2]],
        [board[1][0], board[1][1], board[1][2]],
        [board[2][0], board[2][1], board[2][2]],
        # columns
        [board[0][0], board[1][0], board[2][0]],
        [board[0][1], board[1][1], board[2][1]],
        [board[0][2], board[1][2], board[2][2]],
        # diagonals
        [board[0][0], board[1][1], board[2][2]],
        [board[0][2], board[1][1], board[2][0]],
    ]
    for line in lines:
        if line[0] != EMPTY and line[0] == line[1] == line[2]:
            return line[0]
    return None


def is_draw(board: list[list[str]]) -> bool:
    """Return True when every cell is occupied (caller must confirm no winner)."""
    return all(cell != EMPTY for row in board for cell in row)


def apply_move(state: GameState, move: Move) -> GameState:
    """
    Apply *move* to *state* and return the resulting GameState.

    Raises ValueError for:
    - game already over
    - wrong player's turn
    - target cell already occupied
    """
    if state.status != STATUS_ACTIVE:
        raise ValueError("Cannot move: game is already over")

    if state.current_player != move.player:
        raise ValueError(
            f"It is {state.current_player}'s turn, not {move.player}'s"
        )

    if state.board[move.row][move.col] != EMPTY:
        raise ValueError(
            f"Cell ({move.row}, {move.col}) is already occupied"
        )

    new_board = [row[:] for row in state.board]
    new_board[move.row][move.col] = move.player

    winner = check_winner(new_board)
    if winner == PLAYER_X:
        status       = STATUS_X_WINS
        next_player  = state.current_player   # game over; value is informational
    elif winner == PLAYER_O:
        status       = STATUS_O_WINS
        next_player  = state.current_player
    elif is_draw(new_board):
        status       = STATUS_DRAW
        winner       = None
        next_player  = state.current_player
    else:
        status       = STATUS_ACTIVE
        winner       = None
        next_player  = PLAYER_O if move.player == PLAYER_X else PLAYER_X

    return GameState(
        game_id        = state.game_id,
        board          = new_board,
        current_player = next_player,
        status         = status,
        winner         = winner,
    )
