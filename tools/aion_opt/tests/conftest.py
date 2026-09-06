"""Pytest configuration for the aion_opt test suite.

Run from the repository root with::

    make aion-opt-test          # or: python -m pytest tools/aion_opt/tests
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))
