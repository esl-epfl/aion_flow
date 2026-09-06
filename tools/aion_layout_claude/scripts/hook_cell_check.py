#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               PostToolUse hook: check a cell generator on save
# ================================================================

"""Static check of a cell generator, run automatically whenever one is edited.

A full DRC/LVS round takes minutes in the container.  Most of what goes wrong
between two rounds does not need it: the module does not import, ``generate``
raises, the boundary is off the site grid, a transistor is missing, or two nets
overlap on Metal1.  All five are answerable from the GDS alone in about a
second, and answering them at the moment of the edit is worth far more than
answering them three minutes later.

So this hook builds the cell into a scratch GDS and reports:

    build          the traceback, if it did not
    geometry       width x height, sites, and whether the cell is row-legal
    devices        gate crossings drawn against devices the netlist asks for
    shorts         every pair of differently-named nets that touch, by coordinate

It is deliberately **advisory**.  It never blocks an edit and it never reports a
verdict: nothing here is a substitute for DRC and LVS, and a cell that passes
every check above can still be dirty.  The one thing it must not do is give a
false all-clear, so a check that cannot run says so rather than staying silent.

Contract: reads the PostToolUse hook payload on stdin, writes one JSON object on
stdout carrying ``additionalContext``, and always exits 0.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent.parent
CELLS_DIR = TOOL_DIR / "cells"

#: The check runs the generator, so it needs a wall-clock limit of its own.
BUILD_TIMEOUT = 60


def emit(context: str) -> None:
    """Hand ``context`` back to the session and exit successfully."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": context,
                }
            }
        )
    )
    sys.exit(0)


def target_path(payload: dict) -> Path | None:
    """Return the edited cell generator, or ``None`` if this edit is not one."""
    tool_input = payload.get("tool_input") or {}
    raw = tool_input.get("file_path") or tool_input.get("filePath")
    if not raw:
        return None
    path = Path(raw)
    if path.suffix != ".py":
        return None
    try:
        resolved = path.resolve()
    except OSError:
        return None
    if resolved.parent != CELLS_DIR:
        return None
    if resolved.name.startswith("_") or resolved.name == "__init__.py":
        return None
    return resolved


#: Run in a subprocess: the generator is code that may exit, print or loop.
PROBE = r"""
import importlib.util, json, sys, os
sys.stdout = sys.stderr                      # a generator that prints must not
                                             # corrupt the JSON on stdout
out = {}
try:
    spec = importlib.util.spec_from_file_location("_cell_under_test", MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "generate"):
        raise AttributeError("module defines no generate(name, tech)")
    from aion_layout.tech import sg13g2_tech
    cell = mod.generate(CELL, sg13g2_tech)
    cell.write_gds(GDS)
    out["built"] = True
except BaseException as exc:
    import traceback
    out["built"] = False
    out["error"] = traceback.format_exc(limit=8)

if out["built"]:
    try:
        from aion_layout.metrics import gds_boundary, routing_metals_used
        g = gds_boundary(GDS, allow_bbox_fallback=True)
        out["geometry"] = {
            "describe": g.describe(),
            "problems": list(g.problems),
            "source": g.source,
        }
        out["metals"] = routing_metals_used(GDS)
    except BaseException as exc:
        out["geometry_error"] = f"{type(exc).__name__}: {exc}"
    try:
        from aion_layout.layout_metrics import count_gate_crossings
        c = count_gate_crossings(GDS)
        out["crossings"] = {"count": c.count, "reason": c.reason}
    except BaseException as exc:
        out["crossings_error"] = f"{type(exc).__name__}: {exc}"
    if NETLIST:
        try:
            from aion_layout.spice_parser import parse_first_subckt
            # A gate crossing is one FINGER, not one device: an ng=2 device is
            # drawn as two poly-over-active regions and must be counted twice,
            # or every folded cell reads as having too many transistors.
            devs = parse_first_subckt(NETLIST).devices
            out["devices_required"] = sum(max(1, int(d.fingers or 1)) for d in devs)
            out["devices_declared"] = len(devs)
        except BaseException as exc:
            out["netlist_error"] = f"{type(exc).__name__}: {exc}"
    try:
        from aion_layout.metrics import cross_net_overlaps
        out["shorts"] = [str(s) for s in cross_net_overlaps(GDS)]
    except BaseException as exc:
        out["shorts_error"] = f"{type(exc).__name__}: {exc}"

sys.__stdout__.write(json.dumps(out))
"""


