"""Generate a visual HTML test results dashboard with pass/fail pie chart."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "dashboard.html"
DEFAULT_JSON = PROJECT_ROOT / "reports" / "results.json"

OUTCOME_COLORS = {
    "passed": "#22c55e",
    "failed": "#ef4444",
    "skipped": "#f59e0b",
    "error": "#8b5cf6",
}


@dataclass
class TestResult:
    nodeid: str
    outcome: str
    duration: float
    module: str


def summarize(results: list[TestResult]) -> dict[str, Any]:
    counts = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
    for result in results:
        outcome = result.outcome if result.outcome in counts else "error"
        counts[outcome] += 1

    total = len(results)
    executed = counts["passed"] + counts["failed"] + counts["error"]
    pass_rate = round((counts["passed"] / executed * 100), 1) if executed else 0.0

    by_module: dict[str, dict[str, int]] = {}
    for result in results:
        module_stats = by_module.setdefault(
            result.module,
            {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "total": 0},
        )
        outcome = result.outcome if result.outcome in counts else "error"
        module_stats[outcome] += 1
        module_stats["total"] += 1

    return {
        "total": total,
        "counts": counts,
        "pass_rate": pass_rate,
        "by_module": by_module,
    }


def _format_duration(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _build_rows(results: list[TestResult]) -> str:
    rows = []
    for result in sorted(results, key=lambda item: (item.module, item.nodeid)):
        color = OUTCOME_COLORS.get(result.outcome, OUTCOME_COLORS["error"])
        short_name = result.nodeid.split("::")[-1]
        rows.append(
            f"""
            <tr>
              <td>{escape(result.module)}</td>
              <td>{escape(short_name)}</td>
              <td><span class="badge" style="background:{color}">{escape(result.outcome)}</span></td>
              <td>{result.duration:.2f}s</td>
            </tr>"""
        )
    return "\n".join(rows)


def generate_dashboard(
    results: list[TestResult],
    *,
    output_path: Path = DEFAULT_OUTPUT,
    json_path: Path = DEFAULT_JSON,
    started_at: datetime | None = None,
    duration_seconds: float = 0.0,
    exit_status: int = 0,
) -> Path:
    """Write dashboard.html and results.json from collected pytest outcomes."""
    summary = summarize(results)
    counts = summary["counts"]
    labels = [key.title() for key, value in counts.items() if value > 0]
    values = [value for value in counts.values() if value > 0]
    colors = [OUTCOME_COLORS[key] for key, value in counts.items() if value > 0]

    started = started_at or datetime.now(timezone.utc)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "started_at": started.isoformat(),
        "duration_seconds": duration_seconds,
        "exit_status": exit_status,
        "summary": summary,
        "results": [asdict(result) for result in results],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    status_label = "PASSED" if exit_status == 0 else "FAILED"
    status_color = OUTCOME_COLORS["passed"] if exit_status == 0 else OUTCOME_COLORS["failed"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Dream Team Test Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #1e293b;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --border: #334155;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", system-ui, sans-serif;
      background: linear-gradient(160deg, #0f172a 0%, #1e293b 100%);
      color: var(--text);
      min-height: 100vh;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem 3rem; }}
    header {{
      display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
      gap: 1rem; margin-bottom: 2rem;
    }}
    h1 {{ margin: 0; font-size: 1.75rem; }}
    .subtitle {{ color: var(--muted); margin-top: 0.35rem; }}
    .status-pill {{
      padding: 0.5rem 1rem; border-radius: 999px; font-weight: 700;
      background: {status_color}; color: #fff;
    }}
    .cards {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 1rem; margin-bottom: 2rem;
    }}
    .card {{
      background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
      padding: 1rem 1.25rem;
    }}
    .card .label {{ color: var(--muted); font-size: 0.85rem; }}
    .card .value {{ font-size: 1.75rem; font-weight: 700; margin-top: 0.25rem; }}
    .grid {{
      display: grid; grid-template-columns: 1fr 1.2fr; gap: 1.5rem; margin-bottom: 2rem;
    }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    .panel {{
      background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
      padding: 1.25rem;
    }}
    .panel h2 {{ margin: 0 0 1rem; font-size: 1.1rem; }}
    .chart-wrap {{ max-width: 360px; margin: 0 auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ padding: 0.65rem 0.5rem; border-bottom: 1px solid var(--border); text-align: left; }}
    th {{ color: var(--muted); font-weight: 600; }}
    .badge {{
      display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px;
      color: #fff; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
    }}
    .links {{ margin-top: 1rem; }}
    .links a {{ color: #60a5fa; text-decoration: none; }}
    .links a:hover {{ text-decoration: underline; }}
    .module-grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;
    }}
    .module-card {{
      background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border);
      border-radius: 10px; padding: 1rem;
    }}
    .module-card h3 {{ margin: 0 0 0.5rem; font-size: 0.95rem; }}
    .module-stats {{ color: var(--muted); font-size: 0.85rem; line-height: 1.6; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>Dream Team Test Dashboard</h1>
        <p class="subtitle">
          Run: {escape(started.strftime("%Y-%m-%d %H:%M:%S UTC"))}
          &nbsp;|&nbsp; Duration: {_format_duration(duration_seconds)}
        </p>
      </div>
      <div class="status-pill">{status_label}</div>
    </header>

    <div class="cards">
      <div class="card"><div class="label">Total</div><div class="value">{summary["total"]}</div></div>
      <div class="card"><div class="label">Passed</div><div class="value" style="color:{OUTCOME_COLORS["passed"]}">{counts["passed"]}</div></div>
      <div class="card"><div class="label">Failed</div><div class="value" style="color:{OUTCOME_COLORS["failed"]}">{counts["failed"]}</div></div>
      <div class="card"><div class="label">Skipped</div><div class="value" style="color:{OUTCOME_COLORS["skipped"]}">{counts["skipped"]}</div></div>
      <div class="card"><div class="label">Pass rate</div><div class="value">{summary["pass_rate"]}%</div></div>
    </div>

    <div class="grid">
      <div class="panel">
        <h2>Results overview</h2>
        <div class="chart-wrap">
          <canvas id="resultsPie"></canvas>
        </div>
        <p class="links"><a href="report.html">Open detailed pytest-html report</a></p>
      </div>
      <div class="panel">
        <h2>By module</h2>
        <div class="module-grid">
          {_build_module_cards(summary["by_module"])}
        </div>
      </div>
    </div>

    <div class="panel">
      <h2>All tests</h2>
      <table>
        <thead>
          <tr><th>Module</th><th>Test</th><th>Status</th><th>Duration</th></tr>
        </thead>
        <tbody>
          {_build_rows(results)}
        </tbody>
      </table>
    </div>
  </div>

  <script>
    const ctx = document.getElementById("resultsPie");
    new Chart(ctx, {{
      type: "pie",
      data: {{
        labels: {json.dumps(labels)},
        datasets: [{{
          data: {json.dumps(values)},
          backgroundColor: {json.dumps(colors)},
          borderColor: "#1e293b",
          borderWidth: 2
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ position: "bottom", labels: {{ color: "#e2e8f0", padding: 16 }} }},
          tooltip: {{
            callbacks: {{
              label: (ctx) => {{
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const pct = total ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                return `${{ctx.label}}: ${{ctx.raw}} (${{pct}}%)`;
              }}
            }}
          }}
        }}
      }}
    }});
  </script>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    return output_path


def _build_module_cards(by_module: dict[str, dict[str, int]]) -> str:
    cards = []
    for module, stats in sorted(by_module.items()):
        cards.append(
            f"""
            <div class="module-card">
              <h3>{escape(module)}</h3>
              <div class="module-stats">
                Total: {stats["total"]}<br />
                Passed: {stats["passed"]}<br />
                Failed: {stats["failed"]}<br />
                Skipped: {stats["skipped"]}
              </div>
            </div>"""
        )
    return "\n".join(cards) if cards else "<p>No results collected.</p>"
