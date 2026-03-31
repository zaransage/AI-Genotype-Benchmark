import json
import sqlite3

DB_PATH = "tictactoe.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS completed_games (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                winner TEXT,
                board TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS game_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                move_number INTEGER NOT NULL,
                player TEXT NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY (game_id) REFERENCES completed_games(id)
            )
        """)
        conn.commit()


def save_completed_game(game_dict: dict, moves: list) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO completed_games (id, status, winner, board) VALUES (?, ?, ?, ?)",
            (game_dict["id"], game_dict["status"], game_dict["winner"],
             json.dumps(game_dict["board"])),
        )
        for i, move in enumerate(moves):
            conn.execute(
                "INSERT OR IGNORE INTO game_moves (game_id, move_number, player, position)"
                " VALUES (?, ?, ?, ?)",
                (game_dict["id"], i + 1, move["player"], move["position"]),
            )
        conn.commit()


def list_completed_games() -> list:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT cg.id, cg.status, cg.winner, cg.board, cg.created_at,"
            " COUNT(gm.id) AS move_count"
            " FROM completed_games cg"
            " LEFT JOIN game_moves gm ON gm.game_id = cg.id"
            " GROUP BY cg.id"
            " ORDER BY cg.created_at DESC"
        ).fetchall()
        return [
            {**dict(r), "board": json.loads(r["board"])}
            for r in rows
        ]


def get_completed_game(game_id: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, status, winner, board, created_at"
            " FROM completed_games WHERE id = ?",
            (game_id,),
        ).fetchone()
        if row is None:
            return None
        game = {**dict(row), "board": json.loads(row["board"])}
        moves = conn.execute(
            "SELECT move_number, player, position FROM game_moves"
            " WHERE game_id = ? ORDER BY move_number",
            (game_id,),
        ).fetchall()
        game["moves"] = [dict(m) for m in moves]
        return game
