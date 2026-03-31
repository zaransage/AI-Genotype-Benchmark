import json
import sqlite3

DB_PATH = "games.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS completed_games (
                id          TEXT PRIMARY KEY,
                board       TEXT NOT NULL,
                status      TEXT NOT NULL,
                moves       TEXT NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_completed_game(
    game_id: str, board: list, status: str, moves: list
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO completed_games (id, board, status, moves) VALUES (?, ?, ?, ?)",
            (game_id, json.dumps(board), status, json.dumps(moves)),
        )
        conn.commit()


def get_completed_games() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, board, status, moves, created_at FROM completed_games ORDER BY created_at DESC"
        ).fetchall()
    return [
        {
            "id": row["id"],
            "board": json.loads(row["board"]),
            "status": row["status"],
            "moves": json.loads(row["moves"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
