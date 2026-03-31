"""
UiRouter — inbound adaptor for the HTML web UI.

Calls IDashboardController to obtain domain data and renders server-side HTML.
Framework concerns (HTMLResponse, routing) belong at the composition root (main.py).
Aligned column formatting is intentional; excluded from auto-formatters via pyproject.toml.
"""
from __future__ import annotations

from domain.dashboard.core.adaptors.i_dashboard_controller import IDashboardController
from domain.dashboard.core.adaptors.i_ui_router             import IUiRouter
from domain.dashboard.core.models                           import Dashboard, Widget


_CSS = """
body { font-family: sans-serif; margin: 2rem; background: #f5f5f5; color: #222; }
h1   { color: #333; margin-top: 0; }
a    { color: #0066cc; }
.dashboard-card { background: white; border-radius: 6px; padding: 1rem 1.5rem;
                  margin-bottom: .75rem; box-shadow: 0 1px 3px rgba(0,0,0,.12); }
.widget-card    { background: #fafafa; border: 1px solid #ddd; border-radius: 4px;
                  padding: .75rem 1rem; margin: .5rem 0; }
.metric-table   { border-collapse: collapse; width: 100%; font-size: .9rem; margin-top: .5rem; }
.metric-table th,
.metric-table td { border: 1px solid #ccc; padding: .3rem .6rem; text-align: left; }
.metric-table th { background: #eee; }
.meta            { color: #888; margin-left: 1rem; font-size: .85rem; }
.back            { display: inline-block; margin-bottom: 1rem; }
"""


class UiRouter(IUiRouter):

    def __init__(self, controller: IDashboardController) -> None:
        self._ctrl = controller

    # ------------------------------------------------------------------
    # IUiRouter implementation
    # ------------------------------------------------------------------

    def render_dashboard_list(self) -> str:
        dashboards = self._ctrl.list_dashboards()
        if dashboards:
            cards = "".join(self._dashboard_card(d) for d in dashboards)
        else:
            cards = "<p>No dashboards yet. Use the REST API to create one.</p>"
        return _page(
            title   = "Dashboards",
            content = f"<h1>Dashboards</h1>{cards}",
        )

    def render_dashboard_detail(self, dashboard_id: str) -> str:
        matched = [d for d in self._ctrl.list_dashboards() if d.id == dashboard_id]
        if not matched:
            raise KeyError(f"Dashboard not found: {dashboard_id}")
        d       = matched[0]
        widgets = "".join(self._widget_card(w) for w in d.widgets) if d.widgets \
                  else "<p>No widgets on this dashboard.</p>"
        return _page(
            title   = f"Dashboard \u2014 {d.name}",
            content = (
                f'<a class="back" href="/ui">&larr; All Dashboards</a>'
                f"<h1>{_esc(d.name)}</h1>"
                f'<p class="meta">Created: {_esc(d.created_at)}</p>'
                f"{widgets}"
            ),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _dashboard_card(self, d: Dashboard) -> str:
        return (
            f'<div class="dashboard-card">'
            f'<a href="/ui/dashboards/{_esc(d.id)}">{_esc(d.name)}</a>'
            f'<span class="meta">{_esc(d.created_at)}</span>'
            f"</div>"
        )

    def _widget_card(self, w: Widget) -> str:
        if w.values:
            rows  = "".join(
                f"<tr><td>{_esc(mv.timestamp)}</td><td>{mv.value}</td></tr>"
                for mv in w.values
            )
            table = (
                f'<table class="metric-table">'
                f"<thead><tr><th>Timestamp</th><th>Value ({_esc(w.unit)})</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>"
            )
        else:
            table = "<p><em>No metrics recorded.</em></p>"
        return (
            f'<div class="widget-card">'
            f"<strong>{_esc(w.name)}</strong> <em>({_esc(w.unit)})</em>"
            f"{table}</div>"
        )


# ---------------------------------------------------------------------------
# Module-level helpers (pure functions, not part of the interface)
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    """Minimal HTML escaping to prevent XSS."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _page(title: str, content: str) -> str:
    return (
        "<!doctype html><html lang='en'><head>"
        f"<meta charset='utf-8'><title>{_esc(title)}</title>"
        f"<style>{_CSS}</style>"
        "</head><body>"
        f"{content}"
        "</body></html>"
    )
