import pytest
from fastapi.testclient import TestClient

from main import app, games

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_games():
    games.clear()
    yield
    games.clear()


def create_game():
    response = client.post("/games")
    assert response.status_code == 201
    return response.json()


def move(game_id, player, position):
    return client.post(f"/games/{game_id}/moves", json={"player": player, "position": position})


# --- create game ---

def test_create_game_returns_empty_board():
    data = create_game()
    assert data["board"] == [None] * 9
    assert data["status"] == "in_progress"
    assert data["current_player"] == "X"
    assert "id" in data


def test_create_game_unique_ids():
    id1 = create_game()["id"]
    id2 = create_game()["id"]
    assert id1 != id2


# --- get game ---

def test_get_game():
    game = create_game()
    response = client.get(f"/games/{game['id']}")
    assert response.status_code == 200
    assert response.json() == game


def test_get_game_not_found():
    response = client.get("/games/nonexistent")
    assert response.status_code == 404


# --- make move ---

def test_make_move_updates_board():
    game = create_game()
    gid = game["id"]
    response = move(gid, "X", 0)
    assert response.status_code == 200
    data = response.json()
    assert data["board"][0] == "X"
    assert data["current_player"] == "O"
    assert data["status"] == "in_progress"


def test_make_move_alternates_players():
    gid = create_game()["id"]
    move(gid, "X", 0)
    response = move(gid, "O", 1)
    assert response.status_code == 200
    assert response.json()["current_player"] == "X"


def test_make_move_wrong_player():
    gid = create_game()["id"]
    response = move(gid, "O", 0)
    assert response.status_code == 400


def test_make_move_invalid_player():
    gid = create_game()["id"]
    response = move(gid, "Z", 0)
    assert response.status_code == 400


def test_make_move_position_taken():
    gid = create_game()["id"]
    move(gid, "X", 4)
    response = move(gid, "O", 4)
    assert response.status_code == 400


def test_make_move_position_out_of_range():
    gid = create_game()["id"]
    response = move(gid, "X", 9)
    assert response.status_code == 400


def test_make_move_game_not_found():
    response = move("nonexistent", "X", 0)
    assert response.status_code == 404


# --- win/loss/draw ---

def _play_sequence(moves):
    gid = create_game()["id"]
    for player, pos in moves:
        response = move(gid, player, pos)
    return response.json()


def test_x_wins_row():
    # X: 0,1,2  O: 3,4
    data = _play_sequence([("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)])
    assert data["status"] == "X_wins"
    assert data["current_player"] is None


def test_o_wins_column():
    # O wins col 0: positions 0,3,6
    data = _play_sequence([("X", 1), ("O", 0), ("X", 2), ("O", 3), ("X", 8), ("O", 6)])
    assert data["status"] == "O_wins"
    assert data["current_player"] is None


def test_x_wins_diagonal():
    # X: 0,4,8  O: 1,2
    data = _play_sequence([("X", 0), ("O", 1), ("X", 4), ("O", 2), ("X", 8)])
    assert data["status"] == "X_wins"


def test_draw():
    # Board: X O X / O X X / O X O  => draw
    data = _play_sequence([
        ("X", 0), ("O", 1), ("X", 2),
        ("O", 4), ("X", 3), ("O", 5),
        ("X", 7), ("O", 6), ("X", 8),
    ])
    assert data["status"] == "draw"
    assert data["current_player"] is None


def test_move_after_game_over():
    gid = create_game()["id"]
    move(gid, "X", 0)
    move(gid, "O", 3)
    move(gid, "X", 1)
    move(gid, "O", 4)
    move(gid, "X", 2)  # X wins
    response = move(gid, "O", 5)
    assert response.status_code == 400
