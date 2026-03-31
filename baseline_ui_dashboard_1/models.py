from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WidgetCreate(BaseModel):
    name: str
    unit: Optional[str] = None


class MetricValueCreate(BaseModel):
    value: float
    timestamp: Optional[datetime] = None


class MetricValue(BaseModel):
    id: str
    value: float
    timestamp: datetime


class Widget(BaseModel):
    id: str
    name: str
    unit: Optional[str]
    metrics: List[MetricValue] = Field(default_factory=list)
    created_at: datetime


class Dashboard(BaseModel):
    id: str
    name: str
    description: Optional[str]
    widgets: List[Widget] = Field(default_factory=list)
    created_at: datetime
