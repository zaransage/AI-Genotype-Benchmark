from __future__ import annotations

import subprocess
from datetime import datetime

from models import Job, RunRecord
from storage import storage

_TIMEOUT_SECONDS = 300


def run_job(job: Job, triggered_manually: bool = False) -> RunRecord:
    """Execute *job* in a subprocess and persist the result to storage."""
    run = RunRecord(
        job_id=job.id,
        started_at=datetime.utcnow(),
        triggered_manually=triggered_manually,
    )
    try:
        result = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
        run.exit_code = result.returncode
        run.stdout = result.stdout
        run.stderr = result.stderr
    except subprocess.TimeoutExpired:
        run.exit_code = -1
        run.stderr = f"Command timed out after {_TIMEOUT_SECONDS} seconds"
    except Exception as exc:
        run.exit_code = -1
        run.stderr = str(exc)
    finally:
        run.finished_at = datetime.utcnow()

    storage.add_run(run)
    return run
