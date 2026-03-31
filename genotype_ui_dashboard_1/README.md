# Genotype UI Dashboard — Metrics Dashboard API

A REST API for a metrics dashboard built with FastAPI, following the
[Agentic Code Genotype](https://github.com/dmarble/Agentic-Code-Genotype-main)
hexagonal architecture conventions.

## Purpose

Provides five core operations:

| Method | Path                                          | Description              |
|--------|-----------------------------------------------|--------------------------|
| POST   | `/dashboards`                                 | Create a dashboard       |
| GET    | `/dashboards`                                 | List all dashboards      |
| POST   | `/dashboards/{id}/widgets`                    | Add a metric widget      |
| POST   | `/dashboards/{id}/widgets/{wid}/values`       | Post a metric value      |
| GET    | `/dashboards/{id}/widgets/{wid}/values`       | Read current widget values |

## Setup

```bash
uv venv
uv pip install -r requirements.txt
```

## Running

```bash
uv run uvicorn main:app --reload
```

Or directly:

```bash
uv run python main.py
```

API docs are served at `http://127.0.0.1:8000/docs`.

## Testing

```bash
uv run python -m unittest discover -s tests
```

## Project Layout

```
domain/
  core/
    models.py              — canonical dataclasses: Dashboard, MetricWidget, MetricValue
    commands.py            — use-case command handlers (dependency-injected)
    ports/                 — outbound: storage interfaces + in-memory implementations
      i_dashboard_repository.py
      i_widget_repository.py
      i_metric_value_repository.py
      in_memory_dashboard_repository.py
      in_memory_widget_repository.py
      in_memory_metric_value_repository.py
    adaptors/              — inbound: how the outside drives the core
      i_metrics_dashboard_adaptor.py
      fastapi_router.py
tests/
  dashboard/
    test_core.py           — canonical model validation + command logic
    test_ports.py          — in-memory repository behaviour
    test_adaptors.py       — HTTP adaptor translation (fixtures → canonical → response)
fixtures/
  raw/dashboard/v1/        — versioned raw HTTP request payloads
  expected/dashboard/v1/  — versioned expected canonical model outputs
main.py                    — composition root (wires concrete types)
pyproject.toml
requirements.txt
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for Mermaid diagrams.

## Genotype Lineage

This codebase is bred from
[Agentic-Code-Genotype-main](https://github.com/dmarble/Agentic-Code-Genotype-main).
All conventions from `AGENTS.md`, `AI_CONTRACT.md`, and ADRs 0001–0008 are applied exactly.
