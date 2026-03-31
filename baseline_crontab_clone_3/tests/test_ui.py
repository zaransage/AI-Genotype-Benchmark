"""Tests for the web UI endpoint (GET /)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app
from storage import storage


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_storage():
    storage._jobs.clear()
    storage._history.clear()
    yield
    storage._jobs.clear()
    storage._history.clear()


# ── GET / ─────────────────────────────────────────────────────────────────────


def test_ui_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_ui_content_type_is_html(client):
    resp = client.get("/")
    assert "text/html" in resp.headers["content-type"]


def test_ui_contains_title(client):
    resp = client.get("/")
    assert "Job Scheduler" in resp.text


def test_ui_contains_jobs_table(client):
    resp = client.get("/")
    assert "jobs-body" in resp.text


def test_ui_contains_history_section(client):
    resp = client.get("/")
    assert "history-body" in resp.text


def test_ui_references_jobs_api(client):
    """The page's JavaScript must call the /jobs endpoint."""
    resp = client.get("/")
    assert "/jobs" in resp.text


def test_ui_not_included_in_openapi_schema(client):
    """The UI route should be hidden from the OpenAPI spec."""
    schema = client.get("/openapi.json").json()
    paths = schema.get("paths", {})
    assert "/" not in paths
