from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class MetricValueCreate(BaseModel):
    value: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MetricValue(BaseModel):
    value: float
    timestamp: datetime


class WidgetCreate(BaseModel):
    name: str
    unit: str = ""


class Widget(BaseModel):
    id: str
    dashboard_id: str
    name: str
    unit: str
    values: list[MetricValue] = Field(default_factory=list)

    @property
    def current_value(self) -> MetricValue | None:
        return self.values[-1] if self.values else None


class WidgetResponse(BaseModel):
    id: str
    dashboard_id: str
    name: str
    unit: str
    current_value: MetricValue | None


class DashboardCreate(BaseModel):
    name: str
    description: str = ""


class Dashboard(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    widgets: dict[str, Widget] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    widget_count: int


class DashboardDetail(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    widgets: list[WidgetResponse]
