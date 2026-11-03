#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Via1/Metal2 primitive DRC regression cell
# ================================================================

"""DRC probe for the Via1 and Metal2 primitives in ``building_blocks``.

This cell exists to be run through DRC, not to compute anything.  Every
Via1/Metal2 number the layout loop depends on -- the exact cut size, the two
enclosure tiers, the Metal2 minimum area, the Via1 array pitch -- is a number
that looks right in a rule table and is only *known* to be right once both
engines have signed off on real geometry built from it.  Drawing that geometry
by hand each time the loop hits a Via1 costs several DRC rounds; drawing it
once, here, costs one.

So each structure is the *minimum* legal case, never a comfortable one:

  A  a Metal1 strip only 210 nm tall -- the thinnest Metal1 that can carry a
     Via1 at all (190 nm cut + 10 nm of V1.c on each side) -- with a Via1 up
     to a Metal2 stub of exactly 200 x 720 nm.  Both landings sit on their
     rules to the nanometre: 10 nm of Metal1 above and below the cut, 5 nm of
     Metal2 left and right, and 0.144 um2 of Metal2 exactly.  If the endcap
     rules were "50 nm on all four sides" this structure would be illegal
     twice over; if M2.d were checked as ``<=`` rather than ``<`` the stub
     would fail.  It passing is the evidence.
  B  a 2 x 2 Via1 array under a shared Metal1/Metal2 pad, at the V1.b pitch
     (190 + 220 nm) with the 50 nm endcap margin above and below.
  C  a free-standing minimum-area Metal2 rectangle, 200 x 720 nm, sized by
     ``m2_min_length_for_area``.
  D  a Metal2 pin, drawing rectangle plus 10/2 pin rectangle plus label.
  E  a Via1 with *both* landings left to ``via1_landing_rect`` -- the default
     path, and so the one every future caller gets: a 210 x 430 nm Metal1 stub
     (0.0903 um2, 3 nm of slack over M1.d) and a 200 x 720 nm Metal2 stub.
     A and B both hand in their own metal, so without E the sizes the module
     computes for itself would never be drawn and never be checked.
  F  a Via1 array with ``rows``/``cols`` left to the auto-fit, which is a
     different arithmetic path from B's explicit 2 x 2.
  G  a 4 x 4 array, the only shape here that trips V1.b1: more than 3 rows
     *and* more than 3 columns, so the column pitch has to open from 190 + 220
     to 190 + 290 nm while the row pitch stays at 190 + 220.  Neither engine
     available here implements V1.b1 (see below), so G is not proof that the
     wider pitch is *required* -- it is proof that drawing it breaks nothing
     else, and it is the shape that fails first if the widening is ever lost.

The frame around them -- rails, taps, well, implant -- is lifted verbatim from
``AION_inv_nand2_nor2_1``, which is DRC and LVS clean, so a violation here is a
violation in the primitives and not in the frame.  There are no transistors,
so this cell has no netlist and must not be handed to LVS.

Which engine proves what, because it is not the obvious answer.  The shipped
KLayout runset (``sak-drc.sh -k``, the modular ``ihp-sg13g2.drc``) runs V1.a,
V1.b, V1.c, M1.a/b, M2.a/b and the whole Offgrid table -- but NOT M1.c1, M1.d,
M2.c, M2.c1, M2.d or V1.c1.  Those live only in ``sg13g2_maximal.drc``, which
that runset never invokes.  Magic does check them, so ``verification.run_drc``
covers everything here between its two engines; that was confirmed by running
a deliberately illegal twin of this cell, on which Magic reported M1.d, M2.d,
V1.c1 and M2.c1 while KLayout reported only V1.a.  For belt and braces the
maximal deck was also run directly::

    klayout -b -zz -r context/drc/rule_decks/sg13g2_maximal.drc \
        -rd input=build/_m2_probe.gds -rd topcell=_m2_probe \
        -rd report=<abs>.lyrdb -rd log=<abs>.log -rd thr=4 -rd run_mode=deep

(``report`` and ``log`` must be absolute container paths; the deck prefixes a
relative one and then fails only at cleanup, with the exit status still 0.)
It reported ``M1.c 0, M1.c1 0, M1.d 0, M2.c 0, M2.c1 0, M2.d 0, V1.b1 0,
V1.c1 0`` and 0 for the whole 292-rule maximum set.  The same deck fires on
wrong geometry: 5 errors (M1.d, M2.c1, M2.d) on the illegal twin, and exactly
22 V1.b1 errors on a 4 x 4 array whose columns keep the narrow 220 nm pitch --
which is what makes structure G below a real regression and not decoration.
If this cell ever stops being clean, the rule numbers in ``building_blocks``
and ``tech`` are what moved.
"""

from __future__ import annotations

import sys

from aion_layout.building_blocks import (
    draw_m2_pin,
    draw_m2_wire,
    draw_via1,
    draw_via1_array,
    m2_min_length_for_area,
)
from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import RectShape, TextShape
from aion_layout.tech import Layer, Tech, sg13g2_tech

CELL_NAME = "_m2_probe"

# ------------------------------------------------------------- floorplan ---
SITE_W = 480
CELL_W = 16 * SITE_W             # 7680 nm
CELL_H = 3780

# Frame y skeleton, copied from AION_inv_nand2_nor2_1.
VSS_M1 = (-220, 220)
VDD_M1 = (CELL_H - 220, CELL_H + 220)
PTAP_ACT = (-150, 150)
NTAP_ACT = (3630, 3930)
PTAP_CONT = (-80, 80)
NTAP_CONT = (3700, 3860)
PSD_BOT = (-180, 180)
NWELL_Y = (1750, 4170)
CONT_HW = 80
TAP_CONT_PITCH = 430
TAP_CONT_X0 = 150

