"""IWebUIAdaptor — inbound adaptor interface for the HTML dashboard."""
from abc import ABC, abstractmethod
from typing import Any


class IWebUIAdaptor(ABC):

    @abstractmethod
    def jobs_page(self) -> Any: ...
