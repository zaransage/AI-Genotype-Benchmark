"""
main.py — Composition root.

The only module that instantiates concrete types and wires them together.
HTTPException lives here (route level), not in domain or adaptors (ADR 0006, AI_CONTRACT §9).
logging.basicConfig() is called here — the application boundary only (ADR 0006).
"""

import logging
import os

from fastapi import FastAPI, HTTPException

from domain.game.core.adaptors.api_schemas      import GameStateResponse, MoveRequest
from domain.game.core.adaptors.rest_controller  import RestGameController
from domain.game.core.adaptors.web_ui_adaptor   import WebUIAdaptor
from domain.game.core.game_service              import GameService
from domain.game.core.ports.in_memory_repository import InMemoryGameRepository
from domain.game.core.ports.sqlite_game_archive  import SqliteGameArchive

# Application boundary: configure logging once, here only.
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Tic-Tac-Toe API", version="0.0.1")

# Composition: inject concrete implementations — never instantiated inside domain classes.
_db_path    = os.environ.get("TTT_DB_PATH", "games.db")
_html_path  = os.path.join(os.path.dirname(__file__), "static", "index.html")

_repository = InMemoryGameRepository()
_service    = GameService()
_archive    = SqliteGameArchive(db_path=_db_path)
_controller = RestGameController(service=_service, repository=_repository, archive=_archive)

# Web UI inbound adaptor — serves the browser game at GET /
_web_ui = WebUIAdaptor(html_path=_html_path)
app.include_router(_web_ui.create_router())


# ---------------------------------------------------------------------------
# Routes — framework exceptions (HTTPException) belong here only.
# ---------------------------------------------------------------------------

@app.post("/games", response_model=GameStateResponse, status_code=201)
def create_game() -> GameStateResponse:
    """Create a new two-player tic-tac-toe game. Player X moves first."""
    state = _controller.create_game()
    log.info("Game created: %s", state.game_id)
    return GameStateResponse.from_canonical(state)


@app.get("/games/{game_id}", response_model=GameStateResponse)
def get_game(game_id: str) -> GameStateResponse:
    """Retrieve the current state of a game."""
    try:
        state = _controller.get_game(game_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return GameStateResponse.from_canonical(state)


@app.post("/games/{game_id}/moves", response_model=GameStateResponse)
def make_move(game_id: str, body: MoveRequest) -> GameStateResponse:
    """Make a move. Provide player ('X' or 'O'), row (0–2), col (0–2)."""
    move = body.to_canonical()
    try:
        state = _controller.make_move(game_id, move)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    log.info("Move applied: game=%s player=%s row=%d col=%d status=%s",
             game_id, move.player, move.row, move.col, state.status)
    return GameStateResponse.from_canonical(state)
