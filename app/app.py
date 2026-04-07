import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
COMPARABLE_SALES_FILE = OUTPUT_DIR / "comparable_sales_dataset.json"
PROPERTY_CASES_FILE = DATA_DIR / "property_cases.json"
LISTINGS_FILE = DATA_DIR / "listings.json"
SUBURB_STATS_FILE = DATA_DIR / "suburb_stats.json"
HOST = "127.0.0.1"
PORT = 8010


def load_dotenv_file(path: Path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv_file(BASE_DIR / ".env")


def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_market_fallback():
    suburb_stats = load_json(SUBURB_STATS_FILE) or []
    listings = load_json(LISTINGS_FILE) or []
    if not suburb_stats:
        return None

    sale_counts = {}
    for row in listings:
        suburb = row.get("suburb")
        if suburb and row.get("listing_type") == "sale":
            sale_counts[suburb] = sale_counts.get(suburb, 0) + 1

    summary = []
    for row in suburb_stats:
        suburb = row.get("suburb")
        if not suburb:
            continue
        summary.append(
            {
                "suburb": suburb,
                "sales_count": sale_counts.get(suburb, 0),
                "median_sale_price": row.get("median_sale_price"),
                "latest_sale_date": None,
                "top_sales": [],
            }
        )

    summary.sort(key=lambda item: item.get("median_sale_price") or 0, reverse=True)
    return {
        "dataset_name": "market_fallback",
        "coverage": {
            "total_sales": sum(item["sales_count"] for item in summary),
            "suburb_count": len(summary),
            "date_from": None,
            "date_to": None,
        },
        "suburb_summary": summary,
        "sales": [],
    }


def load_comparable_payload():
    return load_json(COMPARABLE_SALES_FILE) or build_market_fallback()


def load_property_cases_payload():
    payload = load_json(PROPERTY_CASES_FILE)
    if isinstance(payload, dict):
        return payload
    return {"dataset_name": "property_cases", "records": []}


def render_nav(active):
    def link(path, label, key):
        class_name = "nav-link active" if active == key else "nav-link"
        return f'<a class="{class_name}" href="{path}">{label}</a>'

    return (
        '<div class="nav">'
        + link("/", "Comparable Sales", "sales")
        + link("/premium", "Premium Property Cases", "premium")
        + "</div>"
    )


def render_comparable_sales_html(payload):
    payload_json = json.dumps(payload or {}, ensure_ascii=False)
    nav_html = render_nav("sales")
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Comparable Sales Explorer</title>
  <style>
    :root {{
      --bg: #f6f1e8;
      --paper: #fffdf9;
      --ink: #1f1c17;
      --muted: #6c6356;
      --line: #ddd2c2;
      --accent: #6f4e37;
      --shadow: 0 18px 50px rgba(65, 44, 24, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(111,78,55,0.10), transparent 30%),
        radial-gradient(circle at bottom right, rgba(47,107,59,0.08), transparent 28%),
        var(--bg);
    }}
    .shell {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 28px 18px 40px;
    }}
    .nav {{
      display: flex;
      gap: 10px;
      margin-bottom: 18px;
    }}
    .nav-link {{
      text-decoration: none;
      color: var(--ink);
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.75);
      padding: 10px 14px;
      border-radius: 999px;
      font-size: 14px;
    }}
    .nav-link.active {{
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(111,78,55,0.96), rgba(58,43,31,0.96));
      color: #fdf7ef;
      border-radius: 28px;
      padding: 32px;
      box-shadow: var(--shadow);
    }}
    .eyebrow {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      opacity: 0.82;
      margin-bottom: 10px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(34px, 5vw, 54px);
      line-height: 0.96;
    }}
    .hero p {{
      max-width: 780px;
      margin: 14px 0 0;
      line-height: 1.55;
      color: rgba(253,247,239,0.9);
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-top: 24px;
    }}
    .stat {{
      background: rgba(255,255,255,0.10);
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 18px;
      padding: 16px;
    }}
    .stat-label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      opacity: 0.75;
    }}
    .stat-value {{
      margin-top: 8px;
      font-size: 28px;
      font-weight: 700;
    }}
    .content {{
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      gap: 22px;
      margin-top: 22px;
    }}
    .panel {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      padding: 20px;
    }}
    .panel h2 {{
      margin: 0 0 14px;
      font-size: 22px;
    }}
    .controls {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }}
    .search, .filter {{
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: #fff;
      font-size: 15px;
    }}
    .search {{ flex: 1 1 260px; }}
    .summary-list {{
      display: grid;
      gap: 10px;
    }}
    .summary-item {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
    }}
    .summary-item strong {{
      display: block;
      font-size: 16px;
      margin-bottom: 4px;
    }}
    .summary-item span {{
      color: var(--muted);
      font-size: 14px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      border: 1px solid var(--line);
      border-radius: 18px;
      overflow: hidden;
      background: #fff;
    }}
    th, td {{
      text-align: left;
      padding: 12px 14px;
      font-size: 14px;
      border-top: 1px solid #efe5d8;
      vertical-align: top;
    }}
    thead th {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      background: #f4eee4;
      border-top: none;
    }}
    tbody tr:hover {{ background: #fcf7ef; }}
    .muted {{ color: var(--muted); }}
    @media (max-width: 980px) {{
      .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .content {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 640px) {{
      .shell {{ padding: 18px 14px 28px; }}
      .hero {{ padding: 24px; }}
      .stats {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    {nav_html}
    <section class="hero">
      <div class="eyebrow">Reference Track</div>
      <h1>Recent real sales for street-level market reading.</h1>
      <p>
        This is the official-history reference line. Search by suburb or street, compare recent sales,
        and use the suburb summary as a comp anchor while the premium property workflow grows separately.
      </p>
      <div class="stats" id="hero-stats"></div>
    </section>
    <section class="content">
      <aside class="panel">
        <h2>Suburb Summary</h2>
        <div class="summary-list" id="suburb-summary"></div>
      </aside>
      <main class="panel">
        <h2>Sales Table</h2>
        <div class="controls">
          <input id="search" class="search" type="search" placeholder="Search suburb, street, or address">
          <select id="suburb-filter" class="filter"></select>
        </div>
        <div style="overflow:auto; max-height: 820px;">
          <table>
            <thead>
              <tr>
                <th>Address</th>
                <th>Suburb</th>
                <th>Sale Price</th>
                <th>Sale Date</th>
                <th>Land Size</th>
                <th>Type</th>
              </tr>
            </thead>
            <tbody id="sales-body"></tbody>
          </table>
        </div>
      </main>
    </section>
  </div>
  <script>
    const payload = __PAYLOAD__;
    const currency = new Intl.NumberFormat('en-AU', {{
      style: 'currency',
      currency: 'AUD',
      maximumFractionDigits: 0
    }});

    function formatMoney(value) {{
      if (value === null || value === undefined) return '-';
      return currency.format(value);
    }}

    function formatLand(value) {{
      if (value === null || value === undefined) return '-';
      return `${{Number(value).toFixed(0)}} sqm`;
    }}

    function renderHeroStats() {{
      const coverage = payload.coverage || {{}};
      const stats = [
        ['Sales loaded', coverage.total_sales || 0],
        ['Tracked suburbs', coverage.suburb_count || 0],
        ['Date from', coverage.date_from || '-'],
        ['Date to', coverage.date_to || '-']
      ];
      document.getElementById('hero-stats').innerHTML = stats.map(([label, value]) => `
        <div class="stat">
          <div class="stat-label">${{label}}</div>
          <div class="stat-value">${{value}}</div>
        </div>
      `).join('');
    }}

    function renderSuburbSummary() {{
      const rows = (payload.suburb_summary || []).slice(0, 8);
      document.getElementById('suburb-summary').innerHTML = rows.map(row => `
        <div class="summary-item">
          <strong>${{row.suburb}}</strong>
          <span>${{formatMoney(row.median_sale_price)}} median | ${{row.sales_count}} sales | latest ${{row.latest_sale_date || '-'}}</span>
        </div>
      `).join('');
    }}

    function renderSuburbFilter() {{
      const suburbs = Array.from(new Set((payload.sales || []).map(row => row.suburb))).sort();
      const select = document.getElementById('suburb-filter');
      select.innerHTML = ['<option value="all">All suburbs</option>']
        .concat(suburbs.map(suburb => `<option value="${{suburb}}">${{suburb}}</option>`))
        .join('');
    }}

    function renderSales(rows) {{
      const body = document.getElementById('sales-body');
      body.innerHTML = rows.map(row => `
        <tr>
          <td><strong>${{row.full_address}}</strong><br><span class="muted">${{row.street || '-'}}</span></td>
          <td>${{row.suburb}}</td>
          <td>${{formatMoney(row.sale_price)}}</td>
          <td>${{row.sale_date}}</td>
          <td>${{formatLand(row.land_size_sqm)}}</td>
          <td>${{row.property_type || '-'}}</td>
        </tr>
      `).join('');
    }}

    function wireFilters() {{
      const search = document.getElementById('search');
      const suburb = document.getElementById('suburb-filter');
      const rows = payload.sales || [];

      function apply() {{
        const term = search.value.trim().toLowerCase();
        const suburbValue = suburb.value;
        const filtered = rows.filter(row => {{
          const haystack = `${{row.full_address}} ${{row.suburb}} ${{row.street || ''}}`.toLowerCase();
          const matchesTerm = !term || haystack.includes(term);
          const matchesSuburb = suburbValue === 'all' || row.suburb === suburbValue;
          return matchesTerm && matchesSuburb;
        }});
        renderSales(filtered);
      }}

      search.addEventListener('input', apply);
      suburb.addEventListener('change', apply);
      apply();
    }}

    renderHeroStats();
    renderSuburbSummary();
    renderSuburbFilter();
    wireFilters();
  </script>
</body>
</html>
""".replace("__PAYLOAD__", payload_json)


def render_property_cases_html(payload):
    payload_json = json.dumps(payload or {}, ensure_ascii=False)
    nav_html = render_nav("premium")
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Premium Property Cases</title>
  <style>
    :root {{
      --bg: #efe8dd;
      --paper: rgba(255,255,255,0.84);
      --paper-strong: #fffdf8;
      --ink: #1f1b17;
      --muted: #6f6659;
      --line: rgba(91, 72, 53, 0.12);
      --accent: #184c3a;
      --accent-2: #9a6a3a;
      --accent-soft: #e7f0eb;
      --warn: #8e5d1c;
      --shadow: 0 24px 60px rgba(40, 28, 16, 0.10);
      --radius: 24px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(24,76,58,0.16), transparent 26%),
        radial-gradient(circle at 80% 20%, rgba(154,106,58,0.14), transparent 20%),
        linear-gradient(180deg, rgba(255,255,255,0.55), rgba(255,255,255,0.15)),
        var(--bg);
      min-height: 100vh;
    }}
    .shell {{
      max-width: 1480px;
      margin: 0 auto;
      padding: 28px 18px 56px;
    }}
    .nav {{
      display: flex;
      gap: 10px;
      margin-bottom: 18px;
    }}
    .nav-link {{
      text-decoration: none;
      color: var(--ink);
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.72);
      padding: 10px 14px;
      border-radius: 999px;
      font-size: 14px;
      backdrop-filter: blur(12px);
    }}
    .nav-link.active {{
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }}
    .hero {{
      background:
        radial-gradient(circle at top right, rgba(255,255,255,0.10), transparent 28%),
        linear-gradient(135deg, rgba(24,76,58,0.96), rgba(20,46,39,0.98));
      color: #f5fbf8;
      border-radius: 36px;
      padding: 34px;
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(255,255,255,0.10);
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.12);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      opacity: 0.9;
      margin-bottom: 14px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(40px, 5vw, 64px);
      line-height: 0.95;
      letter-spacing: -0.04em;
      max-width: 900px;
    }}
    .hero p {{
      max-width: 860px;
      margin: 16px 0 0;
      line-height: 1.6;
      color: rgba(245,251,248,0.92);
      font-size: 17px;
    }}
    .hero-band {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
      margin-top: 22px;
    }}
    .hero-card {{
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 22px;
      padding: 16px 18px;
      backdrop-filter: blur(10px);
    }}
    .hero-card strong {{
      display: block;
      margin-bottom: 8px;
      font-size: 14px;
      letter-spacing: 0.04em;
    }}
    .hero-card span {{
      display: block;
      color: rgba(245,251,248,0.86);
      line-height: 1.55;
      font-size: 14px;
    }}
    .hero-stats {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 18px;
    }}
    .hero-stat {{
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,0.12);
      background: rgba(255,255,255,0.06);
      padding: 14px 16px;
    }}
    .hero-stat strong {{
      display: block;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      color: rgba(245,251,248,0.72);
      margin-bottom: 8px;
    }}
    .hero-stat span {{
      display: block;
      font-size: 15px;
      line-height: 1.45;
      color: rgba(245,251,248,0.92);
    }}
    .content {{
      display: grid;
      gap: 22px;
      margin-top: 22px;
    }}
    .queue-panel {{
      display: grid;
      gap: 16px;
    }}
    .queue-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    .main-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 22px;
      align-items: start;
    }}
    .bottom-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr);
    }}
    .panel {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 22px;
      backdrop-filter: blur(14px);
    }}
    .panel.intake-panel {{
      position: static;
    }}
    .panel h2 {{
      margin: 0 0 14px;
      font-size: 28px;
      line-height: 1.05;
      letter-spacing: -0.03em;
    }}
    .panel h3 {{
      margin: 18px 0 10px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .card-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 16px;
    }}
    .metric {{
      background: var(--paper-strong);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 14px;
    }}
    .metric-label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .metric-value {{
      margin-top: 8px;
      font-size: 26px;
      font-weight: 700;
    }}
    .list {{
      display: grid;
      gap: 10px;
    }}
    .item {{
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--paper-strong);
      padding: 14px;
    }}
    #case-list .item {{
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease, background 120ms ease;
    }}
    #case-list .item:hover {{
      transform: translateY(-1px);
      border-color: rgba(24,76,58,0.24);
      box-shadow: 0 14px 28px rgba(24,76,58,0.08);
    }}
    #case-list .item.active {{
      background: linear-gradient(180deg, #eef7f2, #fffdf8);
      border-color: rgba(24,76,58,0.32);
    }}
    .item strong {{
      display: block;
      margin-bottom: 4px;
    }}
    .muted {{
      color: var(--muted);
    }}
    .tag {{
      display: inline-flex;
      align-items: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 700;
    }}
    .stack {{
      display: grid;
      gap: 22px;
    }}
    #case-detail {{
      padding: 0;
      overflow: hidden;
    }}
    .case-detail-shell {{
      padding: 26px;
      background: linear-gradient(180deg, rgba(255,255,255,0.76), rgba(255,250,244,0.98));
    }}
    .case-address {{
      color: var(--muted);
      font-size: 15px;
      line-height: 1.6;
      margin-top: 10px;
      margin-bottom: 18px;
    }}
    .detail-section {{
      margin-top: 18px;
      padding-top: 18px;
      border-top: 1px solid var(--line);
    }}
    .detail-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .section-subtitle {{
      margin: -4px 0 14px;
      color: var(--muted);
      line-height: 1.55;
      font-size: 14px;
    }}
    .form-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .field {{
      display: grid;
      gap: 6px;
    }}
    .field label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .field input, .field textarea {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(255,255,255,0.92);
      padding: 12px 14px;
      font-size: 14px;
      font-family: inherit;
      color: var(--ink);
    }}
    .field textarea {{
      min-height: 96px;
      resize: vertical;
    }}
    .field.span-2 {{
      grid-column: span 2;
    }}
    .button-row {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 8px;
    }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 42px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.92);
      color: var(--muted);
      font-size: 13px;
      line-height: 1.3;
    }}
    .status-pill.busy {{
      color: var(--accent);
      border-color: rgba(24,76,58,0.24);
      background: #eef7f2;
    }}
    .status-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
      opacity: 0.9;
    }}
    .btn {{
      border: 1px solid var(--accent);
      background: var(--accent);
      color: #fff;
      border-radius: 999px;
      padding: 11px 16px;
      font-size: 14px;
      cursor: pointer;
      box-shadow: 0 10px 24px rgba(24,76,58,0.16);
    }}
    .btn.secondary {{
      background: rgba(255,255,255,0.92);
      color: var(--accent);
    }}
    .code-preview {{
      margin-top: 12px;
      background: rgba(255,255,255,0.92);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      font-size: 12px;
      line-height: 1.55;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 320px;
      overflow: auto;
    }}
    .upload-grid {{
      display: grid;
      gap: 10px;
      margin-top: 10px;
    }}
    .upload-preview {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 10px;
    }}
    .thumb {{
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--paper-strong);
      overflow: hidden;
    }}
    .thumb img {{
      display: block;
      width: 100%;
      height: 160px;
      object-fit: cover;
      background: #f3eee6;
    }}
    .thumb-meta {{
      padding: 10px 12px;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.45;
      word-break: break-word;
    }}
    .insight-card {{
      border-radius: 18px;
      padding: 15px;
      border: 1px solid var(--line);
      background: var(--paper-strong);
    }}
    .insight-card.good {{
      background: linear-gradient(180deg, #eef7f2, #fbfffc);
    }}
    .insight-card.warn {{
      background: linear-gradient(180deg, #fff6ea, #fffdfa);
    }}
    .insight-card strong {{
      display: block;
      margin-bottom: 4px;
    }}
    .analysis-report {{
      margin-top: 14px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(231,240,235,0.55), rgba(255,255,255,0.9));
      line-height: 1.65;
      color: var(--ink);
      font-size: 14px;
    }}
    .analysis-report strong {{
      display: block;
      margin-bottom: 8px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
    }}
    @media (max-width: 980px) {{
      .hero-band {{ grid-template-columns: 1fr; }}
      .hero-stats {{ grid-template-columns: 1fr; }}
      .queue-grid,
      .main-grid,
      .content {{ grid-template-columns: 1fr; }}
      .card-grid {{ grid-template-columns: 1fr; }}
      .detail-grid {{ grid-template-columns: 1fr; }}
      .upload-preview {{ grid-template-columns: 1fr; }}
      .form-grid {{ grid-template-columns: 1fr; }}
      .field.span-2 {{ grid-column: auto; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    __NAV_HTML__
    <section class="hero">
      <div class="eyebrow">Premium Track</div>
      <h1>Single-property premium analysis for buyer decision support.</h1>
      <p>
        This interface is for the high-touch route: one property, one case, with manual inputs,
        AI analysis, and richer hidden context that broad listing platforms do not capture well.
      </p>
      <div class="hero-band">
        <div class="hero-card">
          <strong>What This Track Is For</strong>
          <span>One property at a time. Capture the things public portals miss: floor plan logic, walk feel, slope, privacy, light, and your own inspection notes.</span>
        </div>
        <div class="hero-card">
          <strong>Current Workflow</strong>
          <span>Use the intake form, upload photos and floor plan, then review the live insight and structured draft before we enrich the case further.</span>
        </div>
      </div>
      <div class="hero-stats">
        <div class="hero-stat">
          <strong>Product Mode</strong>
          <span>Premium single-property memo, not mass browsing.</span>
        </div>
        <div class="hero-stat">
          <strong>Data Strategy</strong>
          <span>Manual high-quality input plus structured enrichment.</span>
        </div>
        <div class="hero-stat">
          <strong>Decision Goal</strong>
          <span>Turn one target property into a clear buyer-facing case.</span>
        </div>
      </div>
    </section>
    <section class="content">
      <section class="panel queue-panel">
        <h2>Case Queue</h2>
        <p class="section-subtitle">Start with one featured property case, then build a shortlist of properties worth deeper buyer-side analysis.</p>
        <div class="queue-grid" id="case-list"></div>
      </section>

      <section class="main-grid">
        <aside class="panel intake-panel">
          <h2>Case Intake</h2>
          <p class="section-subtitle">
            Paste a Domain URL as a reference if you have one. This page stores it as metadata only.
            We cannot rely on automatic Domain scraping without an API or explicit access.
          </p>
          <div class="form-grid">
            <div class="field">
              <label for="intake-address">Address</label>
              <input id="intake-address" type="text" placeholder="12 Example Street, Beecroft NSW 2119">
            </div>
            <div class="field">
              <label for="intake-domain-url">Domain URL</label>
              <input id="intake-domain-url" type="url" placeholder="https://www.domain.com.au/...">
            </div>
            <div class="field">
              <label for="intake-price">Sold Price</label>
              <input id="intake-price" type="number" placeholder="2500000">
            </div>
            <div class="field">
              <label for="intake-beds">Bedrooms</label>
              <input id="intake-beds" type="number" placeholder="4">
            </div>
            <div class="field">
              <label for="intake-baths">Bathrooms</label>
              <input id="intake-baths" type="number" placeholder="2">
            </div>
            <div class="field">
              <label for="intake-parking">Parking Spaces</label>
              <input id="intake-parking" type="number" placeholder="2">
            </div>
            <div class="field">
              <label for="intake-orientation">Orientation</label>
              <input id="intake-orientation" type="text" placeholder="North rear">
            </div>
            <div class="field span-2">
              <label for="intake-layout">Layout Summary</label>
              <textarea id="intake-layout" placeholder="Open plan living, kitchen facing yard, bedrooms split across levels..."></textarea>
            </div>
            <div class="field span-2">
              <label for="intake-notes">Inspection Notes</label>
              <textarea id="intake-notes" placeholder="Flat walk to station, quiet street, strong morning light, some road noise from back boundary..."></textarea>
            </div>
            <div class="field">
              <label for="intake-train-name">Nearest Train Station</label>
              <input id="intake-train-name" type="text" placeholder="Beecroft Station">
            </div>
            <div class="field">
              <label for="intake-train-mins">Train Station Minutes</label>
              <input id="intake-train-mins" type="number" placeholder="12">
            </div>
            <div class="field">
              <label for="intake-bus-name">Nearest Bus Stop</label>
              <input id="intake-bus-name" type="text" placeholder="Chapman Ave bus stop">
            </div>
            <div class="field">
              <label for="intake-bus-mins">Bus Stop Minutes</label>
              <input id="intake-bus-mins" type="number" placeholder="4">
            </div>
            <div class="field">
              <label for="intake-shopping-name">Nearest Shopping Centre</label>
              <input id="intake-shopping-name" type="text" placeholder="Beecroft Place">
            </div>
            <div class="field">
              <label for="intake-shopping-mins">Shopping Minutes</label>
              <input id="intake-shopping-mins" type="number" placeholder="10">
            </div>
            <div class="field span-2">
              <label for="intake-schools">Nearby Schools</label>
              <textarea id="intake-schools" placeholder="Beecroft Public School - 9 min walk&#10;Cheltenham Girls High School - 8 min drive"></textarea>
            </div>
            <div class="field span-2">
              <label for="intake-photos">Property Photos</label>
              <input id="intake-photos" type="file" accept="image/*" multiple>
            </div>
            <div class="field span-2">
              <label for="intake-floorplan">Floor Plan</label>
              <input id="intake-floorplan" type="file" accept="image/*,.pdf">
            </div>
            <div class="button-row" style="grid-column: span 2;">
              <button class="btn" id="generate-case">Generate Draft</button>
              <button class="btn secondary" id="run-ai-analysis">Run AI Analysis</button>
              <button class="btn secondary" id="copy-case">Copy JSON</button>
              <div class="status-pill" id="draft-status"><span class="status-dot"></span><span id="draft-status-text">Idle</span></div>
            </div>
          </div>
          <div class="upload-grid">
            <div>
              <h3 style="margin-top:16px;">Photo Preview</h3>
              <div class="upload-preview" id="photo-preview"></div>
            </div>
            <div>
              <h3 style="margin-top:16px;">Floor Plan Preview</h3>
              <div class="upload-preview" id="floorplan-preview"></div>
            </div>
          </div>
          <h3 style="margin-top:16px;">Structured Draft</h3>
          <div class="code-preview" id="case-preview">Fill the form to generate a structured premium case draft.</div>
        </aside>
      </section>

      <section class="bottom-grid">
        <section class="panel" id="case-detail"></section>
        <section class="panel">
          <h2>Live Insight</h2>
          <p class="section-subtitle">A quick first-pass reading based on the details you have entered so far. This is meant to surface what looks strong, what remains risky, and what still needs to be checked.</p>
          <div class="list" id="draft-insight"></div>
          <div class="analysis-report" id="analysis-report"><strong>AI Analysis</strong>Run a deeper analysis to turn the current draft into a more buyer-facing memo.</div>
        </section>
      </section>
    </section>
  </div>
  <script>
    const payload = __PAYLOAD__;
    const currency = new Intl.NumberFormat('en-AU', {{
      style: 'currency',
      currency: 'AUD',
      maximumFractionDigits: 0
    }});

    function formatMoney(value) {{
      if (value === null || value === undefined) return 'TBD';
      return currency.format(value);
    }}

    function renderCase(caseItem) {{
      const detail = document.getElementById('case-detail');
      detail.innerHTML = `
        <div class="case-detail-shell">
          <div class="tag">${{caseItem.status}}</div>
          <h2 style="margin-top:14px; font-size: clamp(30px, 4vw, 44px); line-height: 0.98; letter-spacing: -0.04em;">${{caseItem.title}}</h2>
          <div class="case-address">${{caseItem.address}}</div>
          <div class="card-grid">
            <div class="metric">
              <div class="metric-label">Sold Price</div>
              <div class="metric-value">${{formatMoney(caseItem.sold_price)}}</div>
            </div>
            <div class="metric">
              <div class="metric-label">Property Type</div>
              <div class="metric-value">${{caseItem.property_type || 'TBD'}}</div>
            </div>
            <div class="metric">
              <div class="metric-label">Bedrooms</div>
              <div class="metric-value">${{caseItem.bedrooms ?? 'TBD'}}</div>
            </div>
            <div class="metric">
              <div class="metric-label">Bathrooms</div>
              <div class="metric-value">${{caseItem.bathrooms ?? 'TBD'}}</div>
            </div>
          </div>

          <div class="detail-section">
            <div class="detail-grid">
              <div>
                <h3>Floor Plan Notes</h3>
                <div class="list">
                  ${(caseItem.floor_plan_notes || []).map(item => `<div class="item">${{item}}</div>`).join('') || '<div class="item"><span class="muted">No floor plan notes yet.</span></div>'}
                </div>
              </div>
              <div>
                <h3>Manual Inputs Needed</h3>
                <div class="list">
                  ${(caseItem.manual_inputs_needed || []).map(item => `<div class="item"><strong>${{item}}</strong><span class="muted">To be captured during inspection or from floor plan.</span></div>`).join('') || '<div class="item"><span class="muted">No manual inputs listed.</span></div>'}
                </div>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <div class="detail-grid">
              <div>
                <h3>Inspection Notes</h3>
                <div class="list">
                  ${(caseItem.inspection_notes || []).map(item => `<div class="item">${{item}}</div>`).join('') || '<div class="item"><span class="muted">No inspection notes yet.</span></div>'}
                </div>
              </div>
              <div>
                <h3>Accessibility</h3>
                <div class="list">
                  <div class="item"><strong>Train Station</strong><span class="muted">${{caseItem.accessibility?.nearest_train_station?.name || 'TBD'}} | ${{caseItem.accessibility?.nearest_train_station?.travel_time_minutes ?? 'TBD'}} min</span></div>
                  <div class="item"><strong>Bus Stop</strong><span class="muted">${{caseItem.accessibility?.nearest_bus_stop?.name || 'TBD'}} | ${{caseItem.accessibility?.nearest_bus_stop?.travel_time_minutes ?? 'TBD'}} min</span></div>
                  <div class="item"><strong>Shopping Centre</strong><span class="muted">${{caseItem.accessibility?.nearest_shopping_centre?.name || 'TBD'}} | ${{caseItem.accessibility?.nearest_shopping_centre?.travel_time_minutes ?? 'TBD'}} min</span></div>
                </div>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <div class="detail-grid">
              <div>
                <h3>Nearby Schools</h3>
                <div class="list">
                  ${(caseItem.schools || []).length
                    ? (caseItem.schools || []).map(item => `<div class="item">${{item}}</div>`).join('')
                    : '<div class="item"><span class="muted">No school notes added yet.</span></div>'}
                </div>
              </div>
              <div>
                <h3>Decision Summary</h3>
                <div class="list">
                  <div class="item"><strong>Overall View</strong><span class="muted">${{caseItem.decision_summary?.overall_view || 'TBD'}}</span></div>
                  <div class="item"><strong>Strengths</strong><span class="muted">${{(caseItem.decision_summary?.strengths || []).join(' | ') || 'TBD'}}</span></div>
                  <div class="item"><strong>Risks</strong><span class="muted">${{(caseItem.decision_summary?.risks || []).join(' | ') || 'TBD'}}</span></div>
                  <div class="item"><strong>Next Actions</strong><span class="muted">${{(caseItem.decision_summary?.next_actions || []).join(' | ') || 'TBD'}}</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    }}

    function renderCaseList() {{
      const list = document.getElementById('case-list');
      list.innerHTML = (payload.records || []).map((item, index) => `
        <div class="item ${index === 0 ? 'active' : ''}" data-index="${{index}}">
          <strong>${{item.title}}</strong>
          <div class="muted">${{item.address}}</div>
          <div class="muted" style="margin-top:10px; font-size:12px; text-transform:uppercase; letter-spacing:0.08em;">${{formatMoney(item.sold_price)}}</div>
        </div>
      `).join('');

      Array.from(list.querySelectorAll('.item')).forEach(node => {{
        node.addEventListener('click', () => {{
          Array.from(list.querySelectorAll('.item')).forEach(card => card.classList.remove('active'));
          node.classList.add('active');
          const index = Number(node.getAttribute('data-index'));
          renderCase(payload.records[index]);
        }});
      }});
    }}

    function slugify(value) {{
      return String(value || '')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
    }}

    function parseAddressParts(address) {{
      const text = String(address || '').trim();
      const parts = text.split(',');
      const first = parts[0] || '';
      const rest = parts.slice(1).join(' ').trim();
      const suburbMatch = rest.match(/([A-Za-z ]+)\s+NSW\s+(\d{{4}})/i);
      return {{
        title: first || text,
        suburb: suburbMatch ? suburbMatch[1].trim() : null,
        postcode: suburbMatch ? suburbMatch[2] : null
      }};
    }}

    function buildDraftCase() {{
      const address = document.getElementById('intake-address').value.trim();
      const domainUrl = document.getElementById('intake-domain-url').value.trim();
      const soldPrice = document.getElementById('intake-price').value.trim();
      const bedrooms = document.getElementById('intake-beds').value.trim();
      const bathrooms = document.getElementById('intake-baths').value.trim();
      const parking = document.getElementById('intake-parking').value.trim();
      const orientation = document.getElementById('intake-orientation').value.trim();
      const layout = document.getElementById('intake-layout').value.trim();
      const notes = document.getElementById('intake-notes').value.trim();
      const trainName = document.getElementById('intake-train-name').value.trim();
      const trainMins = document.getElementById('intake-train-mins').value.trim();
      const busName = document.getElementById('intake-bus-name').value.trim();
      const busMins = document.getElementById('intake-bus-mins').value.trim();
      const shoppingName = document.getElementById('intake-shopping-name').value.trim();
      const shoppingMins = document.getElementById('intake-shopping-mins').value.trim();
      const schoolsText = document.getElementById('intake-schools').value.trim();
      const photoFiles = Array.from(document.getElementById('intake-photos').files || []);
      const floorPlanFiles = Array.from(document.getElementById('intake-floorplan').files || []);
      const parsed = parseAddressParts(address);

      return {{
        case_id: slugify(address) || 'new-property-case',
        status: 'draft',
        title: parsed.title ? `${{parsed.title}} Review` : 'New Property Review',
        address: address || null,
        suburb: parsed.suburb,
        postcode: parsed.postcode,
        sold_price: soldPrice ? Number(soldPrice) : null,
        bedrooms: bedrooms ? Number(bedrooms) : null,
        bathrooms: bathrooms ? Number(bathrooms) : null,
        parking_spaces: parking ? Number(parking) : null,
        property_type: null,
        land_size_sqm: null,
        building_size_sqm: null,
        orientation: orientation || null,
        layout_summary: layout || null,
        source_links: {{
          domain_url: domainUrl || null
        }},
        uploaded_assets: {{
          property_photos: photoFiles.map(file => ({{
            filename: file.name,
            size_bytes: file.size,
            mime_type: file.type || null
          }})),
          floor_plans: floorPlanFiles.map(file => ({{
            filename: file.name,
            size_bytes: file.size,
            mime_type: file.type || null
          }}))
        }},
        floor_plan_notes: layout ? [layout] : [],
        inspection_notes: notes ? [notes] : [],
        manual_inputs_needed: [
          'property_type',
          'floor_plan',
          'room_sizes',
          'light_quality',
          'noise_level',
          'slope_feel'
        ],
        accessibility: {{
          nearest_train_station: {{
            name: trainName || null,
            travel_time_minutes: trainMins ? Number(trainMins) : null,
            walking_distance_km: null,
            walk_flatness: null
          }},
          nearest_bus_stop: {{
            name: busName || null,
            travel_time_minutes: busMins ? Number(busMins) : null
          }},
          nearest_shopping_centre: {{
            name: shoppingName || null,
            travel_time_minutes: shoppingMins ? Number(shoppingMins) : null
          }}
        }},
        schools: schoolsText ? schoolsText.split('\n').map(item => item.trim()).filter(Boolean) : [],
        ai_tasks: [
          'Enrich train, bus, shopping centre, and school proximity.',
          'Summarise layout strengths and weaknesses.',
          'Generate a buyer-focused decision memo.'
        ],
        decision_summary: {{
          overall_view: 'Draft only. Needs enrichment and manual inspection detail.',
          strengths: [],
          risks: [],
          next_actions: [
            'Verify property details from listing or inspection.',
            'Add floor plan and room measurements.',
            'Enrich transport, shopping, and school context.'
          ]
        }}
      }};
    }}

    function buildDraftInsight(draft) {{
      const strengths = [];
      const risks = [];
      const nextQuestions = [];
      let score = 0;

      if (draft.orientation) {{
        strengths.push(`Orientation noted: ${draft.orientation}`);
        score += 1;
      }} else {{
        risks.push('Orientation has not been captured yet.');
      }}

      if (draft.bedrooms !== null && draft.bathrooms !== null) {{
        strengths.push(`Core room count captured: ${draft.bedrooms} bed / ${draft.bathrooms} bath.`);
        score += 1;
      }} else {{
        risks.push('Bedroom and bathroom count still incomplete.');
      }}

      if (draft.parking_spaces !== null) {{
        strengths.push(`Parking captured: ${draft.parking_spaces} space(s).`);
        score += 1;
      }} else {{
        nextQuestions.push('Confirm off-street parking or garage situation.');
      }}

      if ((draft.uploaded_assets?.property_photos || []).length > 0) {{
        strengths.push(`Property photos uploaded: ${(draft.uploaded_assets.property_photos || []).length}.`);
        score += 1;
      }} else {{
        nextQuestions.push('Upload property photos to assess light, condition, and privacy.');
      }}

      if ((draft.uploaded_assets?.floor_plans || []).length > 0) {{
        strengths.push('Floor plan uploaded and ready for layout review.');
        score += 1;
      }} else {{
        risks.push('No floor plan uploaded yet, so layout analysis is limited.');
      }}

      if (draft.layout_summary) {{
        strengths.push('Layout summary provided, which improves early analysis quality.');
        score += 1;
      }} else {{
        nextQuestions.push('Add a brief layout summary: living flow, bedroom separation, and outdoor connection.');
      }}

      if ((draft.inspection_notes || []).length > 0) {{
        strengths.push('Inspection notes captured for subjective assessment.');
        score += 1;
      }} else {{
        nextQuestions.push('Add inspection notes for noise, light, slope, privacy, and street feel.');
      }}

      if (draft.accessibility?.nearest_train_station?.travel_time_minutes !== null) {{
        strengths.push(`Train access captured: ${draft.accessibility.nearest_train_station.travel_time_minutes} minutes.`);
        score += 1;
      }} else {{
        nextQuestions.push('Add nearest train station and walking time.');
      }}

      if (draft.accessibility?.nearest_bus_stop?.travel_time_minutes !== null) {{
        strengths.push(`Bus access captured: ${draft.accessibility.nearest_bus_stop.travel_time_minutes} minutes.`);
      }} else {{
        nextQuestions.push('Add nearest bus stop and walking time.');
      }}

      if (draft.accessibility?.nearest_shopping_centre?.travel_time_minutes !== null) {{
        strengths.push(`Shopping convenience captured: ${draft.accessibility.nearest_shopping_centre.travel_time_minutes} minutes.`);
        score += 1;
      }} else {{
        nextQuestions.push('Add nearest shopping centre and travel time.');
      }}

      if ((draft.schools || []).length > 0) {{
        strengths.push(`Nearby school notes captured: ${(draft.schools || []).length}.`);
        score += 1;
      }} else {{
        nextQuestions.push('Add nearby schools and approximate travel or walking time.');
      }}

      if (draft.source_links?.domain_url) {{
        strengths.push('Domain reference URL attached for manual cross-checking.');
      }}

      const overall = score >= 7
        ? 'Good early draft. This is starting to look like a serious buyer-side memo.'
        : score >= 4
          ? 'Useful draft, but still missing a few pieces that affect real confidence.'
          : 'Early draft only. More structure is needed before the case becomes decision-ready.';

      return {{ overall, strengths, risks, nextQuestions, score: Math.round((score / 10) * 100) }};
    }}

    function renderDraftInsight(draft) {{
      const insight = buildDraftInsight(draft);
      document.getElementById('draft-insight').setAttribute('data-score', String(insight.score));
      const node = document.getElementById('draft-insight');
      node.innerHTML = `
        <div class="insight-card good">
          <strong>Case Readiness</strong>
          <span class="muted">${{insight.score}} / 100 | ${{insight.overall}}</span>
        </div>
        <div class="insight-card good">
          <strong>Strengths</strong>
          <span class="muted">${{insight.strengths.length ? insight.strengths.join(' | ') : 'No strengths identified yet.'}}</span>
        </div>
        <div class="insight-card warn">
          <strong>Risks</strong>
          <span class="muted">${{insight.risks.length ? insight.risks.join(' | ') : 'No major risks identified yet.'}}</span>
        </div>
        <div class="insight-card">
          <strong>Next Questions</strong>
          <span class="muted">${{insight.nextQuestions.length ? insight.nextQuestions.join(' | ') : 'No immediate questions. Ready for deeper enrichment.'}}</span>
        </div>
      `;
    }}

    function buildAiMemo(draft) {{
      const positives = [];
      const concerns = [];
      const nextSteps = [];

      if (draft.orientation) {{
        positives.push(`orientation is already captured as ${draft.orientation}`);
      }} else {{
        concerns.push('orientation is still missing, which makes light and outdoor usability harder to judge');
      }}

      if (draft.bedrooms !== null && draft.bathrooms !== null) {{
        positives.push(`the room count is clear at ${draft.bedrooms} bedrooms and ${draft.bathrooms} bathrooms`);
      }} else {{
        concerns.push('core bedroom and bathroom counts are incomplete');
      }}

      if (draft.parking_spaces !== null) {{
        positives.push(`parking is documented at ${draft.parking_spaces} space(s)`);
      }} else {{
        nextSteps.push('confirm garage, carport, or off-street parking details');
      }}

      if (draft.layout_summary) {{
        positives.push('a layout summary is present, which gives us an early read on flow and zoning');
      }} else {{
        nextSteps.push('add a layout summary covering living flow, bedroom separation, and outdoor connection');
      }}

      if ((draft.inspection_notes || []).length > 0) {{
        positives.push('inspection notes are present, which improves decision quality beyond listing data');
      }} else {{
        concerns.push('there are no inspection notes yet, so noise, privacy, slope, and feel remain unclear');
      }}

      if ((draft.uploaded_assets?.floor_plans || []).length > 0) {{
        positives.push('a floor plan has been uploaded, which makes deeper layout analysis possible');
      }} else {{
        concerns.push('no floor plan has been uploaded yet');
      }}

      if ((draft.uploaded_assets?.property_photos || []).length > 0) {{
        positives.push(`there are ${(draft.uploaded_assets.property_photos || []).length} property photos available for visual review`);
      }} else {{
        nextSteps.push('upload property photos so condition, light, and privacy can be reviewed properly');
      }}

      if (draft.accessibility?.nearest_train_station?.travel_time_minutes !== null) {{
        positives.push(`train access is noted at ${draft.accessibility.nearest_train_station.travel_time_minutes} minutes`);
      }} else {{
        nextSteps.push('add walking time to the nearest train station');
      }}

      if (draft.accessibility?.nearest_shopping_centre?.travel_time_minutes !== null) {{
        positives.push(`shopping access is noted at ${draft.accessibility.nearest_shopping_centre.travel_time_minutes} minutes`);
      }} else {{
        nextSteps.push('add travel time to the nearest shopping centre');
      }}

      if ((draft.schools || []).length > 0) {{
        positives.push(`school context is partly covered with ${(draft.schools || []).length} school note(s)`);
      }} else {{
        nextSteps.push('add nearby school notes if family use matters for this property');
      }}

      const summary = positives.length >= 5
        ? 'This case is already strong enough for a meaningful first buyer memo.'
        : 'This case is promising, but it still needs more structure before it becomes a confident decision document.';

      return {{
        summary,
        positives,
        concerns,
        nextSteps: Array.from(new Set(nextSteps)).slice(0, 5)
      }};
    }}

    function renderAiMemoResult(result) {{
      const node = document.getElementById('analysis-report');
      const modeLabel = result.mode === 'openai' ? 'OpenAI Analysis' : 'Local Analysis';
      const report = result.report || 'No analysis text returned.';
      const fallback = result.fallback_reason ? `<div style="margin-top:10px; color:#6f6659;"><b>Fallback:</b> ${result.fallback_reason}</div>` : '';
      node.innerHTML = `
        <strong>${modeLabel}</strong>
        <div style="white-space: pre-wrap;">${report}</div>
        ${fallback}
      `;
    }}

    function renderFilePreview(inputId, targetId, kind) {{
      const files = Array.from(document.getElementById(inputId).files || []);
      const target = document.getElementById(targetId);

      if (files.length === 0) {{
        target.innerHTML = '<div class="item muted">No files selected yet.</div>';
        return;
      }}

      target.innerHTML = '';
      files.forEach(file => {{
        const wrapper = document.createElement('div');
        wrapper.className = 'thumb';

        const meta = document.createElement('div');
        meta.className = 'thumb-meta';
        meta.textContent = `${{file.name}} | ${{Math.round(file.size / 1024)}} KB`;

        if (file.type && file.type.startsWith('image/')) {{
          const img = document.createElement('img');
          img.alt = file.name;
          img.src = URL.createObjectURL(file);
          wrapper.appendChild(img);
        }} else {{
          const placeholder = document.createElement('div');
          placeholder.style.height = '160px';
          placeholder.style.display = 'grid';
          placeholder.style.placeItems = 'center';
          placeholder.style.background = '#f3eee6';
          placeholder.style.fontSize = '14px';
          placeholder.style.color = '#6c6356';
          placeholder.textContent = kind === 'floorplan' ? 'Floor plan file selected' : 'File selected';
          wrapper.appendChild(placeholder);
        }}

        wrapper.appendChild(meta);
        target.appendChild(wrapper);
      }});
    }}

    function refreshDraftPreview() {{
      const draft = buildDraftCase();
      document.getElementById('case-preview').textContent = JSON.stringify(draft, null, 2);
      renderFilePreview('intake-photos', 'photo-preview', 'photo');
      renderFilePreview('intake-floorplan', 'floorplan-preview', 'floorplan');
      renderDraftInsight(draft);
    }}

    function setDraftStatus(text, busy = false) {{
      const pill = document.getElementById('draft-status');
      const label = document.getElementById('draft-status-text');
      label.textContent = text;
      pill.classList.toggle('busy', busy);
    }}

    async function runDraftGeneration() {{
      const generateBtn = document.getElementById('generate-case');
      generateBtn.disabled = true;
      generateBtn.textContent = 'Analyzing...';
      setDraftStatus('Analyzing input and generating draft', true);

      await new Promise(resolve => setTimeout(resolve, 320));
      refreshDraftPreview();

      const preview = document.getElementById('case-preview');
      preview.scrollIntoView({ behavior: 'smooth', block: 'center' });

      generateBtn.disabled = false;
      generateBtn.textContent = 'Generate Draft';
      setDraftStatus('Draft generated locally. No LLM call yet.', false);
    }}

    async function runAiAnalysis() {{
      const analysisBtn = document.getElementById('run-ai-analysis');
      analysisBtn.disabled = true;
      analysisBtn.textContent = 'Analyzing...';
      const draft = buildDraftCase();
      setDraftStatus('Running deeper analysis on current draft', true);

      try {{
        const response = await fetch('/api/premium-analysis', {{
          method: 'POST',
          headers: {{
            'Content-Type': 'application/json'
          }},
          body: JSON.stringify({{ draft }})
        }});

        const payload = await response.json();
        if (!response.ok || !payload.ok) {{
          throw new Error(payload.error || 'Premium analysis failed');
        }}

        renderAiMemoResult(payload.analysis);
        document.getElementById('analysis-report').scrollIntoView({ behavior: 'smooth', block: 'center' });
        setDraftStatus(
          payload.analysis.mode === 'openai'
            ? 'Analysis complete with OpenAI.'
            : 'Analysis complete with local fallback.',
          false
        );
      }} catch (err) {{
        const fallback = buildAiMemo(draft);
        renderAiMemoResult({{
          mode: 'local_fallback',
          report:
            `Summary: ${fallback.summary}\\n\\n` +
            `What looks good: ${fallback.positives.length ? fallback.positives.join(' | ') : 'Not enough strong signals yet.'}\\n\\n` +
            `What still feels weak: ${fallback.concerns.length ? fallback.concerns.join(' | ') : 'No obvious weak spots from the current draft.'}\\n\\n` +
            `What to verify next: ${fallback.nextSteps.length ? fallback.nextSteps.join(' | ') : 'The current draft is ready for a deeper manual review.'}`,
          fallback_reason: err.message
        }});
        setDraftStatus('Analysis completed with client-side fallback.', false);
      }} finally {{
        analysisBtn.disabled = false;
        analysisBtn.textContent = 'Run AI Analysis';
      }}
    }}

    function wireIntake() {{
      const ids = [
        'intake-address',
        'intake-domain-url',
        'intake-price',
        'intake-beds',
        'intake-baths',
        'intake-parking',
        'intake-orientation',
        'intake-layout',
        'intake-notes',
        'intake-train-name',
        'intake-train-mins',
        'intake-bus-name',
        'intake-bus-mins',
        'intake-shopping-name',
        'intake-shopping-mins',
        'intake-schools'
      ];
      ids.forEach(id => {{
        const node = document.getElementById(id);
        node.addEventListener('input', refreshDraftPreview);
      }});
      document.getElementById('intake-photos').addEventListener('change', refreshDraftPreview);
      document.getElementById('intake-floorplan').addEventListener('change', refreshDraftPreview);

      document.getElementById('generate-case').addEventListener('click', async () => {{
        await runDraftGeneration();
      }});
      document.getElementById('run-ai-analysis').addEventListener('click', async () => {{
        await runAiAnalysis();
      }});
      document.getElementById('copy-case').addEventListener('click', async () => {{
        const text = document.getElementById('case-preview').textContent;
        try {{
          await navigator.clipboard.writeText(text);
          document.getElementById('copy-case').textContent = 'Copied';
          setTimeout(() => {{
            document.getElementById('copy-case').textContent = 'Copy JSON';
          }}, 1200);
        }} catch (err) {{
          document.getElementById('case-preview').textContent = text + "\\n\\nClipboard copy failed. You can still copy this JSON manually.";
        }}
      }});

      refreshDraftPreview();
      renderAiMemoResult({{
        mode: 'local_preview',
        report: 'Run a deeper analysis to turn the current draft into a more buyer-facing memo.'
      }});
      setDraftStatus('Ready. Generate a local draft from current inputs.', false);
    }}

    renderCaseList();
    if ((payload.records || []).length > 0) {{
      renderCase(payload.records[0]);
    }}
    wireIntake();
  </script>
</body>
</html>
""".replace("{{", "{").replace("}}", "}").replace("__NAV_HTML__", nav_html).replace("__PAYLOAD__", payload_json)


def build_local_premium_analysis(draft):
    positives = []
    concerns = []
    next_steps = []

    if draft.get("orientation"):
        positives.append(f"Orientation is captured as {draft['orientation']}.")
    else:
        concerns.append("Orientation is still missing, so light and outdoor usability are harder to judge.")

    bedrooms = draft.get("bedrooms")
    bathrooms = draft.get("bathrooms")
    if bedrooms is not None and bathrooms is not None:
        positives.append(f"Core room count is clear at {bedrooms} bedrooms and {bathrooms} bathrooms.")
    else:
        concerns.append("Bedroom and bathroom counts are still incomplete.")

    parking = draft.get("parking_spaces")
    if parking is not None:
        positives.append(f"Parking is documented at {parking} space(s).")
    else:
        next_steps.append("Confirm garage, carport, or off-street parking details.")

    if draft.get("layout_summary"):
        positives.append("A layout summary is present, which gives an early read on flow and zoning.")
    else:
        next_steps.append("Add a layout summary covering living flow, bedroom separation, and outdoor connection.")

    if draft.get("inspection_notes"):
        positives.append("Inspection notes are present, which improves decision quality beyond listing data.")
    else:
        concerns.append("There are no inspection notes yet, so noise, privacy, slope, and feel remain unclear.")

    uploaded_assets = draft.get("uploaded_assets") or {}
    if uploaded_assets.get("floor_plans"):
        positives.append("A floor plan has been uploaded, which makes deeper layout analysis possible.")
    else:
        concerns.append("No floor plan has been uploaded yet.")

    if uploaded_assets.get("property_photos"):
        positives.append(f"There are {len(uploaded_assets['property_photos'])} property photos available for visual review.")
    else:
        next_steps.append("Upload property photos so condition, light, and privacy can be reviewed properly.")

    access = draft.get("accessibility") or {}
    train = (access.get("nearest_train_station") or {}).get("travel_time_minutes")
    shopping = (access.get("nearest_shopping_centre") or {}).get("travel_time_minutes")
    if train is not None:
        positives.append(f"Train access is noted at {train} minutes.")
    else:
        next_steps.append("Add walking time to the nearest train station.")

    if shopping is not None:
        positives.append(f"Shopping access is noted at {shopping} minutes.")
    else:
        next_steps.append("Add travel time to the nearest shopping centre.")

    schools = draft.get("schools") or []
    if schools:
        positives.append(f"School context is partly covered with {len(schools)} school note(s).")
    else:
        next_steps.append("Add nearby school notes if family use matters for this property.")

    summary = (
        "This case is already strong enough for a meaningful first buyer memo."
        if len(positives) >= 5
        else "This case is promising, but it still needs more structure before it becomes a confident decision document."
    )

    return {
        "mode": "local_fallback",
        "summary": summary,
        "positives": positives,
        "concerns": concerns,
        "next_steps": list(dict.fromkeys(next_steps))[:5],
        "report": (
            f"Summary: {summary}\n\n"
            f"What looks good: {' | '.join(positives) if positives else 'Not enough strong signals yet.'}\n\n"
            f"What still feels weak: {' | '.join(concerns) if concerns else 'No obvious weak spots from the current draft.'}\n\n"
            f"What to verify next: {' | '.join(list(dict.fromkeys(next_steps))[:5]) if next_steps else 'The current draft is ready for a deeper manual review.'}"
        ),
    }


def run_openai_premium_analysis(draft):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    prompt = (
        "You are a property-buying analyst helping a home buyer review a single property case. "
        "Write a concise, practical analysis with 4 sections: Summary, What looks good, "
        "What still feels weak, What to verify next. Focus on decision usefulness, not hype.\n\n"
        f"Property case JSON:\n{json.dumps(draft, ensure_ascii=False, indent=2)}"
    )

    request_body = {
        "model": "gpt-4.1-mini",
        "input": prompt,
    }

    req = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    text = ""
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text += content.get("text", "")

    text = text.strip()
    if not text:
        raise RuntimeError("OpenAI response did not include analysis text")

    return {
        "mode": "openai",
        "report": text,
    }


class DashboardHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            payload = load_comparable_payload()
            if payload is None:
                self._send_html("<h1>Missing data files</h1><p>Build a dataset first.</p>", status=500)
                return
            self._send_html(render_comparable_sales_html(payload))
            return

        if parsed.path == "/premium":
            payload = load_property_cases_payload()
            self._send_html(render_property_cases_html(payload))
            return

        if parsed.path == "/api/comparable-sales":
            payload = load_json(COMPARABLE_SALES_FILE)
            if payload is None:
                self._send_json({"error": "Missing comparable sales dataset"}, status=404)
                return
            self._send_json(payload)
            return

        if parsed.path == "/api/property-cases":
            self._send_json(load_property_cases_payload())
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/premium-analysis":
            try:
                payload = self._read_json_body()
                draft = payload.get("draft") or {}

                try:
                    analysis = run_openai_premium_analysis(draft)
                except Exception as llm_error:
                    analysis = build_local_premium_analysis(draft)
                    analysis["fallback_reason"] = str(llm_error)

                self._send_json({"ok": True, "analysis": analysis})
                return
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=500)
                return

        self._send_json({"error": "Not found"}, status=404)


def main():
    server = HTTPServer((HOST, PORT), DashboardHandler)
    print(f"Dashboard running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
