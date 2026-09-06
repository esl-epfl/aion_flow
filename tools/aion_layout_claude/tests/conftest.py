# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Shared fixtures for the host-only test suite
# ================================================================

"""Fixtures for a suite that runs in seconds with no Docker and no PDK.

Two things this file exists to guarantee.

**Nothing here calls a tool.**  The container-only steps (``sak-drc.sh``,
``sak-lvs.sh``, PEX, characterisation) are never invoked; the suite grades the
*parsers* against real output those tools already produced, committed under
``tests/fixtures``.  A test that would need the container is marked
``@pytest.mark.docker`` and is deselected by ``pytest.ini``.

**The committed fixtures are read-only.**  They are the only real artifacts the
suite owns; a test that corrupts one in place destroys the ground truth every
other test is graded against.  Anything that plants, truncates or deletes works
on a copy, which is what :func:`work_tree` hands out.

**Nothing in this suite may skip.**  Every module the package promises has
landed and every artifact the suite grades against is committed under
``tests/fixtures``, so a missing one is a broken checkout, not a to-do.  A skip
exits 0 and prints nothing anyone reads, which is the same fail-open the whole
suite exists to forbid: absence of evidence is not evidence of a pass.  So
:func:`optional_module` imports for real and lets the ImportError stand, and
every fixture asserts rather than skips.
"""

from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Optional

import pytest

#: ``tools/aion_layout_claude`` -- the tool directory, importable as the package root.
TOOL_DIR = Path(__file__).resolve().parent.parent
FIXTURES = TOOL_DIR / "tests" / "fixtures"

#: The worked example: the AION cell this whole tool exists to lay out.
CELL = "AION_inv_nand2_nor2_1"
#: The same logic built by abutting PDK standard cells -- the baseline it races.
GATE_CELL = "AION_inv_nand2_nor2"

#: Ground truth for the committed GDS, measured from its prBoundary.
KNOWN_WIDTH_UM = 2.88
KNOWN_HEIGHT_UM = 3.78
KNOWN_AREA_UM2 = KNOWN_WIDTH_UM * KNOWN_HEIGHT_UM  # 10.8864

if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))


def optional_module(name: str) -> ModuleType:
    """Import ``name``, letting a failure stand as a collection error.

    This was ``pytest.importorskip`` while the package was being written in
    parallel.  Every module has landed, so the skip is now the most dangerous
    line in the suite: deleting ``aion_layout/compare.py`` turned 26 tests into
    "1 skipped" and the run still exited 0.  A module that will not import is
    the loudest possible failure, not a to-do -- so it is imported for real and
    the ImportError becomes a collection error and exit status 2.

    The name is kept because every test file calls it; what changed is that it
    can no longer answer "not today".
    """
    return importlib.import_module(name)


# ---------------------------------------------------------------------------
# Paths to real, committed artifacts
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def tool_dir() -> Path:
    return TOOL_DIR


@pytest.fixture(scope="session")
def cell_name() -> str:
    return CELL


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    assert FIXTURES.is_dir(), f"fixture tree missing: {FIXTURES}"
    return FIXTURES


@pytest.fixture(scope="session")
def known_gds() -> Path:
    """The built, DRC- and LVS-clean GDS of the worked example.

    2.88 x 3.78 um from its prBoundary, Metal1 only.  Every geometry assertion
    in the suite is anchored to this file rather than to a number typed twice.

    It is read from ``tests/fixtures/gds/`` and NOT from ``build/``.  ``build/``
    is a ``.gitignore``d scratch tree, so pointing at it made the whole geometry
    ground truth -- 15 tests, including every one that grades ``steps.verify``
    -- skip silently on any checkout that had not run ``make`` yet, and the
    suite still exited 0 reporting "186 passed".  A committed copy cannot go
    missing without the checkout itself being broken, which is why it asserts
    here instead of skipping.
    """
    path = FIXTURES / "gds" / f"{CELL}.gds"
    assert path.is_file(), (
        f"the committed copy of the verified layout is missing: {path}; it is "
        "the ground truth every geometry assertion in this suite is measured "
        "against and cannot be regenerated from anything else in the checkout"
    )
    return path


@pytest.fixture(scope="session")
def netlist_path() -> Path:
    """The transistor-level AION netlist the layout must match."""
    path = TOOL_DIR / f"{CELL}_minimized.spice"
    assert path.is_file(), f"the worked netlist is missing: {path}"
    return path


@pytest.fixture(scope="session")
def gate_netlist_path() -> Path:
    """The same logic as three abutted PDK standard cells."""
    path = TOOL_DIR / f"{GATE_CELL}.spice"
    assert path.is_file(), f"the gate-level netlist is missing: {path}"
    return path


@pytest.fixture(scope="session")
def clean_tree() -> Path:
    """Read-only: the captured artifacts of the run that passed everything."""
    path = FIXTURES / "clean"
    assert (path / "drc").is_dir(), f"clean fixture tree missing: {path}"
    return path


@pytest.fixture(scope="session")
def dirty_tree() -> Path:
    """Read-only: the captured artifacts of a run with 8 real DRC violations."""
    path = FIXTURES / "dirty"
    assert (path / "drc").is_dir(), f"dirty fixture tree missing: {path}"
    return path


