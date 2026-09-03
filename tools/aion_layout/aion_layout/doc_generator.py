# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Updated:                   2026-09-03
#  Description:               Markdown documentation generator for AION cells
# ================================================================

"""Generate a markdown report for a verified AION standard cell.

The report combines:

* the parsed SPICE netlist (device list, topology),
* the cell generator's boundary and ports,
* the layout strategy suggested by the netlist viewer, and
* the most recent DRC/LVS verification result.

The verification section fails closed.  Reports are read only from the canonical
directories the ``sak-*`` wrappers write, every artifact gets a line whether or
not it was found, and an artifact that is missing or only partly readable makes
the document say ``ERROR``.  This generator used to print "*No verification
reports found*" and "**Overall:** PASS" four lines apart, over a layout with
eight DRC violations and a failed LVS; absence is not a pass.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

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
    VerificationError,
    parse_klayout_reports,
    parse_magic_drc_report,
    parse_netgen_lvs_report,
)

# The canonical artifact-discovery helpers of ``verification``: they resolve the
# exact directories the sak-* wrappers write (``<cell>.magic.drc/``,
# ``<cell>.klayout.drc/``, ``<cell>.magic.lvs/``) and refuse anything else.  The
# hand-rolled paths that used to live here inserted an extra ``/<cell>/`` level
# no tool writes, so every report missed and the document declared PASS over a
# layout with eight violations.
from .verification import _find_magic_drc_report as find_magic_drc_report
from .verification import _find_netgen_lvs_report as find_netgen_lvs_report

# ---------------------------------------------------------------------------
# Verification status taxonomy
#
# The same four tokens, with the same meanings and the same precedence, are used
# by ``scripts/report_verification.py`` and ``scripts/evidence.py``: an artifact
# is ``PASS`` only on positive evidence that the tool ran and found nothing, and
# an artifact that is missing or only partly readable forces an overall
# ``ERROR`` -- it never reads as a pass.
# ---------------------------------------------------------------------------

#: Positive evidence that the artifact was produced and is clean.
STATUS_PASS = "PASS"
#: Positive evidence that the artifact was produced and records violations.
STATUS_FAIL = "FAIL"
#: The artifact does not exist, is empty, or carries no verdict of its own.
STATUS_UNAVAILABLE = "NOT AVAILABLE"
#: The artifact exists but could only be read in part.
STATUS_DEGRADED = "DEGRADED"
#: Statuses that mean "nothing was actually verified".
STATUS_UNVERIFIED = (STATUS_UNAVAILABLE, STATUS_DEGRADED)

#: ``verification.LVS_VERDICTS`` members that carry no information either way.
LVS_UNKNOWN_TOKENS = frozenset({"no_final_result", "uncertain"})

#: Cap on one externally sourced value interpolated into the document.
_MAX_NOTE_LEN = 1000


def _one_line(value: object, max_len: int = _MAX_NOTE_LEN) -> str:
    """Return ``value`` as a single printable line.

    Report files and paths are written by the model under test; a newline in one
    of them must not be able to open a line of its own in the document and spell
    a verdict this generator never reached.
    """
    text = "".join(ch if ch.isprintable() else " " for ch in str(value)).strip()
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text


def _load_verification_reports(
    cell_name: str, runs_dir: Path
) -> tuple[
    Optional[DrcReport], Optional[DrcReport], Optional[LvsReport], dict[str, str]
]:
    """Parse the DRC/LVS reports at their canonical paths under ``runs_dir``.

    Returns ``(magic, klayout, lvs, reasons)``.  A report that could not be
    found leaves its slot ``None`` and records why in ``reasons``; the caller
    reports that as ``NOT AVAILABLE`` and refuses to call the cell verified.
    ``parse_klayout_reports`` never raises -- it returns a report whose
    ``available`` flag is ``False`` -- so its slot is always filled.
    """
    reasons: dict[str, str] = {}

    magic: Optional[DrcReport] = None
    try:
        magic = parse_magic_drc_report(find_magic_drc_report(runs_dir, cell_name))
    except (VerificationError, OSError) as exc:
        reasons["magic"] = _one_line(exc)

    klayout = parse_klayout_reports(runs_dir, cell_name)

    lvs: Optional[LvsReport] = None
    try:
        lvs = parse_netgen_lvs_report(find_netgen_lvs_report(runs_dir, cell_name))
    except (VerificationError, OSError) as exc:
        reasons["lvs"] = _one_line(exc)

    return magic, klayout, lvs, reasons


def _drc_status(report: Optional[DrcReport], reason: str) -> tuple[str, str]:
    """Return ``(status, detail)`` for one DRC engine, never guessing "clean"."""
    if report is None:
        return STATUS_UNAVAILABLE, reason or "no report file found"
    if not report.available:
        return STATUS_UNAVAILABLE, _one_line(
            report.unavailable_reason or "no report file found"
        )
    if report.unparsed_files:
        if report.violations:
            # Violations are positive evidence of failure even when part of the
            # report was lost.
            return STATUS_FAIL, f"{report.unparsed_files} report file(s) unreadable"
        return (
            STATUS_DEGRADED,
            f"{report.unparsed_files} report file(s) unreadable, so a clean "
            "result cannot be confirmed",
        )
    return (STATUS_PASS if report.clean else STATUS_FAIL), ""


def _lvs_status(report: Optional[LvsReport], reason: str) -> tuple[str, str]:
    """Return ``(status, detail)`` for the Netgen run."""
    if report is None:
        return STATUS_UNAVAILABLE, reason or "no report file found"
    if report.verdict == "no_final_result":
        return STATUS_UNAVAILABLE, "Netgen printed no 'Final result:' line"
    if report.verdict == "uncertain":
        return STATUS_DEGRADED, "Netgen's final result could not be classified"
    return (STATUS_PASS if report.clean else STATUS_FAIL), ""


def _overall_status(
    magic_on_disk: bool, lvs_on_disk: bool, statuses: Sequence[str]
) -> str:
    """Return ``PASS``, ``FAIL`` or ``ERROR`` for the three artifact statuses.

    ``PASS`` needs every artifact to be positively clean; nothing short of that
    reaches it, which is what the old ``magic is None or magic.clean`` could not
    say -- it read "no report" as "nothing wrong" and printed "*No verification
    reports found*" four lines above "**Overall:** PASS".

    ``ERROR`` is reserved for the cell that could not be graded at all: the
    Magic or the Netgen report is not on disk.  Everything else that is not
    clean is ``FAIL``.  ``scripts/report_verification.py`` and
    ``scripts/evidence.py`` grade with the same tokens and the same precedence.
    """
    if not magic_on_disk or not lvs_on_disk:
        return "ERROR"
    if all(status == STATUS_PASS for status in statuses):
        return STATUS_PASS
    return STATUS_FAIL


def _device_table(subckt: Subckt) -> str:
    """Return a markdown table of MOSFET devices."""
    lines = [
        "| Device | Model | Drain | Gate | Source | Bulk | W (nm) | L (nm) | ng | m |",
        "|--------|-------|-------|------|--------|------|--------|--------|----|----|",
    ]
    for d in subckt.devices:
        # Netlist identifiers are external text: keep each one on its own line
        # so none of them can open a line of its own in the document.
        lines.append(
            f"| {_one_line(d.name)} | {_one_line(d.model)} | {_one_line(d.drain)} "
            f"| {_one_line(d.gate)} | {_one_line(d.source)} | {_one_line(d.bulk)} "
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
        # Port names come from the model-written generator module.
        direction = _one_line(port.direction or "-")
        layer = _one_line(port.layer.name)
        r = port.rect
        lines.append(
            f"| {_one_line(name)} | {direction} | {layer} | {r.left:g} | {r.bottom:g} "
            f"| {r.right:g} | {r.top:g} |"
        )
    return "\n".join(lines)


def _layout_strategy(subckt: Subckt) -> str:
    """Return a short human-readable layout plan."""
    out = _one_line(subckt.output_net or "?")
    vdd = _one_line(subckt.vdd_net or "?")
    vss = _one_line(subckt.vss_net or "?")
    gate_order = [_one_line(g) for g in suggest_gate_order(subckt)]

    lines = [
        f"* **Output net:** {out}",
        f"* **Power net:** {vdd}",
        f"* **Ground net:** {vss}",
        f"* **Suggested gate order (left-to-right):** {' '.join(gate_order)}",
    ]

    def describe_group(group, head, rail):
        names = [_one_line(d.name) for d in group]
        if len(group) == 1:
            return f"{names[0]} connects {head} to {rail}"
        if all({d.drain, d.source} == {head, rail} for d in group):
            gates = [_one_line(d.gate) for d in group]
            return f"parallel group ({', '.join(names)}) driven by {', '.join(gates)}"
        chain = series_chain(group, head, rail)
        if chain:
            chain_names = [_one_line(d.name) for d in chain]
            chain_gates = [_one_line(d.gate) for d in chain]
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


def _drc_line(label: str, report: Optional[DrcReport], status: str, detail: str) -> str:
    """Return the markdown bullet for one DRC engine."""
    if status == STATUS_UNAVAILABLE or report is None:
        return f"* **{label}:** {STATUS_UNAVAILABLE} — {_one_line(detail)}"
    count = f"{report.error_count} error" + ("" if report.error_count == 1 else "s")
    extra = ""
    mismatched = (
        report.reported_count is not None and report.reported_count != report.error_count
    )
    if report.reported_count is not None and (mismatched or report.tool == "magic"):
        # Echo the tool's own count so a parser that went blind shows up as a
        # disagreement instead of as a clean layout.
        extra = f", tool reported COUNT: {report.reported_count}"
    text = f"* **{label}:** {status} ({count}{extra})"
    if detail:
        text += f"\n  * NOT VERIFIED: {_one_line(detail)}"
    if report.location_note:
        text += f"\n  * WARNING: non-canonical report location: {_one_line(report.location_note)}"
    return text


def _verification_summary(
    magic: Optional[DrcReport],
    klayout: Optional[DrcReport],
    lvs: Optional[LvsReport],
    magic_status: tuple[str, str],
    klayout_status: tuple[str, str],
    lvs_status: tuple[str, str],
) -> str:
    """Return a markdown verification block.

    Every artifact gets a line whether or not it was found: a report that is
    absent is stated as absent, never omitted.  Omitting it is what left the
    block empty and let the document below it read ``PASS``.
    """
    lines = [
        _drc_line("Magic DRC", magic, *magic_status),
        _drc_line("KLayout DRC", klayout, *klayout_status),
    ]

    tool = lvs.tool if lvs is not None else "netgen"
    if lvs is None or lvs_status[0] == STATUS_UNAVAILABLE:
        message = _one_line(lvs_status[1] if lvs is None else lvs.message)
        lines.append(f"* **LVS ({tool}):** {STATUS_UNAVAILABLE} — {message}")
    else:
        lines.append(
            f"* **LVS ({tool}):** {lvs_status[0]} "
            f"(`{lvs.verdict}`) — {_one_line(lvs.message)}"
        )
        if lvs_status[1]:
            lines.append(f"  * NOT VERIFIED: {_one_line(lvs_status[1])}")
        if lvs.device_counts:
            lines.append("  * Device counts:")
            for dev, (layout_count, schematic_count) in sorted(lvs.device_counts.items()):
                mark = "✓" if layout_count == schematic_count else "✗"
                lines.append(
                    f"    * {mark} `{_one_line(dev)}`: layout={layout_count}, "
                    f"schematic={schematic_count}"
                )
        if lvs.disconnected_nodes:
            nodes = ", ".join(f"`{_one_line(n)}`" for n in lvs.disconnected_nodes)
            lines.append(f"  * Disconnected nodes: {nodes}")
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

    magic, klayout, lvs, reasons = _load_verification_reports(cell_name, runs_dir)
    magic_status = _drc_status(magic, reasons.get("magic", ""))
    klayout_status = _drc_status(klayout, reasons.get("klayout", ""))
    lvs_status = _lvs_status(lvs, reasons.get("lvs", ""))
    # A missing report is not a pass.  The overall line says ERROR when any
    # artifact is absent or only partly readable, so "no report" can never be
    # read as "nothing wrong".
    overall = _overall_status(
        magic is not None,
        lvs is not None,
        [magic_status[0], klayout_status[0], lvs_status[0]],
    )
    overall_note = ""
    if overall == "ERROR":
        missing = " and no ".join(
            label
            for label, present in (("Magic DRC", magic is not None), ("Netgen LVS", lvs is not None))
            if not present
        )
        overall_note = (
            f" — no {missing} report on disk, so nothing was verified; "
            "**this cell has not been checked**"
        )
    elif overall == STATUS_FAIL:
        unverified = [
            label
            for label, status in (
                ("Magic DRC", magic_status[0]),
                ("KLayout DRC", klayout_status[0]),
                ("Netgen LVS", lvs_status[0]),
            )
            if status in STATUS_UNVERIFIED
        ]
        if unverified:
            overall_note = (
                f" — {' and '.join(unverified)} produced no usable verdict; a "
                "report that is absent, empty, truncated or unreadable is NOT clean"
            )

    width = boundary.right - boundary.left
    height = boundary.top - boundary.bottom

    md = f"""# {_one_line(cell_name)}

Auto-generated documentation for the AION layout of `{_one_line(cell_name)}`.

## Netlist

* **Source:** `{_one_line(netlist_path)}`
* **Subckt:** `{_one_line(subckt.name)}`
* **Pins:** {' '.join(f"`{_one_line(p)}`" for p in subckt.pins)}

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

{_verification_summary(magic, klayout, lvs, magic_status, klayout_status, lvs_status)}

**Overall:** {overall}{overall_note}

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