# ------------------------------------------------------- test structures ---
# A: Metal1 strip + one Via1 + the default Metal2 landing.
A_M1 = Rect.from_lbrt(300, 1600, 1100, 1810)     # 800 x 210, the thinnest legal
A_VIA = Point(500, 1705)                         # 200 nm in from the strip end

# B: 2 x 2 Via1 array under a shared pad.
B_PAD = Rect.from_lbrt(1500, 1400, 2200, 2100)   # 700 x 700

# C: free-standing minimum-area Metal2.
C_W = 200
C_X = 2600
C_Y = 1400

# D: Metal2 pin.
D_PIN = Rect.from_lbrt(3100, 1500, 3380, 2060)   # 280 x 560, the PDK's own shape

# E: a Via1 whose two landings are both the module's own defaults.
E_VIA = Point(3800, 1705)

# F: a Via1 array sized by the auto-fit rather than by explicit rows/cols.
F_PAD = Rect.from_lbrt(4300, 1400, 5000, 2100)   # 700 x 700 -> 2 x 2

# G: the V1.b1 case.  1700 x 1550 is the smallest pad on the 5 nm grid that
# holds 4 x 4 cuts at the widened 290 nm column pitch (4*190 + 3*290 = 1630,
# plus 2 x 10 nm of V1.c) and the 220 nm row pitch (4*190 + 3*220 = 1420, plus
# 2 x 50 nm of endcap), with the slack spent on margin rather than on pitch.
G_PAD = Rect.from_lbrt(5300, 1100, 7000, 2650)


def generate(cell_name: str = CELL_NAME, tech: Tech = sg13g2_tech) -> Cell:
    """Build the probe.  Signature required by scripts/generate_cell.py."""
    cell = Cell(cell_name, tech)

    activ = tech["Activ"]
    cont = tech["Cont"]
    metal1 = tech["Metal1"]
    psd = tech["PSD"]
    nwell = tech["NWell"]
    prbnd = tech["prBoundary"]
    metal1_pin = Layer(name=f"{metal1.name}.pin",
                       gds_layer=metal1.gds_layer,
                       gds_datatype=metal1.pin_datatype)

    def box(layer: Layer, x1, y1, x2, y2) -> None:
        cell.add_shape(RectShape(layer, Rect.from_lbrt(x1, y1, x2, y2)))

    def rail_pin(name: str, y0, y1, direction: str) -> None:
        rect = Rect.from_lbrt(0, y0, CELL_W, y1)
        cell.add_shape(RectShape(metal1_pin, rect))
        cell.add_shape(TextShape(metal1, name, rect.center, purpose="label"))
        cell.add_port(Port(name=name, net=name, layer=metal1, rect=rect,
                           direction=direction))

    # ------------------------------------------- boundary, well, implants --
    cell.set_boundary(Rect.from_lbrt(0, 0, CELL_W, CELL_H))
    box(prbnd, 0, 0, CELL_W, CELL_H)
    box(nwell, -240, NWELL_Y[0], CELL_W + 240, NWELL_Y[1])
    box(psd, -70, PSD_BOT[0], CELL_W + 70, PSD_BOT[1])

    # ------------------------------------------------- rails, taps, wells --
    box(activ, 0, PTAP_ACT[0], CELL_W, PTAP_ACT[1])
    box(activ, 0, NTAP_ACT[0], CELL_W, NTAP_ACT[1])
    box(metal1, 0, VSS_M1[0], CELL_W, VSS_M1[1])
    box(metal1, 0, VDD_M1[0], CELL_W, VDD_M1[1])
    xc = TAP_CONT_X0
    while xc + CONT_HW <= CELL_W - CONT_HW:
        for y0, y1 in (PTAP_CONT, NTAP_CONT):
            box(cont, xc - CONT_HW, y0, xc + CONT_HW, y1)
        xc += TAP_CONT_PITCH
    rail_pin("VSS", VSS_M1[0], VSS_M1[1], "GROUND")
    rail_pin("VDD", VDD_M1[0], VDD_M1[1], "POWER")

    # ------------------------------------------------- A: strip + one via --
    cell.merge_subcell(draw_via1(A_VIA, tech, metal1_rect=A_M1))

    # ------------------------------------------------------ B: via array ---
    cell.merge_subcell(draw_via1_array(B_PAD, tech, rows=2, cols=2))

    # --------------------------------------------- C: minimum-area Metal2 --
    c_len = m2_min_length_for_area(C_W, tech)
    cell.merge_subcell(
        draw_m2_wire(Rect.from_lbrt(C_X, C_Y, C_X + C_W, C_Y + c_len), tech)
    )

    # ---------------------------------------------------------- D: pin -----
    cell.merge_subcell(draw_m2_pin("M2PIN", D_PIN, tech, direction="INPUT"))

    # ------------------------------------------- E: both landings default --
    cell.merge_subcell(draw_via1(E_VIA, tech))

    # ------------------------------------------------- F: auto-fit array ---
    cell.merge_subcell(draw_via1_array(F_PAD, tech))

    # ---------------------------------------------------- G: V1.b1 array ---
    cell.merge_subcell(draw_via1_array(G_PAD, tech, rows=4, cols=4))

    return cell


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else f"{CELL_NAME}.gds"
    generate().write_gds(out)
    assert CELL_W % SITE_W == 0
    print(f"wrote {out}  ({CELL_W} x {CELL_H} nm = {CELL_W // SITE_W} sites)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
