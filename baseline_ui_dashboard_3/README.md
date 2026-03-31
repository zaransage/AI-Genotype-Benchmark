# Metrics Dashboard API

A REST API for managing metrics dashboards and widgets, built with FastAPI.

## Setup

```bash
pip install -r requirements.txt
```

## Running the server

```bash
uvicorn main:app --reload
```

Interactive docs are available at `http://localhost:8000/docs`.

## Running tests

```bash
pytest test_api.py -v
```

## API Endpoints

### Dashboards

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/dashboards` | Create a new dashboard |
| `GET` | `/dashboards` | List all dashboards |
| `GET` | `/dashboards/{id}` | Get dashboard details with widgets |

### Widgets

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/dashboards/{id}/widgets` | Add a widget to a dashboard |
| `GET` | `/dashboards/{id}/widgets` | List all widgets on a dashboard |
| `GET` | `/dashboards/{id}/widgets/{wid}` | Get a single widget |

### Metric Values

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/dashboards/{id}/widgets/{wid}/values` | Post a new metric value |
| `GET` | `/dashboards/{id}/widgets/{wid}/values` | Get all metric values for a widget |

## Example Usage

```bash
# Create a dashboard
curl -X POST http://localhost:8000/dashboards \
  -H "Content-Type: application/json" \
  -d '{"name": "Production", "description": "Prod metrics"}'

# Add a widget (use the dashboard id from above)
curl -X POST http://localhost:8000/dashboards/<dashboard_id>/widgets \
  -H "Content-Type: application/json" \
  -d '{"name": "CPU Usage", "unit": "%"}'

# Post a metric value
curl -X POST http://localhost:8000/dashboards/<dashboard_id>/widgets/<widget_id>/values \
  -H "Content-Type: application/json" \
  -d '{"value": 73.4}'

# Read current widget value
curl http://localhost:8000/dashboards/<dashboard_id>/widgets/<widget_id>

# Read all metric values for a widget
curl http://localhost:8000/dashboards/<dashboard_id>/widgets/<widget_id>/values
```

## Data Model

- **Dashboard** — named container for metric widgets; has `id`, `name`, `description`, `created_at`.
- **Widget** — a named metric stream attached to a dashboard; has `id`, `name`, `unit`.
- **MetricValue** — a `value` (float) + `timestamp` (ISO-8601); `current_value` on a widget is always the most recently posted value.

Storage is in-memory and resets on server restart.
