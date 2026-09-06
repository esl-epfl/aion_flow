# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               python3 -m aion_layout
# ================================================================

"""Module entry point.  All of the behaviour lives in :mod:`aion_layout.cli`."""

import sys

from .cli import main

sys.exit(main())
