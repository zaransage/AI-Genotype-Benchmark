"""
tests/game/test_ports.py

Unit tests for InMemoryGameRepository (outbound port implementation).
Per AI_CONTRACT.md: tests first, unittest only, never removed.
"""

import unittest


class TestInMemoryGameRepository(unittest.TestCase):
    """Tests for the outbound persistence port."""

    def _make_repo(self):
        from domain.game.core.ports.in_memory_repository import InMemoryGameRepository
        return InMemoryGameRepository()

    def _make_state(self, game_id="test-id"):
        from domain.game.core.models import GameState
        return GameState(
            game_id=game_id,
            board=[["", "", ""], ["", "", ""], ["", "", ""]],
            current_player="X",
            status="in_progress",
            winner=None,
        )

    def test_find_by_id_returns_none_for_unknown_game(self):
        repo = self._make_repo()
        result = repo.find_by_id("does-not-exist")
        self.assertIsNone(result)

    def test_save_and_find_by_id(self):
        repo = self._make_repo()
        state = self._make_state("abc")
        repo.save(state)
        found = repo.find_by_id("abc")
        self.assertIsNotNone(found)
        self.assertEqual(found.game_id, "abc")

    def test_save_overwrites_existing_game(self):
        repo = self._make_repo()
        from domain.game.core.models import GameState
        original = self._make_state("g1")
        repo.save(original)

        updated = GameState(
            game_id="g1",
            board=[["X", "", ""], ["", "", ""], ["", "", ""]],
            current_player="O",
            status="in_progress",
            winner=None,
        )
        repo.save(updated)

        found = repo.find_by_id("g1")
        self.assertEqual(found.board[0][0], "X")
        self.assertEqual(found.current_player, "O")

    def test_multiple_games_are_isolated(self):
        repo = self._make_repo()
        s1 = self._make_state("game-1")
        s2 = self._make_state("game-2")
        repo.save(s1)
        repo.save(s2)
        self.assertEqual(repo.find_by_id("game-1").game_id, "game-1")
        self.assertEqual(repo.find_by_id("game-2").game_id, "game-2")

    def test_repository_implements_interface(self):
        from domain.game.core.ports.i_game_repository import IGameRepository
        from domain.game.core.ports.in_memory_repository import InMemoryGameRepository
        self.assertTrue(issubclass(InMemoryGameRepository, IGameRepository))


if __name__ == "__main__":
    unittest.main()
