"""
RestController — FastAPI inbound adaptor for the game domain.

HTTPException is the ONLY framework concern allowed here; it must not leak
into GameService or GameState. All domain errors (ValueError) are caught here
and translated to appropriate HTTP status codes.
"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from domain.game.adaptors.i_game_controller import IGameController
from domain.game.game import GameState
from domain.game.game_service import GameService


class MoveRequest(BaseModel):
    position: int = Field(..., ge=0, le=8, description="Zero-based board index (0–8)")


def _serialize(state: GameState) -> dict:
    return asdict(state)


class RestController(IGameController):
    def __init__(self, service: GameService) -> None:
        self._service = service
        self.router   = APIRouter()
        self.router.add_api_route("/games",                self.create_game, methods=["POST"])
        self.router.add_api_route("/games/{game_id}",      self.get_game,    methods=["GET"])
        self.router.add_api_route("/games/{game_id}/moves", self.make_move,   methods=["POST"])

    def create_game(self):
        state = self._service.create_game()
        return JSONResponse(status_code=201, content=_serialize(state))

    def get_game(self, game_id: str):
        try:
            state = self._service.get_game(game_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return _serialize(state)

    def make_move(self, game_id: str, body: MoveRequest):
        try:
            state = self._service.make_move(game_id, body.position)
        except ValueError as exc:
            msg = str(exc)
            if "not found" in msg:
                raise HTTPException(status_code=404, detail=msg)
            raise HTTPException(status_code=400, detail=msg)
        return _serialize(state)
