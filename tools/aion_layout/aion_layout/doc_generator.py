# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               Markdown documentation generator for AION cells
# ================================================================

"""Generate a markdown report for a verified AION standard cell.

The report combines:

* the parsed SPICE netlist (device list, topology),
* the cell generator's boundary and ports,
* the layout strategy suggested by the netlist viewer, and
* the most recent DRC/LVS verification result.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .cell import Cell
from .netlist_view import (
    netlist_summary,
    series_chain,
    series_parallel_groups,
    suggest_gate_order,
)
from .spice_parser import Subckt, parse_first_subckt
from .tech import Tech, sg13g2_tech
from .verification import (
    DrcReport,
    LvsReport,
    parse_klayout_lyrdb,
    parse_magic_drc_report,
    parse_netgen_lvs_report,
)


def _load_verification_reports(
    cell_name: str, runs_dir: Path
) -> tuple[Optional[DrcReport], Optional[DrcReport], Optional[LvsReport]]:
    """Parse existing DRC/LVS reports if they are present."""
    drc_dir = runs_dir / "drc" / cell_name
    lvs_dir = runs_dir / "lvs" / cell_name

    magic_rpt = drc_dir / f"{cell_name}.magic.drc" / f"{cell_name}.magic.drc.rpt"
    klayout_rpt_candidates = list(drc_dir.glob(f"{cell_name}.klayout.drc/*_full.lyrdb"))
    lvs_rpt = lvs_dir / f"{cell_name}.magic.lvs" / f"{cell_name}.lvs.out"

    magic = parse_magic_drc_report(magic_rpt) if magic_rpt.exists() else None
    klayout = (
        parse_klayout_lyrdb(klayout_rpt_candidates[0])
        if klayout_rpt_candidates
        else None
    )
    lvs = parse_netgen_lvs_report(lvs_rpt) if lvs_rpt.exists() else None
    return magic, klayout, lvs


def _device_table(subckt: Subckt) -> str:
    """Return a markdown table of MOSFET devices."""
    lines = [
        "| Device | Model | Drain | Gate | Source | Bulk | W (nm) | L (nm) | ng | m |",
        "|--------|-------|-------|------|--------|------|--------|--------|----|----|",
    ]
    for d in subckt.devices:
        lines.append(
            f"| {d.name} | {d.model} | {d.drain} | {d.gate} | {d.source} | {d.bulk} "
            f"| {d.width_nm:g} | {d.length_nm:g} | {d.fingers} | {d.multiplier} |"
        )
    return "\n".join(lines)


def _port_table(cell: Cell) -> str:
    """Return a markdown table of cell ports."""
    lines = [
        "| Pin | Direction | Layer | Left (nm) | Bottom (nm) | Right (nm) | Top (nm) |",
        "|-----|-----------|-------|-----------|-------------|------------|----------|",
    ]
    for name, port in sorted(cell.ports.items()):
        direction = port.direction or "-"
        layer = port.layer.name
        r = port.rect
        lines.append(
            f"| {name} | {direction} | {layer} | {r.left:g} | {r.bottom:g} | {r.right:g} | {r.top:g} |"
        )
    return "\n".join(lines)


def _layout_strategy(subckt: Subckt) -> str:
    """Return a short human-readable layout plan."""
    out = subckt.output_net or "?"
    vdd = subckt.vdd_net or "?"
    vss = subckt.vss_net or "?"
    gate_order = suggest_gate_order(subckt)

    lines = [
        f"* **Output net:** {out}",
        f"* **Power net:** {vdd}",
        f"* **Ground net:** {vss}",
        f"* **Suggested gate order (left-to-right):** {' '.join(gate_order)}",
    ]

    def describe_group(group, head, rail):
        names = [d.name for d in group]
        if len(group) == 1:
            return f"{names[0]} connects {head} to {rail}"
        if all({d.drain, d.source} == {head, rail} for d in group):
            gates = [d.gate for d in group]
            return f"parallel group ({', '.join(names)}) driven by {', '.join(gates)}"
        chain = series_chain(group, head, rail)
        if chain:
            chain_names = [d.name for d in chain]
            chain_gates = [d.gate for d in chain]
            return f"series chain ({' -> '.join(chain_names)}) driven by {' -> '.join(chain_gates)}"
        return f"group ({', '.join(names)})"

    pmos_groups = series_parallel_groups(subckt.pmos_devices, out, vdd)
    if pmos_groups:
        lines.append("* **Pull-up network (PMOS):**")
        for group in pmos_groups:
            lines.append(f"  * {describe_group(group, out, vdd)}")

    nmos_groups = series_parallel_groups(subckt.nmos_devices, out, vss)
    if nmos_groups:
        lines.append("* **Pull-down network (NMOS):**")
        for group in nmos_groups:
            lines.append(f"  * {describe_group(group, out, vss)}")

    return "\n".join(lines)


def _verification_summary(
    magic: Optional[DrcReport], klayout: Optional[DrcReport], lvs: Optional[LvsReport]
) -> str:
    """Return a markdown verification block."""
    lines = []
    if magic is not None:
        status = "PASS" if magic.clean else f"FAIL ({magic.error_count} errors)"
        lines.append(f"* **Magic DRC:** {status}")
    if klayout is not None:
        status = "PASS" if klayout.clean else f"FAIL ({klayout.error_count} errors)"
        lines.append(f"* **KLayout DRC:** {status}")
    if lvs is not None:
        status = "PASS" if lvs.clean else "FAIL"
        lines.append(f"* **LVS ({lvs.tool}):** {status} — {lvs.message}")
        if lvs.device_counts:
            lines.append("  * Device counts:")
            for dev, (layout_count, schematic_count) in sorted(lvs.device_counts.items()):
                mark = "✓" if layout_count == schematic_count else "✗"
                lines.append(f"    * {mark} `{dev}`: layout={layout_count}, schematic={schematic_count}")
    if not lines:
        lines.append("*No verification reports found. Run verification first.*")
    return "\n".join(lines)


def _load_cell_module(cell_module_path: Path) -> object:
    """Load a cell generator from a file path."""
    module_name = cell_module_path.stem
    spec = importlib.util.spec_from_file_location(module_name, cell_module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load cell module from {cell_module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def generate_doc(
    cell_name: str,
    netlist_path: Path,
    output_path: Path,
    runs_dir: Path = Path("runs"),
    tech: Tech = sg13g2_tech,
    cell_module_path: Path | None = None,
) -> str:
    """Generate a markdown documentation file for ``cell_name``.

    Returns the generated markdown text and writes it to ``output_path``.
    """
    subckt = parse_first_subckt(netlist_path)

    # Import the cell generator and render it to obtain the boundary/ports.
    if cell_module_path is None:
        raise RuntimeError("cell_module_path is required")
    cell_module = _load_cell_module(cell_module_path)
    if not hasattr(cell_module, "generate"):
        raise RuntimeError(f"{cell_module_path} does not define generate()")
    cell: Cell = cell_module.generate(cell_name, tech)

    boundary = cell.bbox
    if cell._boundary is not None:
        boundary = cell._boundary

    magic, klayout, lvs = _load_verification_reports(cell_name, runs_dir)
    passed = (
        (magic is None or magic.clean)
        and (klayout is None or klayout.clean)
        and (lvs is None or lvs.clean)
    )

    width = boundary.right - boundary.left
    height = boundary.top - boundary.bottom

    md = f"""# {cell_name}

Auto-generated documentation for the AION layout of `{cell_name}`.

## Netlist

* **Source:** `{netlist_path}`
* **Subckt:** `{subckt.name}`
* **Pins:** {' '.join(f"`{p}`" for p in subckt.pins)}

### Devices

{_device_table(subckt)}

## Cell dimensions

* **Width:** {width:g} nm
* **Height:** {height:g} nm
* **Area:** {width * height:g} nm²

## Pin locations

{_port_table(cell)}

## Layout strategy

{_layout_strategy(subckt)}

## Verification

{_verification_summary(magic, klayout, lvs)}

**Overall:** {'PASS' if passed else 'FAIL'}

## Usage

Generate and verify the cell with:

```bash
python3 scripts/generate_cell.py {cell_module_path} path/to/{cell_name}.gds
python3 scripts/report_verification.py --cell {cell_name} --gds path/to/{cell_name}.gds --netlist {netlist_path.name} --runs-dir path/to/runs
```

Generate this documentation with:

```bash
python3 scripts/generate_cell_doc.py --cell-module {cell_module_path} --netlist {netlist_path.name} -o path/to/{cell_name}.md --runs-dir path/to/runs
```

---

*Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} by AION doc generator.*
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md)
    return md


__all__ = ["generate_doc"]
