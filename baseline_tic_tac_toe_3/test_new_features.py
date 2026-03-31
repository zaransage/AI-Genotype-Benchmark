"""Tests for SQLite persistence and web UI."""
import json
import pytest
from fastapi.testclient import TestClient

import main
from main import app, games

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    """Clear in-memory games and use a fresh in-memory SQLite DB for every test."""
    games.clear()
    main._reset_db(":memory:")
    yield
    games.clear()
    main._reset_db(":memory:")


# ── helpers ───────────────────────────────────────────────────────────────────

def new_game():
    r = client.post("/games")
    assert r.status_code == 201
    return r.json()


def move(game_id, position):
    return client.post(f"/games/{game_id}/moves", json={"position": position})


def play(game_id, positions):
    for pos in positions:
        move(game_id, pos)


def x_wins(game_id):
    """Play a sequence that makes X win (row 0)."""
    play(game_id, [0, 3, 1, 4, 2])


# ── web UI ────────────────────────────────────────────────────────────────────

def test_ui_returns_200():
    r = client.get("/")
    assert r.status_code == 200


def test_ui_returns_html():
    r = client.get("/")
    assert "text/html" in r.headers["content-type"]


def test_ui_contains_board():
    r = client.get("/")
    assert "Tic-Tac-Toe" in r.text


# ── completed-games list ──────────────────────────────────────────────────────

def test_completed_games_empty_initially():
    r = client.get("/completed-games")
    assert r.status_code == 200
    assert r.json() == []


def test_completed_game_persisted_after_win():
    g = new_game()
    x_wins(g["id"])
    r = client.get("/completed-games")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["id"] == g["id"]
    assert data[0]["outcome"] == "X_wins"


def test_completed_game_persisted_after_draw():
    g = new_game()
    # X: 0,1,5,6,7  O: 2,3,4,8
    play(g["id"], [0, 2, 1, 3, 5, 4, 6, 8, 7])
    r = client.get("/completed-games")
    data = r.json()
    assert len(data) == 1
    assert data[0]["outcome"] == "draw"


def test_in_progress_game_not_in_completed():
    g = new_game()
    move(g["id"], 0)  # just one move, still in progress
    r = client.get("/completed-games")
    assert r.json() == []


def test_multiple_completed_games():
    for _ in range(3):
        g = new_game()
        x_wins(g["id"])
    r = client.get("/completed-games")
    assert len(r.json()) == 3


# ── completed-game detail ─────────────────────────────────────────────────────

def test_completed_game_detail_not_found():
    r = client.get("/completed-games/nonexistent")
    assert r.status_code == 404


def test_completed_game_detail_has_moves():
    g = new_game()
    x_wins(g["id"])
    r = client.get(f"/completed-games/{g['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == g["id"]
    assert data["outcome"] == "X_wins"
    assert isinstance(data["moves"], list)
    assert len(data["moves"]) == 5  # X plays 0,1,2 and O plays 3,4
    assert data["moves"] == [0, 3, 1, 4, 2]


def test_completed_game_detail_has_board():
    g = new_game()
    x_wins(g["id"])
    r = client.get(f"/completed-games/{g['id']}")
    data = r.json()
    assert isinstance(data["board"], list)
    assert len(data["board"]) == 9
    # X won on row 0
    assert data["board"][0] == "X"
    assert data["board"][1] == "X"
    assert data["board"][2] == "X"


def test_completed_game_detail_has_created_at():
    g = new_game()
    x_wins(g["id"])
    r = client.get(f"/completed-games/{g['id']}")
    data = r.json()
    assert "created_at" in data
    assert data["created_at"]  # non-empty string


def test_completed_game_o_wins():
    g = new_game()
    # X: 0,1,3  O: 2,5,8
    play(g["id"], [0, 2, 1, 5, 3, 8])
    r = client.get(f"/completed-games/{g['id']}")
    assert r.status_code == 200
    assert r.json()["outcome"] == "O_wins"


def test_completed_game_detail_summary_fields():
    g = new_game()
    x_wins(g["id"])
    summary = client.get("/completed-games").json()[0]
    assert set(summary.keys()) == {"id", "outcome", "created_at"}


def test_completed_games_ordered_most_recent_first():
    ids = []
    for _ in range(3):
        g = new_game()
        x_wins(g["id"])
        ids.append(g["id"])
    data = client.get("/completed-games").json()
    returned_ids = [d["id"] for d in data]
    # Most recent last-inserted should appear first (DESC order)
    assert returned_ids[0] == ids[-1]
