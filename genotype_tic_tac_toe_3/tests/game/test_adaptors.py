"""
tests/game/test_adaptors.py

Unit tests for RestGameController (inbound adaptor) and API schema translation.
Per AI_CONTRACT.md §6: assert (1) raw fixture source fields, (2) canonical model fields after conversion.
Per AI_CONTRACT.md: tests first, unittest only, never removed.
"""

import json
import pathlib
import unittest
from unittest.mock import MagicMock

FIXTURES_RAW      = pathlib.Path(__file__).parents[2] / "fixtures" / "raw"      / "game" / "v1"
FIXTURES_EXPECTED = pathlib.Path(__file__).parents[2] / "fixtures" / "expected" / "game" / "v1"


class TestRestGameController(unittest.TestCase):
    """Inbound adaptor: RestGameController wires service + repository."""

    def _make_controller(self):
        from domain.game.core.game_service import GameService
        from domain.game.core.ports.in_memory_repository import InMemoryGameRepository
        from domain.game.core.adaptors.rest_controller import RestGameController
        return RestGameController(service=GameService(), repository=InMemoryGameRepository())

    def test_create_game_returns_gamestate(self):
        from domain.game.core.models import GameState
        ctrl = self._make_controller()
        state = ctrl.create_game()
        self.assertIsInstance(state, GameState)
        self.assertEqual(state.status, "in_progress")
        self.assertEqual(state.current_player, "X")

    def test_create_game_persists_state(self):
        ctrl = self._make_controller()
        state = ctrl.create_game()
        fetched = ctrl.get_game(state.game_id)
        self.assertEqual(fetched.game_id, state.game_id)

    def test_get_game_raises_key_error_for_unknown_id(self):
        ctrl = self._make_controller()
        with self.assertRaises(KeyError):
            ctrl.get_game("does-not-exist")

    def test_make_move_raises_key_error_for_unknown_game(self):
        from domain.game.core.models import Move
        ctrl = self._make_controller()
        with self.assertRaises(KeyError):
            ctrl.make_move("no-such-game", Move(player="X", row=0, col=0))

    def test_make_move_updates_board(self):
        from domain.game.core.models import Move
        ctrl = self._make_controller()
        state = ctrl.create_game()
        new_state = ctrl.make_move(state.game_id, Move(player="X", row=1, col=1))
        self.assertEqual(new_state.board[1][1], "X")
        self.assertEqual(new_state.current_player, "O")

    def test_make_move_win_detection(self):
        from domain.game.core.models import Move
        ctrl = self._make_controller()
        gid = ctrl.create_game().game_id

        # X: (0,0), O: (1,0), X: (0,1), O: (1,1), X: (0,2) → X wins
        ctrl.make_move(gid, Move(player="X", row=0, col=0))
        ctrl.make_move(gid, Move(player="O", row=1, col=0))
        ctrl.make_move(gid, Move(player="X", row=0, col=1))
        ctrl.make_move(gid, Move(player="O", row=1, col=1))
        result = ctrl.make_move(gid, Move(player="X", row=0, col=2))

        self.assertEqual(result.status, "x_wins")
        self.assertEqual(result.winner, "X")

    def test_controller_implements_interface(self):
        from domain.game.core.adaptors.i_game_controller import IGameController
        from domain.game.core.adaptors.rest_controller import RestGameController
        self.assertTrue(issubclass(RestGameController, IGameController))


class TestApiSchemaTranslation(unittest.TestCase):
    """
    Translation tests: raw fixture → Pydantic schema → canonical dataclass.
    ADR 0003 / AI_CONTRACT §6.
    """

    def test_raw_make_move_fixture_has_required_fields(self):
        """Assert raw fixture contains expected source fields (contract check #1)."""
        raw = json.loads((FIXTURES_RAW / "make_move.0.0.1.json").read_text())
        self.assertIn("player", raw)
        self.assertIn("row",    raw)
        self.assertIn("col",    raw)

    def test_move_request_schema_maps_to_canonical_move(self):
        """Assert canonical dataclass has correct field values after schema conversion (contract check #2)."""
        from domain.game.core.adaptors.api_schemas import MoveRequest
        from domain.game.core.models import Move

        raw = json.loads((FIXTURES_RAW / "make_move.0.0.1.json").read_text())

        # 1. Raw fixture source fields
        self.assertEqual(raw["player"], "X")
        self.assertEqual(raw["row"],    0)
        self.assertEqual(raw["col"],    0)

        # 2. Canonical model after conversion
        schema = MoveRequest(**raw)
        move = schema.to_canonical()
        self.assertIsInstance(move, Move)
        self.assertEqual(move.player, "X")
        self.assertEqual(move.row,    0)
        self.assertEqual(move.col,    0)

    def test_expected_game_state_fixture_has_required_fields(self):
        """Assert expected fixture contains all canonical model fields."""
        expected = json.loads((FIXTURES_EXPECTED / "game_state.0.0.1.json").read_text())
        self.assertIn("game_id",        expected)
        self.assertIn("board",          expected)
        self.assertIn("current_player", expected)
        self.assertIn("status",         expected)
        self.assertIn("winner",         expected)

    def test_game_state_response_schema_from_canonical(self):
        """Assert GameStateResponse serialises canonical model correctly."""
        from domain.game.core.adaptors.api_schemas import GameStateResponse
        from domain.game.core.models import GameState

        expected = json.loads((FIXTURES_EXPECTED / "game_state.0.0.1.json").read_text())

        state = GameState(
            game_id        = expected["game_id"],
            board          = expected["board"],
            current_player = expected["current_player"],
            status         = expected["status"],
            winner         = expected["winner"],
        )
        response = GameStateResponse.from_canonical(state)
        self.assertEqual(response.game_id,        state.game_id)
        self.assertEqual(response.board,          state.board)
        self.assertEqual(response.current_player, state.current_player)
        self.assertEqual(response.status,         state.status)
        self.assertIsNone(response.winner)

    def test_raw_create_game_fixture_is_empty_object(self):
        """create_game takes no body — fixture is an empty object."""
        raw = json.loads((FIXTURES_RAW / "create_game.0.0.1.json").read_text())
        self.assertIsInstance(raw, dict)
        self.assertEqual(len(raw), 0)


if __name__ == "__main__":
    unittest.main()
