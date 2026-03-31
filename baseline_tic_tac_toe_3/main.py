import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator

app = FastAPI(title="Tic-Tac-Toe API")

# In-memory store: game_id -> game dict
games: dict[str, dict] = {}

WINNING_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
    (0, 4, 8), (2, 4, 6),             # diagonals
]


def _check_winner(board: list) -> Optional[str]:
    for a, b, c in WINNING_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def _compute_status(board: list) -> str:
    winner = _check_winner(board)
    if winner:
        return f"{winner}_wins"
    if all(cell is not None for cell in board):
        return "draw"
    return "in_progress"


def _new_game() -> dict:
    return {
        "id": str(uuid4()),
        "board": [None] * 9,
        "current_player": "X",
        "status": "in_progress",
        "moves": [],
    }


# ── database ──────────────────────────────────────────────────────────────────

# Mutable so tests can replace it
_db_path: str = os.environ.get("DB_PATH", "games.db")
_db_conn: Optional[sqlite3.Connection] = None


def get_db() -> sqlite3.Connection:
    global _db_conn, _db_path
    if _db_conn is None:
        _db_conn = sqlite3.connect(_db_path, check_same_thread=False)
        _db_conn.row_factory = sqlite3.Row
        _db_conn.execute("""
            CREATE TABLE IF NOT EXISTS completed_games (
                id TEXT PRIMARY KEY,
                outcome TEXT NOT NULL,
                moves TEXT NOT NULL,
                board TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        _db_conn.commit()
    return _db_conn


def _reset_db(path: str = ":memory:") -> None:
    """Drop and re-open the DB connection. Used by tests."""
    global _db_conn, _db_path
    if _db_conn is not None:
        _db_conn.close()
        _db_conn = None
    _db_path = path


def _persist_completed_game(game: dict) -> None:
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO completed_games (id, outcome, moves, board, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            game["id"],
            game["status"],
            json.dumps(game["moves"]),
            json.dumps(game["board"]),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()


# ── schemas ──────────────────────────────────────────────────────────────────

class GameOut(BaseModel):
    id: str
    board: list[Optional[str]]
    current_player: str
    status: str


class MoveIn(BaseModel):
    position: int  # 0-8, row-major order

    @field_validator("position")
    @classmethod
    def position_in_range(cls, v: int) -> int:
        if not (0 <= v <= 8):
            raise ValueError("position must be 0-8")
        return v


class CompletedGameSummary(BaseModel):
    id: str
    outcome: str
    created_at: str


class CompletedGameDetail(BaseModel):
    id: str
    outcome: str
    board: list[Optional[str]]
    moves: list[int]
    created_at: str


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTMLResponse(content=_HTML, status_code=200)


@app.post("/games", response_model=GameOut, status_code=201)
def create_game():
    game = _new_game()
    games[game["id"]] = game
    return game


@app.get("/games/{game_id}", response_model=GameOut)
def get_game(game_id: str):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@app.post("/games/{game_id}/moves", response_model=GameOut)
def make_move(game_id: str, move: MoveIn):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game["status"] != "in_progress":
        raise HTTPException(status_code=409, detail="Game is already over")
    if game["board"][move.position] is not None:
        raise HTTPException(status_code=409, detail="Cell is already occupied")

    game["board"][move.position] = game["current_player"]
    game["moves"].append(move.position)
    game["status"] = _compute_status(game["board"])
    if game["status"] == "in_progress":
        game["current_player"] = "O" if game["current_player"] == "X" else "X"
    else:
        _persist_completed_game(game)
    return game


@app.get("/completed-games", response_model=list[CompletedGameSummary])
def list_completed_games():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, outcome, created_at FROM completed_games ORDER BY created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


@app.get("/completed-games/{game_id}", response_model=CompletedGameDetail)
def get_completed_game(game_id: str):
    conn = get_db()
    row = conn.execute(
        "SELECT id, outcome, board, moves, created_at FROM completed_games WHERE id = ?",
        (game_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Completed game not found")
    return {
        "id": row["id"],
        "outcome": row["outcome"],
        "board": json.loads(row["board"]),
        "moves": json.loads(row["moves"]),
        "created_at": row["created_at"],
    }


# ── web UI ────────────────────────────────────────────────────────────────────

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tic-Tac-Toe</title>
  <style>
    body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; padding: 2rem; background: #f0f2f5; }
    h1 { margin-bottom: 0.5rem; }
    #status { font-size: 1.2rem; margin: 0.75rem 0; min-height: 1.5rem; }
    #board { display: grid; grid-template-columns: repeat(3, 90px); gap: 6px; margin: 1rem 0; }
    .cell {
      width: 90px; height: 90px; font-size: 2.5rem; font-weight: bold;
      display: flex; align-items: center; justify-content: center;
      background: #fff; border: 2px solid #ccc; border-radius: 8px;
      cursor: pointer; transition: background 0.15s;
    }
    .cell:hover:not(.taken) { background: #e8f4ff; }
    .cell.taken { cursor: default; }
    .cell.X { color: #e63946; }
    .cell.O { color: #457b9d; }
    button { margin: 0.4rem; padding: 0.5rem 1.4rem; font-size: 1rem; border: none; border-radius: 6px; cursor: pointer; }
    #newBtn { background: #457b9d; color: #fff; }
    #newBtn:hover { background: #1d3557; }
    h2 { margin-top: 2rem; }
    #history { width: 100%; max-width: 500px; }
    .hrow { display: flex; justify-content: space-between; padding: 0.4rem 0.6rem; background: #fff; border-radius: 6px; margin: 0.25rem 0; font-size: 0.9rem; }
    .hrow:nth-child(even) { background: #eaf0f6; }
    .hid { color: #888; font-size: 0.75rem; }
    #loadMoreBtn { background: #a8dadc; border: none; }
  </style>
</head>
<body>
  <h1>Tic-Tac-Toe</h1>
  <div id="status">Press "New Game" to start.</div>
  <div id="board"></div>
  <div>
    <button id="newBtn">New Game</button>
  </div>

  <h2>Completed Games</h2>
  <div id="history"></div>
  <button id="loadMoreBtn">Refresh History</button>

  <script>
    let gameId = null;
    let board = Array(9).fill(null);
    let currentPlayer = 'X';
    let gameOver = false;

    const statusEl = document.getElementById('status');
    const boardEl = document.getElementById('board');
    const historyEl = document.getElementById('history');

    function renderBoard() {
      boardEl.innerHTML = '';
      board.forEach((val, idx) => {
        const cell = document.createElement('div');
        cell.className = 'cell' + (val ? ' taken ' + val : '');
        cell.textContent = val || '';
        if (!val && !gameOver) cell.addEventListener('click', () => makeMove(idx));
        boardEl.appendChild(cell);
      });
    }

    async function newGame() {
      const res = await fetch('/games', { method: 'POST' });
      const data = await res.json();
      gameId = data.id;
      board = data.board;
      currentPlayer = data.current_player;
      gameOver = false;
      statusEl.textContent = "Player X's turn";
      renderBoard();
    }

    async function makeMove(position) {
      if (!gameId || gameOver) return;
      const res = await fetch('/games/' + gameId + '/moves', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position })
      });
      if (!res.ok) return;
      const data = await res.json();
      board = data.board;
      currentPlayer = data.current_player;
      if (data.status === 'in_progress') {
        statusEl.textContent = "Player " + currentPlayer + "'s turn";
      } else {
        gameOver = true;
        if (data.status === 'draw') {
          statusEl.textContent = "It's a draw!";
        } else {
          const winner = data.status.replace('_wins', '');
          statusEl.textContent = 'Player ' + winner + ' wins!';
        }
        loadHistory();
      }
      renderBoard();
    }

    async function loadHistory() {
      const res = await fetch('/completed-games');
      const games = await res.json();
      historyEl.innerHTML = '';
      if (games.length === 0) {
        historyEl.innerHTML = '<p>No completed games yet.</p>';
        return;
      }
      games.forEach(g => {
        const row = document.createElement('div');
        row.className = 'hrow';
        const outcome = g.outcome.replace('_wins', ' wins').replace('draw', 'Draw');
        row.innerHTML = '<span>' + outcome + '</span><span class="hid">' + g.id.slice(0, 8) + '&hellip;</span><span>' + new Date(g.created_at).toLocaleString() + '</span>';
        historyEl.appendChild(row);
      });
    }

    document.getElementById('newBtn').addEventListener('click', newGame);
    document.getElementById('loadMoreBtn').addEventListener('click', loadHistory);

    renderBoard();
    loadHistory();
  </script>
</body>
</html>
"""
