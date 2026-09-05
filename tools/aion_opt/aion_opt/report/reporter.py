"""JSON / Markdown / HTML report generation.

Every report is built from the same intermediate structure so the three
renderers stay in sync:

``summary``
    Design-level totals (cells, nets, area) for the whole run.
``patterns``
    One entry per applied pattern, carrying its module name, how often it was
    selected, its area figures and whether it made the *elite* cut.

Area numbers are estimates.  An AION cell is assumed to occupy ``area_factor``
times the summed area of the standard cells it replaces; the real number is
only known after the cell has been minimised and characterised.
"""

from __future__ import annotations

import html as html_module
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from aion_opt.pattern.cover import pattern_area

if TYPE_CHECKING:
    from aion_opt.io.cell_lib import CellLib
    from aion_opt.pattern.cover import CoverResult
    from aion_opt.pattern.miner import MiningResult
    from aion_opt.pattern.subgraph import Pattern


def _pattern_entry(
    key: str,
    pattern: "Pattern",
    count: int,
    cell_lib: "CellLib",
    area_factor: float,
    module_name: str | None = None,
    elite: bool = False,
) -> dict[str, Any]:
    """Build the per-pattern record shared by all three report renderers."""
    area = pattern_area(pattern.node_types, cell_lib)
    new_area = area * area_factor
    return {
        "pattern_key": key,
        "module_name": module_name,
        "size": pattern.size(),
        "occurrences": count,
        "node_types": dict(sorted(pattern.node_types.items())),
        "inputs": len(pattern.boundary_inputs),
        "outputs": len(pattern.boundary_outputs),
        "elite": elite,
        "total_original_area": area * count,
        "total_new_area": new_area * count,
        "total_saved_area": (area - new_area) * count,
        "example_boundary_inputs": list(pattern.boundary_inputs),
        "example_boundary_outputs": list(pattern.boundary_outputs),
    }


def rank_patterns(
    cover: "CoverResult",
    keys: list[str] | None = None,
) -> list[str]:
    """Rank pattern keys by total estimated area saved, best first.

    This is the ordering behind the *elite* cell selection: the patterns at the
    top of the list are the ones whose characterisation and minimisation buy
    the most area back.
    """
    candidates = list(cover.counts) if keys is None else list(keys)
    return sorted(candidates, key=lambda k: (-cover.total_saved_area(k), k))


def select_elite_keys(
    cover: "CoverResult",
    count: int | None,
    metric: str = "saved-area",
) -> list[str]:
    """Return the ``count`` best pattern keys under ``metric``.

    ``count`` of ``None`` or ``0`` means "no limit" and returns every selected
    pattern, ranked.  Supported metrics:

    ``saved-area``
        Total area saved across all selected occurrences (default).
    ``occurrences``
        How often the pattern is instantiated.
    ``saved-area-per-cell``
        Area saved per generated cell, i.e. return on the characterisation and
        minimisation effort that each new cell costs.
    """
    if metric == "saved-area":
        ranked = rank_patterns(cover)
    elif metric == "occurrences":
        ranked = sorted(cover.counts, key=lambda k: (-cover.counts[k], k))
    elif metric == "saved-area-per-cell":
        ranked = sorted(
            cover.counts,
            key=lambda k: (-cover.saved_area_per_occurrence.get(k, 0.0), k),
        )
    else:
        raise ValueError(
            "elite metric must be one of: saved-area, occurrences, "
            f"saved-area-per-cell (got {metric!r})"
        )
    if not count:
        return ranked
    return ranked[:count]


