import pytest
from fastapi.testclient import TestClient

import database
from main import app, game_moves, games

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Each test gets its own fresh SQLite file and empty in-memory state."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    games.clear()
    game_moves.clear()
    yield
    games.clear()
    game_moves.clear()


def create_game():
    resp = client.post("/games")
    assert resp.status_code == 201
    return resp.json()


def move(game_id, player, position):
    return client.post(
        f"/games/{game_id}/moves",
        json={"player": player, "position": position},
    )


def play_sequence(moves_list):
    gid = create_game()["id"]
    resp = None
    for player, pos in moves_list:
        resp = move(gid, player, pos)
    return gid, resp.json()


# ── Web UI ──────────────────────────────────────────────────────────────────


def test_ui_returns_200():
    resp = client.get("/")
    assert resp.status_code == 200


def test_ui_content_type_is_html():
    resp = client.get("/")
    assert "text/html" in resp.headers["content-type"]


def test_ui_contains_board():
    resp = client.get("/")
    assert "board" in resp.text.lower()


# ── /games/history ──────────────────────────────────────────────────────────


def test_history_empty_at_start():
    resp = client.get("/games/history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_history_not_updated_during_game():
    gid = create_game()["id"]
    move(gid, "X", 0)
    move(gid, "O", 1)
    resp = client.get("/games/history")
    assert resp.json() == []


def test_history_saved_after_x_wins():
    gid, final = play_sequence(
        [("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)]
    )
    assert final["status"] == "X_wins"
    resp = client.get("/games/history")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == gid
    assert data[0]["status"] == "X_wins"


def test_history_saved_after_o_wins():
    gid, final = play_sequence(
        [("X", 1), ("O", 0), ("X", 2), ("O", 3), ("X", 8), ("O", 6)]
    )
    assert final["status"] == "O_wins"
    resp = client.get("/games/history")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "O_wins"


def test_history_saved_after_draw():
    # X O X / O X X / O X O
    gid, final = play_sequence([
        ("X", 0), ("O", 1), ("X", 2),
        ("O", 4), ("X", 3), ("O", 5),
        ("X", 7), ("O", 6), ("X", 8),
    ])
    assert final["status"] == "draw"
    resp = client.get("/games/history")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "draw"


def test_history_contains_all_completed_games():
    play_sequence([("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)])
    play_sequence([("X", 1), ("O", 0), ("X", 2), ("O", 3), ("X", 8), ("O", 6)])
    resp = client.get("/games/history")
    assert len(resp.json()) == 2


def test_history_board_persisted_correctly():
    gid, _ = play_sequence(
        [("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)]
    )
    data = client.get("/games/history").json()
    record = next(r for r in data if r["id"] == gid)
    assert record["board"][0] == "X"
    assert record["board"][1] == "X"
    assert record["board"][2] == "X"
    assert record["board"][3] == "O"
    assert record["board"][4] == "O"


def test_history_move_sequence_persisted():
    gid, _ = play_sequence(
        [("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)]
    )
    data = client.get("/games/history").json()
    record = next(r for r in data if r["id"] == gid)
    assert len(record["moves"]) == 5
    assert record["moves"][0] == {"player": "X", "position": 0}
    assert record["moves"][1] == {"player": "O", "position": 3}
    assert record["moves"][4] == {"player": "X", "position": 2}


def test_history_has_created_at_field():
    play_sequence([("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)])
    data = client.get("/games/history").json()
    assert "created_at" in data[0]
    assert data[0]["created_at"] is not None


# ── history does not interfere with active-game lookup ──────────────────────


def test_history_route_not_matched_as_game_id():
    """GET /games/history must not return a 404 'game not found' error."""
    resp = client.get("/games/history")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
