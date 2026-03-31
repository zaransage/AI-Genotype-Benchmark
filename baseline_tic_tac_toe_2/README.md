# Tic-Tac-Toe REST API

Two-player tic-tac-toe over HTTP, built with FastAPI.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

Interactive docs: http://127.0.0.1:8000/docs

## Board layout

Positions are numbered 0–8, left-to-right, top-to-bottom:

```
0 | 1 | 2
---------
3 | 4 | 5
---------
6 | 7 | 8
```

## Endpoints

### Create a game
```
POST /games
```
Response `201`:
```json
{
  "id": "uuid",
  "board": [null, null, null, null, null, null, null, null, null],
  "current_player": "X",
  "status": "in_progress",
  "winner": null
}
```

### Get game state
```
GET /games/{game_id}
```
Response `200`: same shape as above.

### Make a move
```
POST /games/{game_id}/moves
```
Body:
```json
{ "player": "X", "position": 4 }
```
- `player`: `"X"` or `"O"`
- `position`: integer 0–8

Response `200`: updated game state.

`status` values: `in_progress` | `won` | `draw`

## Run tests

```bash
pytest -v
```
