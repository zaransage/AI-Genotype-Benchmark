from models import Dashboard, Widget


class InMemoryStore:
    def __init__(self):
        self._dashboards: dict[str, Dashboard] = {}
        self._widgets: dict[str, Widget] = {}  # keyed by widget_id

    # --- dashboards ---

    def create_dashboard(self, dashboard: Dashboard) -> Dashboard:
        self._dashboards[dashboard.id] = dashboard
        return dashboard

    def get_dashboard(self, dashboard_id: str) -> Dashboard | None:
        return self._dashboards.get(dashboard_id)

    def list_dashboards(self) -> list[Dashboard]:
        return list(self._dashboards.values())

    # --- widgets ---

    def create_widget(self, widget: Widget) -> Widget:
        self._widgets[widget.id] = widget
        return widget

    def get_widget(self, widget_id: str) -> Widget | None:
        return self._widgets.get(widget_id)

    def list_widgets(self, dashboard_id: str) -> list[Widget]:
        return [w for w in self._widgets.values() if w.dashboard_id == dashboard_id]

    def update_widget(self, widget: Widget) -> Widget:
        self._widgets[widget.id] = widget
        return widget


store = InMemoryStore()
