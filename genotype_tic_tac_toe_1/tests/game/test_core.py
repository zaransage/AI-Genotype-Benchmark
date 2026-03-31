"""
Tests for domain/core/models.py and domain/core/game_logic.py.

Coverage:
- GameState canonical model validation
- Move canonical model validation
- check_winner across all eight winning lines
- is_draw detection
- apply_move: normal flow, turn switching, win/draw detection, error paths
"""

import json
import pathlib
import unittest

FIXTURE_EXPECTED = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "expected" / "game" / "v1"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(name: str) -> dict:
    with open(FIXTURE_EXPECTED / name) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TestGameStateModel(unittest.TestCase):

    def _make(self, **overrides):
        from domain.core.models import GameState
        defaults = dict(
            game_id="g1",
            board=[["", "", ""], ["", "", ""], ["", "", ""]],
            current_player="X",
            status="active",
            winner=None,
        )
        defaults.update(overrides)
        return GameState(**defaults)

    def test_valid_new_game(self):
        """A freshly constructed GameState with valid fields should not raise."""
        state = self._make()
        self.assertEqual(state.game_id, "g1")
        self.assertEqual(state.current_player, "X")
        self.assertEqual(state.status, "active")
        self.assertIsNone(state.winner)

    def test_empty_game_id_raises(self):
        from domain.core.models import GameState
        with self.assertRaises(ValueError):
            self._make(game_id="")

    def test_board_wrong_size_raises(self):
        with self.assertRaises(ValueError):
            self._make(board=[["", ""], ["", ""], ["", ""]])

    def test_board_invalid_cell_raises(self):
        with self.assertRaises(ValueError):
            self._make(board=[["Z", "", ""], ["", "", ""], ["", "", ""]])

    def test_invalid_current_player_raises(self):
        with self.assertRaises(ValueError):
            self._make(current_player="A")

    def test_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            self._make(status="unknown")

    def test_invalid_winner_raises(self):
        with self.assertRaises(ValueError):
            self._make(winner="Z")

    # --- fixture integrity ---

    def test_fixture_new_game_fields(self):
        """Raw fixture game_state_new.0.0.1.json contains expected source fields."""
        raw = _load("game_state_new.0.0.1.json")
        self.assertIn("game_id",        raw)
        self.assertIn("board",          raw)
        self.assertIn("current_player", raw)
        self.assertIn("status",         raw)
        self.assertIn("winner",         raw)

    def test_fixture_new_game_canonical_values(self):
        """Canonical GameState built from fixture has correct field values."""
        from domain.core.models import GameState
        raw = _load("game_state_new.0.0.1.json")
        state = GameState(**raw)
        self.assertEqual(state.current_player, "X")
        self.assertEqual(state.status,         "active")
        self.assertIsNone(state.winner)
        self.assertEqual(state.board, [["", "", ""], ["", "", ""], ["", "", ""]])


class TestMoveModel(unittest.TestCase):

    def _make(self, **overrides):
        from domain.core.models import Move
        defaults = dict(game_id="g1", player="X", row=0, col=0)
        defaults.update(overrides)
        return Move(**defaults)

    def test_valid_move(self):
        move = self._make()
        self.assertEqual(move.player, "X")

    def test_empty_game_id_raises(self):
        with self.assertRaises(ValueError):
            self._make(game_id="")

    def test_invalid_player_raises(self):
        with self.assertRaises(ValueError):
            self._make(player="Z")

    def test_row_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            self._make(row=3)

    def test_col_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            self._make(col=-1)

    # --- fixture integrity ---

    def test_fixture_make_move_fields(self):
        """Raw make_move fixture contains the required source fields."""
        raw_path = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "raw" / "game" / "v1" / "make_move.0.0.1.json"
        with open(raw_path) as fh:
            raw = json.load(fh)
        self.assertIn("player", raw)
        self.assertIn("row",    raw)
        self.assertIn("col",    raw)

    def test_fixture_make_move_canonical_values(self):
        """Canonical Move built from fixture has correct field values."""
        from domain.core.models import Move
        raw_path = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "raw" / "game" / "v1" / "make_move.0.0.1.json"
        with open(raw_path) as fh:
            raw = json.load(fh)
        move = Move(game_id="g1", **raw)
        self.assertEqual(move.player, "X")
        self.assertEqual(move.row,    1)
        self.assertEqual(move.col,    1)


# ---------------------------------------------------------------------------
# Game logic — check_winner
# ---------------------------------------------------------------------------

class TestCheckWinner(unittest.TestCase):

    def _board(self, rows):
        return rows

    def test_no_winner_empty_board(self):
        from domain.core.game_logic import check_winner
        board = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.assertIsNone(check_winner(board))

    def test_row_0_winner(self):
        from domain.core.game_logic import check_winner
        board = [["X", "X", "X"], ["O", "O", ""], ["", "", ""]]
        self.assertEqual(check_winner(board), "X")

    def test_row_1_winner(self):
        from domain.core.game_logic import check_winner
        board = [["O", "", ""], ["X", "X", "X"], ["O", "", ""]]
        self.assertEqual(check_winner(board), "X")

    def test_row_2_winner(self):
        from domain.core.game_logic import check_winner
        board = [["X", "", ""], ["X", "O", ""], ["O", "O", "O"]]
        self.assertEqual(check_winner(board), "O")

    def test_col_0_winner(self):
        from domain.core.game_logic import check_winner
        board = [["X", "O", ""], ["X", "O", ""], ["X", "", ""]]
        self.assertEqual(check_winner(board), "X")

    def test_col_1_winner(self):
        from domain.core.game_logic import check_winner
        board = [["", "O", "X"], ["X", "O", ""], ["", "O", "X"]]
        self.assertEqual(check_winner(board), "O")

    def test_col_2_winner(self):
        from domain.core.game_logic import check_winner
        board = [["O", "X", "X"], ["", "O", "X"], ["", "", "X"]]
        self.assertEqual(check_winner(board), "X")

    def test_diagonal_top_left_winner(self):
        from domain.core.game_logic import check_winner
        board = [["X", "O", ""], ["O", "X", ""], ["", "", "X"]]
        self.assertEqual(check_winner(board), "X")

    def test_diagonal_top_right_winner(self):
        from domain.core.game_logic import check_winner
        board = [["X", "O", "O"], ["X", "O", ""], ["O", "", "X"]]
        self.assertEqual(check_winner(board), "O")


