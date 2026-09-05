# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Shared fixtures for the golden regression suite
# ================================================================

"""Fixtures shared by the golden suite.

Every path here points at ``tests/fixtures``, which holds the *real* artifacts
captured from the run that never converged.  They are read-only: a test that
writes into them destroys the only evidence the suite is built on, so anything
generated goes to ``tmp_path``.

Nothing in this suite needs Docker or a model call.  The container-only tools
(``sak-drc.sh`` / ``sak-lvs.sh``) are never invoked; only their output is read.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import List, Sequence

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"
ITER0 = FIXTURES / "iteration_0"
CELL = "AION_inv_nand2_nor2_1"

# The suite imports ``aion_layout`` without an editable install, exactly as
# report_verification.py and evidence.py do.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_script(path: Path, name: str) -> ModuleType:
    """Import a ``scripts/*.py`` entry point as a module.

    ``scripts/`` is not a package, so the helper CLIs can only be imported by
    file location.  Importing them (rather than shelling out) is what lets the
    unit tests reach the parsing functions directly.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"cannot import {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def cell_name() -> str:
    return CELL


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture(scope="session")
def iter0_dir() -> Path:
    """The captured iteration_0 artifact tree (drc/, lvs/, report.txt, the .py)."""
    assert ITER0.is_dir(), f"fixture tree missing: {ITER0}"
    return ITER0


@pytest.fixture(scope="session")
def netlist_path() -> Path:
    path = FIXTURES / f"{CELL}_minimized.spice"
    assert path.is_file(), f"fixture netlist missing: {path}"
    return path


@pytest.fixture(scope="session")
def magic_rpt() -> Path:
    path = ITER0 / "drc" / f"{CELL}.magic.drc" / f"{CELL}.magic.drc.rpt"
    assert path.is_file(), f"fixture Magic report missing: {path}"
    return path


@pytest.fixture(scope="session")
def klayout_dir() -> Path:
    path = ITER0 / "drc" / f"{CELL}.klayout.drc"
    assert path.is_dir(), f"fixture KLayout database dir missing: {path}"
    return path


@pytest.fixture(scope="session")
def netgen_out() -> Path:
    path = ITER0 / "lvs" / f"{CELL}.magic.lvs" / f"{CELL}.lvs.out"
    assert path.is_file(), f"fixture Netgen report missing: {path}"
    return path


@pytest.fixture(scope="session")
def broken_report_txt() -> Path:
    """The 918-byte, verdict-free report.txt the loop used to be fed."""
    path = ITER0 / "report.txt"
    assert path.is_file(), f"fixture report.txt missing: {path}"
    return path


@pytest.fixture
def iteration_tree(tmp_path):
    """Return a factory that copies the read-only fixture tree into ``tmp_path``.

    The regression tests plant, corrupt and truncate artifacts; every one of
    them needs a writable copy, because a test that mutates ``tests/fixtures``
    destroys the only captured evidence the suite grades against.
    """

    def build(name: str = "iteration_0") -> Path:
        dest = tmp_path / name
        shutil.copytree(ITER0, dest)
        return dest

    return build


@pytest.fixture(scope="session")
def iter0_module() -> Path:
    """The iteration_0 generator that self-shorts I1 onto O0."""
    path = ITER0 / f"{CELL}.py"
    assert path.is_file(), f"fixture generator missing: {path}"
    return path


# ---------------------------------------------------------------------------
# Modules under test
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def evidence():
    """``scripts/evidence.py`` imported as a module."""
    return load_script(REPO_ROOT / "scripts" / "evidence.py", "aion_evidence_under_test")


@pytest.fixture(scope="session")
def report_verification():
    """``scripts/report_verification.py`` imported as a module."""
    return load_script(
        REPO_ROOT / "scripts" / "report_verification.py",
        "aion_report_verification_under_test",
    )


# ---------------------------------------------------------------------------
# Process helpers
# ---------------------------------------------------------------------------

def run(cmd: Sequence[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command from the repository root, capturing text output.

    ``PYTHONDONTWRITEBYTECODE`` is forced on: several code paths import the
    generator that lives under ``tests/fixtures``, and a stray ``__pycache__``
    would be the suite writing into its own read-only evidence.
    """
    env = dict(kwargs.pop("env", None) or os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    kwargs["env"] = env
    kwargs.setdefault("cwd", REPO_ROOT)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("timeout", 300)
    return subprocess.run(list(cmd), check=False, **kwargs)


@pytest.fixture(autouse=True, scope="session")
def _keep_fixtures_read_only():
    """Never let an import of a fixture module drop a ``__pycache__`` beside it."""
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    yield
    sys.dont_write_bytecode = previous


@pytest.fixture(scope="session")
def synthetic_netlist():
    """Build an ``n``-input CMOS gate netlist: parallel PMOS, series NMOS.

    Used to drive the scaffold generator at every input count without hand
    writing six SPICE files.  The shape matters only in that ``O0`` is a drain
    on both sides, which is how ``Subckt.output_net`` finds the output.
    """

    def build(n: int, name: str = "SYNTH") -> str:
        inputs = [f"I{i}" for i in range(n)]
        lines = [f".subckt {name} {' '.join(inputs)} O0 VDD VSS"]
        for i, net in enumerate(inputs):
            lines.append(
                f"XP{i} O0 {net} VDD VDD sg13_lv_pmos w=1.0u l=0.13u ng=1 m=1"
            )
        upper = "O0"
        for i, net in enumerate(inputs):
            lower = "VSS" if i == n - 1 else f"n{i}"
            lines.append(
                f"XN{i} {upper} {net} {lower} VSS sg13_lv_nmos w=1.0u l=0.13u ng=1 m=1"
            )
            upper = lower
        lines.append(".ends")
        return "\n".join(lines) + "\n"

    return build


@pytest.fixture(scope="session")
def metal1_net_rects():
    """Attribute every Metal1 rectangle of a ``Cell`` to a net via its ports.

    Returns ``(named, unnamed)``: ``named`` is a list of ``(net, Rect)``,
    ``unnamed`` the rectangles no Port covers.  A rectangle nothing claims is
    reported rather than silently dropped, otherwise a short-detection test
    could pass by detecting nothing at all.
    """

    def attribute(cell, tech) -> tuple:
        from aion_layout.shapes import RectShape

        metal1 = tech["Metal1"]
        ports = [p for p in cell.ports.values() if p.layer == metal1]
        named: List[tuple] = []
        unnamed: List[object] = []
        for shape in cell.shapes.get(metal1, []):
            if not isinstance(shape, RectShape):
                continue  # TextShape carries no area
            rect = shape.rect
            exact = [p for p in ports if p.rect == rect]
            covering = [p for p in ports if p.rect.contains(rect)]
            if exact:
                named.append((exact[0].net, rect))
            elif covering:
                named.append((min(covering, key=lambda p: p.rect.area).net, rect))
            else:
                unnamed.append(rect)
        return named, unnamed

    return attribute
