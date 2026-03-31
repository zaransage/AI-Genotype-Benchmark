"""
GameService — business logic for tic-tac-toe.

Depends only on IGameRepository (injected) and optionally IGameArchive.
When an archive is provided, completed games are persisted with their move
history.  The archive parameter defaults to None for backward compatibility
with existing tests and simple composition roots.

HTTPException and other framework concerns must NOT appear here.
"""
from __future__ import annotations

import datetime
import uuid

from domain.game.completed_game import CompletedGame
from domain.game.game import GameState, GameStatus, Player
from domain.game.ports.i_game_archive import IGameArchive
from domain.game.ports.i_game_repository import IGameRepository

_WIN_LINES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
)


def _detect_winner(board: list[str]) -> str | None:
    for a, b, c in _WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


class GameService:
    def __init__(
        self,
        repository: IGameRepository,
        archive: IGameArchive | None = None,
    ) -> None:
        self._repository = repository
        self._archive    = archive
        # Tracks the sequence of move positions per game_id for archive records.
        self._move_log: dict[str, list[int]] = {}

    def create_game(self) -> GameState:
        state = GameState(game_id=str(uuid.uuid4()))
        self._repository.save(state)
        self._move_log[state.game_id] = []
        return state

    def make_move(self, game_id: str, position: int) -> GameState:
        state = self._repository.get(game_id)
        if state is None:
            raise ValueError(f"Game not found: {game_id!r}")
        if state.status != GameStatus.IN_PROGRESS:
            raise ValueError("Game is already over")
        if not (0 <= position <= 8):
            raise ValueError(f"Position {position} is out of range (0–8)")
        if state.board[position] != "":
            raise ValueError(f"Position {position} is already occupied")

        board = list(state.board)
        board[position] = state.current_player

        winner = _detect_winner(board)
        if winner:
            new_status = GameStatus.X_WINS if winner == Player.X else GameStatus.O_WINS
            new_player = state.current_player  # stays as the player who just won
        elif all(cell != "" for cell in board):
            new_status = GameStatus.DRAW
            new_player = state.current_player
            winner = None
        else:
            new_status = GameStatus.IN_PROGRESS
            new_player = Player.O if state.current_player == Player.X else Player.X
            winner = None

        updated = GameState(
            game_id=state.game_id,
            board=board,
            current_player=new_player,
            status=new_status,
            winner=winner,
        )
        self._repository.save(updated)

        # Accumulate move in the log (initialises lazily if game pre-existed).
        moves = self._move_log.setdefault(game_id, [])
        moves.append(position)

        # Archive on terminal state.
        if updated.status != GameStatus.IN_PROGRESS and self._archive is not None:
            self._archive.save(
                CompletedGame(
                    game_id      = updated.game_id,
                    board        = list(updated.board),
                    moves        = list(moves),
                    winner       = updated.winner,
                    status       = updated.status,
                    completed_at = datetime.datetime.now(
                        datetime.timezone.utc
                    ).isoformat(),
                )
            )

        return updated

    def get_game(self, game_id: str) -> GameState:
        state = self._repository.get(game_id)
        if state is None:
            raise ValueError(f"Game not found: {game_id!r}")
        return state

    def list_completed_games(self) -> list[CompletedGame]:
        """Return all archived completed games (empty list if no archive wired)."""
        if self._archive is None:
            return []
        return self._archive.list_all()
