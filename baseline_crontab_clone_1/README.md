# Job Scheduler API

A crontab-clone REST API built with FastAPI. Schedule commands using standard cron expressions, view run history, and trigger jobs on demand.

## Quick start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The interactive docs are available at `http://127.0.0.1:8000/docs`.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/jobs` | Create a scheduled job |
| `GET` | `/jobs` | List all jobs |
| `DELETE` | `/jobs/{job_id}` | Delete a job and its history |
| `GET` | `/jobs/{job_id}/history` | View run history (newest first) |
| `POST` | `/jobs/{job_id}/trigger` | Manually trigger a job |

### Create a job

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"name": "disk check", "command": "df -h", "cron_expression": "0 * * * *"}'
```

### Trigger a job manually

```bash
curl -X POST http://localhost:8000/jobs/<job_id>/trigger
```

### View run history

```bash
curl http://localhost:8000/jobs/<job_id>/history
```

## Cron expression format

Standard five-field cron syntax: `minute hour day month day_of_week`

Examples:

| Expression | Meaning |
|------------|---------|
| `* * * * *` | Every minute |
| `0 * * * *` | Every hour |
| `0 9 * * 1-5` | Weekdays at 09:00 |
| `*/15 * * * *` | Every 15 minutes |

## Run tests

```bash
pytest tests/ -v
```

## Project layout

```
.
├── main.py          # FastAPI application & routes
├── models.py        # SQLAlchemy ORM models + Pydantic schemas
├── database.py      # SQLite engine & session factory
├── jobs.py          # Command execution logic
├── scheduler.py     # APScheduler wrapper
├── requirements.txt
└── tests/
    └── test_api.py
```

## Data model

**Job**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique identifier |
| `name` | string | Human-readable label |
| `command` | string | Shell command to execute |
| `cron_expression` | string | Schedule (5-field cron) |
| `enabled` | bool | Whether the job is active |
| `created_at` | datetime | Creation timestamp |

**JobRun**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique identifier |
| `job_id` | string | Parent job |
| `started_at` | datetime | When execution began |
| `finished_at` | datetime \| null | When execution finished |
| `exit_code` | int \| null | Process exit code |
| `stdout` | string | Captured standard output |
| `stderr` | string | Captured standard error |
| `triggered_manually` | bool | `true` if triggered via API |
