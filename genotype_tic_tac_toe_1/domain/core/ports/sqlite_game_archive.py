"""
Outbound port implementation: SQLite-backed game archive.

Stores completed games and their full move histories.
Swap for another IGameArchive implementation by changing the binding in main.py.
"""

from __future__ import annotations

import json
import sqlite3

from domain.core.models              import CompletedGameRecord, Move
from domain.core.ports.i_game_archive import IGameArchive


class SqliteGameArchive(IGameArchive):
    """Persists completed games in a local SQLite database."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._init_schema()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS completed_games (
                    game_id  TEXT PRIMARY KEY,
                    outcome  TEXT NOT NULL,
                    winner   TEXT,
                    board    TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS game_moves (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id  TEXT    NOT NULL,
                    seq      INTEGER NOT NULL,
                    player   TEXT    NOT NULL,
                    row      INTEGER NOT NULL,
                    col      INTEGER NOT NULL,
                    FOREIGN KEY (game_id) REFERENCES completed_games(game_id)
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def _load_record(
        self,
        conn: sqlite3.Connection,
        row:  sqlite3.Row,
    ) -> CompletedGameRecord:
        move_rows = conn.execute(
            "SELECT player, row, col FROM game_moves WHERE game_id = ? ORDER BY seq",
            (row["game_id"],),
        ).fetchall()
        moves = [
            Move(game_id=row["game_id"], player=m["player"], row=m["row"], col=m["col"])
            for m in move_rows
        ]
        return CompletedGameRecord(
            game_id = row["game_id"],
            outcome = row["outcome"],
            winner  = row["winner"],
            board   = json.loads(row["board"]),
            moves   = moves,
        )

    # ------------------------------------------------------------------
    # IGameArchive implementation
    # ------------------------------------------------------------------

    def archive(self, record: CompletedGameRecord) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO completed_games (game_id, outcome, winner, board)"
                " VALUES (?, ?, ?, ?)",
                (record.game_id, record.outcome, record.winner, json.dumps(record.board)),
            )
            conn.execute("DELETE FROM game_moves WHERE game_id = ?", (record.game_id,))
            for seq, move in enumerate(record.moves):
                conn.execute(
                    "INSERT INTO game_moves (game_id, seq, player, row, col)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (record.game_id, seq, move.player, move.row, move.col),
                )
            conn.commit()
        finally:
            conn.close()

    def list_completed(self) -> list[CompletedGameRecord]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT game_id, outcome, winner, board"
                " FROM completed_games ORDER BY rowid"
            ).fetchall()
            return [self._load_record(conn, row) for row in rows]
        finally:
            conn.close()

    def get_record(self, game_id: str) -> CompletedGameRecord:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT game_id, outcome, winner, board"
                " FROM completed_games WHERE game_id = ?",
                (game_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Completed game not found: {game_id!r}")
            return self._load_record(conn, row)
        finally:
            conn.close()
