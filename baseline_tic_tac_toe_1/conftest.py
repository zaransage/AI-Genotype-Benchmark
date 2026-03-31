import pytest

import database


@pytest.fixture(autouse=True, scope="session")
def _session_db(tmp_path_factory):
    """Point the database at a temp file for the entire test session."""
    db_file = str(tmp_path_factory.mktemp("db") / "session_test.db")
    database.DB_PATH = db_file
    database.init_db()
