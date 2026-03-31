"""
Tests for the game domain core: GameState canonical model and GameService business logic.

Per AI_CONTRACT.md §1: tests are written before implementation.
Per AI_CONTRACT.md §6: assertions cover model field values and canonical-model correctness.
"""
import json
import pathlib
import unittest

FIXTURE_EXPECTED = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "expected" / "game" / "v1"


class TestGameStateModel(unittest.TestCase):
    """GameState @dataclass — construction, validation, and __post_init__ guards."""

    def test_initial_state_from_fixture(self) -> None:
        """Raw fixture has the fields the canonical model expects."""
        raw = json.loads((FIXTURE_EXPECTED / "game_state_initial.0.0.1.json").read_text())
        self.assertIn("game_id", raw)
        self.assertIn("board", raw)
        self.assertIn("current_player", raw)
        self.assertIn("status", raw)
        self.assertIn("winner", raw)
        self.assertEqual(len(raw["board"]), 9)

    def test_win_fixture_shape(self) -> None:
        """Win fixture has correct status and winner fields."""
        raw = json.loads((FIXTURE_EXPECTED / "game_state_win.0.0.1.json").read_text())
        self.assertEqual(raw["status"], "x_wins")
        self.assertEqual(raw["winner"], "X")
        self.assertEqual(raw["board"][0], "X")
        self.assertEqual(raw["board"][1], "X")
        self.assertEqual(raw["board"][2], "X")

    def test_draw_fixture_shape(self) -> None:
        """Draw fixture has all cells filled and no winner."""
        raw = json.loads((FIXTURE_EXPECTED / "game_state_draw.0.0.1.json").read_text())
        self.assertEqual(raw["status"], "draw")
        self.assertIsNone(raw["winner"])
        self.assertTrue(all(cell != "" for cell in raw["board"]))

    def test_construct_valid_state(self) -> None:
        """GameState constructs successfully with valid inputs."""
        from domain.game.game import GameState
        state = GameState(game_id="abc-123")
        self.assertEqual(state.game_id, "abc-123")
        self.assertEqual(state.board, [""] * 9)
        self.assertEqual(state.current_player, "X")
        self.assertEqual(state.status, "in_progress")
        self.assertIsNone(state.winner)

    def test_empty_game_id_raises(self) -> None:
        """GameState rejects empty game_id at construction time."""
        from domain.game.game import GameState
        with self.assertRaises(ValueError):
            GameState(game_id="")

    def test_board_wrong_length_raises(self) -> None:
        """GameState rejects a board that is not exactly 9 cells."""
        from domain.game.game import GameState
        with self.assertRaises(ValueError):
            GameState(game_id="x", board=["X"] * 8)

    def test_invalid_cell_value_raises(self) -> None:
        """GameState rejects unknown cell values."""
        from domain.game.game import GameState
        with self.assertRaises(ValueError):
            GameState(game_id="x", board=["Z"] + [""] * 8)

    def test_invalid_current_player_raises(self) -> None:
        """GameState rejects a current_player value that is not X or O."""
        from domain.game.game import GameState
        with self.assertRaises(ValueError):
            GameState(game_id="x", current_player="A")


