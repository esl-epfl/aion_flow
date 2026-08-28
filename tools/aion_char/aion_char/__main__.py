"""Allow `python -m aion_char`."""

from __future__ import annotations

import sys

from aion_char.cli import main

if __name__ == "__main__":
    sys.exit(main())
