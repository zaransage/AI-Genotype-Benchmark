"""Tests for the web UI, SQLite persistence, and completed-games endpoints."""
import pytest
from fastapi.testclient import TestClient

import db as db_module
from main import app


# ---------------------------------------------------------------------------
# Fixture: isolated DB per test + a fresh TestClient that triggers lifespan
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_game(client):
    resp = client.post("/games")
    assert resp.status_code == 201
    return resp.json()


def _play_x_wins(client, gid):
    """X wins top row: positions 0, 1, 2  (O plays 3, 4)."""
    moves = [("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)]
    for player, pos in moves:
        client.post(f"/games/{gid}/moves", json={"player": player, "position": pos})


def _play_draw(client, gid):
    # X O X / X X O / O X O
    moves = [
        ("X", 0), ("O", 1), ("X", 2),
        ("O", 5), ("X", 3), ("O", 6),
        ("X", 4), ("O", 8), ("X", 7),
    ]
    for player, pos in moves:
        client.post(f"/games/{gid}/moves", json={"player": player, "position": pos})


# ---------------------------------------------------------------------------
# Web UI
# ---------------------------------------------------------------------------

def test_ui_returns_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "<html" in resp.text.lower()
    assert "Tic-Tac-Toe" in resp.text


def test_ui_contains_board_element(client):
    resp = client.get("/")
    assert "id=\"board\"" in resp.text


def test_ui_contains_new_game_button(client):
    resp = client.get("/")
    assert "newGame" in resp.text or "new-btn" in resp.text


# ---------------------------------------------------------------------------
# Move history on in-progress games
# ---------------------------------------------------------------------------

def test_moves_tracked_in_game_response(client):
    game = _new_game(client)
    gid = game["id"]
    resp = client.post(f"/games/{gid}/moves", json={"player": "X", "position": 4})
    data = resp.json()
    assert "moves" in data
    assert data["moves"] == [{"player": "X", "position": 4}]


def test_moves_accumulate(client):
    game = _new_game(client)
    gid = game["id"]
    client.post(f"/games/{gid}/moves", json={"player": "X", "position": 0})
    resp = client.post(f"/games/{gid}/moves", json={"player": "O", "position": 8})
    data = resp.json()
    assert len(data["moves"]) == 2
    assert data["moves"][0] == {"player": "X", "position": 0}
    assert data["moves"][1] == {"player": "O", "position": 8}


# ---------------------------------------------------------------------------
# DB persistence – db module unit tests
# ---------------------------------------------------------------------------

def test_db_init_creates_tables(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "unit.db"))
    db_module.init_db()
    import sqlite3
    conn = sqlite3.connect(str(tmp_path / "unit.db"))
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "completed_games" in tables
    assert "game_moves" in tables
    conn.close()


def test_save_and_get_completed_game(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "unit.db"))
    db_module.init_db()
    game_dict = {"id": "abc-123", "status": "won", "winner": "X",
                 "board": ["X", "X", "X", "O", "O", None, None, None, None]}
    moves = [{"player": "X", "position": 0}, {"player": "O", "position": 3},
             {"player": "X", "position": 1}, {"player": "O", "position": 4},
             {"player": "X", "position": 2}]
    db_module.save_completed_game(game_dict, moves)

    result = db_module.get_completed_game("abc-123")
    assert result is not None
    assert result["id"] == "abc-123"
    assert result["status"] == "won"
    assert result["winner"] == "X"
    assert result["board"] == game_dict["board"]
    assert len(result["moves"]) == 5
    assert result["moves"][0] == {"move_number": 1, "player": "X", "position": 0}
    assert result["moves"][4] == {"move_number": 5, "player": "X", "position": 2}


def test_get_nonexistent_game_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "unit.db"))
    db_module.init_db()
    assert db_module.get_completed_game("no-such-id") is None


def test_list_completed_games_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "unit.db"))
    db_module.init_db()
    assert db_module.list_completed_games() == []


def test_list_completed_games_returns_move_count(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "unit.db"))
    db_module.init_db()
    game_dict = {"id": "g1", "status": "draw", "winner": None,
                 "board": ["X", "O", "X", "X", "X", "O", "O", "X", "O"]}
    moves = [{"player": "X" if i % 2 == 0 else "O", "position": i} for i in range(9)]
    db_module.save_completed_game(game_dict, moves)
    games = db_module.list_completed_games()
    assert len(games) == 1
    assert games[0]["move_count"] == 9


def test_save_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "unit.db"))
    db_module.init_db()
    game_dict = {"id": "dup", "status": "won", "winner": "O",
                 "board": [None]*9}
    moves = [{"player": "O", "position": 0}]
    db_module.save_completed_game(game_dict, moves)
    db_module.save_completed_game(game_dict, moves)  # should not raise
    assert len(db_module.list_completed_games()) == 1


# ---------------------------------------------------------------------------
# API – completed-games endpoints
# ---------------------------------------------------------------------------

def test_completed_games_empty_initially(client):
    resp = client.get("/completed-games")
    assert resp.status_code == 200
    assert resp.json() == []


def test_completed_game_saved_on_win(client):
    game = _new_game(client)
    gid = game["id"]
    _play_x_wins(client, gid)

    resp = client.get("/completed-games")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == gid
    assert data[0]["status"] == "won"
    assert data[0]["winner"] == "X"
    assert data[0]["move_count"] == 5


def test_completed_game_saved_on_draw(client):
    game = _new_game(client)
    gid = game["id"]
    _play_draw(client, gid)

    resp = client.get("/completed-games")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "draw"
    assert data[0]["winner"] is None
    assert data[0]["move_count"] == 9


def test_in_progress_game_not_in_completed(client):
    game = _new_game(client)
    gid = game["id"]
    client.post(f"/games/{gid}/moves", json={"player": "X", "position": 0})

    resp = client.get("/completed-games")
    assert resp.json() == []


def test_get_completed_game_detail(client):
    game = _new_game(client)
    gid = game["id"]
    _play_x_wins(client, gid)

    resp = client.get(f"/completed-games/{gid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == gid
    assert data["status"] == "won"
    assert data["winner"] == "X"
    assert len(data["moves"]) == 5
    assert data["moves"][0] == {"move_number": 1, "player": "X", "position": 0}


def test_get_completed_game_not_found(client):
    resp = client.get("/completed-games/no-such-game")
    assert resp.status_code == 404


def test_multiple_completed_games_listed(client):
    for _ in range(3):
        game = _new_game(client)
        _play_x_wins(client, game["id"])

    resp = client.get("/completed-games")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_completed_games_board_persisted(client):
    game = _new_game(client)
    gid = game["id"]
    _play_x_wins(client, gid)

    detail = client.get(f"/completed-games/{gid}").json()
    assert detail["board"][0] == "X"
    assert detail["board"][1] == "X"
    assert detail["board"][2] == "X"