class TestGameService(unittest.TestCase):
    """GameService — create_game, make_move, get_game, and outcome detection."""

    def _make_service(self):
        from domain.game.ports.in_memory_repository import InMemoryGameRepository
        from domain.game.game_service import GameService
        return GameService(repository=InMemoryGameRepository())

    def test_create_game_returns_in_progress_state(self) -> None:
        service = self._make_service()
        state = service.create_game()
        self.assertEqual(state.status, "in_progress")
        self.assertEqual(state.board, [""] * 9)
        self.assertEqual(state.current_player, "X")

    def test_create_game_generates_unique_ids(self) -> None:
        service = self._make_service()
        ids = {service.create_game().game_id for _ in range(10)}
        self.assertEqual(len(ids), 10)

    def test_make_move_places_x(self) -> None:
        service = self._make_service()
        state = service.create_game()
        updated = service.make_move(state.game_id, 4)
        self.assertEqual(updated.board[4], "X")

    def test_make_move_switches_player(self) -> None:
        service = self._make_service()
        state = service.create_game()
        after_x = service.make_move(state.game_id, 0)
        self.assertEqual(after_x.current_player, "O")

    def test_make_move_alternates_players(self) -> None:
        service = self._make_service()
        state = service.create_game()
        after_x = service.make_move(state.game_id, 0)
        after_o = service.make_move(state.game_id, 1)
        self.assertEqual(after_o.board[0], "X")
        self.assertEqual(after_o.board[1], "O")

    def test_detect_row_win(self) -> None:
        """X wins by filling the top row."""
        service = self._make_service()
        state = service.create_game()
        gid = state.game_id
        service.make_move(gid, 0)  # X
        service.make_move(gid, 3)  # O
        service.make_move(gid, 1)  # X
        service.make_move(gid, 4)  # O
        final = service.make_move(gid, 2)  # X wins row 0
        self.assertEqual(final.status, "x_wins")
        self.assertEqual(final.winner, "X")

    def test_detect_column_win(self) -> None:
        """O wins by filling the right column."""
        service = self._make_service()
        state = service.create_game()
        gid = state.game_id
        service.make_move(gid, 0)  # X
        service.make_move(gid, 2)  # O
        service.make_move(gid, 1)  # X
        service.make_move(gid, 5)  # O
        service.make_move(gid, 4)  # X
        final = service.make_move(gid, 8)  # O wins col 2
        self.assertEqual(final.status, "o_wins")
        self.assertEqual(final.winner, "O")

    def test_detect_diagonal_win(self) -> None:
        """X wins along the main diagonal (0,4,8)."""
        service = self._make_service()
        state = service.create_game()
        gid = state.game_id
        service.make_move(gid, 0)  # X
        service.make_move(gid, 1)  # O
        service.make_move(gid, 4)  # X
        service.make_move(gid, 2)  # O
        final = service.make_move(gid, 8)  # X wins diagonal
        self.assertEqual(final.status, "x_wins")
        self.assertEqual(final.winner, "X")

    def test_detect_draw(self) -> None:
        """All cells filled with no winner produces a draw."""
        service = self._make_service()
        state = service.create_game()
        gid = state.game_id
        # Board sequence yields draw: X O X / O X X / O X O
        for pos in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            # Moves: X->0, O->1, X->2, O->3, X->4, O->6... need careful ordering
            pass
        # Known draw sequence: X→0 O→1 X→2 O→4 X→3 O→6 X→5 O→8 X→7
        service2 = self._make_service()
        s2 = service2.create_game()
        g2 = s2.game_id
        service2.make_move(g2, 0)  # X
        service2.make_move(g2, 1)  # O
        service2.make_move(g2, 2)  # X
        service2.make_move(g2, 4)  # O
        service2.make_move(g2, 3)  # X
        service2.make_move(g2, 6)  # O
        service2.make_move(g2, 5)  # X
        service2.make_move(g2, 8)  # O
        final = service2.make_move(g2, 7)  # X — last cell, draw
        self.assertEqual(final.status, "draw")
        self.assertIsNone(final.winner)

    def test_move_out_of_range_raises(self) -> None:
        service = self._make_service()
        state = service.create_game()
        with self.assertRaises(ValueError):
            service.make_move(state.game_id, 9)

    def test_move_occupied_cell_raises(self) -> None:
        service = self._make_service()
        state = service.create_game()
        service.make_move(state.game_id, 0)
        with self.assertRaises(ValueError):
            service.make_move(state.game_id, 0)

    def test_move_on_finished_game_raises(self) -> None:
        service = self._make_service()
        state = service.create_game()
        gid = state.game_id
        service.make_move(gid, 0)
        service.make_move(gid, 3)
        service.make_move(gid, 1)
        service.make_move(gid, 4)
        service.make_move(gid, 2)  # X wins
        with self.assertRaises(ValueError):
            service.make_move(gid, 5)

    def test_get_game_returns_current_state(self) -> None:
        service = self._make_service()
        state = service.create_game()
        service.make_move(state.game_id, 0)
        retrieved = service.get_game(state.game_id)
        self.assertEqual(retrieved.board[0], "X")

    def test_get_nonexistent_game_raises(self) -> None:
        service = self._make_service()
        with self.assertRaises(ValueError):
            service.get_game("no-such-id")


if __name__ == "__main__":
    unittest.main()
