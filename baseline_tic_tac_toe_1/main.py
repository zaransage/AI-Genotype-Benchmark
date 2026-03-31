import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import database
from game import Game, GameStatus, Player

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="Tic-Tac-Toe API", lifespan=lifespan)

games: dict[str, Game] = {}
game_moves: dict[str, list] = {}


class MoveRequest(BaseModel):
    player: str
    position: int


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    with open(os.path.join(_STATIC_DIR, "index.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/games", status_code=201)
def create_game():
    game = Game()
    games[game.id] = game
    game_moves[game.id] = []
    return game.to_dict()


@app.get("/games/history")
def get_history():
    return database.get_completed_games()


@app.get("/games/{game_id}")
def get_game(game_id: str):
    game = games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.to_dict()


@app.post("/games/{game_id}/moves")
def make_move(game_id: str, move: MoveRequest):
    game = games.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    try:
        player = Player(move.player)
    except ValueError:
        raise HTTPException(status_code=400, detail="Player must be 'X' or 'O'")

    try:
        game.make_move(move.position, player)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    game_moves[game_id].append({"player": move.player, "position": move.position})

    if game.status != GameStatus.IN_PROGRESS:
        database.save_completed_game(
            game_id, game.board, game.status.value, game_moves[game_id]
        )

    return game.to_dict()
