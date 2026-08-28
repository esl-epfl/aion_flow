#!/usr/bin/env python3
"""Standalone example: parse SPICE netlists with aion_minimizer."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = REPO_ROOT / "examples" / "aion_minimizer"


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "tools" / "aion_minimizer"))

    from aion_minimizer.spice_parser import Mosfet, Subcircuit, SubcircuitInstance, parse_spice_file

    top_path = EXAMPLE_DIR / "AION_inv_nand2_nor2.spice"
    lib_path = EXAMPLE_DIR / "sg13g2_stdcell.spice"

    top = parse_spice_file(top_path)
    assert "AION_inv_nor2_nor3" in top, list(top)
    sub = top["AION_inv_nor2_nor3"]
    assert isinstance(sub, Subcircuit)
    assert sub.pins == ["I0", "I1", "I2", "O0", "VDD", "VSS"]
    assert not sub.is_gate_definition
    assert len(sub.instances) == 3
    assert all(isinstance(i, SubcircuitInstance) for i in sub.instances)
    assert sub.instances[0].subckt_name == "sg13g2_inv_1"
    assert sub.instances[1].subckt_name == "sg13g2_nand2_1"
    assert sub.instances[2].subckt_name == "sg13g2_nor2_1"

    lib = parse_spice_file(lib_path)
    for name in ("sg13g2_inv_1", "sg13g2_nand2_1", "sg13g2_nor2_1"):
        assert name in lib, f"{name} not found in library"
        gate = lib[name]
        assert gate.is_gate_definition
        assert all(isinstance(d, Mosfet) for d in gate.devices)

    inv = lib["sg13g2_inv_1"]
    assert len(inv.mosfets) == 2
    assert any(m.is_nmos for m in inv.mosfets)
    assert any(m.is_pmos for m in inv.mosfets)

    nand = lib["sg13g2_nand2_1"]
    assert len(nand.mosfets) == 4

    nor = lib["sg13g2_nor2_1"]
    assert len(nor.mosfets) == 4

    print("Parse example: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
