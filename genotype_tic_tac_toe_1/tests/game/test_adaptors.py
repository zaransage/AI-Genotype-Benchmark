"""
Tests for domain/core/adaptors/game_service.py (GameService).

Coverage:
- create_game returns a valid initial GameState
- get_game delegates to repository.get
- make_move applies the move and persists the new state
- make_move propagates KeyError from repository on unknown game_id
- make_move propagates ValueError from game_logic on illegal move

Repository is mocked to isolate GameService from InMemoryGameRepository.
"""

import json
import pathlib
import unittest
from unittest.mock import MagicMock

FIXTURE_EXPECTED = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "expected" / "game" / "v1"


def _load(name: str) -> dict:
    with open(FIXTURE_EXPECTED / name) as fh:
        return json.load(fh)


def _make_state(game_id: str = "g1", current_player: str = "X", status: str = "active"):
    from domain.core.models import GameState
    return GameState(
        game_id=game_id,
        board=[["", "", ""], ["", "", ""], ["", "", ""]],
        current_player=current_player,
        status=status,
        winner=None,
    )


class TestGameService(unittest.TestCase):

    def setUp(self):
        from domain.core.adaptors.game_service import GameService
        self.mock_repo = MagicMock()
        self.service = GameService(self.mock_repo)

    # --- create_game ---

    def test_create_game_returns_active_state(self):
        self.mock_repo.save = MagicMock()
        state = self.service.create_game()
        self.assertEqual(state.status,         "active")
        self.assertEqual(state.current_player, "X")
        self.assertIsNone(state.winner)
        self.assertEqual(len(state.board), 3)

    def test_create_game_board_all_empty(self):
        self.mock_repo.save = MagicMock()
        state = self.service.create_game()
        for row in state.board:
            for cell in row:
                self.assertEqual(cell, "")

    def test_create_game_saves_to_repository(self):
        self.mock_repo.save = MagicMock()
        state = self.service.create_game()
        self.mock_repo.save.assert_called_once_with(state)

    def test_create_game_unique_ids(self):
        """Two successive create_game calls must produce different game_ids."""
        self.mock_repo.save = MagicMock()
        a = self.service.create_game()
        b = self.service.create_game()
        self.assertNotEqual(a.game_id, b.game_id)

    # --- get_game ---

    def test_get_game_delegates_to_repository(self):
        stored = _make_state("g99")
        self.mock_repo.get.return_value = stored
        result = self.service.get_game("g99")
        self.mock_repo.get.assert_called_once_with("g99")
        self.assertEqual(result.game_id, "g99")

    def test_get_game_propagates_key_error(self):
        self.mock_repo.get.side_effect = KeyError("g99")
        with self.assertRaises(KeyError):
            self.service.get_game("g99")

    # --- make_move ---

    def test_make_move_applies_and_persists(self):
        from domain.core.models import Move
        stored = _make_state("g1", current_player="X")
        self.mock_repo.get.return_value = stored
        self.mock_repo.save = MagicMock()
        move = Move(game_id="g1", player="X", row=0, col=0)
        result = self.service.make_move(move)
        self.assertEqual(result.board[0][0],  "X")
        self.assertEqual(result.current_player, "O")
        self.mock_repo.save.assert_called_once_with(result)

    def test_make_move_propagates_key_error(self):
        from domain.core.models import Move
        self.mock_repo.get.side_effect = KeyError("g1")
        move = Move(game_id="g1", player="X", row=0, col=0)
        with self.assertRaises(KeyError):
            self.service.make_move(move)

    def test_make_move_propagates_value_error_wrong_player(self):
        from domain.core.models import Move
        stored = _make_state("g1", current_player="X")
        self.mock_repo.get.return_value = stored
        move = Move(game_id="g1", player="O", row=0, col=0)  # wrong turn
        with self.assertRaises(ValueError):
            self.service.make_move(move)

    # --- fixture-driven: raw fixture → canonical model translation ---

    def test_fixture_after_move_raw_fields(self):
        """game_state_after_move fixture contains expected source fields."""
        raw = _load("game_state_after_move.0.0.1.json")
        self.assertIn("game_id",        raw)
        self.assertIn("board",          raw)
        self.assertIn("current_player", raw)
        self.assertIn("status",         raw)
        self.assertIn("winner",         raw)

    def test_fixture_after_move_canonical_values(self):
        """Canonical GameState from after_move fixture reflects X's centre move."""
        from domain.core.models import GameState
        raw = _load("game_state_after_move.0.0.1.json")
        state = GameState(**raw)
        self.assertEqual(state.board[1][1],   "X")
        self.assertEqual(state.current_player, "O")
        self.assertEqual(state.status,         "active")
        self.assertIsNone(state.winner)

    # --- serialized response shape ---

    def test_create_game_response_shape(self):
        """GameState returned by create_game maps cleanly to expected response keys."""
        self.mock_repo.save = MagicMock()
        state = self.service.create_game()
        response = {
            "game_id":        state.game_id,
            "board":          state.board,
            "current_player": state.current_player,
            "status":         state.status,
            "winner":         state.winner,
        }
        for key in ("game_id", "board", "current_player", "status", "winner"):
            self.assertIn(key, response)
        self.assertEqual(response["status"], "active")


if __name__ == "__main__":
    unittest.main()
