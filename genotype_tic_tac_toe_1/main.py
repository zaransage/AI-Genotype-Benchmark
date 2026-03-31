"""
Composition root.

This is the only module that knows about concrete types.
All wiring of interfaces to implementations happens here.
"""

import logging

import uvicorn
from fastapi import FastAPI

from domain.core.adaptors              import routes
from domain.core.adaptors              import ui_routes
from domain.core.adaptors.game_service             import GameService
from domain.core.ports.in_memory_repository        import InMemoryGameRepository
from domain.core.ports.sqlite_game_archive         import SqliteGameArchive

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title       = "Tic-Tac-Toe API",
    description = "Two-player tic-tac-toe served as a REST API.",
    version     = "0.2.0",
)

# --- wire concrete implementations ---
_repository = InMemoryGameRepository()
_archive    = SqliteGameArchive("games.db")
_service    = GameService(_repository, _archive)
routes.configure(_service)

app.include_router(ui_routes.router)
app.include_router(routes.router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
