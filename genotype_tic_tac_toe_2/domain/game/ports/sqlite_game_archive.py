"""
SQLiteGameArchive — outbound port implementation that persists completed games
to a SQLite database using the stdlib sqlite3 module (no third-party driver).

Config: db_path is injected by the composition root (main.py).
Use ":memory:" for tests; a file path for production.

A single connection is kept open for the lifetime of the instance so that
in-memory databases (":memory:") are not silently recreated on each call.
"""
from __future__ import annotations

import json
import sqlite3

from domain.game.completed_game import CompletedGame
from domain.game.ports.i_game_archive import IGameArchive

_DDL = """
CREATE TABLE IF NOT EXISTS completed_games (
    game_id      TEXT PRIMARY KEY,
    board        TEXT    NOT NULL,
    moves        TEXT    NOT NULL,
    winner       TEXT,
    status       TEXT    NOT NULL,
    completed_at TEXT    NOT NULL
)
"""


class SQLiteGameArchive(IGameArchive):
    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_DDL)
        self._conn.commit()

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _row_to_game(row: sqlite3.Row) -> CompletedGame:
        return CompletedGame(
            game_id      = row["game_id"],
            board        = json.loads(row["board"]),
            moves        = json.loads(row["moves"]),
            winner       = row["winner"],
            status       = row["status"],
            completed_at = row["completed_at"],
        )

    # ------------------------------------------------------------------ #
    # IGameArchive implementation                                          #
    # ------------------------------------------------------------------ #

    def save(self, game: CompletedGame) -> None:
        self._conn.execute(
            """
            INSERT INTO completed_games
                (game_id, board, moves, winner, status, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                board        = excluded.board,
                moves        = excluded.moves,
                winner       = excluded.winner,
                status       = excluded.status,
                completed_at = excluded.completed_at
            """,
            (
                game.game_id,
                json.dumps(game.board),
                json.dumps(game.moves),
                game.winner,
                game.status,
                game.completed_at,
            ),
        )
        self._conn.commit()

    def get(self, game_id: str) -> CompletedGame | None:
        row = self._conn.execute(
            "SELECT * FROM completed_games WHERE game_id = ?", (game_id,)
        ).fetchone()
        return self._row_to_game(row) if row else None

    def list_all(self) -> list[CompletedGame]:
        rows = self._conn.execute(
            "SELECT * FROM completed_games ORDER BY completed_at ASC"
        ).fetchall()
        return [self._row_to_game(r) for r in rows]
