"""Inbound-port contract for the web UI adaptor."""
from __future__ import annotations

from abc import ABC, abstractmethod


class IWebUIAdaptor(ABC):
    """Drives the domain to produce an HTML rendering of all dashboards."""

    @abstractmethod
    def render_index(self) -> str: ...
