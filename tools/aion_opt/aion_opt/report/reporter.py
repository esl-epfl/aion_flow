"""JSON/Markdown report generation."""

from __future__ import annotations

import html as html_module
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aion_opt.io.cell_lib import CellLib
    from aion_opt.pattern.subgraph import Pattern


def _pattern_area(pattern: "Pattern", cell_lib: "CellLib") -> float:
    return sum(cell_lib.area(ct) for ct in pattern.node_types.values())


def _pattern_summary(
    key: str,
    occurrences: list["Pattern"],
    cell_lib: "CellLib",
    area_factor: float,
    module_index: dict[str, int] | None = None,
) -> dict[str, Any]:
    rep = occurrences[0]
    area = _pattern_area(rep, cell_lib)
    new_area = area * area_factor
    saved_per_occ = area - new_area
    return {
        "pattern_key": key,
        "module_name": (
            f"AION_{'_'.join(sorted(set(rep.node_types.values()))).replace('sg13g2_', '')}_{module_index[key]}"
            if module_index and key in module_index
            else None
        ),
        "size": rep.size(),
        "occurrences": len(occurrences),
        "node_types": rep.node_types,
        "total_original_area": area * len(occurrences),
        "total_new_area": new_area * len(occurrences),
        "total_saved_area": saved_per_occ * len(occurrences),
        "example_boundary_inputs": list(rep.boundary_inputs),
        "example_boundary_outputs": list(rep.boundary_outputs),
    }


