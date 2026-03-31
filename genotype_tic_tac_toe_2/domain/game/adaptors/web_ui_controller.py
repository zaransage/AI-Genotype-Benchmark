"""
WebUIController — HTML inbound adaptor for the game domain.

Serves a browser-playable game board at GET / and a completed-games history
page at GET /history.  All game logic is delegated to GameService via the
existing REST API (the JS uses fetch()).  Framework concerns (HTMLResponse)
are confined to this adaptor — they must not leak into GameService.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from domain.game.adaptors.i_web_ui_controller import IWebUIController
from domain.game.game_service import GameService

_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tic-Tac-Toe</title>
<style>
  body { font-family: sans-serif; max-width: 420px; margin: 40px auto; text-align: center; background: #fafafa; }
  h1   { margin-bottom: 4px; }
  #status { font-size: 1.2em; margin: 12px 0; min-height: 1.6em; color: #333; }
  #board  { display: grid; grid-template-columns: repeat(3, 110px); gap: 6px;
             justify-content: center; margin: 16px auto; }
  .cell   { width: 110px; height: 110px; font-size: 2.8em; font-weight: bold;
             cursor: pointer; border: 2px solid #555; border-radius: 6px;
             background: #fff; transition: background 0.15s; }
  .cell:not([disabled]):hover { background: #e8eaff; }
  .cell[disabled]             { cursor: default; color: #222; }
  #new-game  { padding: 10px 28px; font-size: 1em; cursor: pointer;
               border: none; border-radius: 6px; background: #4a90d9;
               color: #fff; margin-bottom: 8px; }
  #new-game:hover { background: #357abd; }
  .history-link { display: block; margin-top: 20px; color: #555; font-size: 0.9em; }
</style>
</head>
<body>
<h1>Tic-Tac-Toe</h1>
<button id="new-game" onclick="newGame()">New Game</button>
<div id="status">Press "New Game" to start.</div>
<div id="board"></div>
<a class="history-link" href="/history">View completed games &rarr;</a>

<script>
let gameId   = null;
let gameOver = true;

async function newGame() {
    const resp  = await fetch('/games', { method: 'POST' });
    const state = await resp.json();
    gameId   = state.game_id;
    gameOver = false;
    render(state);
}

async function makeMove(pos) {
    if (!gameId || gameOver) return;
    const resp = await fetch('/games/' + gameId + '/moves', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ position: pos })
    });
    if (!resp.ok) {
        const err = await resp.json();
        document.getElementById('status').textContent = err.detail || 'Invalid move.';
        return;
    }
    render(await resp.json());
}

function render(state) {
    const board = document.getElementById('board');
    board.innerHTML = '';
    state.board.forEach(function(cell, i) {
        const btn       = document.createElement('button');
        btn.className   = 'cell';
        btn.textContent = cell;
        if (cell !== '' || state.status !== 'in_progress') {
            btn.disabled = true;
        } else {
            btn.onclick = function() { makeMove(i); };
        }
        board.appendChild(btn);
    });

    const st = document.getElementById('status');
    if (state.status === 'in_progress') {
        st.textContent = "Player " + state.current_player + "'s turn";
        gameOver = false;
    } else if (state.status === 'draw') {
        st.textContent = "It's a draw!";
        gameOver = true;
    } else {
        st.textContent = "Player " + state.winner + " wins!";
        gameOver = true;
    }
}
</script>
</body>
</html>
"""

_HISTORY_HTML_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Completed Games</title>
<style>
  body  { font-family: sans-serif; max-width: 720px; margin: 40px auto; background: #fafafa; }
  h1    { text-align: center; }
  a.back { display: block; text-align: center; margin-bottom: 20px; color: #555; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 8px 12px; border: 1px solid #ddd; text-align: left; font-size: 0.9em; }
  th    { background: #f0f0f0; }
  tr:nth-child(even) { background: #f9f9f9; }
  .empty { text-align: center; color: #999; padding: 24px; }
</style>
</head>
<body>
<h1>Completed Games</h1>
<a class="back" href="/">&larr; Back to game</a>
"""

_HISTORY_HTML_FOOTER = """
</body>
</html>
"""


class WebUIController(IWebUIController):
    def __init__(self, service: GameService) -> None:
        self._service = service
        self.router   = APIRouter()
        self.router.add_api_route("/",        self.index,   methods=["GET"])
        self.router.add_api_route("/history", self.history, methods=["GET"])

    def index(self):
        return HTMLResponse(content=_INDEX_HTML)

    def history(self):
        games = self._service.list_completed_games()
        if games:
            rows = "".join(
                "<tr>"
                f"<td>{g.game_id[:8]}&hellip;</td>"
                f"<td>{g.status}</td>"
                f"<td>{g.winner if g.winner else '&mdash;'}</td>"
                f"<td>{len(g.moves)}</td>"
                f"<td>{g.completed_at[:19].replace('T', ' ')}</td>"
                "</tr>"
                for g in games
            )
            table = (
                "<table>"
                "<thead><tr>"
                "<th>Game ID</th><th>Outcome</th><th>Winner</th>"
                "<th>Moves</th><th>Completed At</th>"
                "</tr></thead>"
                f"<tbody>{rows}</tbody>"
                "</table>"
            )
        else:
            table = '<p class="empty">No completed games yet. Play one!</p>'

        content = _HISTORY_HTML_HEADER + table + _HISTORY_HTML_FOOTER
        return HTMLResponse(content=content)
