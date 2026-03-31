"""
Composition root — the ONLY place that knows about concrete types.

Wires:
  InMemoryGameRepository → GameService (with SQLiteGameArchive) → RestController → FastAPI app
                                                                → WebUIController → FastAPI app

logging.basicConfig() is called here (application boundary) and nowhere else.
"""
import logging

from fastapi import FastAPI

from domain.game.adaptors.rest_controller import RestController
from domain.game.adaptors.web_ui_controller import WebUIController
from domain.game.game_service import GameService
from domain.game.ports.in_memory_repository import InMemoryGameRepository
from domain.game.ports.sqlite_game_archive import SQLiteGameArchive

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

repository  = InMemoryGameRepository()
archive     = SQLiteGameArchive(db_path="games.db")
service     = GameService(repository=repository, archive=archive)
controller  = RestController(service=service)
ui          = WebUIController(service=service)

app = FastAPI(title="Tic-Tac-Toe API", version="0.2.0")
app.include_router(ui.router)
app.include_router(controller.router)
