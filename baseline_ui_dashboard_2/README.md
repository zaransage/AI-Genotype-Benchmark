# Metrics Dashboard API

A REST API for managing metrics dashboards built with FastAPI.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/dashboards` | Create a dashboard |
| `GET` | `/dashboards` | List all dashboards |
| `GET` | `/dashboards/{id}` | Get a dashboard |
| `POST` | `/dashboards/{id}/widgets` | Add a metric widget |
| `GET` | `/dashboards/{id}/widgets` | List widgets on a dashboard |
| `GET` | `/dashboards/{id}/widgets/{wid}` | Get widget with current values and history |
| `POST` | `/dashboards/{id}/widgets/{wid}/metrics` | Post a new metric value |

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

Interactive docs: http://127.0.0.1:8000/docs

## Examples

```bash
# Create a dashboard
curl -X POST http://localhost:8000/dashboards \
  -H "Content-Type: application/json" \
  -d '{"name": "Production", "description": "Prod metrics"}'

# Add a widget
curl -X POST http://localhost:8000/dashboards/<id>/widgets \
  -H "Content-Type: application/json" \
  -d '{"name": "CPU Usage", "unit": "%"}'

# Post a metric value
curl -X POST http://localhost:8000/dashboards/<id>/widgets/<wid>/metrics \
  -H "Content-Type: application/json" \
  -d '{"value": 72.3, "labels": {"host": "web-1"}}'

# Read current widget values
curl http://localhost:8000/dashboards/<id>/widgets/<wid>
```

## Tests

```bash
pytest tests/
```

## Storage

Data is stored in-memory. All data is lost on server restart.