@pytest.fixture
def work_tree(tmp_path):
    """Return a factory copying a committed tree into ``tmp_path``.

    Every test that plants a file, truncates a report or deletes a database
    needs a writable copy: mutating ``tests/fixtures`` in place would destroy
    the captured evidence the rest of the suite grades against.
    """

    def build(which: str = "clean", name: Optional[str] = None) -> Path:
        source = FIXTURES / which
        assert source.is_dir(), f"no committed fixture tree named {which!r}"
        dest = tmp_path / (name or which)
        shutil.copytree(source, dest)
        return dest

    return build


# ---------------------------------------------------------------------------
# Synthetic layouts
#
# Built with klayout.db alone -- no PDK, no tech file -- so that a test about
# what the measurement code does with a *shape* does not depend on the flow
# being able to produce one.
# ---------------------------------------------------------------------------

@pytest.fixture
def gds_factory(tmp_path):
    """Return ``write(name, *, boundary_um, metal_um, extra_layers)`` -> Path.

    ``boundary_um`` is the prBoundary rectangle in microns, or ``None`` to draw
    none at all; ``metal_um`` is a Metal1 rectangle.  ``extra_layers`` maps a
    ``(layer, datatype)`` GDS pair onto a rectangle, for a stray-metal case.
    """
    # Not importorskip: klayout.db is what metrics.py measures with, so a host
    # without it fails every geometry test anyway.  Skipping here would only
    # hide the cause behind a dozen unrelated MetricsErrors.
    import klayout.db as pya

    def write(
        name: str = "SYNTH",
        *,
        boundary_um: Optional[tuple] = (0.0, 0.0, 2.88, 3.78),
        metal_um: Optional[tuple] = (0.2, 0.2, 1.0, 1.0),
        extra_layers: Optional[dict] = None,
        cells: int = 1,
    ) -> Path:
        layout = pya.Layout()
        layout.dbu = 0.001

        def box(rect):
            l, b, r, t = (round(v / layout.dbu) for v in rect)
            return pya.Box(l, b, r, t)

        for index in range(cells):
            top = layout.create_cell(name if index == 0 else f"{name}_{index}")
            if boundary_um is not None:
                top.shapes(layout.layer(189, 4)).insert(box(boundary_um))
            if metal_um is not None:
                top.shapes(layout.layer(8, 0)).insert(box(metal_um))
            for pair, rect in (extra_layers or {}).items():
                top.shapes(layout.layer(*pair)).insert(box(rect))

        path = tmp_path / f"{name}.gds"
        layout.write(str(path))
        return path

    return write


# ---------------------------------------------------------------------------
# The suite is held to its own rule
# ---------------------------------------------------------------------------

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print the counts at any verbosity, and say why a skip is not a pass.

    Every module has landed and every artifact is committed, so nothing in this
    suite has a reason to skip any more.  A skip prints one grey line, exits 0,
    and hides however many tests were behind it -- deleting one module used to
    report "1 skipped" while 26 assertions quietly stopped running.  The suite
    that exists to say absence is not a pass does not get to make that trade
    for itself.

    A test deliberately excluded lives behind a marker and is *deselected*,
    which this does not touch.
    """
    counts = {
        key: len(terminalreporter.stats.get(key, []))
        for key in ("passed", "failed", "error", "skipped", "deselected", "xfailed")
    }
    # pytest.ini already carries -q, so the brief's `python3 -m pytest tests/ -q`
    # reaches quiet level 2 and prints no "N passed" line at all -- dots, and an
    # exit status nobody looks at.  This line is printed at every verbosity so
    # the one number a reviewer wants is always in the transcript.
    terminalreporter.write_line(
        "TESTS: "
        + ", ".join(f"{n} {key}" for key, n in counts.items() if n or key == "passed")
    )

    skipped = terminalreporter.stats.get("skipped", [])
    if not skipped:
        return
    terminalreporter.write_sep("!", "skips are not passes")
    for report in skipped:
        where = getattr(report, "nodeid", "?")
        reason = ""
        if isinstance(getattr(report, "longrepr", None), tuple):
            reason = report.longrepr[2]
        terminalreporter.write_line(f"  {where}: {reason}")
    terminalreporter.write_line(
        "  a skipped test asserted nothing and still exited 0; every module "
        "and artifact this suite needs is committed, so a skip is a broken "
        "checkout to fix, not a result to accept"
    )


def pytest_sessionfinish(session, exitstatus):
    """Give the skip an exit status, not only a paragraph.

    ``pytest_terminal_summary`` above says why; it runs too late to change the
    process status.  This is the last hook before ``wrap_session`` returns
    ``session.exitstatus``, so it is where a run that skipped stops exiting 0.
    """
    skipped = session.config.pluginmanager.get_plugin("terminalreporter")
    if skipped is None:
        return
    if skipped.stats.get("skipped") and exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


@pytest.fixture(autouse=True, scope="session")
def _never_write_bytecode_into_fixtures():
    """Importing a scaffolded or fixture module must not litter the tree."""
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    yield
    sys.dont_write_bytecode = previous
