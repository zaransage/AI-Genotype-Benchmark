"""
FastAPI inbound adaptor for the metrics dashboard domain.

Aligned column formatting in the serialiser helpers is intentional —
this file is excluded from auto-formatters via pyproject.toml.

HTTPException belongs here only — never in domain or command classes.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from domain.core.adaptors.i_metrics_dashboard_adaptor import IMetricsDashboardAdaptor
from domain.core.commands import (
    AddWidgetCommand,
    CreateDashboardCommand,
    ListDashboardsCommand,
    PostMetricValueCommand,
    ReadWidgetValuesCommand,
)
from domain.core.models import Dashboard, MetricValue, MetricWidget


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CreateDashboardRequest(BaseModel):
    name: str


class AddWidgetRequest(BaseModel):
    name: str
    unit: str


class PostMetricValueRequest(BaseModel):
    value: float


# ---------------------------------------------------------------------------
# Canonical → dict serialisers (aligned column format)
# ---------------------------------------------------------------------------

def _dashboard_to_dict(d: Dashboard) -> dict:
    return {
        "id":         d.id,
        "name":       d.name,
        "created_at": d.created_at.isoformat(),
    }


def _widget_to_dict(w: MetricWidget) -> dict:
    return {
        "id":           w.id,
        "dashboard_id": w.dashboard_id,
        "name":         w.name,
        "unit":         w.unit,
    }


def _value_to_dict(v: MetricValue) -> dict:
    return {
        "id":          v.id,
        "widget_id":   v.widget_id,
        "value":       v.value,
        "recorded_at": v.recorded_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Adaptor implementation
# ---------------------------------------------------------------------------

class MetricsDashboardAdaptor(IMetricsDashboardAdaptor):
    """Translates HTTP payloads to/from canonical domain models."""

    def __init__(
        self,
        create_cmd:      CreateDashboardCommand,
        list_cmd:        ListDashboardsCommand,
        add_widget_cmd:  AddWidgetCommand,
        post_value_cmd:  PostMetricValueCommand,
        read_values_cmd: ReadWidgetValuesCommand,
    ) -> None:
        self._create_cmd      = create_cmd
        self._list_cmd        = list_cmd
        self._add_widget_cmd  = add_widget_cmd
        self._post_value_cmd  = post_value_cmd
        self._read_values_cmd = read_values_cmd

    def create_dashboard(self, name: str) -> dict:
        return _dashboard_to_dict(self._create_cmd.execute(name))

    def list_dashboards(self) -> list[dict]:
        return [_dashboard_to_dict(d) for d in self._list_cmd.execute()]

    def add_widget(self, dashboard_id: str, name: str, unit: str) -> dict:
        return _widget_to_dict(self._add_widget_cmd.execute(dashboard_id, name, unit))

    def post_metric_value(self, widget_id: str, value: float) -> dict:
        return _value_to_dict(self._post_value_cmd.execute(widget_id, value))

    def read_widget_values(self, widget_id: str) -> list[dict]:
        return [_value_to_dict(v) for v in self._read_values_cmd.execute(widget_id)]


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------

def create_router(adaptor: IMetricsDashboardAdaptor) -> APIRouter:
    """Return an APIRouter wired to the given adaptor instance."""
    router = APIRouter()

    @router.post("/dashboards", status_code=201)
    def create_dashboard(body: CreateDashboardRequest) -> dict:
        return adaptor.create_dashboard(body.name)

    @router.get("/dashboards")
    def list_dashboards() -> list[dict]:
        return adaptor.list_dashboards()

    @router.post("/dashboards/{dashboard_id}/widgets", status_code=201)
    def add_widget(dashboard_id: str, body: AddWidgetRequest) -> dict:
        try:
            return adaptor.add_widget(dashboard_id, body.name, body.unit)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post(
        "/dashboards/{dashboard_id}/widgets/{widget_id}/values",
        status_code=201,
    )
    def post_metric_value(
        dashboard_id: str,
        widget_id: str,
        body: PostMetricValueRequest,
    ) -> dict:
        try:
            return adaptor.post_metric_value(widget_id, body.value)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/dashboards/{dashboard_id}/widgets/{widget_id}/values")
    def read_widget_values(dashboard_id: str, widget_id: str) -> list[dict]:
        try:
            return adaptor.read_widget_values(widget_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
