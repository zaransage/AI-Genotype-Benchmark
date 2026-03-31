"""
Tests for the inbound adaptor: REST controller responses and fixture round-trips.

Per AI_CONTRACT.md §6: a translation test asserts:
  1. The raw fixture contains the expected source fields.
  2. The canonical dataclass instance has the correct field values after adaptor conversion.
"""
import json
import pathlib
import unittest

FIXTURE_RAW      = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "raw"      / "game" / "v1"
FIXTURE_EXPECTED = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "expected" / "game" / "v1"


class TestRestControllerFixtureRoundTrip(unittest.TestCase):
    """
    Verify raw request fixtures → canonical GameState → expected response shape.
    Uses a TestClient wrapping the FastAPI app (no live server required).
    """

    def _make_client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    # ------------------------------------------------------------------ #
    # Raw fixture integrity (assertion 1 of the translation contract)      #
    # ------------------------------------------------------------------ #

    def test_raw_make_move_fixture_has_position_field(self) -> None:
        raw = json.loads((FIXTURE_RAW / "make_move_request.0.0.1.json").read_text())
        self.assertIn("position", raw)
        self.assertIsInstance(raw["position"], int)

    def test_raw_get_state_fixture_has_game_id_field(self) -> None:
        raw = json.loads((FIXTURE_RAW / "get_state_request.0.0.1.json").read_text())
        self.assertIn("game_id", raw)

    def test_raw_create_game_fixture_is_empty_body(self) -> None:
        raw = json.loads((FIXTURE_RAW / "create_game_request.0.0.1.json").read_text())
        self.assertIsInstance(raw, dict)

    # ------------------------------------------------------------------ #
    # Expected fixture integrity                                           #
    # ------------------------------------------------------------------ #

    def test_expected_initial_fixture_fields(self) -> None:
        exp = json.loads((FIXTURE_EXPECTED / "game_state_initial.0.0.1.json").read_text())
        self.assertEqual(exp["status"], "in_progress")
        self.assertIsNone(exp["winner"])
        self.assertEqual(exp["current_player"], "X")
        self.assertEqual(len(exp["board"]), 9)

    def test_expected_win_fixture_fields(self) -> None:
        exp = json.loads((FIXTURE_EXPECTED / "game_state_win.0.0.1.json").read_text())
        self.assertEqual(exp["status"], "x_wins")
        self.assertEqual(exp["winner"], "X")

    def test_expected_draw_fixture_fields(self) -> None:
        exp = json.loads((FIXTURE_EXPECTED / "game_state_draw.0.0.1.json").read_text())
        self.assertEqual(exp["status"], "draw")
        self.assertIsNone(exp["winner"])
        self.assertTrue(all(c != "" for c in exp["board"]))

    # ------------------------------------------------------------------ #
    # Canonical model → REST response (assertion 2 of translation contract)
    # ------------------------------------------------------------------ #

    def test_create_game_response_matches_initial_fixture_shape(self) -> None:
        """POST /games returns a body whose shape matches game_state_initial.0.0.1.json."""
        client = self._make_client()
        exp = json.loads((FIXTURE_EXPECTED / "game_state_initial.0.0.1.json").read_text())

        response = client.post("/games")
        self.assertEqual(response.status_code, 201)
        body = response.json()

        # Shape check — every key from the fixture must appear in the response
        for key in exp:
            self.assertIn(key, body, msg=f"Missing field: {key!r}")

        # Value checks (game_id will differ; check everything else)
        self.assertEqual(body["board"], exp["board"])
        self.assertEqual(body["current_player"], exp["current_player"])
        self.assertEqual(body["status"], exp["status"])
        self.assertIsNone(body["winner"])

    def test_make_move_updates_board(self) -> None:
        """POST /games/{id}/moves with fixture payload updates the correct cell."""
        client = self._make_client()
        move_payload = json.loads((FIXTURE_RAW / "make_move_request.0.0.1.json").read_text())

        create_resp = client.post("/games")
        game_id = create_resp.json()["game_id"]

        resp = client.post(f"/games/{game_id}/moves", json=move_payload)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["board"][move_payload["position"]], "X")

    def test_get_game_returns_current_state(self) -> None:
        """GET /games/{id} returns the persisted game state."""
        client = self._make_client()
        game_id = client.post("/games").json()["game_id"]
        client.post(f"/games/{game_id}/moves", json={"position": 0})

        resp = client.get(f"/games/{game_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["board"][0], "X")

    def test_move_to_invalid_position_returns_422_or_400(self) -> None:
        """A move with position outside 0–8 is rejected at the route boundary."""
        client = self._make_client()
        game_id = client.post("/games").json()["game_id"]
        resp = client.post(f"/games/{game_id}/moves", json={"position": 9})
        self.assertIn(resp.status_code, (400, 422))

    def test_get_nonexistent_game_returns_404(self) -> None:
        """GET /games/{id} returns 404 when the game does not exist."""
        client = self._make_client()
        resp = client.get("/games/no-such-game")
        self.assertEqual(resp.status_code, 404)

    def test_move_on_occupied_cell_returns_400(self) -> None:
        """POSTing a move to an occupied cell returns HTTP 400."""
        client = self._make_client()
        game_id = client.post("/games").json()["game_id"]
        client.post(f"/games/{game_id}/moves", json={"position": 0})
        resp = client.post(f"/games/{game_id}/moves", json={"position": 0})
        self.assertEqual(resp.status_code, 400)

    def test_win_is_reflected_in_response(self) -> None:
        """After X completes a winning row the response status is x_wins."""
        exp = json.loads((FIXTURE_EXPECTED / "game_state_win.0.0.1.json").read_text())
        client = self._make_client()
        game_id = client.post("/games").json()["game_id"]
        client.post(f"/games/{game_id}/moves", json={"position": 0})  # X
        client.post(f"/games/{game_id}/moves", json={"position": 3})  # O
        client.post(f"/games/{game_id}/moves", json={"position": 1})  # X
        client.post(f"/games/{game_id}/moves", json={"position": 4})  # O
        resp = client.post(f"/games/{game_id}/moves", json={"position": 2})  # X wins
        body = resp.json()
        self.assertEqual(body["status"], exp["status"])
        self.assertEqual(body["winner"], exp["winner"])

    def test_implements_interface(self) -> None:
        """RestController satisfies the IGameController contract."""
        from domain.game.adaptors.i_game_controller import IGameController
        from domain.game.adaptors.rest_controller import RestController
        self.assertTrue(issubclass(RestController, IGameController))


if __name__ == "__main__":
    unittest.main()
