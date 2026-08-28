"""Allow `python -m aion_minimizer`."""

from __future__ import annotations

import sys

from aion_minimizer.cli import main

if __name__ == "__main__":
    sys.exit(main())
