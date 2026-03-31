"""
Adaptor tests: ui_routes (web UI inbound adaptor)

Tests cover:
  - GET / returns HTTP 200
  - Response content-type is text/html
  - HTML contains expected UI landmarks
  - GET /api/v1/games/completed returns 200 with a JSON list
  - Completed games appear in the list after a game is fully played
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from fastapi           import FastAPI
from fastapi.testclient import TestClient

from domain.core.adaptors              import routes, ui_routes
from domain.core.adaptors.i_game_service import IGameService
from domain.core.models                  import (
    CompletedGameRecord,
    GameState,
    Move,
    PLAYER_X,
    STATUS_ACTIVE,
    STATUS_X_WINS,
)


def _make_app(mock_service: IGameService) -> FastAPI:
    app = FastAPI()
    routes.configure(mock_service)
    app.include_router(ui_routes.router)
    app.include_router(routes.router, prefix="/api/v1")
    return app


class TestUiIndexRoute(unittest.TestCase):

    def setUp(self) -> None:
        mock_service = MagicMock(spec=IGameService)
        self.client  = TestClient(_make_app(mock_service))

    def test_get_index_returns_200(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_get_index_content_type_is_html(self) -> None:
        resp = self.client.get("/")
        self.assertIn("text/html", resp.headers["content-type"])

    def test_html_contains_title(self) -> None:
        resp = self.client.get("/")
        self.assertIn("Tic-Tac-Toe", resp.text)

    def test_html_contains_new_game_button(self) -> None:
        resp = self.client.get("/")
        self.assertIn("New Game", resp.text)

    def test_html_contains_board_element(self) -> None:
        resp = self.client.get("/")
        self.assertIn('id="board"', resp.text)

    def test_html_contains_status_element(self) -> None:
        resp = self.client.get("/")
        self.assertIn('id="status"', resp.text)

    def test_html_contains_history_section(self) -> None:
        resp = self.client.get("/")
        self.assertIn('id="history"', resp.text)

    def test_html_references_api_endpoint(self) -> None:
        resp = self.client.get("/")
        self.assertIn("/api/v1", resp.text)


class TestCompletedGamesEndpoint(unittest.TestCase):

    def _active_state(self, game_id: str = "g1") -> GameState:
        return GameState(
            game_id        = game_id,
            board          = [["", "", ""], ["", "", ""], ["", "", ""]],
            current_player = PLAYER_X,
            status         = STATUS_ACTIVE,
            winner         = None,
        )

    def test_list_completed_returns_200_with_empty_list(self) -> None:
        mock_service = MagicMock(spec=IGameService)
        mock_service.list_completed_games.return_value = []
        client = TestClient(_make_app(mock_service))

        resp = client.get("/api/v1/games/completed")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_list_completed_returns_archived_records(self) -> None:
        record = CompletedGameRecord(
            game_id = "finished-game",
            outcome = "x_wins",
            winner  = "X",
            board   = [["X","X","X"],["O","O",""],["","",""]],
            moves   = [
                Move("finished-game","X",0,0),
                Move("finished-game","O",1,0),
                Move("finished-game","X",0,1),
                Move("finished-game","O",1,1),
                Move("finished-game","X",0,2),
            ],
        )
        mock_service = MagicMock(spec=IGameService)
        mock_service.list_completed_games.return_value = [record]
        client = TestClient(_make_app(mock_service))

        resp = client.get("/api/v1/games/completed")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["game_id"], "finished-game")
        self.assertEqual(data[0]["outcome"], "x_wins")
        self.assertEqual(data[0]["winner"],  "X")
        self.assertEqual(len(data[0]["moves"]), 5)

    def test_completed_response_move_shape(self) -> None:
        record = CompletedGameRecord(
            game_id = "game-x",
            outcome = "draw",
            winner  = None,
            board   = [["X","O","X"],["X","X","O"],["O","X","O"]],
            moves   = [Move("game-x","X",0,0)],
        )
        mock_service = MagicMock(spec=IGameService)
        mock_service.list_completed_games.return_value = [record]
        client = TestClient(_make_app(mock_service))

        data = client.get("/api/v1/games/completed").json()
        move = data[0]["moves"][0]
        self.assertIn("player", move)
        self.assertIn("row",    move)
        self.assertIn("col",    move)
        # game_id is not leaked into the move wire shape
        self.assertNotIn("game_id", move)

    def test_completed_endpoint_does_not_shadow_game_id_route(self) -> None:
        """GET /api/v1/games/completed must not be swallowed by /games/{game_id}."""
        mock_service = MagicMock(spec=IGameService)
        mock_service.list_completed_games.return_value = []
        client = TestClient(_make_app(mock_service))

        resp = client.get("/api/v1/games/completed")
        self.assertEqual(resp.status_code, 200)
        # If it hit the {game_id} route it would call get_game("completed"), not list_completed_games
        mock_service.list_completed_games.assert_called_once()
        mock_service.get_game.assert_not_called()
