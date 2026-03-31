from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None


class Dashboard(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime


class WidgetCreate(BaseModel):
    name: str
    unit: Optional[str] = None


class MetricPoint(BaseModel):
    value: float
    timestamp: datetime
    labels: Optional[dict[str, Any]] = None


class MetricPointCreate(BaseModel):
    value: float
    labels: Optional[dict[str, Any]] = None


class Widget(BaseModel):
    id: str
    dashboard_id: str
    name: str
    unit: Optional[str] = None
    created_at: datetime
    latest_value: Optional[float] = None
    latest_timestamp: Optional[datetime] = None
    history: list[MetricPoint] = []
