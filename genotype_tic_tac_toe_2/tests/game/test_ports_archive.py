"""
Tests for the outbound archive port: IGameArchive and SQLiteGameArchive.

Per AI_CONTRACT.md §6: assertions cover
  1. Raw fixture field integrity.
  2. Canonical CompletedGame model correctness after save/retrieve.
  3. Interface compliance.
"""
import json
import pathlib
import unittest

FIXTURE_RAW      = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "raw"      / "game_archive" / "v1"
FIXTURE_EXPECTED = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "expected" / "game_archive" / "v1"


def _make_game(game_id="test-game-42", winner="X", moves=None):
    from domain.game.completed_game import CompletedGame
    return CompletedGame(
        game_id      = game_id,
        board        = ["X", "X", "X", "O", "O", "", "", "", ""],
        moves        = moves if moves is not None else [0, 3, 1, 4, 2],
        winner       = winner,
        status       = "x_wins",
        completed_at = "2026-03-28T00:00:00+00:00",
    )


class TestRawArchiveFixtureIntegrity(unittest.TestCase):
    """Assertion 1 — raw fixture contains the expected source fields."""

    def test_raw_fixture_has_game_id(self) -> None:
        raw = json.loads((FIXTURE_RAW / "completed_game.0.0.1.json").read_text())
        self.assertIn("game_id", raw)
        self.assertIsInstance(raw["game_id"], str)

    def test_raw_fixture_has_moves_list(self) -> None:
        raw = json.loads((FIXTURE_RAW / "completed_game.0.0.1.json").read_text())
        self.assertIn("moves", raw)
        self.assertIsInstance(raw["moves"], list)

    def test_raw_fixture_has_status(self) -> None:
        raw = json.loads((FIXTURE_RAW / "completed_game.0.0.1.json").read_text())
        self.assertIn("status", raw)

    def test_raw_fixture_has_board_of_9(self) -> None:
        raw = json.loads((FIXTURE_RAW / "completed_game.0.0.1.json").read_text())
        self.assertIn("board", raw)
        self.assertEqual(len(raw["board"]), 9)

    def test_raw_fixture_has_winner(self) -> None:
        raw = json.loads((FIXTURE_RAW / "completed_game.0.0.1.json").read_text())
        self.assertIn("winner", raw)

    def test_raw_fixture_has_completed_at(self) -> None:
        raw = json.loads((FIXTURE_RAW / "completed_game.0.0.1.json").read_text())
        self.assertIn("completed_at", raw)


class TestExpectedArchiveFixtureIntegrity(unittest.TestCase):
    """Assertion 1 — expected fixture matches the canonical model shape."""

    def test_expected_fixture_status_is_terminal(self) -> None:
        exp = json.loads((FIXTURE_EXPECTED / "archived_game.0.0.1.json").read_text())
        self.assertIn(exp["status"], ("x_wins", "o_wins", "draw"))

    def test_expected_fixture_winner_matches_status(self) -> None:
        exp = json.loads((FIXTURE_EXPECTED / "archived_game.0.0.1.json").read_text())
        self.assertEqual(exp["winner"], "X")
        self.assertEqual(exp["status"], "x_wins")

    def test_expected_fixture_moves_is_list_of_ints(self) -> None:
        exp = json.loads((FIXTURE_EXPECTED / "archived_game.0.0.1.json").read_text())
        self.assertTrue(all(isinstance(m, int) for m in exp["moves"]))


class TestSQLiteGameArchiveBehavior(unittest.TestCase):
    """Assertion 2 — canonical model round-trips correctly through SQLite."""

    def setUp(self) -> None:
        from domain.game.ports.sqlite_game_archive import SQLiteGameArchive
        self.archive = SQLiteGameArchive(":memory:")

    def test_save_and_get_returns_same_game_id(self) -> None:
        game = _make_game()
        self.archive.save(game)
        result = self.archive.get(game.game_id)
        self.assertIsNotNone(result)
        self.assertEqual(result.game_id, game.game_id)

    def test_save_and_get_preserves_winner(self) -> None:
        game = _make_game()
        self.archive.save(game)
        result = self.archive.get(game.game_id)
        self.assertEqual(result.winner, "X")

    def test_save_and_get_preserves_moves(self) -> None:
        game = _make_game()
        self.archive.save(game)
        result = self.archive.get(game.game_id)
        self.assertEqual(result.moves, [0, 3, 1, 4, 2])

    def test_save_and_get_preserves_board(self) -> None:
        game = _make_game()
        self.archive.save(game)
        result = self.archive.get(game.game_id)
        self.assertEqual(result.board, ["X", "X", "X", "O", "O", "", "", "", ""])

    def test_save_and_get_preserves_status(self) -> None:
        game = _make_game()
        self.archive.save(game)
        result = self.archive.get(game.game_id)
        self.assertEqual(result.status, "x_wins")

    def test_get_nonexistent_returns_none(self) -> None:
        self.assertIsNone(self.archive.get("no-such-game"))

    def test_list_all_empty_when_nothing_saved(self) -> None:
        self.assertEqual(self.archive.list_all(), [])

    def test_list_all_returns_all_saved_games(self) -> None:
        self.archive.save(_make_game("g-1"))
        self.archive.save(_make_game("g-2", winner="X"))
        games = self.archive.list_all()
        self.assertEqual(len(games), 2)

    def test_list_all_game_ids_match(self) -> None:
        self.archive.save(_make_game("g-alpha"))
        self.archive.save(_make_game("g-beta"))
        ids = {g.game_id for g in self.archive.list_all()}
        self.assertIn("g-alpha", ids)
        self.assertIn("g-beta", ids)

    def test_save_is_idempotent_on_same_game_id(self) -> None:
        """Saving the same game_id twice must not raise and must keep one row."""
        game = _make_game()
        self.archive.save(game)
        self.archive.save(game)
        self.assertEqual(len(self.archive.list_all()), 1)

    def test_draw_game_archives_correctly(self) -> None:
        from domain.game.completed_game import CompletedGame
        draw = CompletedGame(
            game_id      = "draw-001",
            board        = ["X", "O", "X", "O", "X", "X", "O", "X", "O"],
            moves        = [0, 1, 2, 3, 4, 5, 6, 7, 8],
            winner       = None,
            status       = "draw",
            completed_at = "2026-03-28T01:00:00+00:00",
        )
        self.archive.save(draw)
        result = self.archive.get("draw-001")
        self.assertEqual(result.status, "draw")
        self.assertIsNone(result.winner)


class TestIGameArchiveContract(unittest.TestCase):
    """SQLiteGameArchive satisfies the IGameArchive ABC."""

    def test_implements_interface(self) -> None:
        from domain.game.ports.i_game_archive import IGameArchive
        from domain.game.ports.sqlite_game_archive import SQLiteGameArchive
        self.assertTrue(issubclass(SQLiteGameArchive, IGameArchive))


if __name__ == "__main__":
    unittest.main()
