"""
Shared pytest configuration.

1. Set JOBS_DB_PATH to :memory: before any module-level imports occur so that
   the global Storage singleton uses an in-memory SQLite database during tests.
2. Install a default scheduler mock so that test files which do NOT patch the
   scheduler themselves (e.g. test_ui.py, test_db.py) still get a safe mock.
   test_api.py replaces this with its own mock for its own assertions; that's
   fine because conftest.py is processed before test modules.
"""
import os

os.environ.setdefault("JOBS_DB_PATH", ":memory:")

from unittest.mock import MagicMock  # noqa: E402
import scheduler as sched_module      # noqa: E402

sched_module.scheduler = MagicMock()
