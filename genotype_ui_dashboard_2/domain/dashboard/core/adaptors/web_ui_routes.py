"""
Inbound Web UI adaptor — FastAPI router serving HTML pages.

Pages are self-contained HTML+JS; JavaScript calls the existing REST API
endpoints at runtime to fetch and mutate data.

The router is constructed via build_web_ui_router() so it can be composed
in main.py (AI_CONTRACT.md §8 — composition root wires concrete types).

No repo injection is required: data access is performed client-side via
fetch() calls to the REST API.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

# ---------------------------------------------------------------------------
# Static HTML pages
# ---------------------------------------------------------------------------

_DASHBOARD_LIST_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Metrics Dashboards</title>
  <style>
    body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
    h1   { border-bottom: 2px solid #333; padding-bottom: 0.5rem; }
    ul   { list-style: none; padding: 0; }
    li   { padding: 0.5rem 0; border-bottom: 1px solid #eee; }
    a    { text-decoration: none; color: #0066cc; font-size: 1.1rem; }
    a:hover { text-decoration: underline; }
    form { margin-top: 1rem; display: flex; gap: 0.5rem; }
    input[type="text"] { padding: 0.4rem; border: 1px solid #ccc; border-radius: 4px; flex: 1; }
    button { padding: 0.4rem 1rem; background: #0066cc; color: #fff; border: none;
             border-radius: 4px; cursor: pointer; }
    button:hover { background: #0055aa; }
    .empty { color: #666; font-style: italic; }
    .error { color: #cc0000; margin-top: 0.4rem; }
  </style>
</head>
<body>
  <h1>Metrics Dashboards</h1>
  <ul id="list"></ul>
  <p id="empty-msg" class="empty" style="display:none">No dashboards yet.</p>
  <h2>New Dashboard</h2>
  <form id="create-form">
    <input type="text" id="dash-name" placeholder="Dashboard name" required>
    <button type="submit">Create</button>
  </form>
  <p id="error-msg" class="error" style="display:none"></p>
  <script>
    function esc(s) {
      var d = document.createElement('div');
      d.appendChild(document.createTextNode(String(s)));
      return d.innerHTML;
    }

    async function load() {
      var resp = await fetch('/dashboards');
      var items = await resp.json();
      var ul = document.getElementById('list');
      var em = document.getElementById('empty-msg');
      ul.innerHTML = '';
      if (items.length === 0) {
        em.style.display = '';
      } else {
        em.style.display = 'none';
        items.forEach(function(d) {
          var li = document.createElement('li');
          li.innerHTML = '<a href="/ui/dashboards/' + esc(d.id) + '">' + esc(d.name) + '</a>';
          ul.appendChild(li);
        });
      }
    }

    document.getElementById('create-form').addEventListener('submit', async function(e) {
      e.preventDefault();
      var name = document.getElementById('dash-name').value.trim();
      var err  = document.getElementById('error-msg');
      if (!name) { err.textContent = 'Name is required.'; err.style.display = ''; return; }
      err.style.display = 'none';
      var resp = await fetch('/dashboards', {
        method:  'POST',
        headers: {'Content-Type': 'application/json'},
        body:    JSON.stringify({name: name})
      });
      if (!resp.ok) { err.textContent = 'Failed to create dashboard.'; err.style.display = ''; return; }
      document.getElementById('dash-name').value = '';
      await load();
    });

    load();
  </script>
</body>
</html>
"""

