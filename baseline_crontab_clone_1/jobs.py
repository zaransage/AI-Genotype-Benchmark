"""Job execution logic, shared by the API and the background scheduler."""

import subprocess
import uuid
from datetime import datetime

from sqlalchemy.orm import Session


def execute_command(job, db: Session, *, triggered_manually: bool):
    """Run *job.command* in a subprocess, persist the result, and return the run ORM object."""
    from models import JobRunORM  # local import avoids circular deps at module level

    run = JobRunORM(
        id=str(uuid.uuid4()),
        job_id=job.id,
        started_at=datetime.utcnow(),
        triggered_manually=triggered_manually,
        stdout="",
        stderr="",
    )
    db.add(run)
    db.commit()

    try:
        result = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        run.stdout = result.stdout
        run.stderr = result.stderr
        run.exit_code = result.returncode
    except subprocess.TimeoutExpired:
        run.stderr = "Job timed out after 300 seconds"
        run.exit_code = -1
    except Exception as exc:  # pragma: no cover
        run.stderr = str(exc)
        run.exit_code = -1

    run.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(run)
    return run
