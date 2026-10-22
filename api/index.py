import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_server import mcp

from starlette.responses import HTMLResponse
from starlette.routing import Route

app = mcp.streamable_http_app()

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Acme Bearings - Demo Store</title>
<style>
  body { background:#0b0e13; color:#e6e6e6; font-family:system-ui, sans-serif; margin:2rem auto; max-width:760px; padding:0 1rem; }
  h1 { font-size:1.4rem; margin-bottom:0.2rem; }
  .sub { color:#9aa4b2; margin-top:0; }
  table { border-collapse:collapse; width:100%; margin:1rem 0; }
  th, td { border:1px solid #2a3140; padding:0.45rem 0.6rem; text-align:left; }
  th { background:#151a22; }
  input, button { background:#151a22; color:#e6e6e6; border:1px solid #2a3140; padding:0.45rem 0.6rem; }
  pre { background:#151a22; border:1px solid #2a3140; padding:0.8rem; overflow:auto; font-size:0.78rem; white-space:pre-wrap; }
  .foot { color:#9aa4b2; font-size:0.85rem; margin-top:2rem; }
</style>
</head>
<body>
<h1>Acme Bearings - Demo Store</h1>
<p class="sub">The human window. Agents use the machine door at /mcp - same inventory underneath.</p>

<p>
  <input id="q" type="text" placeholder="Search, e.g. flange" size="28">
  <button id="go">Search</button>
</p>

<table>
  <thead><tr><th>SKU</th><th>Description</th><th>Price each</th><th>Stock</th></tr></thead>
  <tbody id="shelf"><tr><td colspan="4">Loading shelf from the MCP server...</td></tr></tbody>
</table>

<h3>Machine talk (what an agent sees)</h3>
<pre id="log"></pre>

<p class="foot">MCP endpoint: /mcp - agents welcome.</p>

<script>
const log = document.getElementById('log');
const shelf = document.getElementById('shelf');

async function callTool(name, args) {
  const req = {jsonrpc: '2.0', id: Date.now(), method: 'tools/call',
               params: {name: name, arguments: args}};
  log.textContent += '>>> ' + JSON.stringify(req) + '\\n';
  const res = await fetch('/mcp', {method: 'POST',
    headers: {'Content-Type': 'application/json',
              'Accept': 'application/json, text/event-stream'},
    body: JSON.stringify(req)});
  const data = await res.json();
  log.textContent += '<<< ' + JSON.stringify(data) + '\\n\\n';
  return data.result.content[0].text;
}

async function fill(keyword) {
  shelf.innerHTML = '<tr><td colspan="4">Asking the MCP server...</td></tr>';
  try {
    const text = await callTool('search_inventory', {keyword: keyword});
    if (text.trim() === 'No matches.') {
      shelf.innerHTML = '<tr><td colspan="4">No matches.</td></tr>';
      return;
    }
    shelf.innerHTML = '';
    for (const line of text.trim().split('\\n')) {
      const m = line.match(/^(.+?): (.+) \(stock: (\d+)\)$/);
      if (!m) continue;
      const sku = m[1], desc = m[2], stock = m[3];
      const quote = await callTool('get_quote', {sku: sku, quantity: 1});
      const pm = quote.match(/\$([\d,]+\.\d{2})\/ea/);
      const price = pm ? '$' + pm[1] : '?';
      const tr = document.createElement('tr');
      tr.innerHTML = '<td>' + sku + '</td><td>' + desc + '</td><td>' +
                     price + '</td><td>' + stock + '</td>';
      shelf.appendChild(tr);
    }
  } catch (e) {
    shelf.innerHTML = '<tr><td colspan="4">Could not reach the MCP server: ' + e + '</td></tr>';
  }
}

document.getElementById('go').onclick = () =>
  fill(document.getElementById('q').value.trim() || 'BRG');
fill('BRG');
</script>
</body>
</html>
"""


async def home(request):
    return HTMLResponse(PAGE)


app.router.routes.append(Route("/", home, methods=["GET"]))
