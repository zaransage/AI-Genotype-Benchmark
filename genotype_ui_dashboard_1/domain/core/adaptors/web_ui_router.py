"""Web UI inbound adaptor — serves a server-rendered HTML dashboard page.

Aligned column formatting in the serialiser helpers is intentional —
this file is excluded from auto-formatters via pyproject.toml.

HTTPException belongs here only — never in domain or command classes.
"""
from __future__ import annotations

import html

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from domain.core.adaptors.i_web_ui_adaptor import IWebUIAdaptor
from domain.core.commands import (
    ListDashboardsCommand,
    ListWidgetsCommand,
    ReadWidgetValuesCommand,
)


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------

_CSS = """
body  { font-family: sans-serif; margin: 2rem; background: #f5f5f5; }
h1    { color: #333; }
h2    { color: #555; border-bottom: 2px solid #ccc; padding-bottom: .3rem; }
h3    { color: #666; margin-top: 1rem; }
table { border-collapse: collapse; width: 100%; max-width: 600px; margin-bottom: 1rem; }
th,td { border: 1px solid #ccc; padding: .4rem .8rem; text-align: left; }
th    { background: #e8e8e8; }
.none { color: #999; font-style: italic; }
"""

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Metrics Dashboard</title>
  <style>{css}</style>
</head>
<body>
<h1>Metrics Dashboard</h1>
{body}
</body>
</html>
"""


def _esc(value: object) -> str:
    """HTML-escape a value for safe embedding in a page."""
    return html.escape(str(value))


def _render_values_table(values: list, unit: str) -> str:
    if not values:
        return '<p class="none">No readings recorded.</p>'
    rows = "".join(
        f"<tr><td>{_esc(v.recorded_at.isoformat())}</td><td>{_esc(v.value)}&nbsp;{_esc(unit)}</td></tr>"
        for v in values[-10:]
    )
    return (
        "<table>"
        "<thead><tr><th>Recorded At</th><th>Value</th></tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
    )


def _render_dashboard_section(dashboard, widgets_with_values: list[tuple]) -> str:
    if not widgets_with_values:
        widget_html = '<p class="none">No widgets on this dashboard.</p>'
    else:
        widget_html = "".join(
            f"<h3>{_esc(w.name)} ({_esc(w.unit)})</h3>{_render_values_table(values, w.unit)}"
            for w, values in widgets_with_values
        )
    return (
        f"<section>"
        f"<h2>{_esc(dashboard.name)}</h2>"
        f"<p><small>ID: {_esc(dashboard.id)} &mdash; Created: {_esc(dashboard.created_at.isoformat())}</small></p>"
        f"{widget_html}"
        f"</section>"
    )


# ---------------------------------------------------------------------------
# Adaptor implementation
# ---------------------------------------------------------------------------

class WebUIAdaptor(IWebUIAdaptor):
    """Renders an HTML page by querying domain commands."""

    def __init__(
        self,
        list_dashboards_cmd: ListDashboardsCommand,
        list_widgets_cmd:    ListWidgetsCommand,
        read_values_cmd:     ReadWidgetValuesCommand,
    ) -> None:
        self._list_dashboards = list_dashboards_cmd
        self._list_widgets    = list_widgets_cmd
        self._read_values     = read_values_cmd

    def render_index(self) -> str:
        dashboards = self._list_dashboards.execute()
        if not dashboards:
            body = '<p class="none">No dashboards have been created yet.</p>'
        else:
            sections = []
            for dash in dashboards:
                widgets = self._list_widgets.execute(dash.id)
                widgets_with_values = [
                    (w, self._read_values.execute(w.id)) for w in widgets
                ]
                sections.append(_render_dashboard_section(dash, widgets_with_values))
            body = "\n".join(sections)
        return _HTML_TEMPLATE.format(css=_CSS, body=body)


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------

def create_web_ui_router(adaptor: IWebUIAdaptor) -> APIRouter:
    """Return an APIRouter that serves the HTML dashboard UI."""
    router = APIRouter()

    @router.get("/ui", response_class=HTMLResponse)
    def index() -> str:
        return adaptor.render_index()

    return router
