"""
Inbound REST adaptor — FastAPI router.

HTTPException lives here only — never in domain or command classes (ADR-0006).
The router is constructed via build_router(repo) so it can be composed in main.py
and injected with a fresh InMemoryDashboardRepo in tests.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from domain.dashboard.core.commands import (
    AddWidgetCommand,
    CreateDashboardCommand,
    GetDashboardCommand,
    GetWidgetCommand,
    ListDashboardsCommand,
    PostMetricCommand,
    ReadWidgetValuesCommand,
)
from domain.dashboard.core.ports.i_dashboard_repo import IDashboardRepo


# ---------------------------------------------------------------------------
# Request / response schemas (Pydantic — boundary only, not canonical models)
# ---------------------------------------------------------------------------

class CreateDashboardRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be blank")
        return v


class DashboardResponse(BaseModel):
    id:         str
    name:       str
    widget_ids: list


class AddWidgetRequest(BaseModel):
    name:        str
    metric_name: str

    @field_validator("name", "metric_name")
    @classmethod
    def field_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field must not be blank")
        return v


class WidgetResponse(BaseModel):
    id:           str
    dashboard_id: str
    name:         str
    metric_name:  str
    values:       list


class PostMetricRequest(BaseModel):
    value: float


class MetricValueResponse(BaseModel):
    value:       float
    recorded_at: str


# ---------------------------------------------------------------------------
# Router factory — accepts injected repo (composition root wires concrete type)
# ---------------------------------------------------------------------------

def build_router(repo: IDashboardRepo) -> APIRouter:
    router = APIRouter()

    @router.post("/dashboards", status_code=201, response_model=DashboardResponse)
    def create_dashboard(body: CreateDashboardRequest) -> DashboardResponse:
        try:
            dashboard = CreateDashboardCommand(repo=repo).execute(name=body.name)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return DashboardResponse(
            id         = dashboard.id,
            name       = dashboard.name,
            widget_ids = dashboard.widget_ids,
        )

    @router.get("/dashboards", response_model=list[DashboardResponse])
    def list_dashboards() -> list:
        dashboards = ListDashboardsCommand(repo=repo).execute()
        return [
            DashboardResponse(id=d.id, name=d.name, widget_ids=d.widget_ids)
            for d in dashboards
        ]

    @router.post(
        "/dashboards/{dashboard_id}/widgets",
        status_code=201,
        response_model=WidgetResponse,
    )
    def add_widget(dashboard_id: str, body: AddWidgetRequest) -> WidgetResponse:
        try:
            widget = AddWidgetCommand(repo=repo).execute(
                dashboard_id = dashboard_id,
                name         = body.name,
                metric_name  = body.metric_name,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return WidgetResponse(
            id           = widget.id,
            dashboard_id = widget.dashboard_id,
            name         = widget.name,
            metric_name  = widget.metric_name,
            values       = widget.values,
        )

    @router.post(
        "/widgets/{widget_id}/values",
        status_code=201,
        response_model=MetricValueResponse,
    )
    def post_metric(widget_id: str, body: PostMetricRequest) -> MetricValueResponse:
        try:
            mv = PostMetricCommand(repo=repo).execute(
                widget_id = widget_id,
                value     = body.value,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return MetricValueResponse(value=mv.value, recorded_at=mv.recorded_at)

    @router.get(
        "/widgets/{widget_id}/values",
        response_model=list[MetricValueResponse],
    )
    def read_widget_values(widget_id: str) -> list:
        try:
            values = ReadWidgetValuesCommand(repo=repo).execute(widget_id=widget_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return [
            MetricValueResponse(value=mv.value, recorded_at=mv.recorded_at)
            for mv in values
        ]

    @router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
    def get_dashboard(dashboard_id: str) -> DashboardResponse:
        try:
            dashboard = GetDashboardCommand(repo=repo).execute(dashboard_id=dashboard_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return DashboardResponse(
            id         = dashboard.id,
            name       = dashboard.name,
            widget_ids = dashboard.widget_ids,
        )

    @router.get("/widgets/{widget_id}", response_model=WidgetResponse)
    def get_widget(widget_id: str) -> WidgetResponse:
        try:
            widget = GetWidgetCommand(repo=repo).execute(widget_id=widget_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return WidgetResponse(
            id           = widget.id,
            dashboard_id = widget.dashboard_id,
            name         = widget.name,
            metric_name  = widget.metric_name,
            values       = [
                MetricValueResponse(value=mv.value, recorded_at=mv.recorded_at)
                for mv in widget.values
            ],
        )

    return router
