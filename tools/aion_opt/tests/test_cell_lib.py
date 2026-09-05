"""Technology-dictionary handling, notably drive-strength collapsing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aion_opt.io.cell_lib import CellLib, collapse_cell_name

REPO_ROOT = Path(__file__).resolve().parents[3]
TECH_DICT = REPO_ROOT / "tech" / "tech_dict" / "sg13g2_stdcell.json"


@pytest.mark.parametrize(
    "name,expected",
    [
        ("sg13g2_inv_1", "sg13g2_inv"),
        ("sg13g2_inv_16", "sg13g2_inv"),   # regression: only _1/_2 were stripped
        ("sg13g2_buf_4", "sg13g2_buf"),
        ("sg13g2_buf_8", "sg13g2_buf"),
        ("sg13g2_and4_1", "sg13g2_and4"),  # the input count must survive
        ("sg13g2_a221oi_1", "sg13g2_a221oi"),
        ("sg13g2_tielo", "sg13g2_tielo"),
        ("sg13g2_sighold", "sg13g2_sighold"),
    ],
)
def test_collapse_strips_only_the_drive_strength(name, expected):
    assert collapse_cell_name(name) == expected


@pytest.mark.skipif(not TECH_DICT.exists(), reason="technology dictionary not present")
def test_every_strength_variant_folds_onto_one_key():
    lib = CellLib(TECH_DICT)
    raw = json.loads(TECH_DICT.read_text())
    raw = raw.get("cells", raw)

    for name in raw:
        assert name in lib, f"{name} is not resolvable through the collapsed keys"

    # All five inverter strengths must share a single generic entry.
    inverters = {n for n in raw if n.startswith("sg13g2_inv_")}
    assert len(inverters) > 1
    assert {lib.collapse_name(n) for n in inverters} == {"sg13g2_inv"}


@pytest.mark.skipif(not TECH_DICT.exists(), reason="technology dictionary not present")
def test_representative_is_the_smallest_variant():
    lib = CellLib(TECH_DICT)
    raw = json.loads(TECH_DICT.read_text())
    raw = raw.get("cells", raw)
    variants = {n: raw[n]["area"] for n in raw if n.startswith("sg13g2_inv_")}
    assert lib.area("sg13g2_inv") == min(variants.values())
    assert lib.concrete_name("sg13g2_inv") in variants


@pytest.mark.skipif(not TECH_DICT.exists(), reason="technology dictionary not present")
def test_sequential_and_physical_cells_are_excluded_from_mining():
    lib = CellLib(TECH_DICT)
    combinational = lib.combinational_types()

    for name in ("sg13g2_dfrbp", "sg13g2_sdfrbp", "sg13g2_dlhq", "sg13g2_slgcp"):
        assert name not in combinational, f"{name} must not be mined"
    for name in ("sg13g2_fill", "sg13g2_decap", "sg13g2_antennanp", "sg13g2_sighold"):
        assert name not in combinational, f"{name} carries no logic"
    for name in ("sg13g2_nand2", "sg13g2_xor2", "sg13g2_mux2", "sg13g2_a21oi"):
        assert name in combinational
