# Tic-Tac-Toe REST API

Two-player tic-tac-toe over HTTP. Built with FastAPI.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

Interactive docs available at `http://127.0.0.1:8000/docs`.

## API

### Create a game

```
POST /games
```

Response `201`:
```json
{
  "id": "a1b2c3...",
  "board": [null, null, null, null, null, null, null, null, null],
  "current_player": "X",
  "status": "in_progress"
}
```

### Get game state

```
GET /games/{game_id}
```

### Make a move

```
POST /games/{game_id}/moves
Content-Type: application/json

{ "position": 4 }
```

`position` is an integer 0–8 in row-major order:

```
0 | 1 | 2
---------
3 | 4 | 5
---------
6 | 7 | 8
```

Player X always goes first. Players alternate automatically.

### Status values

| Value | Meaning |
|-------|---------|
| `in_progress` | Game ongoing |
| `X_wins` | Player X won |
| `O_wins` | Player O won |
| `draw` | Board full, no winner |

### Error codes

| Code | Reason |
|------|--------|
| 404 | Game not found |
| 409 | Cell occupied or game already over |
| 422 | Position out of range (0–8) |

## Tests

```bash
pytest -v
```