def write_pattern_report(
    output_path: Path,
    mining: "MiningResult",
    cover: "CoverResult",
    module_names: dict[str, str],
    cell_lib: "CellLib",
    area_factor: float = 0.85,
    elite_keys: list[str] | None = None,
    parameters: dict[str, Any] | None = None,
) -> None:
    """Write the JSON report for the pattern-mining / cell-generation step."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    elite = set(elite_keys or ())

    data = {
        "parameters": parameters or {},
        "summary": {
            "pattern_types_found": len(mining.occurrences),
            "total_occurrences_found": mining.total_occurrences(),
            "subgraphs_enumerated": mining.subgraphs_enumerated,
            "pattern_types_selected": len(cover.counts),
            "total_occurrences_selected": len(cover.selected),
            "pattern_types_dropped": len(cover.dropped_keys),
            "cover_iterations": cover.iterations,
            "elite_cells": len(elite),
            "estimated_total_saved_area": cover.total_saved_area_all(),
            "area_factor": area_factor,
        },
        "patterns_found": [
            _pattern_entry(
                key,
                mining.representative(key),
                len(occs),
                cell_lib,
                area_factor,
            )
            for key, occs in sorted(mining.occurrences.items())
        ],
        "patterns_selected": [
            _pattern_entry(
                key,
                mining.representative(key),
                cover.counts[key],
                cell_lib,
                area_factor,
                module_names.get(key),
                key in elite,
            )
            for key in rank_patterns(cover)
        ],
    }

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def write_rewrite_report(
    output_prefix: Path,
    mining: "MiningResult",
    cover: "CoverResult",
    module_names: dict[str, str],
    cell_lib: "CellLib",
    original_instances: int,
    rewritten_instances: int,
    original_nets: int,
    rewritten_nets: int,
    area_factor: float = 0.85,
    original_total_area: float | None = None,
    elite_keys: list[str] | None = None,
    parameters: dict[str, Any] | None = None,
) -> None:
    """Write JSON, Markdown and HTML reports for the rewrite step."""
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    elite = set(elite_keys or ())

    patterns = [
        _pattern_entry(
            key,
            mining.representative(key),
            cover.counts[key],
            cell_lib,
            area_factor,
            module_names.get(key, key),
            key in elite,
        )
        for key in rank_patterns(cover, list(cover.counts))
        if key in module_names
    ]

    replaced_original_area = sum(p["total_original_area"] for p in patterns)
    replaced_new_area = sum(p["total_new_area"] for p in patterns)
    saved_area = replaced_original_area - replaced_new_area
    occurrences_applied = sum(p["occurrences"] for p in patterns)

    if original_total_area is None:
        original_total_area = replaced_original_area
    estimated_total_new_area = original_total_area - saved_area

    data = {
        "parameters": parameters or {},
        "summary": {
            "original_cells": original_instances,
            "rewritten_cells": rewritten_instances,
            "cell_reduction": original_instances - rewritten_instances,
            "original_nets": original_nets,
            "rewritten_nets": rewritten_nets,
            "wires_eliminated": max(0, original_nets - rewritten_nets),
            "patterns_applied": len(patterns),
            "occurrences_applied": occurrences_applied,
            # Only meaningful when the caller ranked the cells; `rewrite` is
            # given a library and does not re-rank it.
            **({"elite_cells": len(elite)} if elite_keys is not None else {}),
            "original_replaced_area": replaced_original_area,
            "estimated_new_area": replaced_new_area,
            "estimated_area_savings": saved_area,
            "estimated_area_savings_percent": (
                (saved_area / replaced_original_area * 100)
                if replaced_original_area
                else 0.0
            ),
            "original_total_area": original_total_area,
            "estimated_total_new_area": estimated_total_new_area,
            "estimated_total_area_savings": original_total_area
            - estimated_total_new_area,
            "area_factor": area_factor,
        },
        "patterns": patterns,
    }

    with open(output_prefix.with_suffix(".json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    _write_markdown(output_prefix.with_suffix(".md"), data)
    _write_html(output_prefix.with_suffix(".html"), data)


def _write_markdown(path: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    lines = [
        "# aion_opt Rewrite Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Original cells | {s['original_cells']} |",
        f"| Rewritten cells | {s['rewritten_cells']} |",
        f"| Cell reduction | {s['cell_reduction']} |",
        f"| Original internal nets | {s['original_nets']} |",
        f"| Rewritten internal nets | {s['rewritten_nets']} |",
        f"| Wires eliminated | {s['wires_eliminated']} |",
        f"| Patterns applied | {s['patterns_applied']} |",
        f"| Occurrences applied | {s['occurrences_applied']} |",
        *(
            [f"| Elite cells | {s['elite_cells']} |"]
            if "elite_cells" in s
            else []
        ),
        f"| Original replaced area | {s['original_replaced_area']:.4f} |",
        f"| Estimated new area | {s['estimated_new_area']:.4f} |",
        f"| Estimated area savings | {s['estimated_area_savings']:.4f} ({s['estimated_area_savings_percent']:.2f}%) |",
        f"| Original total area | {s.get('original_total_area', s['original_replaced_area']):.4f} |",
        f"| Estimated total new area | {s.get('estimated_total_new_area', s['estimated_new_area']):.4f} |",
        "",
        "_All area values are in library area units._",
        "",
        "## Applied Patterns",
        "",
        "Patterns are ordered by estimated area saved. Rows marked * are part "
        "of the elite cell library.",
        "",
        "| Elite | Module | Size | Occurrences | Inputs | Outputs | Original area | New area | Savings |",
        "|-------|--------|------|-------------|--------|---------|---------------|----------|---------|",
    ]
    for p in data["patterns"]:
        lines.append(
            f"| {'*' if p.get('elite') else ''} | {p['module_name']} | {p['size']} | "
            f"{p['occurrences']} | {p.get('inputs', 0)} | {p.get('outputs', 0)} | "
            f"{p['total_original_area']:.4f} | {p['total_new_area']:.4f} | "
            f"{p['total_saved_area']:.4f} |"
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

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    show_elite = "elite_cells" in s

    ICON_GRID = '''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>'''
    ICON_BOLT = '''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" /></svg>'''
    ICON_CUBE = '''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>'''
    ICON_MINIMIZE = '''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7V5a2 2 0 012-2h2M17 3h2a2 2 0 012 2v2M21 17v2a2 2 0 01-2 2h-2M7 21H5a2 2 0 01-2-2v-2" /></svg>'''
    ICON_STAR = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>'''

    def card(icon: str, label: str, value: str, delta: str, tone: str = "good") -> str:
        tone_class = "" if tone == "good" else "negative"
        return f"""
        <div class="card">
          <div class="card-icon">{icon}</div>
          <div class="card-label">{html_module.escape(label)}</div>
          <div class="card-value">{value}</div>
          <div class="card-delta {tone_class}">{html_module.escape(delta)}</div>
        </div>
        """

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

    def donut_chart(percent: float, label: str) -> str:
        radius = 42
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
            <span class="donut-label">{html_module.escape(label)}</span>
          </div>
        </div>
        """

    MEDAL_COLORS = {0: "#fbbf24", 1: "#94a3b8", 2: "#f97316"}

    def medal(rank: int) -> str:
        color = MEDAL_COLORS.get(rank)
        if color:
            return f'<span class="medal" title="#{rank + 1} top pattern" style="color:{color}">{ICON_STAR}</span>'
        return f'<span class="rank">#{rank + 1}</span>'

    elite_card = (
        card(
            ICON_STAR,
            "Elite Cells",
            f"{s['elite_cells']}",
            f"of {s['patterns_applied']} generated cells",
        )
        if show_elite
        else ""
    )

    pattern_rows = []
    for rank, p in enumerate(patterns):
        share = (p["total_saved_area"] / total_savings * 100) if total_savings else 0.0
        inputs = p.get("inputs", len(p.get("example_boundary_inputs", [])))
        outputs = p.get("outputs", len(p.get("example_boundary_outputs", [])))
        badge = '<span class="elite-badge" title="part of the elite cell library">ELITE</span>' if p.get("elite") else ""
        pattern_rows.append(
            f"""
            <tr>
              <td class="rank-cell">{medal(rank)}</td>
              <td class="mono">{html_module.escape(str(p['module_name']))}{badge}</td>
              <td>{p['size']}</td>
              <td>{p['occurrences']}</td>
              <td>{inputs}</td>
              <td>{outputs}</td>
              <td>{p['total_original_area']:.4f}</td>
              <td>{p['total_new_area']:.4f}</td>
              <td class="savings">{p['total_saved_area']:.4f}</td>
              <td>
                <div class="mini-bar" title="{share:.1f}% of total savings">
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
  <title>AION Flow - Optimization Report</title>
  <style>
    :root {{
      --bg: #0b0f19;
      --panel: #151b2b;
      --panel-2: #1f293b;
      --text: #f1f5f9;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --accent-2: #818cf8;
      --success: #34d399;
      --danger: #f472b6;
      --warning: #fbbf24;
      --border: #28334d;
      --radius: 16px;
      --shadow: 0 20px 40px rgba(0,0,0,0.45);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background:
        radial-gradient(ellipse at 0% 0%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
        radial-gradient(ellipse at 100% 0%, rgba(129, 140, 248, 0.08) 0%, transparent 40%),
        var(--bg);
      color: var(--text);
      line-height: 1.55;
    }}
    header {{
      background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 55%, #8b5cf6 100%);
      padding: 4rem 1.5rem 4.5rem;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}
    header::before {{
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px);
      background-size: 32px 32px;
      mask-image: radial-gradient(circle at 50% 50%, black 0%, transparent 70%);
      -webkit-mask-image: radial-gradient(circle at 50% 50%, black 0%, transparent 70%);
    }}
    header::after {{
      content: "";
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at 20% 30%, rgba(255,255,255,0.14) 0%, transparent 45%),
                  radial-gradient(circle at 80% 70%, rgba(255,255,255,0.10) 0%, transparent 45%);
    }}
    header h1 {{ margin: 0; font-size: 2.6rem; font-weight: 800; letter-spacing: -0.04em; position: relative; z-index: 1; }}
    header p {{ margin: 0.6rem 0 0; opacity: 0.92; font-size: 1.15rem; position: relative; z-index: 1; }}
    .subtitle-note {{ margin: 0.4rem 0 0; opacity: 0.75; font-size: 0.95rem; font-style: italic; position: relative; z-index: 1; }}
    main {{ max-width: 1200px; margin: -2.5rem auto 3rem; padding: 0 1.5rem; position: relative; z-index: 2; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    .card {{
      background: rgba(21, 27, 43, 0.85);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.5rem;
      box-shadow: var(--shadow);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      position: relative;
      overflow: hidden;
    }}
    .card::before {{
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      opacity: 0.8;
    }}
    .card:hover {{ transform: translateY(-4px); box-shadow: 0 24px 48px rgba(0,0,0,0.55); }}
    .card-icon {{ color: var(--accent); margin-bottom: 0.6rem; }}
    .card-icon svg {{ width: 1.6rem; height: 1.6rem; }}
    .card-label {{ color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.09em; margin-bottom: 0.35rem; }}
    .card-value {{ font-size: 2.1rem; font-weight: 800; letter-spacing: -0.03em; }}
    .card-delta {{ font-size: 0.95rem; margin-top: 0.35rem; color: var(--success); font-weight: 600; }}
    .card-delta.negative {{ color: var(--danger); }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }}
    .panel {{
      background: rgba(21, 27, 43, 0.85);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.75rem;
      box-shadow: var(--shadow);
    }}
    .panel h2 {{ margin: 0 0 1.25rem; font-size: 1.25rem; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 0.5rem; }}
    .panel h2 svg {{ width: 1.25rem; height: 1.25rem; color: var(--accent); }}
    .bar-row {{ display: grid; grid-template-columns: 100px 1fr 70px; align-items: center; gap: 0.9rem; margin: 0.8rem 0; font-size: 0.95rem; }}
    .bar-label {{ color: var(--muted); text-align: right; font-weight: 500; }}
    .bar-track {{ background: var(--panel-2); border-radius: 999px; height: 16px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }}
    .bar-fill {{ height: 100%; border-radius: 999px; transition: width 1s ease; box-shadow: 0 0 12px rgba(56,189,248,0.25); }}
    .bar-value {{ font-weight: 700; text-align: right; }}
    .donut {{ width: 180px; height: 180px; margin: 0 auto; position: relative; }}
    .donut svg {{ transform: rotate(-90deg); width: 100%; height: 100%; filter: drop-shadow(0 0 8px rgba(52,211,153,0.25)); }}
    .donut-bg {{ fill: none; stroke: var(--panel-2); stroke-width: 10; }}
    .donut-fg {{ fill: none; stroke: url(#gradDonut); stroke-width: 10; stroke-linecap: round; transition: stroke-dashoffset 1.2s ease; }}
    .donut-text {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
    .donut-percent {{ font-size: 1.9rem; font-weight: 800; letter-spacing: -0.03em; }}
    .donut-label {{ font-size: 0.85rem; color: var(--muted); font-weight: 500; }}
    .legend {{ display: flex; justify-content: center; gap: 1.75rem; margin-top: 1.25rem; font-size: 0.9rem; color: var(--muted); }}
    .legend span {{ display: inline-flex; align-items: center; gap: 0.4rem; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px currentColor; }}
    .table-wrap {{ border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    thead {{ position: sticky; top: 0; z-index: 3; }}
    th {{ padding: 1rem 0.85rem; text-align: left; background: var(--panel-2); color: var(--muted); font-weight: 700; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.08em; border-bottom: 1px solid var(--border); }}
    td {{ padding: 0.95rem 0.85rem; text-align: left; border-bottom: 1px solid var(--border); }}
    tbody tr:nth-child(even) {{ background: rgba(255,255,255,0.015); }}
    tbody tr:hover td {{ background: rgba(255,255,255,0.045); }}
    td.savings {{ color: var(--success); font-weight: 700; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.85rem; }}
    .rank-cell {{ width: 40px; text-align: center; }}
    .medal {{ filter: drop-shadow(0 0 4px rgba(255,255,255,0.2)); }}
    .medal svg {{ width: 1.2rem; height: 1.2rem; }}
    .rank {{ color: var(--muted); font-size: 0.8rem; font-weight: 700; }}
    .mini-bar {{ background: var(--panel-2); border-radius: 999px; height: 7px; width: 90px; overflow: hidden; display: inline-block; vertical-align: middle; margin-right: 0.5rem; box-shadow: inset 0 1px 2px rgba(0,0,0,0.2); }}
    .mini-bar-fill {{ height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-2)); border-radius: 999px; transition: width 1s ease; }}
    .share {{ color: var(--muted); font-size: 0.8rem; font-weight: 600; min-width: 42px; display: inline-block; }}
    .elite-badge {{ margin-left: 0.5rem; padding: 0.1rem 0.45rem; border-radius: 999px; background: rgba(251,191,36,0.16); color: var(--warning); font-size: 0.65rem; font-weight: 800; letter-spacing: 0.08em; vertical-align: middle; }}
    footer {{ text-align: center; color: var(--muted); padding: 2.5rem 1rem; font-size: 0.85rem; }}
    footer time {{ color: var(--text); font-weight: 600; }}
    .muted-note {{ color: var(--muted); font-size: 0.85rem; margin-top: -0.75rem; margin-bottom: 1.25rem; }}
    @media (max-width: 640px) {{
      header h1 {{ font-size: 1.9rem; }}
      .bar-row {{ grid-template-columns: 75px 1fr 55px; font-size: 0.85rem; }}
      .cards {{ grid-template-columns: 1fr; }}
      .card-value {{ font-size: 1.8rem; }}
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
    <h1>AION Flow - Optimization Report</h1>
    <p>Post-synthesis pattern mining & area optimization</p>
    <p class="subtitle-note">Area savings numbers are estimations based on an area reduction factor of {s['area_factor']}.</p>
  </header>
  <main>
    <section class="cards">
      {card(ICON_GRID, "Cell Reduction", f"{s['cell_reduction']}", f"{cell_reduction_pct:.1f}% fewer cells")}
      {card(ICON_BOLT, "Wires Eliminated", f"{s['wires_eliminated']}", f"{net_reduction_pct:.1f}% fewer nets")}
      {card(ICON_CUBE, "Patterns Applied", f"{s['patterns_applied']}", f"{s['occurrences_applied']} occurrences")}
      {card(ICON_MINIMIZE, "Area Savings", f"{s['estimated_area_savings']:.2f}", f"{area_savings_pct:.1f}% of replaced area")}
      {elite_card}
    </section>

    <section class="grid-2">
      <div class="panel">
        <h2>Resource Comparison</h2>
        {pct_bar("Original cells", original_cells, original_cells, "#38bdf8")}
        {pct_bar("Optimized cells", rewritten_cells, original_cells, "#818cf8")}
        {pct_bar("Original nets", s['original_nets'], s['original_nets'], "#38bdf8")}
        {pct_bar("Optimized nets", s['rewritten_nets'], s['original_nets'], "#818cf8")}
        <div class="legend">
          <span><span class="dot" style="background:#38bdf8"></span>Original</span>
          <span><span class="dot" style="background:#818cf8"></span>Optimized</span>
        </div>
      </div>
      <div class="panel">
        <h2>Area Overview</h2>
        <p class="muted-note">Area values are in library area units.</p>
        {donut_chart(total_area_savings_pct, "total area saved")}
        {pct_bar("Original", total_original_area, total_original_area, "#38bdf8")}
        {pct_bar("New", total_new_area, total_original_area, "#34d399")}
      </div>
    </section>

    <section class="panel">
      <h2>{ICON_CUBE} Applied Patterns</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th></th>
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
  <footer>Generated by aion_opt · <time>{html_module.escape(generated_at)}</time></footer>
</body>
</html>"""

    path.write_text(html_content, encoding="utf-8")
