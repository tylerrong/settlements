"""
Flask dashboard for browsing and filtering settlements.
"""
import json
import logging
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

from db.models import init_db, get_conn
from db.repository import list_settlements, get_settlement

app = Flask(__name__)
CORS(app)
logger = logging.getLogger(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Settlement Monitor</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f0f13; color: #e0e0e0; min-height: 100vh; }
  header { background: #1a1a2e; border-bottom: 1px solid #2a2a4a;
           padding: 16px 24px; display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 20px; font-weight: 700; color: #fff; }
  header .badge { background: #5865f2; color: #fff; font-size: 11px;
                  padding: 2px 8px; border-radius: 12px; font-weight: 600; }
  .filters { padding: 16px 24px; display: flex; gap: 12px; flex-wrap: wrap;
             border-bottom: 1px solid #1e1e2e; background: #12121a; }
  .filters select, .filters input {
    background: #1e1e30; border: 1px solid #2e2e4e; color: #e0e0e0;
    padding: 6px 12px; border-radius: 6px; font-size: 13px; }
  .filters button { background: #5865f2; color: #fff; border: none;
    padding: 6px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; }
  .filters button:hover { background: #4752c4; }
  .stats { padding: 12px 24px; display: flex; gap: 16px; background: #12121a;
           border-bottom: 1px solid #1e1e2e; font-size: 13px; color: #888; }
  .stats span { color: #aaa; } .stats strong { color: #fff; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
          gap: 16px; padding: 20px 24px; }
  .card { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 12px;
          padding: 16px; transition: border-color .2s; }
  .card:hover { border-color: #5865f2; }
  .card-title { font-size: 15px; font-weight: 700; color: #5b9cf6; margin-bottom: 8px;
                line-height: 1.4; }
  .card-title a { color: inherit; text-decoration: none; }
  .card-title a:hover { text-decoration: underline; }
  .card-desc { font-size: 13px; color: #999; margin-bottom: 12px; line-height: 1.5;
               display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
               overflow: hidden; }
  .card-meta { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
  .meta-item { background: #0f0f1a; border-radius: 6px; padding: 6px 8px; }
  .meta-label { font-size: 10px; color: #666; text-transform: uppercase;
                letter-spacing: .5px; margin-bottom: 2px; font-weight: 600; }
  .meta-value { font-size: 13px; color: #ccc; font-weight: 600; }
  .badge-status { display: inline-block; font-size: 10px; font-weight: 700;
                  padding: 2px 8px; border-radius: 10px; margin-bottom: 10px; }
  .status-new { background: #1a3a5c; color: #5b9cf6; }
  .status-open { background: #1a3a1a; color: #5bcd6e; }
  .status-closing_soon { background: #3a2a0a; color: #ffaa33; }
  .status-expired { background: #3a0a0a; color: #ff5555; }
  .status-payment_pending { background: #2a3a1a; color: #aaee55; }
  .category-tag { display: inline-block; font-size: 11px; background: #2a2a4a;
                  color: #888; padding: 2px 8px; border-radius: 10px; margin-bottom: 8px; margin-right: 4px; }
  .empty { padding: 60px 24px; text-align: center; color: #555; font-size: 15px; }
  .loader { padding: 60px 24px; text-align: center; color: #5865f2; }
  .run-btn { background: #1a3a1a; color: #5bcd6e; border: 1px solid #2a4a2a;
             padding: 6px 16px; border-radius: 6px; cursor: pointer; font-size: 13px;
             font-weight: 600; margin-left: auto; }
  .run-btn:hover { background: #1a4a1a; }
  .run-btn:disabled { opacity: .5; cursor: not-allowed; }
</style>
</head>
<body>
<header>
  <h1>Settlement Monitor</h1>
  <span class="badge" id="total-badge">...</span>
  <button class="run-btn" id="run-btn" onclick="runCrawl()">▶ Run Crawl</button>
</header>
<div class="filters">
  <select id="f-status" onchange="load()">
    <option value="">All Statuses</option>
    <option value="new">New</option>
    <option value="open">Open</option>
    <option value="closing_soon">Closing Soon</option>
    <option value="expired">Expired</option>
    <option value="payment_pending">Payment Pending</option>
  </select>
  <select id="f-category" onchange="load()">
    <option value="">All Categories</option>
    <option value="data_breach">Data Breach</option>
    <option value="privacy">Privacy</option>
    <option value="insurance">Insurance</option>
    <option value="product_liability">Product Liability</option>
    <option value="wage_theft">Wage Theft</option>
    <option value="antitrust">Antitrust</option>
    <option value="consumer">Consumer</option>
    <option value="financial">Financial</option>
    <option value="employment">Employment</option>
  </select>
  <select id="f-proof" onchange="load()">
    <option value="">Any Proof Req.</option>
    <option value="no">No Proof Required</option>
    <option value="yes">Proof Required</option>
  </select>
  <select id="f-deadline" onchange="load()">
    <option value="">Any Deadline</option>
    <option value="7">Deadline: Next 7 days</option>
    <option value="14">Deadline: Next 14 days</option>
    <option value="30">Deadline: Next 30 days</option>
  </select>
</div>
<div class="stats" id="stats"></div>
<div class="grid" id="grid"><div class="loader">Loading settlements...</div></div>

<script>
const CAT_EMOJI = {data_breach:'🔓',privacy:'🔒',insurance:'🛡️',product_liability:'⚠️',
  wage_theft:'💼',antitrust:'⚖️',consumer:'🛍️',financial:'💵',employment:'👔',other:'📋'};

async function load() {
  const params = new URLSearchParams();
  const status = document.getElementById('f-status').value;
  const cat = document.getElementById('f-category').value;
  const proof = document.getElementById('f-proof').value;
  const days = document.getElementById('f-deadline').value;
  if (status) params.set('status', status);
  if (cat) params.set('category', cat);
  if (proof) params.set('proof_required', proof);
  if (days) params.set('days_until_deadline', days);

  const resp = await fetch('/api/settlements?' + params);
  const data = await resp.json();
  const items = data.settlements || [];
  document.getElementById('total-badge').textContent = data.total + ' total';
  document.getElementById('stats').innerHTML =
    `<span>Showing <strong>${items.length}</strong> of <strong>${data.total}</strong></span>`;

  const grid = document.getElementById('grid');
  if (!items.length) { grid.innerHTML = '<div class="empty">No settlements match your filters.</div>'; return; }

  grid.innerHTML = items.map(s => {
    const url = s.official_website_url || s.source_url || '#';
    const cat = s.category || 'other';
    const status = s.status || 'new';
    const payout = s.estimated_payout || s.max_payout || 'Varies';
    return `
    <div class="card">
      <span class="badge-status status-${status}">${status.replace('_',' ').toUpperCase()}</span>
      <span class="category-tag">${CAT_EMOJI[cat]||'📋'} ${cat.replace('_',' ')}</span>
      <div class="card-title"><a href="${url}" target="_blank" rel="noopener">${s.title}</a></div>
      <div class="card-desc">${s.eligibility_summary||''}</div>
      <div class="card-meta">
        <div class="meta-item">
          <div class="meta-label">Proof of Purchase</div>
          <div class="meta-value">${(s.proof_required||'Unknown').replace(/^./,c=>c.toUpperCase())}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Deadline</div>
          <div class="meta-value">${s.claim_deadline||'TBD'}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Typical Payout</div>
          <div class="meta-value">${payout}</div>
        </div>
      </div>
    </div>`;
  }).join('');
}

async function runCrawl() {
  const btn = document.getElementById('run-btn');
  btn.disabled = true; btn.textContent = '⏳ Running...';
  try {
    const resp = await fetch('/api/crawl', {method: 'POST'});
    const data = await resp.json();
    btn.textContent = `✓ ${data.new_count} new`;
    setTimeout(() => { btn.textContent = '▶ Run Crawl'; btn.disabled = false; load(); }, 3000);
  } catch(e) {
    btn.textContent = '✗ Error'; btn.disabled = false;
  }
}

load();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/settlements")
def api_settlements():
    status = request.args.get("status")
    category = request.args.get("category")
    proof_required = request.args.get("proof_required")
    days = request.args.get("days_until_deadline")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    rows = list_settlements(
        status=status,
        category=category,
        proof_required=proof_required,
        days_until_deadline=int(days) if days else None,
        limit=limit,
        offset=offset,
    )

    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM settlements").fetchone()[0]
    conn.close()

    return jsonify({"settlements": rows, "total": total, "limit": limit, "offset": offset})


@app.route("/api/settlements/<int:row_id>")
def api_settlement(row_id: int):
    s = get_settlement(row_id)
    if not s:
        return jsonify({"error": "not found"}), 404
    return jsonify(s)


@app.route("/api/crawl", methods=["POST"])
def api_crawl():
    """Trigger a crawl run asynchronously."""
    import threading
    from crawler.pipeline import run_pipeline
    from alerts.webhook import send_settlement_alert

    def _run():
        try:
            run_pipeline(alert_callback=send_settlement_alert)
        except Exception as e:
            logger.error(f"Crawl error: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    # Return immediately; crawl runs in background
    conn = get_conn()
    count_before = conn.execute("SELECT COUNT(*) FROM settlements").fetchone()[0]
    conn.close()

    return jsonify({"status": "started", "new_count": 0, "message": "Crawl running in background"})


@app.route("/api/stats")
def api_stats():
    conn = get_conn()
    stats = {}
    for status in ["new", "open", "closing_soon", "expired", "payment_pending"]:
        stats[status] = conn.execute(
            "SELECT COUNT(*) FROM settlements WHERE status = ?", (status,)
        ).fetchone()[0]
    stats["total"] = conn.execute("SELECT COUNT(*) FROM settlements").fetchone()[0]
    conn.close()
    return jsonify(stats)


def run_dashboard(host: str = "0.0.0.0", port: int = 5050, debug: bool = False):
    init_db()
    app.run(host=host, port=port, debug=debug)