# ---------------------------------------------------------------------------
# Game logic — is_draw
# ---------------------------------------------------------------------------

class TestIsDraw(unittest.TestCase):

    def test_full_board_is_draw(self):
        from domain.core.game_logic import is_draw
        board = [["X", "O", "X"], ["X", "X", "O"], ["O", "X", "O"]]
        self.assertTrue(is_draw(board))

    def test_partial_board_is_not_draw(self):
        from domain.core.game_logic import is_draw
        board = [["X", "O", "X"], ["X", "X", "O"], ["O", "X", ""]]
        self.assertFalse(is_draw(board))

    def test_empty_board_is_not_draw(self):
        from domain.core.game_logic import is_draw
        board = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.assertFalse(is_draw(board))


# ---------------------------------------------------------------------------
# Game logic — apply_move
# ---------------------------------------------------------------------------

class TestApplyMove(unittest.TestCase):

    def _active_state(self, game_id="g1", board=None, current_player="X"):
        from domain.core.models import GameState
        return GameState(
            game_id=game_id,
            board=board or [["", "", ""], ["", "", ""], ["", "", ""]],
            current_player=current_player,
            status="active",
            winner=None,
        )

    def _move(self, player="X", row=0, col=0, game_id="g1"):
        from domain.core.models import Move
        return Move(game_id=game_id, player=player, row=row, col=col)

    def test_move_places_symbol(self):
        from domain.core.game_logic import apply_move
        new_state = apply_move(self._active_state(), self._move(player="X", row=0, col=0))
        self.assertEqual(new_state.board[0][0], "X")

    def test_turn_switches_after_move(self):
        from domain.core.game_logic import apply_move
        new_state = apply_move(self._active_state(), self._move(player="X", row=0, col=0))
        self.assertEqual(new_state.current_player, "O")

    def test_original_state_unchanged(self):
        """apply_move must not mutate the original board."""
        from domain.core.game_logic import apply_move
        state = self._active_state()
        apply_move(state, self._move(player="X", row=0, col=0))
        self.assertEqual(state.board[0][0], "")

    def test_win_detected(self):
        from domain.core.game_logic import apply_move
        board = [["X", "X", ""], ["O", "O", ""], ["", "", ""]]
        state = self._active_state(board=board, current_player="X")
        new_state = apply_move(state, self._move(player="X", row=0, col=2))
        self.assertEqual(new_state.status, "x_wins")
        self.assertEqual(new_state.winner, "X")

    def test_draw_detected(self):
        from domain.core.game_logic import apply_move
        # One cell left; filling it produces a draw.
        board = [["X", "O", "X"], ["X", "X", "O"], ["O", "X", ""]]
        state = self._active_state(board=board, current_player="O")
        new_state = apply_move(state, self._move(player="O", row=2, col=2))
        self.assertEqual(new_state.status, "draw")
        self.assertIsNone(new_state.winner)

    def test_occupied_cell_raises(self):
        from domain.core.game_logic import apply_move
        board = [["X", "", ""], ["", "", ""], ["", "", ""]]
        state = self._active_state(board=board, current_player="O")
        with self.assertRaises(ValueError):
            apply_move(state, self._move(player="O", row=0, col=0))

    def test_wrong_player_raises(self):
        from domain.core.game_logic import apply_move
        with self.assertRaises(ValueError):
            apply_move(self._active_state(), self._move(player="O", row=0, col=0))

    def test_move_on_finished_game_raises(self):
        from domain.core.models import GameState
        from domain.core.game_logic import apply_move
        state = GameState(
            game_id="g1",
            board=[["X", "X", "X"], ["O", "O", ""], ["", "", ""]],
            current_player="O",
            status="x_wins",
            winner="X",
        )
        with self.assertRaises(ValueError):
            apply_move(state, self._move(player="O", row=2, col=0))

    # --- fixture-driven assertion ---

    def test_x_wins_fixture_canonical(self):
        """Canonical GameState built from x_wins fixture has correct field values."""
        from domain.core.models import GameState
        raw = _load("game_state_x_wins.0.0.1.json")
        # 1. raw fixture contains expected source fields
        self.assertIn("status", raw)
        self.assertIn("winner", raw)
        # 2. canonical model has correct field values
        state = GameState(**raw)
        self.assertEqual(state.status, "x_wins")
        self.assertEqual(state.winner, "X")

    def test_draw_fixture_canonical(self):
        """Canonical GameState built from draw fixture has correct field values."""
        from domain.core.models import GameState
        raw = _load("game_state_draw.0.0.1.json")
        self.assertIn("status", raw)
        self.assertIsNone(raw["winner"])
        state = GameState(**raw)
        self.assertEqual(state.status, "draw")
        self.assertIsNone(state.winner)


if __name__ == "__main__":
    unittest.main()
