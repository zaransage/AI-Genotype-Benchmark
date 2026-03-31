"""
domain/scheduler/core/adaptors/i_web_ui_adaptor.py

Inbound adaptor interface: contract for serving the scheduler web UI.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from fastapi import FastAPI


class IWebUiAdaptor(ABC):
    """Inbound adaptor — serves the HTML dashboard for the scheduler."""

    @abstractmethod
    def register_routes(self, app: FastAPI) -> None:
        """Mount web-UI routes onto the given FastAPI application."""
