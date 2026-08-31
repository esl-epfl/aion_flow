#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               CLI helper to generate a standard-cell GDS
# ================================================================

"""Generate a GDS file from a Python cell generator.

The cell module must expose a ``generate(cell_name, tech) -> Cell`` function.
The generator can be specified either as a Python module path or as a file path.
"""

import argparse
import importlib
import importlib.util
import os
import sys
from pathlib import Path

# Allow running from the repository root without an editable install.
ROOT = Path(os.environ.get("AION_ROOT", Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(ROOT))


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a standard-cell GDS")
    parser.add_argument(
        "cell",
        help="cell generator: dotted module path (e.g. cells.sg13g2_nand2_1) or path to a .py file",
    )
    parser.add_argument("output", help="output GDS path")
    parser.add_argument(
        "--cell-name",
        default=None,
        help="top-level cell name (default: module stem or cell argument)",
    )
    parser.add_argument(
        "--tech",
        default="aion_layout.tech:sg13g2_tech",
        help="technology object as 'module.path:object_name' (default: aion_layout.tech:sg13g2_tech)",
    )
    args = parser.parse_args()

    tech = _load_tech(args.tech)

    try:
        cell_module = _load_module(args.cell)
    except Exception as exc:
        print(f"Error: cannot load cell generator {args.cell}: {exc}", file=sys.stderr)
        return 1

    if not hasattr(cell_module, "generate"):
        print(
            f"Error: {args.cell} does not define a generate(cell_name, tech) function",
            file=sys.stderr,
        )
        return 1

    cell_name = args.cell_name
    if cell_name is None:
        path = Path(args.cell)
        cell_name = path.stem if path.suffix == ".py" else args.cell.split(".")[-1]

    cell = cell_module.generate(cell_name, tech)
    cell.write_gds(args.output)
    print(f"Generated {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
