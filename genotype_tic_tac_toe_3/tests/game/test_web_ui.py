"""
tests/game/test_web_ui.py

Unit tests for the WebUIAdaptor (inbound adaptor — serves the browser game UI).
Tests are written before implementation per AI_CONTRACT §1.
"""

import os
import tempfile
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.game.core.adaptors.web_ui_adaptor import WebUIAdaptor


_MINIMAL_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Tic-Tac-Toe</title></head>
<body><h1>Tic-Tac-Toe</h1><div id="board"></div></body>
</html>
"""


def _write_tmp_html(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


class TestWebUIAdaptorRouter(unittest.TestCase):
    """WebUIAdaptor.create_router() contract tests."""

    def setUp(self) -> None:
        self._html_path = _write_tmp_html(_MINIMAL_HTML)
        adaptor = WebUIAdaptor(html_path=self._html_path)
        app = FastAPI()
        app.include_router(adaptor.create_router())
        self._client = TestClient(app)

    def tearDown(self) -> None:
        os.unlink(self._html_path)

    def test_get_root_returns_200(self) -> None:
        response = self._client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_get_root_content_type_is_html(self) -> None:
        response = self._client.get("/")
        self.assertIn("text/html", response.headers["content-type"])

    def test_get_root_contains_expected_title(self) -> None:
        response = self._client.get("/")
        self.assertIn("Tic-Tac-Toe", response.text)

    def test_get_root_contains_board_element(self) -> None:
        response = self._client.get("/")
        self.assertIn('id="board"', response.text)

    def test_router_exposes_root_path(self) -> None:
        adaptor   = WebUIAdaptor(html_path=self._html_path)
        router    = adaptor.create_router()
        paths     = [route.path for route in router.routes]
        self.assertIn("/", paths)


class TestWebUIAdaptorHtmlContent(unittest.TestCase):
    """The real static/index.html must contain key UI elements."""

    def setUp(self) -> None:
        # Resolve relative to project root (two levels up from this file's tests/game/)
        project_root = os.path.join(os.path.dirname(__file__), "..", "..")
        self._html_path = os.path.normpath(
            os.path.join(project_root, "static", "index.html")
        )

    def _load(self) -> str:
        with open(self._html_path, encoding="utf-8") as fh:
            return fh.read()

    def test_index_html_exists(self) -> None:
        self.assertTrue(
            os.path.exists(self._html_path),
            msg=f"static/index.html not found at {self._html_path}",
        )

    def test_index_html_has_doctype(self) -> None:
        self.assertIn("<!DOCTYPE html>", self._load())

    def test_index_html_has_board_element(self) -> None:
        self.assertIn("board", self._load())

    def test_index_html_references_games_api(self) -> None:
        # The UI JavaScript must reference the /games REST endpoint.
        self.assertIn("/games", self._load())

    def test_index_html_has_new_game_trigger(self) -> None:
        # The player must be able to start a new game from the UI.
        html = self._load()
        self.assertTrue(
            "new-game" in html or "New Game" in html or "newGame" in html,
            msg="index.html must contain a 'New Game' button or equivalent trigger",
        )


class TestWebUIAdaptorServesRealHtml(unittest.TestCase):
    """Integration: WebUIAdaptor serves the real static/index.html via TestClient."""

    def setUp(self) -> None:
        project_root    = os.path.join(os.path.dirname(__file__), "..", "..")
        self._html_path = os.path.normpath(
            os.path.join(project_root, "static", "index.html")
        )
        if not os.path.exists(self._html_path):
            self.skipTest("static/index.html not yet written")
        adaptor = WebUIAdaptor(html_path=self._html_path)
        app     = FastAPI()
        app.include_router(adaptor.create_router())
        self._client = TestClient(app)

    def test_real_html_served_with_200(self) -> None:
        response = self._client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_real_html_content_type(self) -> None:
        response = self._client.get("/")
        self.assertIn("text/html", response.headers["content-type"])
