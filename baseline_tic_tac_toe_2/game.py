import uuid
from typing import Optional

WINNING_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
    (0, 4, 8), (2, 4, 6),             # diagonals
]


class GameError(Exception):
    pass


class Game:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.board: list[Optional[str]] = [None] * 9
        self.current_player = "X"
        self.status = "in_progress"  # in_progress | won | draw
        self.winner: Optional[str] = None
        self.moves: list[dict] = []

    def make_move(self, player: str, position: int) -> None:
        if self.status != "in_progress":
            raise GameError("Game is already over.")
        if player != self.current_player:
            raise GameError(f"It is {self.current_player}'s turn.")
        if position < 0 or position > 8:
            raise GameError("Position must be between 0 and 8.")
        if self.board[position] is not None:
            raise GameError("That position is already taken.")

        self.board[position] = player
        self.moves.append({"player": player, "position": position})

        if self._check_winner(player):
            self.status = "won"
            self.winner = player
        elif None not in self.board:
            self.status = "draw"
        else:
            self.current_player = "O" if player == "X" else "X"

    def _check_winner(self, player: str) -> bool:
        for a, b, c in WINNING_LINES:
            if self.board[a] == self.board[b] == self.board[c] == player:
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "board": self.board,
            "current_player": self.current_player,
            "status": self.status,
            "winner": self.winner,
            "moves": self.moves,
        }


# In-memory store
games: dict[str, Game] = {}
