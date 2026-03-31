"""
Inbound adaptor interface: IWebUIController.

Defines the contract for any HTML-serving mechanism that drives the game domain.
Implementations live alongside this interface in the adaptors/ folder.
"""
from __future__ import annotations

import abc


class IWebUIController(abc.ABC):
    @abc.abstractmethod
    def index(self):
        """Serve the main interactive game board page."""

    @abc.abstractmethod
    def history(self):
        """Serve the completed-games history page."""
