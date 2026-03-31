# Job Scheduler API

A REST API for a crontab-style job scheduler built with FastAPI.

## Features

- Create scheduled jobs with a name, shell command, and cron expression
- List all jobs
- Delete a job (and its history)
- View a job's run history
- Manually trigger a job on demand

Jobs run as shell commands via `subprocess`. Run output (stdout/stderr) and exit code are persisted per run.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## API Reference

### Create a job

```
POST /jobs
```

```json
{
  "name": "daily-backup",
  "command": "tar -czf /backup/db.tar.gz /var/db",
  "cron_expression": "0 2 * * *"
}
```

Returns `201` with the created job object.

### List all jobs

```
GET /jobs
```

Returns `200` with an array of job objects.

### Delete a job

```
DELETE /jobs/{job_id}
```

Returns `204` on success, `404` if the job does not exist.
Cascades to delete all associated run history.

### View run history

```
GET /jobs/{job_id}/history
```

Returns `200` with an array of run records ordered newest-first.
Each record includes `started_at`, `finished_at`, `exit_code`, `stdout`, `stderr`, and `triggered_manually`.

### Manually trigger a job

```
POST /jobs/{job_id}/trigger
```

Executes the job synchronously and returns `202` with the resulting run record.

## Cron Expression Format

Standard five-field cron: `minute hour day month day_of_week`

| Field        | Allowed values |
|--------------|----------------|
| minute       | 0–59           |
| hour         | 0–23           |
| day          | 1–31           |
| month        | 1–12           |
| day_of_week  | 0–6 (Sun=0)    |

Examples:

| Expression    | Meaning              |
|---------------|----------------------|
| `* * * * *`   | Every minute         |
| `0 * * * *`   | Every hour           |
| `0 0 * * *`   | Daily at midnight    |
| `*/5 * * * *` | Every 5 minutes      |
| `0 9 * * 1`   | Mondays at 09:00     |

## Running Tests

```bash
pytest tests/ -v
```

Test state is isolated in `test_scheduler.db` which is created and destroyed per test session.

## Data Persistence

Jobs and run history are stored in `scheduler.db` (SQLite). Delete this file to reset all state.
