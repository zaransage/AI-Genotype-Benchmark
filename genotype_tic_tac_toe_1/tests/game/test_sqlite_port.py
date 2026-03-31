"""
Port tests: SqliteGameArchive

Tests cover:
  - raw fixture integrity assumptions (field presence and values)
  - canonical CompletedGameRecord field values after archive/retrieve
  - archive, list_completed, and get_record operations
  - error handling for missing records
  - overwrite (INSERT OR REPLACE) semantics
"""

from __future__ import annotations

import json
import os
import pathlib
import tempfile
import unittest

from domain.core.models                      import CompletedGameRecord, Move
from domain.core.ports.sqlite_game_archive   import SqliteGameArchive

FIXTURES_RAW      = pathlib.Path("fixtures/raw/archive/v1")
FIXTURES_EXPECTED = pathlib.Path("fixtures/expected/archive/v1")

_RAW_FIXTURE      = FIXTURES_RAW      / "completed_game.0.0.1.json"
_EXPECTED_FIXTURE = FIXTURES_EXPECTED / "completed_game.0.0.1.json"


def _make_x_wins_record() -> CompletedGameRecord:
    """Return the canonical CompletedGameRecord matching the v1 fixture."""
    game_id = "test-archive-001"
    return CompletedGameRecord(
        game_id = game_id,
        outcome = "x_wins",
        winner  = "X",
        board   = [["X", "X", "X"], ["O", "O", ""], ["", "", ""]],
        moves   = [
            Move(game_id=game_id, player="X", row=0, col=0),
            Move(game_id=game_id, player="O", row=1, col=0),
            Move(game_id=game_id, player="X", row=0, col=1),
            Move(game_id=game_id, player="O", row=1, col=1),
            Move(game_id=game_id, player="X", row=0, col=2),
        ],
    )


class TestRawFixtureIntegrity(unittest.TestCase):
    """Validate raw fixture assumptions before any transformation."""

    def setUp(self) -> None:
        with open(_RAW_FIXTURE) as f:
            self.raw = json.load(f)

    def test_game_id_present(self) -> None:
        self.assertIn("game_id", self.raw)

    def test_outcome_is_terminal(self) -> None:
        self.assertIn(self.raw["outcome"], {"x_wins", "o_wins", "draw"})

    def test_board_is_3x3(self) -> None:
        board = self.raw["board"]
        self.assertEqual(len(board), 3)
        for row in board:
            self.assertEqual(len(row), 3)

    def test_moves_present_and_nonempty(self) -> None:
        self.assertIn("moves", self.raw)
        self.assertGreater(len(self.raw["moves"]), 0)

    def test_each_move_has_required_fields(self) -> None:
        for move in self.raw["moves"]:
            self.assertIn("player", move)
            self.assertIn("row",    move)
            self.assertIn("col",    move)

    def test_winner_matches_outcome(self) -> None:
        self.assertEqual(self.raw["winner"], "X")
        self.assertEqual(self.raw["outcome"], "x_wins")


class TestExpectedFixtureIntegrity(unittest.TestCase):
    """Validate expected canonical fixture shape."""

    def setUp(self) -> None:
        with open(_EXPECTED_FIXTURE) as f:
            self.expected = json.load(f)

    def test_moves_omit_game_id(self) -> None:
        # Expected fixture moves store only player/row/col (no game_id redundancy)
        for move in self.expected["moves"]:
            self.assertNotIn("game_id", move)

    def test_move_count_matches_raw(self) -> None:
        with open(_RAW_FIXTURE) as f:
            raw = json.load(f)
        self.assertEqual(len(self.expected["moves"]), len(raw["moves"]))


