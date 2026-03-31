"""
IUiRouter — inbound adaptor interface for HTML UI rendering.

Defines the contract for generating HTML page content from domain data.
Framework concerns (HTMLResponse, routing) belong at the composition root.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class IUiRouter(ABC):

    @abstractmethod
    def render_dashboard_list(self) -> str:
        """Return HTML string listing all dashboards."""

    @abstractmethod
    def render_dashboard_detail(self, dashboard_id: str) -> str:
        """Return HTML string for one dashboard with all widgets and metric values.
        Raises KeyError if the dashboard is not found."""
