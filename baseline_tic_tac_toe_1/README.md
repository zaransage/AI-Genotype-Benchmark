# Tic-Tac-Toe REST API

A two-player tic-tac-toe game exposed as a REST API built with FastAPI.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

Interactive docs available at `http://localhost:8000/docs`.

## API

### Create a game
```
POST /games
```
Returns a new game object with a unique `id`.

### Get game state
```
GET /games/{game_id}
```

### Make a move
```
POST /games/{game_id}/moves
Content-Type: application/json

{
  "player": "X",   // "X" or "O"
  "position": 4    // 0–8, left-to-right, top-to-bottom
}
```

Board positions:
```
0 | 1 | 2
---------
3 | 4 | 5
---------
6 | 7 | 8
```

### Game status values
| Value | Meaning |
|-------|---------|
| `in_progress` | Game ongoing |
| `X_wins` | Player X won |
| `O_wins` | Player O won |
| `draw` | Board full, no winner |

## Tests

```bash
pytest test_api.py -v
```
