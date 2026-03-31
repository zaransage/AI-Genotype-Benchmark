# Job Scheduler API

A REST API crontab clone built with FastAPI and APScheduler. Supports creating, listing, deleting, and manually triggering scheduled shell jobs, plus viewing per-job run history.

## Requirements

- Python 3.10+
- Dependencies in `requirements.txt`

## Quick Start

```bash
pip install -r requirements.txt
python main.py          # listens on http://localhost:8000
```

Interactive docs are available at `http://localhost:8000/docs`.

## API Reference

### Create a job

```
POST /jobs
```

**Body**

| Field | Type | Description |
|---|---|---|
| `name` | string | Human-readable label |
| `command` | string | Shell command to execute |
| `cron_expression` | string | Standard 5-field cron expression |

**Example**

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"name":"hello","command":"echo hello","cron_expression":"* * * * *"}'
```

**Response** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "hello",
  "command": "echo hello",
  "cron_expression": "* * * * *",
  "created_at": "2024-01-01T00:00:00",
  "enabled": true
}
```

### List all jobs

```
GET /jobs
```

Returns an array of all registered jobs.

```bash
curl http://localhost:8000/jobs
```

### Delete a job

```
DELETE /jobs/{job_id}
```

Removes the job and cancels its schedule. Returns `204 No Content` on success, `404` if not found.

```bash
curl -X DELETE http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

### View run history

```
GET /jobs/{job_id}/history
```

Returns an array of past run records for the job.

```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000/history
```

**Run record fields**

| Field | Description |
|---|---|
| `id` | Unique run identifier |
| `job_id` | Parent job identifier |
| `started_at` | UTC timestamp when execution began |
| `finished_at` | UTC timestamp when execution completed |
| `exit_code` | Process exit code (`-1` on timeout or exception) |
| `stdout` | Captured standard output |
| `stderr` | Captured standard error |
| `triggered_manually` | `true` if triggered via the API |

### Manually trigger a job

```
POST /jobs/{job_id}/trigger
```

Runs the job immediately (synchronously) and returns the run record.

```bash
curl -X POST http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000/trigger
```

**Response** `202 Accepted`

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
.
├── main.py          # FastAPI application and route handlers
├── models.py        # Pydantic data models
├── storage.py       # Thread-safe in-memory job/history store
├── runner.py        # Subprocess execution and result persistence
├── scheduler.py     # APScheduler integration
├── requirements.txt
├── README.md
└── tests/
    └── test_api.py  # pytest unit tests
```

## Notes

- All state is held in memory; restarting the server resets all jobs and history.
- Commands are executed via `shell=True` with a 300-second timeout.
- The scheduler runs in a background thread and fires jobs according to their cron expressions.
