# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               The starting point must actually start
# ================================================================

"""A scaffold is the first thing a model is handed, so it has to run.

A skeleton that does not import, or imports and defines no ``generate``, or
defines one that raises, costs the whole first iteration -- and the failure
looks like the model's fault rather than the tool's.  So the contract is
executable, not textual: the scaffold is written, imported in a subprocess the
way the build step imports it, called, and the GDS it produced is measured.

Running it in a subprocess through :func:`runner.run_python_isolated` is
deliberate.  That is exactly how ``steps.build_gds`` runs a generator, so a
scaffold that only works when imported into the test process would pass here and
fail in the flow.
"""

from __future__ import annotations

import pytest

from aion_layout.metrics import MetricsError, gds_boundary, layer_inventory
from aion_layout.runner import run_python_isolated
from conftest import CELL, optional_module

scaffold = optional_module("aion_layout.scaffold")

ScaffoldError = scaffold.ScaffoldError


@pytest.fixture
def scaffolded(tmp_path, netlist_path):
    """Write a scaffold for the worked netlist and return its path."""
    return scaffold.scaffold_module(netlist_path, tmp_path / "scaffolded_cell.py")


def test_the_scaffold_is_written_and_parses(scaffolded):
    """A file that does not compile is not a starting point."""
    import ast

    source = scaffolded.read_text()
    assert source.strip(), "the scaffold must not be empty"
    ast.parse(source)  # raises SyntaxError if the generated source is broken

    assert "def generate(" in source, (
        "the build step calls generate(cell_name, tech); a scaffold without it "
        f"fails at the first build:\n{source[:600]}"
    )


def test_the_scaffold_imports_and_exposes_generate(scaffolded):
    """Imported the way steps.build_gds imports it, not the way a test would."""
    result = run_python_isolated(
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('scaf', {str(scaffolded)!r})\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "sys.modules['scaf'] = module\n"
        "spec.loader.exec_module(module)\n"
        "assert callable(getattr(module, 'generate', None)), 'no generate()'\n"
        "print('OK')\n",
        timeout=120,
    )

    assert result.ok, (
        "the scaffold must import cleanly in a fresh interpreter with only the "
        f"tool directory on the path:\n{result.tail(30)}"
    )
    assert "OK" in result.output


def test_the_scaffold_runs_and_writes_a_non_empty_gds(scaffolded, tmp_path):
    """The first iteration has to produce a layout, even a wrong one."""
    out_gds = tmp_path / f"{CELL}.gds"

    result = run_python_isolated(
        "import importlib.util, sys\n"
        "from aion_layout.tech import sg13g2_tech\n"
        f"spec = importlib.util.spec_from_file_location('scaf', {str(scaffolded)!r})\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "sys.modules['scaf'] = module\n"
        "spec.loader.exec_module(module)\n"
        f"cell = module.generate({CELL!r}, sg13g2_tech)\n"
        "assert cell is not None, 'generate() returned None'\n"
        f"cell.write_gds({str(out_gds)!r})\n"
        "print('WROTE')\n",
        timeout=180,
    )

    assert result.ok, (
        f"generate() must run to completion on the worked netlist:\n"
        f"{result.tail(40)}"
    )
    assert out_gds.is_file(), f"no GDS was written to {out_gds}"
    assert out_gds.stat().st_size > 0, (
        "a zero-byte GDS is not a layout; every later step reads this file"
    )


def test_the_scaffolded_layout_can_be_measured(scaffolded, tmp_path):
    """The very first verify() call measures the GDS; it must be measurable."""
    out_gds = tmp_path / f"{CELL}.gds"
    result = run_python_isolated(
        "import importlib.util, sys\n"
        "from aion_layout.tech import sg13g2_tech\n"
        f"spec = importlib.util.spec_from_file_location('scaf', {str(scaffolded)!r})\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "sys.modules['scaf'] = module\n"
        "spec.loader.exec_module(module)\n"
        f"module.generate({CELL!r}, sg13g2_tech).write_gds({str(out_gds)!r})\n",
        timeout=180,
    )
    assert result.ok, result.tail(40)

    try:
        geometry = gds_boundary(out_gds, CELL)
    except MetricsError as exc:
        pytest.fail(
            "the scaffolded GDS must be measurable from the first iteration; "
            f"a layout nothing can measure cannot be graded: {exc}"
        )

    assert geometry.height_um > 0 and geometry.width_um > 0, (
        f"a degenerate footprint is a scaffold that drew nothing: {geometry}"
    )
    inventory = layer_inventory(out_gds, CELL)
    assert inventory, (
        "a scaffold that draws no geometry at all leaves the model nothing to "
        "edit and every downstream step nothing to read"
    )


def test_the_scaffold_names_the_cell_it_was_asked_for(tmp_path, netlist_path):
    """A scaffold under the wrong cell name fails LVS before it is even edited."""
    path = scaffold.scaffold_module(
        netlist_path, tmp_path / "named.py", cell_name=CELL
    )

    assert CELL in path.read_text(), (
        f"the cell name has to appear in the generated module: {path}"
    )


def test_an_existing_module_is_never_silently_overwritten(tmp_path, netlist_path):
    """By iteration two that file is the model's work; replacing it destroys it."""
    path = tmp_path / "cell.py"
    path.write_text("# the model's hand-edited generator\n")

    with pytest.raises(ScaffoldError) as excinfo:
        scaffold.scaffold_module(netlist_path, path)

    assert "already exists" in str(excinfo.value), (
        f"the refusal must say the file is already there: {excinfo.value}"
    )
    assert path.read_text() == "# the model's hand-edited generator\n", (
        "the refused call must not have touched the file"
    )

    scaffold.scaffold_module(netlist_path, path, force=True)
    assert "def generate(" in path.read_text(), (
        "force=True is the explicit way to discard it, and must then work"
    )


def test_a_missing_netlist_is_refused(tmp_path):
    """A scaffold from nothing is a generator for nothing."""
    with pytest.raises(ScaffoldError) as excinfo:
        scaffold.scaffold_module(tmp_path / "nope.spice", tmp_path / "out.py")
    assert "nope.spice" in str(excinfo.value), (
        f"the refusal must name the netlist it could not read: {excinfo.value}"
    )


def test_an_unparseable_netlist_is_refused(tmp_path):
    """A SPICE file the parser cannot read must raise, not scaffold a guess."""
    bad = tmp_path / "bad.spice"
    bad.write_text(".subckt X A Y VDD VSS\nXN0 Y A B C VSS sg13_lv_nmos w=1u l=1u\n.ends\n")

    with pytest.raises(ScaffoldError):
        scaffold.scaffold_module(bad, tmp_path / "out.py")


def test_scaffold_source_mentions_the_ports_of_the_netlist(netlist_path):
    """The model reads the scaffold before it reads the netlist."""
    from aion_layout.spice_parser import parse_first_subckt

    source = scaffold.scaffold_source(parse_first_subckt(netlist_path))

    for pin in ("I0", "I1", "I2", "O0", "VDD", "VSS"):
        assert pin in source, (
            f"port {pin} is part of the cell's interface and must appear in "
            "the scaffold, or the model will draw a cell with the wrong pins"
        )
