"""
Tests for domain/core/ports/in_memory_repository.py (InMemoryGameRepository).

Coverage:
- save + get roundtrip
- get raises KeyError for unknown game_id
- exists returns True / False
- save overwrites an existing entry
"""

import unittest


def _make_state(game_id: str = "g1", current_player: str = "X"):
    from domain.core.models import GameState
    return GameState(
        game_id=game_id,
        board=[["", "", ""], ["", "", ""], ["", "", ""]],
        current_player=current_player,
        status="active",
        winner=None,
    )


class TestInMemoryGameRepository(unittest.TestCase):

    def setUp(self):
        from domain.core.ports.in_memory_repository import InMemoryGameRepository
        self.repo = InMemoryGameRepository()

    def test_save_and_get_roundtrip(self):
        state = _make_state("abc")
        self.repo.save(state)
        retrieved = self.repo.get("abc")
        self.assertEqual(retrieved.game_id, "abc")
        self.assertEqual(retrieved.current_player, "X")
        self.assertEqual(retrieved.status, "active")

    def test_get_unknown_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.repo.get("nonexistent")

    def test_exists_true_after_save(self):
        self.repo.save(_make_state("exists-game"))
        self.assertTrue(self.repo.exists("exists-game"))

    def test_exists_false_before_save(self):
        self.assertFalse(self.repo.exists("not-here"))

    def test_save_overwrites_existing(self):
        from domain.core.models import GameState
        state = _make_state("g1")
        self.repo.save(state)
        updated = GameState(
            game_id="g1",
            board=[["X", "", ""], ["", "", ""], ["", "", ""]],
            current_player="O",
            status="active",
            winner=None,
        )
        self.repo.save(updated)
        retrieved = self.repo.get("g1")
        self.assertEqual(retrieved.current_player, "O")
        self.assertEqual(retrieved.board[0][0], "X")

    def test_multiple_games_independent(self):
        self.repo.save(_make_state("game-1"))
        self.repo.save(_make_state("game-2"))
        self.assertTrue(self.repo.exists("game-1"))
        self.assertTrue(self.repo.exists("game-2"))
        self.assertFalse(self.repo.exists("game-3"))


if __name__ == "__main__":
    unittest.main()