_DASHBOARD_DETAIL_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard</title>
  <style>
    body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
    h1   { border-bottom: 2px solid #333; padding-bottom: 0.5rem; }
    .back { display: inline-block; margin-bottom: 1rem; color: #0066cc; text-decoration: none; }
    .card { border: 1px solid #ccc; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; }
    .card h3 { margin: 0 0 0.2rem; }
    .metric-label { color: #666; font-size: 0.9rem; margin: 0 0 0.5rem; }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { text-align: left; padding: 0.2rem 0.5rem; border-bottom: 1px solid #eee; }
    .post-form { display: flex; gap: 0.5rem; margin-top: 0.75rem; }
    .post-form input { padding: 0.3rem; border: 1px solid #ccc; border-radius: 4px; width: 110px; }
    form { margin-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap; }
    input[type="text"] { padding: 0.4rem; border: 1px solid #ccc; border-radius: 4px; flex: 1; }
    button { padding: 0.4rem 1rem; background: #0066cc; color: #fff; border: none;
             border-radius: 4px; cursor: pointer; }
    button:hover { background: #0055aa; }
    .empty { color: #666; font-style: italic; }
    .error { color: #cc0000; }
  </style>
</head>
<body>
  <a class="back" href="/ui/">&larr; All Dashboards</a>
  <h1 id="title">Loading&#8230;</h1>
  <div id="widgets"></div>
  <h2>Add Widget</h2>
  <form id="add-form">
    <input type="text" id="wname"  placeholder="Widget name"  required>
    <input type="text" id="mname"  placeholder="Metric name"  required>
    <button type="submit">Add Widget</button>
  </form>
  <p id="add-err" class="error" style="display:none"></p>
  <script>
    var DASH_ID = window.location.pathname.split('/').filter(Boolean).pop();

    function esc(s) {
      var d = document.createElement('div');
      d.appendChild(document.createTextNode(String(s)));
      return d.innerHTML;
    }

    async function load() {
      var resp = await fetch('/dashboards/' + DASH_ID);
      if (!resp.ok) { document.getElementById('title').textContent = 'Dashboard not found'; return; }
      var dash = await resp.json();
      document.title = dash.name;
      document.getElementById('title').textContent = dash.name;

      var container = document.getElementById('widgets');
      container.innerHTML = '';
      if (dash.widget_ids.length === 0) {
        container.innerHTML = '<p class="empty">No widgets yet.</p>';
        return;
      }

      for (var i = 0; i < dash.widget_ids.length; i++) {
        var wid = dash.widget_ids[i];
        var wr  = await fetch('/widgets/' + wid);
        if (!wr.ok) continue;
        var w = await wr.json();

        var valRows = '';
        if (w.values.length === 0) {
          valRows = '<p class="empty">No readings yet.</p>';
        } else {
          valRows = '<table><thead><tr><th>Value</th><th>Recorded At</th></tr></thead><tbody>';
          for (var j = 0; j < w.values.length; j++) {
            valRows += '<tr><td>' + esc(w.values[j].value) + '</td><td>' + esc(w.values[j].recorded_at) + '</td></tr>';
          }
          valRows += '</tbody></table>';
        }

        var card = document.createElement('div');
        card.className = 'card';
        card.innerHTML =
          '<h3>' + esc(w.name) + '</h3>' +
          '<p class="metric-label">Metric: ' + esc(w.metric_name) + '</p>' +
          valRows +
          '<form class="post-form" data-wid="' + esc(w.id) + '">' +
          '<input type="number" step="any" placeholder="Value" required>' +
          '<button type="submit">Post Reading</button>' +
          '</form>';
        container.appendChild(card);
      }

      container.querySelectorAll('.post-form').forEach(function(form) {
        form.addEventListener('submit', async function(e) {
          e.preventDefault();
          var val = parseFloat(this.querySelector('input').value);
          await fetch('/widgets/' + this.dataset.wid + '/values', {
            method:  'POST',
            headers: {'Content-Type': 'application/json'},
            body:    JSON.stringify({value: val})
          });
          await load();
        });
      });
    }

    document.getElementById('add-form').addEventListener('submit', async function(e) {
      e.preventDefault();
      var name        = document.getElementById('wname').value.trim();
      var metric_name = document.getElementById('mname').value.trim();
      var err         = document.getElementById('add-err');
      err.style.display = 'none';
      var resp = await fetch('/dashboards/' + DASH_ID + '/widgets', {
        method:  'POST',
        headers: {'Content-Type': 'application/json'},
        body:    JSON.stringify({name: name, metric_name: metric_name})
      });
      if (!resp.ok) { err.textContent = 'Failed to add widget.'; err.style.display = ''; return; }
      document.getElementById('wname').value = '';
      document.getElementById('mname').value = '';
      await load();
    });

    load();
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------

def build_web_ui_router() -> APIRouter:
    """Return an APIRouter that serves the dashboard web UI under /ui."""
    router = APIRouter(prefix="/ui")

    @router.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard_list_page() -> str:
        return _DASHBOARD_LIST_HTML

    @router.get(
        "/dashboards/{dashboard_id}",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    def dashboard_detail_page(dashboard_id: str) -> str:  # noqa: ARG001
        return _DASHBOARD_DETAIL_HTML

    return router
