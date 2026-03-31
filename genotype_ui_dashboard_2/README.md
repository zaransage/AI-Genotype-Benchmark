# Metrics Dashboard API

A REST API for a metrics dashboard built with FastAPI, following the hexagonal architecture
genotype defined in `Agentic-Code-Genotype-main`.

## Purpose

Provides five operations:
1. **Create a dashboard** — `POST /dashboards`
2. **List all dashboards** — `GET /dashboards`
3. **Add a metric widget to a dashboard** — `POST /dashboards/{dashboard_id}/widgets`
4. **Post a new metric value to a widget** — `POST /widgets/{widget_id}/values`
5. **Read current widget values** — `GET /widgets/{widget_id}/values`

## Architecture

```mermaid
graph TD
    subgraph Inbound["Inbound (Driving)"]
        HTTP["HTTP Client"]
        Routes["REST Routes\n(rest_routes.py)"]
    end

    subgraph Core["domain/dashboard/core"]
        Cmds["Commands\n(commands.py)"]
        Models["Canonical Models\n(models.py)"]
    end

    subgraph Outbound["Outbound (Driven)"]
        IRepo["IDashboardRepo\n(i_dashboard_repo.py)"]
        InMem["InMemoryDashboardRepo\n(in_memory_dashboard_repo.py)"]
    end

    HTTP --> Routes
    Routes --> Cmds
    Cmds --> Models
    Cmds --> IRepo
    IRepo --> InMem

    style Inbound fill:#dfe8ff,stroke:#4a6cf7
    style Core fill:#fff3cd,stroke:#f0ad4e
    style Outbound fill:#d4edda,stroke:#28a745
```

```mermaid
sequenceDiagram
    participant Client
    participant Routes as REST Routes (adaptor)
    participant Cmd as Command (core)
    participant Repo as IDashboardRepo (port)

    Client->>Routes: POST /dashboards {name}
    Routes->>Cmd: CreateDashboardCommand.execute(name)
    Cmd->>Repo: save_dashboard(dashboard)
    Cmd-->>Routes: Dashboard dataclass
    Routes-->>Client: 201 {id, name, widget_ids}

    Client->>Routes: POST /dashboards/{id}/widgets {name, metric_name}
    Routes->>Cmd: AddWidgetCommand.execute(dashboard_id, name, metric_name)
    Cmd->>Repo: get_dashboard(id)
    Cmd->>Repo: save_widget(widget)
    Cmd->>Repo: save_dashboard(updated)
    Cmd-->>Routes: Widget dataclass
    Routes-->>Client: 201 {id, dashboard_id, name, metric_name, values}

    Client->>Routes: POST /widgets/{id}/values {value}
    Routes->>Cmd: PostMetricCommand.execute(widget_id, value)
    Cmd->>Repo: get_widget(id)
    Cmd->>Repo: save_widget(updated)
    Cmd-->>Routes: MetricValue dataclass
    Routes-->>Client: 201 {value, recorded_at}

    Client->>Routes: GET /widgets/{id}/values
    Routes->>Cmd: ReadWidgetValuesCommand.execute(widget_id)
    Cmd->>Repo: get_widget(id)
    Cmd-->>Routes: list[MetricValue]
    Routes-->>Client: 200 [{value, recorded_at}, ...]
```

## Folder Layout

```
domain/
  dashboard/
    core/
      models.py                   — Dashboard, Widget, MetricValue dataclasses
      commands.py                 — CreateDashboard, ListDashboards, AddWidget,
                                    PostMetric, ReadWidgetValues commands
      ports/
        i_dashboard_repo.py       — IDashboardRepo (outbound interface)
        in_memory_dashboard_repo.py
      adaptors/
        i_dashboard_adaptor.py    — IDashboardAdaptor (inbound interface)
        rest_routes.py            — FastAPI router
fixtures/
  raw/dashboard/v1/               — versioned raw request payloads
  expected/dashboard/v1/         — versioned expected canonical outputs
tests/
  dashboard/
    test_core.py
    test_ports.py
    test_adaptors.py
main.py                           — composition root
pyproject.toml
requirements.txt
```

## Setup

```bash
uv venv
uv pip install -r requirements.txt
```

## Run

```bash
uv run python main.py
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

## Test

```bash
uv run python -m unittest discover -s tests -v
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/dashboards` | Create a dashboard |
| `GET` | `/dashboards` | List all dashboards |
| `POST` | `/dashboards/{dashboard_id}/widgets` | Add widget to dashboard |
| `POST` | `/widgets/{widget_id}/values` | Post a metric value |
| `GET` | `/widgets/{widget_id}/values` | Read widget values |

### Example requests

```bash
# Create dashboard
curl -X POST http://localhost:8000/dashboards \
  -H "Content-Type: application/json" \
  -d '{"name": "Production"}'

# Add widget
curl -X POST http://localhost:8000/dashboards/<id>/widgets \
  -H "Content-Type: application/json" \
  -d '{"name": "CPU Usage", "metric_name": "cpu_percent"}'

# Post metric value
curl -X POST http://localhost:8000/widgets/<id>/values \
  -H "Content-Type: application/json" \
  -d '{"value": 42.5}'

# Read values
curl http://localhost:8000/widgets/<id>/values
```

## Lineage

Parent genotype: `Agentic-Code-Genotype-main`
ADRs followed: 0001, 0002, 0003, 0004, 0005, 0006, 0007, 0008
