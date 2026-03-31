"""
Tests for the inbound Web UI adaptor: WebUIController.

Per AI_CONTRACT.md §6: assertions cover
  1. Raw/expected fixture field integrity.
  2. HTTP response shape (status codes, content-type, HTML content).
  3. End-to-end: completed game appears in /history after a winning sequence.
  4. Interface compliance.
"""
import json
import pathlib
import unittest

FIXTURE_RAW      = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "raw"      / "game_archive" / "v1"
FIXTURE_EXPECTED = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "expected" / "game_archive" / "v1"


class TestWebUIFixtureIntegrity(unittest.TestCase):
    """Assertion 1 — fixture files have the required fields."""

    def test_raw_completed_game_fixture_has_game_id(self) -> None:
        raw = json.loads((FIXTURE_RAW / "completed_game.0.0.1.json").read_text())
        self.assertIn("game_id", raw)

    def test_raw_completed_game_fixture_has_moves(self) -> None:
        raw = json.loads((FIXTURE_RAW / "completed_game.0.0.1.json").read_text())
        self.assertIn("moves", raw)
        self.assertIsInstance(raw["moves"], list)

    def test_raw_completed_game_fixture_has_status(self) -> None:
        raw = json.loads((FIXTURE_RAW / "completed_game.0.0.1.json").read_text())
        self.assertIn("status", raw)

    def test_expected_archived_game_fixture_has_winner(self) -> None:
        exp = json.loads((FIXTURE_EXPECTED / "archived_game.0.0.1.json").read_text())
        self.assertIn("winner", exp)

    def test_expected_archived_game_fixture_has_moves(self) -> None:
        exp = json.loads((FIXTURE_EXPECTED / "archived_game.0.0.1.json").read_text())
        self.assertIn("moves", exp)


class TestWebUIControllerRoutes(unittest.TestCase):
    """Assertion 2 — HTTP shape of the web UI routes."""

    def _make_client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_index_returns_200(self) -> None:
        client = self._make_client()
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_index_content_type_is_html(self) -> None:
        client = self._make_client()
        resp = client.get("/")
        self.assertIn("text/html", resp.headers["content-type"])

    def test_index_contains_new_game_button(self) -> None:
        client = self._make_client()
        resp = client.get("/")
        self.assertIn("New Game", resp.text)

    def test_index_contains_board_element(self) -> None:
        client = self._make_client()
        resp = client.get("/")
        self.assertIn("board", resp.text)

    def test_index_contains_history_link(self) -> None:
        client = self._make_client()
        resp = client.get("/")
        self.assertIn("/history", resp.text)

    def test_history_returns_200(self) -> None:
        client = self._make_client()
        resp = client.get("/history")
        self.assertEqual(resp.status_code, 200)

    def test_history_content_type_is_html(self) -> None:
        client = self._make_client()
        resp = client.get("/history")
        self.assertIn("text/html", resp.headers["content-type"])

    def test_history_contains_back_link(self) -> None:
        client = self._make_client()
        resp = client.get("/history")
        self.assertIn("Back", resp.text)


class TestWebUIControllerEndToEnd(unittest.TestCase):
    """Assertion 3 — completed game appears in /history after a winning game."""

    def _make_client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def _play_winning_game(self, client) -> None:
        """X wins via top row: X@0, O@3, X@1, O@4, X@2."""
        game_id = client.post("/games").json()["game_id"]
        client.post(f"/games/{game_id}/moves", json={"position": 0})  # X
        client.post(f"/games/{game_id}/moves", json={"position": 3})  # O
        client.post(f"/games/{game_id}/moves", json={"position": 1})  # X
        client.post(f"/games/{game_id}/moves", json={"position": 4})  # O
        client.post(f"/games/{game_id}/moves", json={"position": 2})  # X wins

    def test_history_contains_x_wins_after_winning_game(self) -> None:
        client = self._make_client()
        self._play_winning_game(client)
        resp = client.get("/history")
        self.assertIn("x_wins", resp.text)

    def test_history_shows_winner_after_winning_game(self) -> None:
        client = self._make_client()
        self._play_winning_game(client)
        resp = client.get("/history")
        # Winner column should contain "X"
        self.assertIn(">X<", resp.text)

    def test_history_shows_draw_outcome(self) -> None:
        """A draw game is also archived and shown in history."""
        client = self._make_client()
        # Known draw sequence: X→0 O→1 X→2 O→4 X→3 O→6 X→5 O→8 X→7
        game_id = client.post("/games").json()["game_id"]
        for pos in [0, 1, 2, 4, 3, 6, 5, 8, 7]:
            client.post(f"/games/{game_id}/moves", json={"position": pos})
        resp = client.get("/history")
        self.assertIn("draw", resp.text)


class TestIWebUIControllerContract(unittest.TestCase):
    """WebUIController satisfies the IWebUIController ABC."""

    def test_implements_interface(self) -> None:
        from domain.game.adaptors.i_web_ui_controller import IWebUIController
        from domain.game.adaptors.web_ui_controller import WebUIController
        self.assertTrue(issubclass(WebUIController, IWebUIController))


if __name__ == "__main__":
    unittest.main()