def write_pattern_report(
    output_path: Path,
    patterns: dict[str, list["Pattern"]],
    selected: list["Pattern"],
    module_index: dict[str, int],
    cell_lib: "CellLib",
    area_factor: float = 0.85,
) -> None:
    """Write a JSON report for the pattern-mining step."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    selected_keys = {occ.canonical_key for occ in selected}

    data = {
        "summary": {
            "pattern_types_found": len(patterns),
            "total_occurrences_found": sum(len(v) for v in patterns.values()),
            "pattern_types_selected": len(selected_keys),
            "total_occurrences_selected": len(selected),
            "area_factor": area_factor,
        },
        "patterns_found": [
            _pattern_summary(key, occs, cell_lib, area_factor, None)
            for key, occs in patterns.items()
        ],
        "patterns_selected": [
            _pattern_summary(key, patterns[key], cell_lib, area_factor, module_index)
            for key in selected_keys
        ],
    }

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def write_rewrite_report(
    output_prefix: Path,
    patterns: dict[str, list["Pattern"]],
    selected: list["Pattern"],
    module_names: dict[str, str],
    cell_lib: "CellLib",
    original_instances: int,
    rewritten_instances: int,
    original_nets: int,
    rewritten_nets: int,
    area_factor: float = 0.85,
    original_total_area: float | None = None,
    estimated_total_new_area: float | None = None,
) -> None:
    """Write JSON, Markdown, and HTML reports for the rewrite step."""
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    selected_counts: dict[str, int] = {}
    for occ in selected:
        selected_counts[occ.canonical_key] = selected_counts.get(
            occ.canonical_key, 0
        ) + 1

    replaced_original_area = sum(
        _pattern_area(occ, cell_lib) for occ in selected
    )
    replaced_new_area = replaced_original_area * area_factor
    saved_area = replaced_original_area - replaced_new_area
    wires_eliminated = max(0, original_nets - rewritten_nets)

    # Whole-design area totals: if only the original total is supplied,
    # derive the new total by subtracting the replaced-area savings.
    if original_total_area is None:
        original_total_area = replaced_original_area
    if estimated_total_new_area is None:
        estimated_total_new_area = original_total_area - saved_area

    data = {
        "summary": {
            "original_cells": original_instances,
            "rewritten_cells": rewritten_instances,
            "cell_reduction": original_instances - rewritten_instances,
            "original_nets": original_nets,
            "rewritten_nets": rewritten_nets,
            "wires_eliminated": wires_eliminated,
            "patterns_applied": len(selected_counts),
            "occurrences_applied": len(selected),
            "original_replaced_area": replaced_original_area,
            "estimated_new_area": replaced_new_area,
            "estimated_area_savings": saved_area,
            "estimated_area_savings_percent": (
                (saved_area / replaced_original_area * 100) if replaced_original_area else 0.0
            ),
            "original_total_area": original_total_area,
            "estimated_total_new_area": estimated_total_new_area,
            "estimated_total_area_savings": original_total_area - estimated_total_new_area,
            "area_factor": area_factor,
        },
        "patterns": [
            {
                "module_name": module_names[key],
                "occurrences": count,
                **_pattern_summary(key, patterns[key], cell_lib, area_factor, None),
            }
            for key, count in selected_counts.items()
        ],
    }

    json_path = output_prefix.with_suffix(".json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    md_path = output_prefix.with_suffix(".md")
    _write_markdown(md_path, data)

    html_path = output_prefix.with_suffix(".html")
    _write_html(html_path, data)


def _write_markdown(path: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    lines = [
        "# aion_opt Rewrite Report",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Original cells | {s['original_cells']} |",
        f"| Rewritten cells | {s['rewritten_cells']} |",
        f"| Cell reduction | {s['cell_reduction']} |",
        f"| Original internal nets | {s['original_nets']} |",
        f"| Rewritten internal nets | {s['rewritten_nets']} |",
        f"| Wires eliminated | {s['wires_eliminated']} |",
        f"| Patterns applied | {s['patterns_applied']} |",
        f"| Occurrences applied | {s['occurrences_applied']} |",
        f"| Original replaced area | {s['original_replaced_area']:.4f} |",
        f"| Estimated new area | {s['estimated_new_area']:.4f} |",
        f"| Estimated area savings | {s['estimated_area_savings']:.4f} ({s['estimated_area_savings_percent']:.2f}%) |",
        f"| Original total area | {s.get('original_total_area', s['original_replaced_area']):.4f} |",
        f"| Estimated total new area | {s.get('estimated_total_new_area', s['estimated_new_area']):.4f} |",
        "",
        "## Applied Patterns",
        "",
        "| Module | Size | Occurrences | Original area | New area | Savings |",
        "|--------|------|-------------|---------------|----------|---------|",
    ]
    for p in data["patterns"]:
        orig = p["total_original_area"]
        new = p["total_new_area"]
        saved = p["total_saved_area"]
        lines.append(
            f"| {p['module_name']} | {p['size']} | {p['occurrences']} | "
            f"{orig:.4f} | {new:.4f} | {saved:.4f} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_html(path: Path, data: dict[str, Any]) -> None:
    """Render an aesthetic standalone HTML report with inline SVG charts."""
    s = data["summary"]
    patterns = sorted(
        data["patterns"], key=lambda p: p["total_saved_area"], reverse=True
    )

    original_cells = s["original_cells"]
    rewritten_cells = s["rewritten_cells"]
    cell_reduction_pct = (
        (s["cell_reduction"] / original_cells * 100) if original_cells else 0.0
    )
    net_reduction_pct = (
        (s["wires_eliminated"] / s["original_nets"] * 100)
        if s["original_nets"]
        else 0.0
    )
    area_savings_pct = s["estimated_area_savings_percent"]
    total_savings = s["estimated_area_savings"]

    total_original_area = s.get("original_total_area", s["original_replaced_area"])
    total_new_area = s.get("estimated_total_new_area", s["estimated_new_area"])
    total_area_savings_pct = (
        ((total_original_area - total_new_area) / total_original_area * 100)
        if total_original_area
        else 0.0
    )

    def pct_bar(label: str, value: float, max_value: float, color: str) -> str:
        pct = (value / max_value * 100) if max_value else 0.0
        return f"""
        <div class="bar-row">
          <span class="bar-label">{html_module.escape(label)}</span>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div>
          </div>
          <span class="bar-value">{value:,.0f}</span>
        </div>
        """

    def donut_chart(percent: float) -> str:
        radius = 36
        circumference = 2 * 3.1416 * radius
        offset = circumference * (1 - percent / 100)
        return f"""
        <div class="donut">
          <svg viewBox="0 0 100 100">
            <circle class="donut-bg" cx="50" cy="50" r="{radius}"/>
            <circle class="donut-fg" cx="50" cy="50" r="{radius}"
                    stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"/>
          </svg>
          <div class="donut-text">
            <span class="donut-percent">{percent:.1f}%</span>
            <span class="donut-label">area saved</span>
          </div>
        </div>
        """

    pattern_rows = []
    for p in patterns:
        share = (p["total_saved_area"] / total_savings * 100) if total_savings else 0.0
        inputs = len(p.get("example_boundary_inputs", []))
        outputs = len(p.get("example_boundary_outputs", []))
        pattern_rows.append(
            f"""
            <tr>
              <td class="mono">{html_module.escape(str(p['module_name']))}</td>
              <td>{p['size']}</td>
              <td>{p['occurrences']}</td>
              <td>{inputs}</td>
              <td>{outputs}</td>
              <td>{p['total_original_area']:.4f}</td>
              <td>{p['total_new_area']:.4f}</td>
              <td class="savings">{p['total_saved_area']:.4f}</td>
              <td>
                <div class="mini-bar">
                  <div class="mini-bar-fill" style="width:{share:.1f}%"></div>
                </div>
                <span class="share">{share:.1f}%</span>
              </td>
            </tr>
            """
        )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>aion_opt Rewrite Report</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #1e293b;
      --panel-2: #27354f;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --accent-2: #818cf8;
      --success: #34d399;
      --danger: #f472b6;
      --border: #334155;
      --radius: 14px;
      --shadow: 0 10px 30px rgba(0,0,0,0.35);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    header {{
      background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
      padding: 3rem 1.5rem 3.5rem;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}
    header::after {{
      content: "";
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at 20% 30%, rgba(255,255,255,0.12) 0%, transparent 40%),
                  radial-gradient(circle at 80% 70%, rgba(255,255,255,0.08) 0%, transparent 40%);
    }}
    header h1 {{ margin: 0; font-size: 2.4rem; letter-spacing: -0.03em; position: relative; z-index: 1; }}
    header p {{ margin: 0.5rem 0 0; opacity: 0.9; font-size: 1.1rem; position: relative; z-index: 1; }}
    main {{ max-width: 1200px; margin: -2rem auto 3rem; padding: 0 1.5rem; position: relative; z-index: 2; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.5rem;
      box-shadow: var(--shadow);
      transition: transform 0.15s ease;
    }}
    .card:hover {{ transform: translateY(-3px); }}
    .card-label {{ color: var(--muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; }}
    .card-value {{ font-size: 2rem; font-weight: 700; }}
    .card-delta {{ font-size: 0.95rem; margin-top: 0.3rem; color: var(--success); }}
    .card-delta.negative {{ color: var(--danger); }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.5rem;
      box-shadow: var(--shadow);
    }}
    .panel h2 {{ margin: 0 0 1.25rem; font-size: 1.2rem; color: var(--text); }}
    .bar-row {{ display: grid; grid-template-columns: 110px 1fr 70px; align-items: center; gap: 0.8rem; margin: 0.7rem 0; font-size: 0.95rem; }}
    .bar-label {{ color: var(--muted); text-align: right; }}
    .bar-track {{ background: var(--panel-2); border-radius: 999px; height: 14px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 999px; transition: width 0.8s ease; }}
    .bar-value {{ font-weight: 600; text-align: right; }}
    .donut {{ width: 160px; height: 160px; margin: 0 auto; position: relative; }}
    .donut svg {{ transform: rotate(-90deg); width: 100%; height: 100%; }}
    .donut-bg {{ fill: none; stroke: var(--panel-2); stroke-width: 12; }}
    .donut-fg {{ fill: none; stroke: url(#gradDonut); stroke-width: 12; stroke-linecap: round; transition: stroke-dashoffset 1s ease; }}
    .donut-text {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
    .donut-percent {{ font-size: 1.6rem; font-weight: 700; }}
    .donut-label {{ font-size: 0.8rem; color: var(--muted); }}
    .legend {{ display: flex; justify-content: center; gap: 1.5rem; margin-top: 1rem; font-size: 0.9rem; color: var(--muted); }}
    .legend span {{ display: inline-flex; align-items: center; gap: 0.35rem; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th, td {{ padding: 0.85rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }}
    th {{ color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.06em; }}
    tr:hover td {{ background: rgba(255,255,255,0.03); }}
    td.savings {{ color: var(--success); font-weight: 600; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.85rem; }}
    .mini-bar {{ background: var(--panel-2); border-radius: 999px; height: 6px; width: 80px; overflow: hidden; display: inline-block; vertical-align: middle; margin-right: 0.4rem; }}
    .mini-bar-fill {{ height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-2)); border-radius: 999px; }}
    .share {{ color: var(--muted); font-size: 0.8rem; }}
    footer {{ text-align: center; color: var(--muted); padding: 2rem 1rem; font-size: 0.85rem; }}
    @media (max-width: 640px) {{
      .bar-row {{ grid-template-columns: 80px 1fr 55px; font-size: 0.85rem; }}
      .cards {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <svg width="0" height="0" style="position:absolute;">
    <defs>
      <linearGradient id="gradDonut" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#34d399"/>
        <stop offset="100%" stop-color="#38bdf8"/>
      </linearGradient>
    </defs>
  </svg>
  <header>
    <h1>aion_opt Rewrite Report</h1>
    <p>Post-synthesis pattern mining & area optimization</p>
  </header>
  <main>
    <section class="cards">
      <div class="card">
        <div class="card-label">Cell Reduction</div>
        <div class="card-value">{s['cell_reduction']}</div>
        <div class="card-delta">{cell_reduction_pct:.1f}% fewer cells</div>
      </div>
      <div class="card">
        <div class="card-label">Wires Eliminated</div>
        <div class="card-value">{s['wires_eliminated']}</div>
        <div class="card-delta">{net_reduction_pct:.1f}% fewer nets</div>
      </div>
      <div class="card">
        <div class="card-label">Patterns Applied</div>
        <div class="card-value">{s['patterns_applied']}</div>
        <div class="card-delta">{s['occurrences_applied']} occurrences</div>
      </div>
      <div class="card">
        <div class="card-label">Area Savings</div>
        <div class="card-value">{s['estimated_area_savings']:.2f}</div>
        <div class="card-delta">{area_savings_pct:.1f}% of replaced area</div>
      </div>
      <div class="card">
        <div class="card-label">Total Original Area</div>
        <div class="card-value">{total_original_area:.2f}</div>
        <div class="card-delta">whole design</div>
      </div>
      <div class="card">
        <div class="card-label">Estimated Total New Area</div>
        <div class="card-value">{total_new_area:.2f}</div>
        <div class="card-delta">{total_area_savings_pct:.1f}% total savings</div>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <h2>Resource Comparison</h2>
        {pct_bar("Cells", original_cells, original_cells, "#38bdf8")}
        {pct_bar("Cells", rewritten_cells, original_cells, "#818cf8")}
        {pct_bar("Nets", s['original_nets'], s['original_nets'], "#38bdf8")}
        {pct_bar("Nets", s['rewritten_nets'], s['original_nets'], "#818cf8")}
        <div class="legend">
          <span><span class="dot" style="background:#38bdf8"></span>Original</span>
          <span><span class="dot" style="background:#818cf8"></span>Optimized</span>
        </div>
      </div>
      <div class="panel">
        <h2>Area Overview</h2>
        {donut_chart(total_area_savings_pct)}
        {pct_bar("Original", total_original_area, total_original_area, "#38bdf8")}
        {pct_bar("New", total_new_area, total_original_area, "#34d399")}
      </div>
    </section>

    <section class="panel">
      <h2>Applied Patterns</h2>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Module</th>
              <th>Size</th>
              <th>Occurrences</th>
              <th>Inputs</th>
              <th>Outputs</th>
              <th>Original Area</th>
              <th>New Area</th>
              <th>Savings</th>
              <th>Share</th>
            </tr>
          </thead>
          <tbody>
            {''.join(pattern_rows)}
          </tbody>
        </table>
      </div>
    </section>
  </main>
  <footer>Generated by aion_opt · {html_module.escape(str(path.name))}</footer>
</body>
</html>"""

    path.write_text(html_content, encoding="utf-8")