def probe(module: Path, cell: str, gds: Path, netlist: Path | None) -> dict:
    """Build the cell in a subprocess and return the measurements it took."""
    netlist_literal = repr(str(netlist)) if netlist else "None"
    preamble = (
        f"MODULE = {str(module)!r}\n"
        f"CELL = {cell!r}\n"
        f"GDS = {str(gds)!r}\n"
        f"NETLIST = {netlist_literal}\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(TOOL_DIR)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", preamble + PROBE],
            cwd=str(TOOL_DIR),
            capture_output=True,
            text=True,
            timeout=BUILD_TIMEOUT,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {"built": False, "error": f"generate() did not finish in {BUILD_TIMEOUT}s"}
    except OSError as exc:
        return {"probe_failed": f"could not run the probe: {exc}"}
    if not proc.stdout.strip():
        tail = "\n".join((proc.stderr or "").splitlines()[-20:])
        return {"probe_failed": f"probe produced no result. stderr tail:\n{tail}"}
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {"probe_failed": f"probe output was not JSON: {proc.stdout[:400]}"}


def find_netlist(cell: str) -> Path | None:
    """Find the netlist for ``cell`` by the naming the flow uses, or None."""
    for name in (
        f"{cell}.spice",
        f"{cell}_minimized.spice",
        f"{cell.removesuffix('_1')}_minimized.spice",
    ):
        candidate = TOOL_DIR / name
        if candidate.is_file():
            return candidate
    return None


def render(cell: str, module: Path, result: dict) -> str:
    """Turn the probe's measurements into the lines the session will read."""
    lines = [f"aion-layout static check of cells/{module.name} (advisory, not a verdict):"]

    if "probe_failed" in result:
        lines.append(f"  CHECK DID NOT RUN: {result['probe_failed']}")
        lines.append("  Nothing was verified. Run `make verify` before trusting this edit.")
        return "\n".join(lines)

    if not result.get("built"):
        lines.append("  BUILD FAILED — generate() did not produce a GDS:")
        lines.append("    " + (result.get("error", "no traceback captured")).replace("\n", "\n    "))
        return "\n".join(lines)

    lines.append("  build: ok")

    geometry = result.get("geometry")
    if geometry:
        lines.append(f"  geometry: {geometry['describe']}")
        for problem in geometry["problems"]:
            lines.append(f"    NOT ROW-LEGAL: {problem}")
        if not geometry["problems"]:
            lines.append("    row-legal: 3.78 um tall, a whole number of 0.48 um sites")
    elif "geometry_error" in result:
        lines.append(f"  geometry: COULD NOT MEASURE — {result['geometry_error']}")

    metals = result.get("metals")
    if metals is not None:
        lines.append(f"  routing metals drawn: {', '.join(metals) or 'none'}")

    crossings = result.get("crossings") or {}
    required = result.get("devices_required")
    if crossings.get("count") is not None:
        drawn = crossings["count"]
        declared = result.get("devices_declared")
        folded = "" if declared in (None, required) else f" ({declared} devices, folded)"
        if required is None:
            lines.append(f"  devices: {drawn} gate-over-active regions drawn")
        elif drawn == required:
            lines.append(
                f"  devices: {drawn}/{required} fingers drawn{folded} — "
                "every device in the netlist"
            )
        else:
            lines.append(
                f"  devices: {drawn} finger(s) drawn but the netlist needs {required} — "
                f"{'add' if drawn < required else 'remove'} "
                f"{abs(required - drawn)} gate-over-active region(s)"
            )
    elif crossings.get("reason"):
        lines.append(f"  devices: COULD NOT COUNT — {crossings['reason']}")

    shorts = result.get("shorts")
    if shorts is None:
        note = result.get("shorts_error", "no reason recorded")
        lines.append(f"  shorts: NOT CHECKED — {note}")
    elif shorts:
        lines.append(f"  SHORTS: {len(shorts)} cross-net overlap(s):")
        for row in shorts[:12]:
            lines.append("    " + row)
        if len(shorts) > 12:
            lines.append(f"    ... and {len(shorts) - 12} more")
    else:
        lines.append("  shorts: none — no two differently-named nets touch")

    lines.append("  This is a static check. DRC and LVS still decide: `make verify`.")
    return "\n".join(lines)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    module = target_path(payload)
    if module is None:
        return 0
    cell = module.stem
    with tempfile.TemporaryDirectory(prefix="aion_hook_") as tmp:
        gds = Path(tmp) / f"{cell}.gds"
        result = probe(module, cell, gds, find_netlist(cell))
    emit(render(cell, module, result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
