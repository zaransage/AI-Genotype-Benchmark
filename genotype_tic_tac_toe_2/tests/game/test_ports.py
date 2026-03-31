"""
Tests for the outbound port: IGameRepository and InMemoryGameRepository.

Per AI_CONTRACT.md §5: one test file per layer within each use case.
"""
import unittest

from domain.game.game import GameState


class TestInMemoryGameRepository(unittest.TestCase):
    """InMemoryGameRepository — save, get, overwrite, and missing-key behaviour."""

    def _make_repo(self):
        from domain.game.ports.in_memory_repository import InMemoryGameRepository
        return InMemoryGameRepository()

    def test_save_and_retrieve(self) -> None:
        repo = self._make_repo()
        state = GameState(game_id="test-id-1")
        repo.save(state)
        retrieved = repo.get("test-id-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.game_id, "test-id-1")

    def test_retrieve_nonexistent_returns_none(self) -> None:
        repo = self._make_repo()
        result = repo.get("ghost-id")
        self.assertIsNone(result)

    def test_save_overwrites_existing(self) -> None:
        repo = self._make_repo()
        original = GameState(game_id="game-1")
        repo.save(original)
        updated = GameState(
            game_id="game-1",
            board=["X"] + [""] * 8,
            current_player="O",
            status="in_progress",
        )
        repo.save(updated)
        retrieved = repo.get("game-1")
        self.assertEqual(retrieved.board[0], "X")
        self.assertEqual(retrieved.current_player, "O")

    def test_multiple_games_stored_independently(self) -> None:
        repo = self._make_repo()
        a = GameState(game_id="game-a")
        b = GameState(game_id="game-b")
        repo.save(a)
        repo.save(b)
        self.assertEqual(repo.get("game-a").game_id, "game-a")
        self.assertEqual(repo.get("game-b").game_id, "game-b")

    def test_implements_interface(self) -> None:
        """InMemoryGameRepository satisfies the IGameRepository contract."""
        from domain.game.ports.i_game_repository import IGameRepository
        from domain.game.ports.in_memory_repository import InMemoryGameRepository
        self.assertTrue(issubclass(InMemoryGameRepository, IGameRepository))


if __name__ == "__main__":
    unittest.main()
