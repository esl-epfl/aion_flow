#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               CLI to scaffold a cell from a SPICE netlist
# ================================================================

"""Generate a starter AION cell generator from a SPICE netlist.

Optionally generate the GDS and run DRC/LVS/report generation in one shot.

Examples::

    python3 scripts/generate_from_netlist.py path/to/netlist.spice -o path/to/cell.py
    python3 scripts/generate_from_netlist.py path/to/netlist.spice -o path/to/cell.py --generate-gds --run-verification
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

# Allow running from the repository root without an editable install.
ROOT = Path(os.environ.get("AION_ROOT", Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(ROOT))

from aion_layout.auto_scaffold import write_scaffold
from aion_layout.netlist_view import netlist_summary
from aion_layout.spice_parser import parse_first_subckt


def _load_module(spec: str) -> object:
    """Load a module from a dotted path or a file path."""
    path = Path(spec)
    if path.exists() and path.suffix == ".py":
        module_name = path.stem
        spec_obj = importlib.util.spec_from_file_location(module_name, path)
        if spec_obj is None or spec_obj.loader is None:
            raise ImportError(f"Cannot load module from {path}")
        module = importlib.util.module_from_spec(spec_obj)
        sys.modules[module_name] = module
        spec_obj.loader.exec_module(module)
        return module
    return importlib.import_module(spec)


def _load_tech(spec: str) -> object:
    module_name, obj_name = spec.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, obj_name)


def _generate_gds(cell_path: Path, gds_path: Path, cell_name: str | None, tech_spec: str) -> int:
    """Generate a GDS from the freshly-written cell generator."""
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "generate_cell.py"),
        str(cell_path),
        str(gds_path),
        "--tech",
        tech_spec,
    ]
    if cell_name is not None:
        cmd.extend(["--cell-name", cell_name])
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return result.returncode
    print(result.stdout.strip())
    return 0


def _run_verification(
    gds_path: Path,
    netlist_path: Path,
    cell_name: str,
    runs_dir: Path,
    run_script: Path,
) -> int:
    """Run DRC/LVS and print a verification report."""
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "report_verification.py"),
        "--cell",
        cell_name,
        "--runs-dir",
        str(runs_dir),
        "--gds",
        str(gds_path),
        "--netlist",
        str(netlist_path),
        "--run-script",
        str(run_script),
    ]
    result = subprocess.run(cmd, check=False)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold an AION cell generator from a SPICE netlist.",
    )
    parser.add_argument("spice", help="Path to the SPICE netlist.")
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output path for the generated Python cell generator.",
    )
    parser.add_argument(
        "--width",
        type=float,
        default=None,
        help="Override the scaffolded cell width (nm).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a netlist summary before writing the scaffold.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing output file.",
    )
    parser.add_argument(
        "--generate-gds",
        action="store_true",
        help="Generate a GDS after writing the scaffold.",
    )
    parser.add_argument(
        "--gds-output",
        default=None,
        help="GDS output path (default: runs/<cell_name>.gds).",
    )
    parser.add_argument(
        "--cell-name",
        default=None,
        help="Top-level cell name (default: stem of the output path).",
    )
    parser.add_argument(
        "--tech",
        default="aion_layout.tech:sg13g2_tech",
        help="Technology object as 'module.path:object_name' (default: aion_layout.tech:sg13g2_tech).",
    )
    parser.add_argument(
        "--run-verification",
        action="store_true",
        help="Run DRC/LVS and print a verification report after GDS generation.",
    )
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory for verification artifacts (default: runs).",
    )
    parser.add_argument(
        "--run-script",
        default=str(Path(__file__).resolve().parent.parent / "scripts" / "docker_run.sh"),
        help="Path to the docker_run.sh wrapper script.",
    )
    args = parser.parse_args(argv)

    spice_path = Path(args.spice)
    if not spice_path.exists():
        print(f"Error: netlist not found: {spice_path}", file=sys.stderr)
        return 2

    output_path = Path(args.output)
    if output_path.exists() and not args.force:
        print(
            f"Error: output file already exists: {output_path}. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 2

    subckt = parse_first_subckt(spice_path)
    if args.summary:
        print(netlist_summary(subckt))
        print()

    output_path = write_scaffold(spice_path, output_path, cell_width=args.width, force=args.force)
    print(f"Scaffold written to {output_path}")

    cell_name = args.cell_name
    if cell_name is None:
        # Default to the SPICE subckt name so LVS can match the netlist cell.
        cell_name = subckt.name

    if args.generate_gds or args.run_verification:
        gds_path = Path(args.gds_output) if args.gds_output else Path(args.runs_dir) / f"{cell_name}.gds"
        gds_path.parent.mkdir(parents=True, exist_ok=True)
        rc = _generate_gds(output_path, gds_path, cell_name, args.tech)
        if rc != 0:
            return rc

    if args.run_verification:
        run_script = Path(args.run_script)
        if not run_script.exists():
            print(f"Error: run script not found: {run_script}", file=sys.stderr)
            return 2
        return _run_verification(
            gds_path=gds_path,
            netlist_path=spice_path,
            cell_name=cell_name,
            runs_dir=Path(args.runs_dir),
            run_script=run_script,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
