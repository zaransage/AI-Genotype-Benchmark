"""
domain/scheduler/core/adaptors/i_http_adaptor.py

Inbound adaptor interface: contract for how HTTP clients drive the scheduler core.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class IHttpAdaptor(ABC):
    """Inbound adaptor — exposes scheduler use cases over HTTP."""

    @abstractmethod
    def create_job(self, name: str, command: str, cron_expression: str) -> dict:
        """Handle a create-job request. Returns serialisable job dict."""

    @abstractmethod
    def list_jobs(self) -> list[dict]:
        """Handle a list-jobs request. Returns list of serialisable job dicts."""

    @abstractmethod
    def delete_job(self, job_id: str) -> None:
        """Handle a delete-job request. Raises HTTPException 404 if not found."""

    @abstractmethod
    def get_run_history(self, job_id: str) -> list[dict]:
        """Handle a run-history request. Returns list of serialisable run-record dicts."""

    @abstractmethod
    def trigger_job(self, job_id: str) -> dict:
        """Handle a manual-trigger request. Returns serialisable run-record dict."""
