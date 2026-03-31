"""
tests/game/test_core.py

Unit tests for GameService (core business logic) and canonical model validation.
Per AI_CONTRACT.md: tests first, unittest only, never removed.
"""

import json
import pathlib
import unittest

FIXTURES_RAW      = pathlib.Path(__file__).parents[2] / "fixtures" / "raw"      / "game" / "v1"
FIXTURES_EXPECTED = pathlib.Path(__file__).parents[2] / "fixtures" / "expected" / "game" / "v1"


class TestGameStateModel(unittest.TestCase):
    """Canonical @dataclass model validation — ADR 0002."""

    def _import_models(self):
        from domain.game.core.models import GameState, Move
        return GameState, Move

    def test_gamestate_valid_construction(self):
        GameState, _ = self._import_models()
        state = GameState(
            game_id="abc",
            board=[["", "", ""], ["", "", ""], ["", "", ""]],
            current_player="X",
            status="in_progress",
            winner=None,
        )
        self.assertEqual(state.game_id, "abc")
        self.assertEqual(state.current_player, "X")
        self.assertEqual(state.status, "in_progress")
        self.assertIsNone(state.winner)

    def test_gamestate_rejects_empty_game_id(self):
        GameState, _ = self._import_models()
        with self.assertRaises(ValueError):
            GameState(
                game_id="",
                board=[["", "", ""], ["", "", ""], ["", "", ""]],
                current_player="X",
                status="in_progress",
            )

    def test_gamestate_rejects_invalid_status(self):
        GameState, _ = self._import_models()
        with self.assertRaises(ValueError):
            GameState(
                game_id="abc",
                board=[["", "", ""], ["", "", ""], ["", "", ""]],
                current_player="X",
                status="bad_status",
            )

    def test_gamestate_rejects_invalid_player(self):
        GameState, _ = self._import_models()
        with self.assertRaises(ValueError):
            GameState(
                game_id="abc",
                board=[["", "", ""], ["", "", ""], ["", "", ""]],
                current_player="Z",
                status="in_progress",
            )

    def test_gamestate_rejects_non_3x3_board(self):
        GameState, _ = self._import_models()
        with self.assertRaises(ValueError):
            GameState(
                game_id="abc",
                board=[["", ""], ["", ""]],
                current_player="X",
                status="in_progress",
            )

    def test_move_valid_construction(self):
        _, Move = self._import_models()
        m = Move(player="X", row=1, col=2)
        self.assertEqual(m.player, "X")
        self.assertEqual(m.row, 1)
        self.assertEqual(m.col, 2)

    def test_move_rejects_invalid_player(self):
        _, Move = self._import_models()
        with self.assertRaises(ValueError):
            Move(player="Q", row=0, col=0)

    def test_move_rejects_out_of_bounds_row(self):
        _, Move = self._import_models()
        with self.assertRaises(ValueError):
            Move(player="X", row=3, col=0)

    def test_move_rejects_out_of_bounds_col(self):
        _, Move = self._import_models()
        with self.assertRaises(ValueError):
            Move(player="X", row=0, col=-1)


