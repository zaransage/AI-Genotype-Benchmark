"""
domain/game/core/ports/sqlite_game_archive.py

Outbound port implementation: persists completed games in a local SQLite database.
Uses only the stdlib sqlite3 module — no extra dependencies.
Config (db_path) is injected by the composition root (main.py).

A single persistent connection is kept so that :memory: databases survive across
method calls.  check_same_thread=False is set because FastAPI may dispatch routes
on different threads; sqlite3's GIL-level serialisation keeps writes safe.
"""

import sqlite3
from datetime import datetime, timezone
from typing   import Optional

from domain.game.core.ports.i_game_archive import IGameArchive


_DDL = """
CREATE TABLE IF NOT EXISTS archived_games (
    game_id     TEXT    PRIMARY KEY,
    outcome     TEXT    NOT NULL,
    winner      TEXT,
    archived_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS archived_moves (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     TEXT    NOT NULL,
    player      TEXT    NOT NULL,
    row         INTEGER NOT NULL,
    col         INTEGER NOT NULL,
    FOREIGN KEY (game_id) REFERENCES archived_games (game_id)
);
"""


class SqliteGameArchive(IGameArchive):
    """Stores completed game records and per-move history in SQLite."""

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)

    # ------------------------------------------------------------------
    # IGameArchive
    # ------------------------------------------------------------------

    def record_move(
        self,
        game_id: str,
        player:  str,
        row:     int,
        col:     int,
    ) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO archived_moves (game_id, player, row, col)"
                " VALUES (?, ?, ?, ?)",
                (game_id, player, row, col),
            )

    def close_game(
        self,
        game_id: str,
        outcome: str,
        winner:  Optional[str],
    ) -> None:
        archived_at = datetime.now(timezone.utc).isoformat()
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO archived_games"
                " (game_id, outcome, winner, archived_at)"
                " VALUES (?, ?, ?, ?)",
                (game_id, outcome, winner, archived_at),
            )

    def find_completed_games(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT game_id, outcome, winner, archived_at"
            " FROM archived_games"
            " ORDER BY archived_at ASC"
        ).fetchall()
        return [dict(row) for row in rows]
