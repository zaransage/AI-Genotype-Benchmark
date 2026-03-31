"""
Inbound HTTP adaptor: FastAPI router for the tic-tac-toe API.

HTTPException belongs here — not in domain or service classes.
Pydantic request/response models translate between JSON wire format
and the canonical domain models.
"""

from __future__ import annotations

from fastapi   import APIRouter, HTTPException
from pydantic  import BaseModel

from domain.core.adaptors.i_game_service import IGameService
from domain.core.models                  import CompletedGameRecord, GameState, Move

router: APIRouter = APIRouter()

_service: IGameService | None = None


def configure(service: IGameService) -> None:
    """Inject the concrete service implementation (called from main.py)."""
    global _service
    _service = service


# ---------------------------------------------------------------------------
# Wire-format models
# ---------------------------------------------------------------------------

class MoveRequest(BaseModel):
    player: str
    row:    int
    col:    int


class GameStateResponse(BaseModel):
    game_id:        str
    board:          list[list[str]]
    current_player: str
    status:         str
    winner:         str | None


class MoveDetail(BaseModel):
    player: str
    row:    int
    col:    int


class CompletedGameResponse(BaseModel):
    game_id: str
    outcome: str
    winner:  str | None
    board:   list[list[str]]
    moves:   list[MoveDetail]


# ---------------------------------------------------------------------------
# Translation: canonical → response
# ---------------------------------------------------------------------------

def _to_response(state: GameState) -> GameStateResponse:
    return GameStateResponse(
        game_id        = state.game_id,
        board          = state.board,
        current_player = state.current_player,
        status         = state.status,
        winner         = state.winner,
    )


def _to_completed_response(record: CompletedGameRecord) -> CompletedGameResponse:
    return CompletedGameResponse(
        game_id = record.game_id,
        outcome = record.outcome,
        winner  = record.winner,
        board   = record.board,
        moves   = [
            MoveDetail(player=m.player, row=m.row, col=m.col)
            for m in record.moves
        ],
    )


# ---------------------------------------------------------------------------
# Routes — literal paths before parameterised paths
# ---------------------------------------------------------------------------

@router.post("/games", response_model=GameStateResponse, status_code=201)
def create_game() -> GameStateResponse:
    state = _service.create_game()
    return _to_response(state)


@router.get("/games/completed", response_model=list[CompletedGameResponse])
def list_completed_games() -> list[CompletedGameResponse]:
    records = _service.list_completed_games()
    return [_to_completed_response(r) for r in records]


@router.get("/games/{game_id}", response_model=GameStateResponse)
def get_game(game_id: str) -> GameStateResponse:
    try:
        state = _service.get_game(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    return _to_response(state)


@router.post("/games/{game_id}/moves", response_model=GameStateResponse)
def make_move(game_id: str, body: MoveRequest) -> GameStateResponse:
    try:
        move  = Move(game_id=game_id, player=body.player, row=body.row, col=body.col)
        state = _service.make_move(move)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _to_response(state)


@router.get("/games/{game_id}/result", response_model=GameStateResponse)
def get_result(game_id: str) -> GameStateResponse:
    try:
        state = _service.get_game(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")
    return _to_response(state)