class TestGameService(unittest.TestCase):
    """GameService business logic tests."""

    def _make_service(self):
        from domain.game.core.game_service import GameService
        return GameService()

    def _import_models(self):
        from domain.game.core.models import GameState, Move
        return GameState, Move

    def test_create_game_returns_initial_state(self):
        svc = self._make_service()
        state = svc.create_game()
        self.assertIsNotNone(state.game_id)
        self.assertEqual(state.current_player, "X")
        self.assertEqual(state.status, "in_progress")
        self.assertIsNone(state.winner)
        self.assertEqual(state.board, [["", "", ""], ["", "", ""], ["", "", ""]])

    def test_create_game_produces_unique_ids(self):
        svc = self._make_service()
        ids = {svc.create_game().game_id for _ in range(10)}
        self.assertEqual(len(ids), 10)

    def test_apply_move_places_piece(self):
        svc = self._make_service()
        GameState, Move = self._import_models()
        state = svc.create_game()
        move = Move(player="X", row=0, col=0)
        new_state = svc.apply_move(state, move)
        self.assertEqual(new_state.board[0][0], "X")
        self.assertEqual(new_state.current_player, "O")
        self.assertEqual(new_state.status, "in_progress")

    def test_apply_move_alternates_players(self):
        svc = self._make_service()
        _, Move = self._import_models()
        state = svc.create_game()
        state = svc.apply_move(state, Move(player="X", row=0, col=0))
        self.assertEqual(state.current_player, "O")
        state = svc.apply_move(state, Move(player="O", row=1, col=1))
        self.assertEqual(state.current_player, "X")

    def test_apply_move_rejects_wrong_player(self):
        svc = self._make_service()
        _, Move = self._import_models()
        state = svc.create_game()
        with self.assertRaises(ValueError):
            svc.apply_move(state, Move(player="O", row=0, col=0))

    def test_apply_move_rejects_occupied_cell(self):
        svc = self._make_service()
        _, Move = self._import_models()
        state = svc.create_game()
        state = svc.apply_move(state, Move(player="X", row=0, col=0))
        with self.assertRaises(ValueError):
            svc.apply_move(state, Move(player="O", row=0, col=0))

    def test_apply_move_rejects_move_on_finished_game(self):
        svc = self._make_service()
        GameState, Move = self._import_models()
        state = GameState(
            game_id="finished",
            board=[["X", "X", "X"], ["O", "O", ""], ["", "", ""]],
            current_player="O",
            status="x_wins",
            winner="X",
        )
        with self.assertRaises(ValueError):
            svc.apply_move(state, Move(player="O", row=1, col=2))

    def test_x_wins_row(self):
        svc = self._make_service()
        GameState, Move = self._import_models()
        state = GameState(
            game_id="g1",
            board=[["X", "X", ""], ["O", "O", ""], ["", "", ""]],
            current_player="X",
            status="in_progress",
        )
        new_state = svc.apply_move(state, Move(player="X", row=0, col=2))
        self.assertEqual(new_state.status, "x_wins")
        self.assertEqual(new_state.winner, "X")

    def test_o_wins_column(self):
        svc = self._make_service()
        GameState, Move = self._import_models()
        state = GameState(
            game_id="g2",
            board=[["X", "O", ""], ["X", "O", ""], ["", "", ""]],
            current_player="O",
            status="in_progress",
        )
        new_state = svc.apply_move(state, Move(player="O", row=2, col=1))
        self.assertEqual(new_state.status, "o_wins")
        self.assertEqual(new_state.winner, "O")

    def test_x_wins_diagonal(self):
        svc = self._make_service()
        GameState, Move = self._import_models()
        state = GameState(
            game_id="g3",
            board=[["X", "O", ""], ["O", "X", ""], ["", "", ""]],
            current_player="X",
            status="in_progress",
        )
        new_state = svc.apply_move(state, Move(player="X", row=2, col=2))
        self.assertEqual(new_state.status, "x_wins")
        self.assertEqual(new_state.winner, "X")

    def test_draw(self):
        svc = self._make_service()
        GameState, Move = self._import_models()
        # Board: X O X / O _ X / O X O  — X plays (1,1) => draw (no line for either player)
        # After move: X O X / O X X / O X O — verify no winner exists
        state = GameState(
            game_id="g4",
            board=[["X", "O", "X"], ["O", "", "X"], ["O", "X", "O"]],
            current_player="X",
            status="in_progress",
        )
        new_state = svc.apply_move(state, Move(player="X", row=1, col=1))
        self.assertEqual(new_state.status, "draw")
        self.assertIsNone(new_state.winner)

    def test_expected_fixture_matches_apply_move_output(self):
        """
        ADR 0003 / AI_CONTRACT §6: assert raw fixture → canonical model fields.
        Loads make_move.0.0.1.json (raw) and game_state.0.0.1.json (expected).
        """
        raw_move = json.loads((FIXTURES_RAW / "make_move.0.0.1.json").read_text())
        expected  = json.loads((FIXTURES_EXPECTED / "game_state.0.0.1.json").read_text())

        # 1. Raw fixture contains expected source fields
        self.assertIn("player", raw_move)
        self.assertIn("row",    raw_move)
        self.assertIn("col",    raw_move)

        # 2. Canonical model fields match expected fixture after apply_move
        svc = self._make_service()
        from domain.game.core.models import GameState, Move
        initial = GameState(
            game_id=expected["game_id"],
            board=[["", "", ""], ["", "", ""], ["", "", ""]],
            current_player="X",
            status="in_progress",
        )
        move = Move(player=raw_move["player"], row=raw_move["row"], col=raw_move["col"])
        result = svc.apply_move(initial, move)

        self.assertEqual(result.board[0][0], expected["board"][0][0])
        self.assertEqual(result.current_player, expected["current_player"])
        self.assertEqual(result.status, expected["status"])
        self.assertEqual(result.winner, expected["winner"])


if __name__ == "__main__":
    unittest.main()