class TestSqliteGameArchive(unittest.TestCase):

    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self._archive = SqliteGameArchive(self._tmp.name)

    def tearDown(self) -> None:
        os.unlink(self._tmp.name)

    # --- archive + get_record ---

    def test_archive_and_retrieve_game_id(self) -> None:
        record = _make_x_wins_record()
        self._archive.archive(record)
        retrieved = self._archive.get_record("test-archive-001")
        self.assertEqual(retrieved.game_id, "test-archive-001")

    def test_archive_and_retrieve_outcome(self) -> None:
        record = _make_x_wins_record()
        self._archive.archive(record)
        retrieved = self._archive.get_record("test-archive-001")
        self.assertEqual(retrieved.outcome, "x_wins")

    def test_archive_and_retrieve_winner(self) -> None:
        record = _make_x_wins_record()
        self._archive.archive(record)
        retrieved = self._archive.get_record("test-archive-001")
        self.assertEqual(retrieved.winner, "X")

    def test_archive_and_retrieve_board(self) -> None:
        record = _make_x_wins_record()
        self._archive.archive(record)
        retrieved = self._archive.get_record("test-archive-001")
        self.assertEqual(retrieved.board, record.board)

    def test_archive_and_retrieve_move_count(self) -> None:
        record = _make_x_wins_record()
        self._archive.archive(record)
        retrieved = self._archive.get_record("test-archive-001")
        self.assertEqual(len(retrieved.moves), 5)

    def test_archive_and_retrieve_move_order(self) -> None:
        record = _make_x_wins_record()
        self._archive.archive(record)
        retrieved = self._archive.get_record("test-archive-001")
        self.assertEqual(retrieved.moves[0].player, "X")
        self.assertEqual(retrieved.moves[0].row,    0)
        self.assertEqual(retrieved.moves[0].col,    0)
        self.assertEqual(retrieved.moves[1].player, "O")

    def test_archive_draw_winner_is_none(self) -> None:
        record = CompletedGameRecord(
            game_id = "draw-game",
            outcome = "draw",
            winner  = None,
            board   = [["X","O","X"],["X","X","O"],["O","X","O"]],
            moves   = [],
        )
        self._archive.archive(record)
        retrieved = self._archive.get_record("draw-game")
        self.assertIsNone(retrieved.winner)

    # --- get_record error ---

    def test_get_record_raises_key_error_when_missing(self) -> None:
        with self.assertRaises(KeyError):
            self._archive.get_record("does-not-exist")

    # --- list_completed ---

    def test_list_completed_empty_initially(self) -> None:
        self.assertEqual(self._archive.list_completed(), [])

    def test_list_completed_returns_archived_records(self) -> None:
        self._archive.archive(_make_x_wins_record())
        records = self._archive.list_completed()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].game_id, "test-archive-001")

    def test_list_completed_preserves_insertion_order(self) -> None:
        for i in range(3):
            self._archive.archive(
                CompletedGameRecord(
                    game_id = f"game-{i}",
                    outcome = "draw",
                    winner  = None,
                    board   = [["","",""],["","",""],["","",""]],
                    moves   = [],
                )
            )
        ids = [r.game_id for r in self._archive.list_completed()]
        self.assertEqual(ids, ["game-0", "game-1", "game-2"])

    # --- overwrite semantics ---

    def test_archive_overwrites_existing_record(self) -> None:
        record_v1 = _make_x_wins_record()
        self._archive.archive(record_v1)

        record_v2 = CompletedGameRecord(
            game_id = "test-archive-001",
            outcome = "o_wins",
            winner  = "O",
            board   = [["O","O","O"],["X","X",""],["","",""]],
            moves   = [Move("test-archive-001","O",0,0)],
        )
        self._archive.archive(record_v2)

        retrieved = self._archive.get_record("test-archive-001")
        self.assertEqual(retrieved.outcome, "o_wins")
        self.assertEqual(len(retrieved.moves), 1)

    # --- fixture-driven canonical model assertion ---

    def test_canonical_model_matches_expected_fixture(self) -> None:
        with open(_EXPECTED_FIXTURE) as f:
            expected = json.load(f)

        record = _make_x_wins_record()
        self._archive.archive(record)
        retrieved = self._archive.get_record(expected["game_id"])

        self.assertEqual(retrieved.game_id, expected["game_id"])
        self.assertEqual(retrieved.outcome, expected["outcome"])
        self.assertEqual(retrieved.winner,  expected["winner"])
        self.assertEqual(retrieved.board,   expected["board"])
        self.assertEqual(len(retrieved.moves), len(expected["moves"]))
        for got, exp in zip(retrieved.moves, expected["moves"]):
            self.assertEqual(got.player, exp["player"])
            self.assertEqual(got.row,    exp["row"])
            self.assertEqual(got.col,    exp["col"])
