# Metrics Dashboard API

A REST API for managing metric dashboards, built with FastAPI.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
# or
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/dashboards` | Create a dashboard |
| `GET` | `/dashboards` | List all dashboards |
| `GET` | `/dashboards/{dashboard_id}` | Get a single dashboard |
| `POST` | `/dashboards/{dashboard_id}/widgets` | Add a metric widget |
| `GET` | `/dashboards/{dashboard_id}/widgets/{widget_id}` | Get a widget |
| `POST` | `/dashboards/{dashboard_id}/widgets/{widget_id}/metrics` | Post a metric value |
| `GET` | `/dashboards/{dashboard_id}/widgets/{widget_id}/metrics` | List metric values |

## Usage Examples

**Create a dashboard**
```bash
curl -X POST http://localhost:8000/dashboards \
  -H "Content-Type: application/json" \
  -d '{"name": "Production", "description": "Prod metrics"}'
```

**Add a widget**
```bash
curl -X POST http://localhost:8000/dashboards/{dashboard_id}/widgets \
  -H "Content-Type: application/json" \
  -d '{"name": "CPU Usage", "unit": "%"}'
```

**Post a metric value**
```bash
curl -X POST http://localhost:8000/dashboards/{dashboard_id}/widgets/{widget_id}/metrics \
  -H "Content-Type: application/json" \
  -d '{"value": 72.5}'
```

**Read metric values**
```bash
curl http://localhost:8000/dashboards/{dashboard_id}/widgets/{widget_id}/metrics
```

## Tests

```bash
pytest tests/ -v
```

## Notes

- Storage is in-memory; data is lost on restart.
- Timestamps default to the current UTC time if not provided.
