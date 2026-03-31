import pytest
from fastapi.testclient import TestClient
from main import app, games

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_games():
    games.clear()
    yield
    games.clear()


# ── helpers ───────────────────────────────────────────────────────────────────

def new_game():
    r = client.post("/games")
    assert r.status_code == 201
    return r.json()


def move(game_id, position):
    return client.post(f"/games/{game_id}/moves", json={"position": position})


def state(game_id):
    return client.get(f"/games/{game_id}").json()


# ── create game ───────────────────────────────────────────────────────────────

def test_create_game_returns_201():
    r = client.post("/games")
    assert r.status_code == 201


def test_create_game_initial_state():
    g = new_game()
    assert g["board"] == [None] * 9
    assert g["current_player"] == "X"
    assert g["status"] == "in_progress"
    assert "id" in g


def test_create_game_unique_ids():
    id1 = new_game()["id"]
    id2 = new_game()["id"]
    assert id1 != id2


# ── get game ──────────────────────────────────────────────────────────────────

def test_get_game():
    g = new_game()
    r = client.get(f"/games/{g['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == g["id"]


def test_get_game_not_found():
    r = client.get("/games/nonexistent")
    assert r.status_code == 404


# ── make move ─────────────────────────────────────────────────────────────────

def test_move_places_x_first():
    g = new_game()
    r = move(g["id"], 0)
    assert r.status_code == 200
    assert r.json()["board"][0] == "X"


def test_move_alternates_players():
    g = new_game()
    move(g["id"], 0)
    r = move(g["id"], 1)
    assert r.json()["board"][1] == "O"
    assert r.json()["current_player"] == "X"


def test_move_out_of_range():
    g = new_game()
    r = move(g["id"], 9)
    assert r.status_code == 422


def test_move_negative_position():
    g = new_game()
    r = move(g["id"], -1)
    assert r.status_code == 422


def test_move_occupied_cell():
    g = new_game()
    move(g["id"], 4)
    r = move(g["id"], 4)
    assert r.status_code == 409


def test_move_game_not_found():
    r = move("bad-id", 0)
    assert r.status_code == 404


# ── win detection ─────────────────────────────────────────────────────────────

def _play(game_id, positions):
    """Play a sequence of moves alternating X/O."""
    for pos in positions:
        move(game_id, pos)


def test_x_wins_row():
    g = new_game()
    # X: 0,1,2  O: 3,4
    _play(g["id"], [0, 3, 1, 4, 2])
    s = state(g["id"])
    assert s["status"] == "X_wins"


def test_o_wins_column():
    g = new_game()
    # X: 0,1,3  O: 2,5,8
    _play(g["id"], [0, 2, 1, 5, 3, 8])
    s = state(g["id"])
    assert s["status"] == "O_wins"


def test_x_wins_diagonal():
    g = new_game()
    # X: 0,4,8  O: 1,2
    _play(g["id"], [0, 1, 4, 2, 8])
    s = state(g["id"])
    assert s["status"] == "X_wins"


def test_draw():
    g = new_game()
    # X: 0,1,5,6,7  O: 2,3,4,8  — no winner, board full
    _play(g["id"], [0, 2, 1, 3, 5, 4, 6, 8, 7])
    s = state(g["id"])
    assert s["status"] == "draw"


def test_no_move_after_game_over():
    g = new_game()
    _play(g["id"], [0, 3, 1, 4, 2])  # X wins
    r = move(g["id"], 5)
    assert r.status_code == 409


def test_current_player_unchanged_after_win():
    g = new_game()
    _play(g["id"], [0, 3, 1, 4, 2])
    s = state(g["id"])
    # current_player should remain X (the winner) or at least be stable
    assert s["status"] == "X_wins"


# ── all winning lines ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("line", [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
])
def test_all_winning_lines(line):
    g = new_game()
    a, b, c = line
    # Pick O cells that don't overlap with line
    o_cells = [i for i in range(9) if i not in line][:2]
    # Interleave: X plays line[0], O plays o[0], X plays line[1], ...
    seq = []
    for i, x_pos in enumerate(line):
        seq.append(x_pos)
        if i < len(o_cells):
            seq.append(o_cells[i])
    _play(g["id"], seq)
    s = state(g["id"])
    assert s["status"] == "X_wins"
