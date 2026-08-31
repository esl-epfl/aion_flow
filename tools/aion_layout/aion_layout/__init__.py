# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Description:               AION layout framework package
# ================================================================

"""Generic, technology-aware standard-cell layout framework."""

__version__ = "0.1.0"

from .tech import Layer, Tech, sg13g2_tech

__all__ = ["Layer", "Tech", "sg13g2_tech"]
