from enum import Enum
from typing import Optional
import uuid


class Player(str, Enum):
    X = "X"
    O = "O"


class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    X_WINS = "X_wins"
    O_WINS = "O_wins"
    DRAW = "draw"


class Game:
    def __init__(self):
        self.id: str = str(uuid.uuid4())
        self.board: list[Optional[str]] = [None] * 9
        self.current_player: Player = Player.X
        self.status: GameStatus = GameStatus.IN_PROGRESS

    WIN_LINES = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
        (0, 4, 8), (2, 4, 6),              # diagonals
    ]

    def make_move(self, position: int, player: Player) -> None:
        if self.status != GameStatus.IN_PROGRESS:
            raise ValueError("Game is already over")
        if player != self.current_player:
            raise ValueError(f"It is {self.current_player.value}'s turn")
        if position < 0 or position > 8:
            raise ValueError("Position must be between 0 and 8")
        if self.board[position] is not None:
            raise ValueError("Position is already taken")

        self.board[position] = player.value
        self._update_status()
        if self.status == GameStatus.IN_PROGRESS:
            self.current_player = Player.O if player == Player.X else Player.X

    def _update_status(self) -> None:
        for a, b, c in self.WIN_LINES:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                self.status = GameStatus.X_WINS if self.board[a] == "X" else GameStatus.O_WINS
                return
        if all(cell is not None for cell in self.board):
            self.status = GameStatus.DRAW

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "board": self.board,
            "current_player": self.current_player.value if self.status == GameStatus.IN_PROGRESS else None,
            "status": self.status.value,
        }
