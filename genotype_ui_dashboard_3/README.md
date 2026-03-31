# Metrics Dashboard API

A REST API for managing dashboards and metric widgets, built with FastAPI following the hexagonal (ports & adaptors) architecture defined in the Agentic-Code-Genotype lineage.

## Purpose

Provide a backend service that allows clients to:

- Create named dashboards
- Add metric widgets to dashboards (each widget tracks a named measurement with a unit)
- Post new metric values to widgets over time
- Read the current accumulated values for any widget
- List all known dashboards

## Architecture

```mermaid
graph TD
    subgraph Inbound ["Inbound (Driving Side)"]
        HTTP["HTTP Client"]
        Routes["FastAPI Routes<br/>(main.py)"]
    end

    subgraph Domain ["domain/dashboard/core"]
        Adaptor["DashboardController<br/>(adaptors/)"]
        Models["Canonical Models<br/>Dashboard · Widget · MetricValue"]
        Port["IDashboardRepository<br/>(ports/)"]
    end

    subgraph Outbound ["Outbound (Driven Side)"]
        Repo["InMemoryDashboardRepository<br/>(ports/)"]
    end

    HTTP --> Routes
    Routes --> Adaptor
    Adaptor --> Models
    Adaptor --> Port
    Port -.-> Repo

    style Inbound fill:#dfe8ff,stroke:#5572c8
    style Domain fill:#e8f5e9,stroke:#43a047
    style Outbound fill:#fff8e1,stroke:#f9a825
```

### Data-flow diagram

```mermaid
sequenceDiagram
    participant Client
    participant Routes as FastAPI Routes
    participant Ctrl as DashboardController
    participant Repo as InMemoryDashboardRepository

    Client->>Routes: POST /dashboards {name}
    Routes->>Ctrl: create_dashboard(name)
    Ctrl->>Repo: save(dashboard)
    Ctrl-->>Routes: Dashboard
    Routes-->>Client: 201 {id, name, created_at, widgets}

    Client->>Routes: POST /dashboards/{id}/widgets {name, unit}
    Routes->>Ctrl: add_widget(dashboard_id, name, unit)
    Ctrl->>Repo: get(dashboard_id)
    Ctrl->>Repo: save(dashboard)
    Ctrl-->>Routes: Widget
    Routes-->>Client: 201 {id, name, unit, values}

    Client->>Routes: POST /dashboards/{id}/widgets/{wid}/metrics {value, timestamp}
    Routes->>Ctrl: post_metric(dashboard_id, widget_id, value, timestamp)
    Ctrl->>Repo: get + save
    Ctrl-->>Routes: MetricValue
    Routes-->>Client: 201 {timestamp, value}

    Client->>Routes: GET /dashboards/{id}/widgets/{wid}
    Routes->>Ctrl: get_widget(dashboard_id, widget_id)
    Ctrl->>Repo: get(dashboard_id)
    Ctrl-->>Routes: Widget
    Routes-->>Client: 200 {id, name, unit, values:[...]}
```

### Folder layout

```
domain/
  dashboard/
    core/
      models.py                          — Dashboard, Widget, MetricValue dataclasses
      ports/
        i_dashboard_repository.py        — IDashboardRepository (outbound interface)
        in_memory_dashboard_repository.py — in-memory implementation
      adaptors/
        i_dashboard_controller.py        — IDashboardController (inbound interface)
        dashboard_controller.py          — use-case orchestrator
main.py                                  — composition root + FastAPI routes
tests/
  dashboard/
    test_core.py                         — canonical model validation
    test_ports.py                        — repository behaviour
    test_adaptors.py                     — controller use-cases (mock repository)
fixtures/
  raw/dashboard/v1/                      — raw incoming request payloads
  expected/dashboard/v1/                 — expected canonical model outputs
schemas/
  dashboard.json                         — JSON schema for wire format validation
```

## Setup

```bash
# Create virtual environment
uv venv

# Activate
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

## Running

```bash
uv run python -m uvicorn main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs` (Swagger UI).

## Running Tests

```bash
uv run python -m unittest discover -s tests -p "test_*.py" -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/dashboards` | Create a dashboard |
| `GET` | `/dashboards` | List all dashboards |
| `POST` | `/dashboards/{id}/widgets` | Add a widget to a dashboard |
| `POST` | `/dashboards/{id}/widgets/{wid}/metrics` | Post a metric value to a widget |
| `GET` | `/dashboards/{id}/widgets/{wid}` | Read current widget values |

## Lineage

Parent genotype: `Agentic-Code-Genotype-main`
Conventions: AGENTS.md · AI_CONTRACT.md · ADR 0001–0008
