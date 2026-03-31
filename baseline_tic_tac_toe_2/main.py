from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import db
from game import Game, GameError, games

db.init_db()  # ensure tables exist even without lifespan (e.g. bare TestClient)

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Tic-Tac-Toe</title>
  <style>
    body{font-family:Arial,sans-serif;text-align:center;padding:20px;background:#fafafa}
    h1{color:#222}
    #status{font-size:1.2em;margin:12px 0;color:#444;min-height:1.5em}
    #board{display:inline-grid;grid-template-columns:repeat(3,100px);gap:4px;margin:16px}
    .cell{width:100px;height:100px;font-size:2.4em;font-weight:bold;cursor:pointer;
          border:2px solid #444;background:#fff;display:flex;align-items:center;
          justify-content:center;transition:background .15s}
    .cell:hover:not(.taken){background:#e8f4ff}
    .cell.taken{cursor:default;color:#333}
    button{padding:9px 20px;font-size:1em;cursor:pointer;margin:4px;border:none;
           border-radius:4px}
    #new-btn{background:#4caf50;color:#fff}
    #new-btn:hover{background:#388e3c}
    #refresh-btn{background:#1976d2;color:#fff}
    #refresh-btn:hover{background:#1565c0}
    #completed{margin-top:32px}
    table{border-collapse:collapse;margin:0 auto}
    th,td{border:1px solid #ccc;padding:7px 14px;text-align:left}
    th{background:#f0f0f0}
    tr:nth-child(even){background:#fafafa}
  </style>
</head>
<body>
  <h1>Tic-Tac-Toe</h1>
  <button id="new-btn" onclick="newGame()">New Game</button>
  <div id="status">Click &ldquo;New Game&rdquo; to start!</div>
  <div id="board"></div>

  <div id="completed">
    <h2>Completed Games</h2>
    <button id="refresh-btn" onclick="loadCompleted()">Refresh</button>
    <div id="games-list" style="margin-top:12px"></div>
  </div>

  <script>
    let gameId = null, gameOver = false, currentPlayer = 'X';

    async function newGame() {
      const resp = await fetch('/games', {method:'POST'});
      const data = await resp.json();
      gameId = data.id; gameOver = false; currentPlayer = data.current_player;
      render(data);
      document.getElementById('status').textContent = "Player " + currentPlayer + "'s turn";
    }

    async function move(pos) {
      if (!gameId || gameOver) return;
      const resp = await fetch('/games/' + gameId + '/moves', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({player:currentPlayer, position:pos})
      });
      const data = await resp.json();
      if (!resp.ok) { document.getElementById('status').textContent = 'Error: ' + data.detail; return; }
      currentPlayer = data.current_player;
      render(data);
      if (data.status === 'won') {
        document.getElementById('status').textContent = 'Player ' + data.winner + ' wins!';
        gameOver = true; loadCompleted();
      } else if (data.status === 'draw') {
        document.getElementById('status').textContent = "It's a draw!";
        gameOver = true; loadCompleted();
      } else {
        document.getElementById('status').textContent = "Player " + currentPlayer + "'s turn";
      }
    }

    function render(data) {
      const el = document.getElementById('board');
      el.innerHTML = '';
      data.board.forEach((cell, i) => {
        const d = document.createElement('div');
        d.className = 'cell' + (cell ? ' taken' : '');
        d.textContent = cell || '';
        if (!cell && !gameOver) d.onclick = () => move(i);
        el.appendChild(d);
      });
    }

    async function loadCompleted() {
      const resp = await fetch('/completed-games');
      const games = await resp.json();
      const el = document.getElementById('games-list');
      if (!games.length) { el.innerHTML = '<p>No completed games yet.</p>'; return; }
      let html = '<table><tr><th>ID</th><th>Status</th><th>Winner</th><th>Moves</th><th>Completed At</th></tr>';
      for (const g of games)
        html += '<tr><td>' + g.id.slice(0,8) + '&hellip;</td><td>' + g.status +
                '</td><td>' + (g.winner || '&mdash;') + '</td><td>' + g.move_count +
                '</td><td>' + g.created_at + '</td></tr>';
      el.innerHTML = html + '</table>';
    }

    loadCompleted();
  </script>
</body>
</html>"""


@asynccontextmanager
async def lifespan(app):
    db.init_db()
    yield


app = FastAPI(title="Tic-Tac-Toe API", lifespan=lifespan)


class MoveRequest(BaseModel):
    player: str = Field(..., pattern="^[XO]$")
    position: int = Field(..., ge=0, le=8)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui():
    return HTMLResponse(content=_HTML)


@app.post("/games", status_code=201)
def create_game():
    game = Game()
    games[game.id] = game
    return game.to_dict()


@app.get("/games/{game_id}")
def get_game(game_id: str):
    game = games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found.")
    return game.to_dict()


@app.post("/games/{game_id}/moves")
def make_move(game_id: str, move: MoveRequest):
    game = games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found.")
    try:
        game.make_move(move.player, move.position)
    except GameError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if game.status in ("won", "draw"):
        db.save_completed_game(game.to_dict(), game.moves)
    return game.to_dict()


@app.get("/completed-games")
def list_completed_games():
    return db.list_completed_games()


@app.get("/completed-games/{game_id}")
def get_completed_game(game_id: str):
    game = db.get_completed_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Completed game not found.")
    return game
