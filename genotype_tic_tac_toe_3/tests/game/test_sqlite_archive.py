"""
tests/game/test_sqlite_archive.py

Unit tests for the SQLite game archive port (IGameArchive / SqliteGameArchive).
Tests are written before implementation per AI_CONTRACT §1.
Raw and expected fixture assertions follow AI_CONTRACT §6.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from domain.game.core.ports.i_game_archive      import IGameArchive
from domain.game.core.ports.sqlite_game_archive import SqliteGameArchive


_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"
_RAW_V1      = _FIXTURE_DIR / "raw"      / "game" / "v1"
_EXPECTED_V1 = _FIXTURE_DIR / "expected" / "game" / "v1"


class TestSqliteGameArchiveInterface(unittest.TestCase):
    """SqliteGameArchive must satisfy IGameArchive."""

    def test_implements_interface(self) -> None:
        archive = SqliteGameArchive(db_path=":memory:")
        self.assertIsInstance(archive, IGameArchive)


class TestSqliteGameArchiveLifecycle(unittest.TestCase):
    """Core record/close/query lifecycle using an in-memory DB for speed."""

    def setUp(self) -> None:
        self._archive = SqliteGameArchive(db_path=":memory:")

    # ------------------------------------------------------------------
    # find_completed_games
    # ------------------------------------------------------------------

    def test_find_completed_games_empty_on_fresh_db(self) -> None:
        self.assertEqual(self._archive.find_completed_games(), [])

    # ------------------------------------------------------------------
    # record_move + close_game + find
    # ------------------------------------------------------------------

    def test_close_game_x_wins(self) -> None:
        self._archive.record_move("g1", "X", 0, 0)
        self._archive.close_game("g1", "x_wins", "X")
        games = self._archive.find_completed_games()
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["game_id"],  "g1")
        self.assertEqual(games[0]["outcome"],  "x_wins")
        self.assertEqual(games[0]["winner"],   "X")

    def test_close_game_o_wins(self) -> None:
        self._archive.record_move("g2", "O", 2, 2)
        self._archive.close_game("g2", "o_wins", "O")
        games = self._archive.find_completed_games()
        self.assertEqual(games[0]["outcome"], "o_wins")
        self.assertEqual(games[0]["winner"],  "O")

    def test_close_game_draw_has_null_winner(self) -> None:
        self._archive.record_move("g3", "X", 1, 1)
        self._archive.close_game("g3", "draw", None)
        games = self._archive.find_completed_games()
        self.assertEqual(games[0]["outcome"], "draw")
        self.assertIsNone(games[0]["winner"])

    def test_multiple_games_all_archived(self) -> None:
        self._archive.record_move("ga", "X", 0, 0)
        self._archive.close_game("ga", "x_wins", "X")
        self._archive.record_move("gb", "O", 1, 1)
        self._archive.close_game("gb", "draw", None)
        games = self._archive.find_completed_games()
        self.assertEqual(len(games), 2)
        ids = {g["game_id"] for g in games}
        self.assertIn("ga", ids)
        self.assertIn("gb", ids)

    def test_close_game_stores_archived_at_timestamp(self) -> None:
        self._archive.record_move("g4", "X", 0, 0)
        self._archive.close_game("g4", "x_wins", "X")
        games = self._archive.find_completed_games()
        self.assertIn("archived_at", games[0])
        self.assertTrue(games[0]["archived_at"])  # non-empty string

    # ------------------------------------------------------------------
    # Multiple moves per game (move log integrity)
    # ------------------------------------------------------------------

    def test_multiple_moves_recorded_for_one_game(self) -> None:
        for player, row, col in [("X", 0, 0), ("O", 1, 1), ("X", 0, 1)]:
            self._archive.record_move("g5", player, row, col)
        self._archive.close_game("g5", "in_progress", None)
        # Game is closed; verify it appears in completed list
        games = self._archive.find_completed_games()
        self.assertEqual(games[0]["game_id"], "g5")


class TestSqliteGameArchiveFileDb(unittest.TestCase):
    """Verify persistence survives a fresh SqliteGameArchive instance on same file."""

    def setUp(self) -> None:
        fd, self._db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

    def tearDown(self) -> None:
        os.unlink(self._db_path)

    def test_data_persists_across_instances(self) -> None:
        a1 = SqliteGameArchive(db_path=self._db_path)
        a1.record_move("persist-1", "X", 0, 0)
        a1.close_game("persist-1", "x_wins", "X")

        a2 = SqliteGameArchive(db_path=self._db_path)
        games = a2.find_completed_games()
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["game_id"], "persist-1")


class TestSqliteArchiveFixtures(unittest.TestCase):
    """Raw and expected fixture integrity (AI_CONTRACT §6)."""

    def test_raw_game_archive_fixture_has_required_fields(self) -> None:
        with open(_RAW_V1 / "game_archive.0.0.1.json") as fh:
            raw = json.load(fh)
        self.assertIn("game_id", raw)
        self.assertIn("moves",   raw)
        self.assertIn("outcome", raw)

    def test_raw_game_archive_moves_is_list(self) -> None:
        with open(_RAW_V1 / "game_archive.0.0.1.json") as fh:
            raw = json.load(fh)
        self.assertIsInstance(raw["moves"], list)

    def test_expected_archived_game_fixture_has_required_fields(self) -> None:
        with open(_EXPECTED_V1 / "archived_game.0.0.1.json") as fh:
            expected = json.load(fh)
        self.assertIn("game_id",     expected)
        self.assertIn("outcome",     expected)
        self.assertIn("winner",      expected)
        self.assertIn("archived_at", expected)

    def test_expected_archived_game_outcome_is_terminal(self) -> None:
        with open(_EXPECTED_V1 / "archived_game.0.0.1.json") as fh:
            expected = json.load(fh)
        terminal = {"x_wins", "o_wins", "draw"}
        self.assertIn(expected["outcome"], terminal)
