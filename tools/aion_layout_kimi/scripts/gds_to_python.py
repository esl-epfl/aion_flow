#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               CLI to convert a GDS cell into Python code
# ================================================================

"""Convert a GDSII cell into a runnable AION Python generator.

Example::

    python3 scripts/gds_to_python.py path/to/cell.gds
    python3 scripts/gds_to_python.py path/to/cell.gds -o path/to/cell_from_gds.py
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

# Allow running from the repository root without an editable install.
ROOT = Path(os.environ.get("AION_ROOT", Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(ROOT))

from aion_layout.gds_to_python import GdsReader, emit_python


def _load_tech(spec: str) -> object:
    module_name, obj_name = spec.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, obj_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a GDSII cell into an AION Python generator.",
    )
    parser.add_argument("gds", help="Path to the input GDS file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Output Python file (default: print to stdout).",
    )
    parser.add_argument(
        "--cell",
        help="Top cell name to read (default: first top-level cell).",
    )
    parser.add_argument(
        "--tech",
        default="aion_layout.tech:sg13g2_tech",
        help="Technology object as 'module.path:object_name' (default: aion_layout.tech:sg13g2_tech).",
    )
    parser.add_argument(
        "--no-ports",
        action="store_true",
        help="Skip reconstructing Port objects from text labels.",
    )
    args = parser.parse_args(argv)

    gds_path = Path(args.gds)
    if not gds_path.exists():
        print(f"Error: GDS file not found: {gds_path}", file=sys.stderr)
        return 2

    tech = _load_tech(args.tech)
    reader = GdsReader(tech)
    cell = reader.read(gds_path, top_cell_name=args.cell)

    if args.no_ports:
        cell.ports.clear()

    module_name = gds_path.stem
    py_code = emit_python(cell, module_name=module_name, tech_name=args.tech.split(":")[-1])

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(py_code)
        print(f"Python generator written to {output_path}")
    else:
        print(py_code)

    return 0


if __name__ == "__main__":
    sys.exit(main())
