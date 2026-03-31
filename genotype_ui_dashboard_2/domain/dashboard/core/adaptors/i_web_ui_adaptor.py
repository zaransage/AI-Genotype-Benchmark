"""
Inbound adaptor interface: IWebUIAdaptor.

Defines the contract for how external callers request rendered HTML pages
for the dashboard web UI.  Implementations live alongside this interface
(AI_CONTRACT.md §8).
"""

from abc import ABC, abstractmethod


class IWebUIAdaptor(ABC):
    """Inbound contract — how external callers request dashboard UI pages."""

    @abstractmethod
    def dashboard_list_page(self) -> str:
        """Return HTML content for the page listing all dashboards."""

    @abstractmethod
    def dashboard_detail_page(self, dashboard_id: str) -> str:
        """Return HTML content for a specific dashboard's detail page."""
