"""Pytest configuration for the aion_minimizer test suite.

Run from the repository root with::

    make aion-minimizer-test    # or: python -m pytest tools/aion_minimizer/tests
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

GATE_LIBRARY = REPO_ROOT / "tech" / "spice" / "sg13g2_stdcell.spice"


@pytest.fixture(scope="session")
def gate_library_path() -> Path:
    if not GATE_LIBRARY.exists():  # pragma: no cover - depends on the checkout
        pytest.skip(f"gate library not found at {GATE_LIBRARY}")
    return GATE_LIBRARY


@pytest.fixture(scope="session")
def gate_subckts(gate_library_path):
    from aion_minimizer.spice_parser import parse_spice_file

    return parse_spice_file(gate_library_path)


@pytest.fixture(scope="session")
def gate_functions(gate_subckts):
    from aion_minimizer.gate_extractor import extract_gate_functions

    return extract_gate_functions(gate_subckts)


@pytest.fixture
def synth(gate_functions, gate_subckts):
    """Synthesize a top-level netlist given as SPICE text."""
    from aion_minimizer.spice_parser import parse_spice
    from aion_minimizer.synthesis import synthesize

    def run(text: str, **kwargs):
        subckts = parse_spice(text)
        top = next(s for s in subckts.values() if not s.is_gate_definition)
        return synthesize(top, gate_functions, gate_subckts, **kwargs)

    return run
