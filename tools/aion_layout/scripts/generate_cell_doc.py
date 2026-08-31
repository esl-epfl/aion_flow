#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               CLI to generate markdown docs for an AION cell
# ================================================================

"""Generate a markdown documentation file for a verified AION cell.

Example::

    python3 scripts/generate_cell_doc.py --cell-module path/to/cell.py --netlist path/to/cell.spice -o path/to/cell.md --runs-dir path/to/runs
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Allow running from the repository root without an editable install.
ROOT = Path(os.environ.get("AION_ROOT", Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(ROOT))

from aion_layout.doc_generator import generate_doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate markdown documentation for an AION standard cell.",
    )
    parser.add_argument(
        "--cell-module",
        required=True,
        help="Path to the Python cell generator module.",
    )
    parser.add_argument(
        "--cell-name",
        default=None,
        help="Top-level cell name (default: module stem).",
    )
    parser.add_argument(
        "--netlist",
        required=True,
        help="Path to the SPICE netlist for the cell.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output markdown file.",
    )
    parser.add_argument(
        "--runs-dir",
        required=True,
        help="Directory containing DRC/LVS reports.",
    )
    args = parser.parse_args(argv)

    netlist_path = Path(args.netlist)
    if not netlist_path.exists():
        print(f"Error: netlist not found: {netlist_path}", file=sys.stderr)
        return 2

    output_path = Path(args.output)
    runs_dir = Path(args.runs_dir)
    cell_module_path = Path(args.cell_module)
    if not cell_module_path.exists():
        print(f"Error: cell module not found: {cell_module_path}", file=sys.stderr)
        return 2

    cell_name = args.cell_name
    if cell_name is None:
        cell_name = cell_module_path.stem

    try:
        generate_doc(
            cell_name,
            netlist_path,
            output_path,
            runs_dir=runs_dir,
            cell_module_path=cell_module_path,
        )
    except Exception as exc:  # pragma: no cover - CLI error handling
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Documentation written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
