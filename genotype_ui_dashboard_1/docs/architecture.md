# Architecture

## Hexagonal Overview

```mermaid
flowchart TB
    subgraph Driving["Driving Side (Inbound)"]
        Client["HTTP Client"]
    end

    subgraph Adaptor["domain/core/adaptors/"]
        IAdaptor["IMetricsDashboardAdaptor\n(i_metrics_dashboard_adaptor.py)"]
        FastAPI["MetricsDashboardAdaptor\n(fastapi_router.py)"]
    end

    subgraph Core["domain/core/"]
        Models["Canonical Models\n(models.py)\nDashboard · MetricWidget · MetricValue"]
        Commands["Command Handlers\n(commands.py)\nCreate · List · AddWidget\nPostValue · ReadValues"]
    end

    subgraph Ports["domain/core/ports/"]
        IDash["IDashboardRepository"]
        IWidget["IWidgetRepository"]
        IValue["IMetricValueRepository"]
    end

    subgraph Driven["Driven Side (Outbound)"]
        InMemDash["InMemoryDashboardRepository"]
        InMemWidget["InMemoryWidgetRepository"]
        InMemValue["InMemoryMetricValueRepository"]
    end

    subgraph Root["main.py (composition root)"]
        Wire["Wires concrete types"]
    end

    Client -->|HTTP request| FastAPI
    FastAPI -->|implements| IAdaptor
    FastAPI --> Commands
    Commands --> Models
    Commands --> IDash
    Commands --> IWidget
    Commands --> IValue
    IDash -.->|impl| InMemDash
    IWidget -.->|impl| InMemWidget
    IValue -.->|impl| InMemValue
    Wire -.->|creates & injects| FastAPI
    Wire -.->|creates| InMemDash
    Wire -.->|creates| InMemWidget
    Wire -.->|creates| InMemValue
```

## Data Flow — Create Dashboard

```mermaid
sequenceDiagram
    participant C as HTTP Client
    participant R as FastAPI Router
    participant CMD as CreateDashboardCommand
    participant M as Dashboard (model)
    participant REPO as InMemoryDashboardRepository

    C->>R: POST /dashboards {"name": "..."}
    R->>CMD: execute(name)
    CMD->>M: Dashboard(id=uuid, name, created_at=now)
    M-->>CMD: validated instance (raises on bad input)
    CMD->>REPO: save(dashboard)
    CMD-->>R: Dashboard instance
    R-->>C: 201 {"id", "name", "created_at"}
```

## Data Flow — Post Metric Value

```mermaid
sequenceDiagram
    participant C as HTTP Client
    participant R as FastAPI Router
    participant CMD as PostMetricValueCommand
    participant M as MetricValue (model)
    participant WREPO as InMemoryWidgetRepository
    participant VREPO as InMemoryMetricValueRepository

    C->>R: POST /dashboards/{id}/widgets/{wid}/values {"value": 42.5}
    R->>CMD: execute(widget_id, value)
    CMD->>WREPO: get(widget_id)
    WREPO-->>CMD: MetricWidget or None
    CMD->>M: MetricValue(id=uuid, widget_id, value, recorded_at=now)
    M-->>CMD: validated instance
    CMD->>VREPO: append(metric_value)
    CMD-->>R: MetricValue instance
    R-->>C: 201 {"id", "widget_id", "value", "recorded_at"}
```

## Use-Case Interactions

```mermaid
flowchart LR
    CreateDashboard["POST /dashboards\nCreateDashboardCommand"]
    ListDashboards["GET /dashboards\nListDashboardsCommand"]
    AddWidget["POST /dashboards/{id}/widgets\nAddWidgetCommand"]
    PostValue["POST .../widgets/{wid}/values\nPostMetricValueCommand"]
    ReadValues["GET .../widgets/{wid}/values\nReadWidgetValuesCommand"]

    DashRepo[("IDashboardRepository")]
    WidgetRepo[("IWidgetRepository")]
    ValueRepo[("IMetricValueRepository")]

    CreateDashboard --> DashRepo
    ListDashboards  --> DashRepo
    AddWidget       --> DashRepo
    AddWidget       --> WidgetRepo
    PostValue       --> WidgetRepo
    PostValue       --> ValueRepo
    ReadValues      --> WidgetRepo
    ReadValues      --> ValueRepo
```

## Fixture Versioning

```
fixtures/
  raw/
    dashboard/
      v1/
        create_dashboard.0.0.1.json   ← raw POST /dashboards body
        add_widget.0.0.1.json         ← raw POST /widgets body
        post_metric_value.0.0.1.json  ← raw POST /values body
  expected/
    dashboard/
      v1/
        dashboard.0.0.1.json          ← stable canonical Dashboard fields
        widget.0.0.1.json             ← stable canonical MetricWidget fields
        metric_value.0.0.1.json       ← stable canonical MetricValue fields
```
