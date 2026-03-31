import pytest
from fastapi.testclient import TestClient

from game import Game, GameError, games
from main import app

client = TestClient(app)


# --- Unit tests for Game logic ---

def test_initial_state():
    g = Game()
    assert g.board == [None] * 9
    assert g.current_player == "X"
    assert g.status == "in_progress"
    assert g.winner is None


def test_valid_move_alternates_player():
    g = Game()
    g.make_move("X", 0)
    assert g.board[0] == "X"
    assert g.current_player == "O"


def test_wrong_player_raises():
    g = Game()
    with pytest.raises(GameError, match="X's turn"):
        g.make_move("O", 0)


def test_occupied_position_raises():
    g = Game()
    g.make_move("X", 4)
    g.make_move("O", 0)
    with pytest.raises(GameError, match="already taken"):
        g.make_move("X", 4)


def test_invalid_position_raises():
    g = Game()
    with pytest.raises(GameError, match="between 0 and 8"):
        g.make_move("X", 9)


def test_win_detection_row():
    g = Game()
    # X wins top row: 0,1,2
    moves = [("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)]
    for player, pos in moves:
        g.make_move(player, pos)
    assert g.status == "won"
    assert g.winner == "X"


def test_win_detection_column():
    g = Game()
    moves = [("X", 0), ("O", 1), ("X", 3), ("O", 2), ("X", 6)]
    for player, pos in moves:
        g.make_move(player, pos)
    assert g.status == "won"
    assert g.winner == "X"


def test_win_detection_diagonal():
    g = Game()
    moves = [("X", 0), ("O", 1), ("X", 4), ("O", 2), ("X", 8)]
    for player, pos in moves:
        g.make_move(player, pos)
    assert g.status == "won"
    assert g.winner == "X"


def test_draw_detection():
    g = Game()
    # X O X
    # X X O
    # O X O
    moves = [
        ("X", 0), ("O", 1), ("X", 2),
        ("O", 5), ("X", 3), ("O", 6),
        ("X", 4), ("O", 8), ("X", 7),
    ]
    for player, pos in moves:
        g.make_move(player, pos)
    assert g.status == "draw"
    assert g.winner is None


def test_move_after_game_over_raises():
    g = Game()
    moves = [("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)]
    for player, pos in moves:
        g.make_move(player, pos)
    with pytest.raises(GameError, match="already over"):
        g.make_move("O", 5)


def test_o_wins():
    g = Game()
    # O wins diagonal 2,4,6
    moves = [("X", 0), ("O", 2), ("X", 1), ("O", 4), ("X", 3), ("O", 6)]
    for player, pos in moves:
        g.make_move(player, pos)
    assert g.status == "won"
    assert g.winner == "O"


# --- API integration tests ---

def _new_game():
    resp = client.post("/games")
    assert resp.status_code == 201
    return resp.json()


def test_api_create_game():
    data = _new_game()
    assert "id" in data
    assert data["status"] == "in_progress"
    assert data["board"] == [None] * 9


def test_api_get_game():
    game = _new_game()
    resp = client.get(f"/games/{game['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == game["id"]


def test_api_get_nonexistent_game():
    resp = client.get("/games/does-not-exist")
    assert resp.status_code == 404


def test_api_make_move():
    game = _new_game()
    resp = client.post(f"/games/{game['id']}/moves", json={"player": "X", "position": 0})
    assert resp.status_code == 200
    data = resp.json()
    assert data["board"][0] == "X"
    assert data["current_player"] == "O"


def test_api_invalid_player():
    game = _new_game()
    resp = client.post(f"/games/{game['id']}/moves", json={"player": "Z", "position": 0})
    assert resp.status_code == 422


def test_api_position_out_of_range():
    game = _new_game()
    resp = client.post(f"/games/{game['id']}/moves", json={"player": "X", "position": 9})
    assert resp.status_code == 422


def test_api_wrong_turn():
    game = _new_game()
    resp = client.post(f"/games/{game['id']}/moves", json={"player": "O", "position": 0})
    assert resp.status_code == 400


def test_api_full_game_x_wins():
    game = _new_game()
    gid = game["id"]
    moves = [("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)]
    for player, pos in moves:
        client.post(f"/games/{gid}/moves", json={"player": player, "position": pos})
    resp = client.get(f"/games/{gid}")
    data = resp.json()
    assert data["status"] == "won"
    assert data["winner"] == "X"


def test_api_move_on_nonexistent_game():
    resp = client.post("/games/no-such-game/moves", json={"player": "X", "position": 0})
    assert resp.status_code == 404
