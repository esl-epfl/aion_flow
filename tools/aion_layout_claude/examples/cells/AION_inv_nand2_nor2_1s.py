#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               INV + NOR3 with a x2 series pull-up (IHP SG13G2)
# ================================================================

"""Generator for ``AION_inv_nand2_nor2_1s`` -- the resized AION cell.

Same logic as ``AION_inv_nand2_nor2_1`` (``O0 = I1 & !I0 & !I2``) and the same
netlist topology, but the three devices of the pull-up stack are twice as wide,
folded into two fingers each.  ``make resize`` chose the x2 multiplier and this
generator implements it; ``AION_inv_nand2_nor2_1s.spice`` is its netlist.

Why:  the unsized cell is 45% smaller than the abutted PDK row but 29% slower,
and the whole gap is the 3-high series pull-up -- measured, by characterizing
the same layout with and without parasitics, which differed by 1.6%.  Widening
only the stacked devices costs 3 poly columns and buys 20%.

Netlist (AION_inv_nand2_nor2_1s.spice):

    XP0 I1_bar  I1     VDD     VDD  pmos w=1.12u ng=1
    XN0 I1_bar  I1     VSS     VSS  nmos w=740n  ng=1
    XP1 net_p_0 I1_bar VDD     VDD  pmos w=2.24u ng=2   \\
    XP2 net_p_1 I0     net_p_0 VDD  pmos w=2.24u ng=2    > the series pull-up
    XP3 O0      I2     net_p_1 VDD  pmos w=2.24u ng=2   /
    XN1 O0      I0     VSS     VSS  nmos w=740n  ng=1
    XN2 O0      I2     VSS     VSS  nmos w=740n  ng=1
    XN3 O0      I1_bar VSS     VSS  nmos w=740n  ng=1

Floorplan -- 7 gates, 8 pmos nodes, 9 sites
-------------------------------------------

A folded series chain lays out as a *palindrome* around its output.  Reading
the pmos row left to right, each stacked device contributes one finger on the
way in and one on the way out, so both fingers of every device sit between the
same pair of nets and the two halves are one 2-finger device each:

    node   I1_bar   VDD    net_p_0  net_p_1   O0    net_p_1  net_p_0   VDD
    gate        I1     I1_bar     I0      I2     I2      I0      I1_bar
    node   I1_bar   VSS      O0      VSS     O0      -        -        -
             n0      n1      n2      n3      n4

That is 7 gates and 8 pmos nodes -- 7 x 510 nm of contacted pitch plus 190 nm
of diffusion overhang each side, which rounds to **9 sites (4320 nm)** against
11 for the abutted row.  The nmos row needs only 4 gates (I1, I1_bar, I0, I2),
so it uses the leftmost four columns and stops after n4; columns 4-6 carry
pmos-only poly, which is why their stripes start above the nmos diffusion.

Routing -- Metal1, plus two Metal2 straps
-----------------------------------------

The palindrome duplicates every internal node, so ``net_p_0`` (p2, p6) and
``net_p_1`` (p3, p5) each need a strap, and the two outer gate pairs need one
too.  Metal1 alone cannot do it: a vertical Metal1 riser cannot pass between
two contacted pmos nodes (510 nm pitch leaves 70 nm on each side of a 160 nm
wire, against the 180 nm ``M1.b``), so a gate in the middle of the row has no
way up to a strap above the diffusion.

What each net does, and why:

``net_p_0`` / ``net_p_1``   Metal1 straps stacked above the pmos contacts, at
                            3090 and 2750 nm.  Both endpoints are *nodes*, so
                            their risers start at the node's own contact and
                            never have to pass one.

``O0``                      Metal1, crossing the rows at **x = 2670** -- column
                            4, whose gate is tied to column 3 in poly and so
                            needs no Metal1 pad of its own.  That gap in the
                            pad row is the only place a riser fits, and it is
                            what keeps the output off Metal2, where it would
                            have blocked both straps below.

``I1_bar`` / ``I0``         Metal2, on two horizontal tracks over the pad row.
                            Their endpoints are gate pads, which Metal1 cannot
                            reach upward -- but Metal2 drops straight onto the
                            pads through a Via1, and the two tracks clear each
                            other by 240 nm.  ``I1_bar`` also collects the
                            inverter's own drain (p0) and the nmos node n0 with
                            two more Via1 on the same strap.

``I2``                      Nothing: columns 3 and 4 are adjacent, so their two
                            gates are joined by a poly bar and share one pad.

The vertical stack (rails, taps, implants, well, contact rows) is the shipped
library's, so it is known DRC-good; only the x coordinates are this cell's.
"""

from __future__ import annotations

import sys

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import RectShape, TextShape
from aion_layout.tech import Tech, sg13g2_tech

CELL_NAME = "AION_inv_nand2_nor2_1s"

# --------------------------------------------------------------- floorplan --
SITE_W = 480
CELL_W = 4320                     # 9 sites
CELL_H = 3780

PITCH = 510                       # contacted poly pitch: 110 + 160 + 110 + 130
X0 = 375                          # centre of the leftmost diffusion node
XP = [X0 + k * PITCH for k in range(8)]      # pmos nodes p0..p7
XG = [x + PITCH // 2 for x in XP[:-1]]       # gate columns g0..g6
XN = XP[:5]                                  # nmos nodes n0..n4 reuse p0..p4

ACT_MARGIN = 190                  # diffusion overhang past the outer node
ACT_L = XP[0] - ACT_MARGIN        # 185
ACT_R = XP[-1] + ACT_MARGIN       # 4135
NACT_R = XN[-1] + ACT_MARGIN      # 2605 -- the nmos row stops after n4

CONT_HW = 80                      # Cnt.a: contacts are exactly 160 nm
POLY_HW = 65                      # Gat.a: 130 nm gates
PAD_HW = 150                      # poly landing pad half width (Cnt.d = 70)
M1_PAD_HW = 140
STUB_HW = 105                     # half width of a Metal1 stub over a node
RISER_HW = 80

# -------------------------------------------------------------- y skeleton --
VSS_M1 = (-220, 220)
VDD_M1 = (CELL_H - 220, CELL_H + 220)
PTAP_ACT = (-150, 150)
NTAP_ACT = (3630, 3930)
PTAP_CONT = (-80, 80)
NTAP_CONT = (3700, 3860)
PSD_BOT = (-180, 180)
PSD_TOP = (1760, 3600)
NWELL_Y = (1750, 4170)

NACT = (600, 1340)                # nmos diffusion, W = 740  (netlist exact)
PACT = (2075, 3195)               # pmos diffusion, W = 1120 (netlist exact)

POLY_FULL = (410, 3375)           # a gate that crosses both rows
POLY_PMOS = (1410, 3375)          # a pmos-only finger: 70 nm clear of NACT top
POLY_PAD_Y = (1420, 1720)
POLY_CONT_Y = (1490, 1650)        # Cnt.e: 150 nm clear of the nmos diffusion

NCONT_Y = [(680, 840), (1020, 1180)]
PCONT_Y = [(2360, 2520), (2700, 2860)]

M1_PAD_Y = (1430, 1810)           # 280 x 380 nm = 0.106 um^2, clears M1.d;
                                  # 180 nm above the nmos row, per M1.b
O0_CH_Y = (1090, 1250)            # the output's channel in the nmos row
NP1_Y = (2750, 2910)              # net_p_1 strap, on the upper pmos contacts
NP0_Y = (3090, 3250)              # net_p_0 strap, above it

# Metal2 tracks.  Two horizontals over the pad row; the Via1 drop straight onto
# the Metal1 pads, which is the whole reason these two nets are on Metal2.
I0_M2_Y = (1435, 1745)
IBAR_M2_Y = (1970, 2170)
VIA_HW = 95                       # V1.a: Via1 is exactly 190 nm, min and max
M2_HW = 100                       # M2.a: 200 nm tracks

# Which net sits on each pmos node and each gate column.
PNET = ["I1_bar", "VDD", "net_p_0", "net_p_1", "O0", "net_p_1", "net_p_0", "VDD"]
GNET = ["I1", "I1_bar", "I0", "I2", "I2", "I0", "I1_bar"]
NNET = ["I1_bar", "VSS", "O0", "VSS", "O0"]
NGATE = [0, 1, 2, 3]              # gate columns that also cross the nmos row

TAP_CONT_X = [150 + 430 * k for k in range(10)]


def _r(cell: Cell, layer: str, left: float, bottom: float, right: float, top: float,
       tech: Tech) -> None:
    """Add one rectangle, so the body below reads as coordinates and not calls."""
    cell.add_shape(RectShape(tech[layer], Rect.from_lbrt(left, bottom, right, top)))


def _via1(cell: Cell, x: float, y_bot: float, tech: Tech) -> None:
    """Drop a Via1 at ``x`` with its bottom at ``y_bot``.  190 nm, exactly."""
    _r(cell, "Via1", x - VIA_HW, y_bot, x + VIA_HW, y_bot + 2 * VIA_HW, tech)


def generate(name: str, tech: Tech) -> Cell:
    """Build the resized cell."""
    cell = Cell(name, tech)
    cell.set_boundary(Rect.from_lbrt(0, 0, CELL_W, CELL_H))
    _r(cell, "prBoundary", 0, 0, CELL_W, CELL_H, tech)

    # ---- wells and implants -------------------------------------------------
    # Both overhang the boundary on purpose: an abutted neighbour shares them.
    _r(cell, "NWell", -240, NWELL_Y[0], CELL_W + 240, NWELL_Y[1], tech)
    _r(cell, "PSD", -70, PSD_TOP[0], CELL_W + 70, PSD_TOP[1], tech)
    _r(cell, "PSD", -70, PSD_BOT[0], CELL_W + 70, PSD_BOT[1], tech)

    # ---- diffusion ----------------------------------------------------------
    _r(cell, "Activ", ACT_L, NACT[0], NACT_R, NACT[1], tech)
    _r(cell, "Activ", ACT_L, PACT[0], ACT_R, PACT[1], tech)
    _r(cell, "Activ", 0, PTAP_ACT[0], CELL_W, PTAP_ACT[1], tech)
    _r(cell, "Activ", 0, NTAP_ACT[0], CELL_W, NTAP_ACT[1], tech)

    # ---- gates --------------------------------------------------------------
    for k, x in enumerate(XG):
        span = POLY_FULL if k in NGATE else POLY_PMOS
        _r(cell, "GatPoly", x - POLY_HW, span[0], x + POLY_HW, span[1], tech)
        # Every column gets a landing pad; columns 3 and 4 share one, drawn as
        # a bar below, so that the I2 pair needs no metal strap at all.
        if k != 4:
            _r(cell, "GatPoly", x - PAD_HW, POLY_PAD_Y[0], x + PAD_HW,
               POLY_PAD_Y[1], tech)
    # The I2 poly bar: columns 3 and 4 are adjacent, so one shape joins them.
    _r(cell, "GatPoly", XG[3] - PAD_HW, POLY_PAD_Y[0], XG[4] + PAD_HW,
       POLY_PAD_Y[1], tech)

    # ---- gate contacts and Metal1 pads --------------------------------------
    # Column 4 has neither: it is tied to column 3 in poly.
    for k, x in enumerate(XG):
        if k == 4:
            continue
        _r(cell, "Cont", x - CONT_HW, POLY_CONT_Y[0], x + CONT_HW,
           POLY_CONT_Y[1], tech)
        _r(cell, "Metal1", x - M1_PAD_HW, M1_PAD_Y[0], x + M1_PAD_HW,
           M1_PAD_Y[1], tech)

    # ---- pmos node contacts and stubs ---------------------------------------
    for k, x in enumerate(XP):
        net = PNET[k]
        if net == "O0":
            rows, stub = PCONT_Y[:1], (2260, 2570)
        elif net == "net_p_1":
            rows, stub = PCONT_Y[1:], (2650, 2910)
        elif net == "I1_bar":
            rows, stub = PCONT_Y[:1], (2310, 2810)
        elif net == "VDD":
            rows, stub = PCONT_Y, (2310, VDD_M1[0])
        else:                                     # net_p_0
            rows, stub = PCONT_Y, (2310, NP0_Y[1])
        for bot, top in rows:
            _r(cell, "Cont", x - CONT_HW, bot, x + CONT_HW, top, tech)
        half = 110 if net == "I1_bar" else STUB_HW
        _r(cell, "Metal1", x - half, stub[0], x + half, stub[1], tech)

    # ---- the two internal-node straps ---------------------------------------
    _r(cell, "Metal1", XP[3] - STUB_HW, NP1_Y[0], XP[5] + STUB_HW, NP1_Y[1], tech)
    _r(cell, "Metal1", XP[2] - STUB_HW, NP0_Y[0], XP[6] + STUB_HW, NP0_Y[1], tech)

    # ---- nmos node contacts and stubs ---------------------------------------
    for k, x in enumerate(XN):
        net = NNET[k]
        if net == "VSS":
            rows, stub = NCONT_Y[:1], (VSS_M1[1], 890)
        elif net == "O0":
            rows, stub = NCONT_Y[1:], (970, O0_CH_Y[1])
        else:                                     # I1_bar, at n0
            rows, stub = NCONT_Y, (400, 1250)
        for bot, top in rows:
            _r(cell, "Cont", x - CONT_HW, bot, x + CONT_HW, top, tech)
        _r(cell, "Metal1", x - STUB_HW, stub[0], x + STUB_HW, stub[1], tech)

    # ---- the output --------------------------------------------------------
    # Its channel gathers n2 and n4 and runs out to column 4, the one gate
    # column with no Metal1 pad, where the riser can legally cross the pad row.
    _r(cell, "Metal1", XN[2] - STUB_HW, O0_CH_Y[0], XG[4] + RISER_HW,
       O0_CH_Y[1], tech)
    _r(cell, "Metal1", XG[4] - RISER_HW, O0_CH_Y[1], XG[4] + RISER_HW, 2420, tech)
    _r(cell, "Metal1", XP[4] - STUB_HW, 2260, XG[4] + RISER_HW, 2420, tech)

    # ---- Metal2: the two gate straps ---------------------------------------
    _r(cell, "Metal2", XG[2] - VIA_HW - 55, I0_M2_Y[0], XG[5] + VIA_HW + 55,
       I0_M2_Y[1], tech)
    for x in (XG[2], XG[5]):
        _via1(cell, x, 1495, tech)

    _r(cell, "Metal2", XP[0] - M2_HW, IBAR_M2_Y[0], XG[6] + M2_HW,
       IBAR_M2_Y[1], tech)
    # Down to the nmos node and up to the inverter drain, on one Metal2 spine.
    _r(cell, "Metal2", XP[0] - M2_HW, 350, XP[0] + M2_HW, 2810, tech)
    _via1(cell, XP[0], 450, tech)                 # onto n0
    _via1(cell, XP[0], 2570, tech)                # onto p0
    for x in (XG[1], XG[6]):
        # 145 nm half width, not 100: the Via1 needs 50 nm of Metal2 on both
        # sides of one axis, and this spur is too short to give it in y.
        _r(cell, "Metal2", x - VIA_HW - 50, 1400, x + VIA_HW + 50,
           IBAR_M2_Y[1], tech)
        _via1(cell, x, 1495, tech)

    # ---- power rails and taps ----------------------------------------------
    _r(cell, "Metal1", 0, VSS_M1[0], CELL_W, VSS_M1[1], tech)
    _r(cell, "Metal1", 0, VDD_M1[0], CELL_W, VDD_M1[1], tech)
    for x in TAP_CONT_X:
        _r(cell, "Cont", x - CONT_HW, PTAP_CONT[0], x + CONT_HW, PTAP_CONT[1], tech)
        _r(cell, "Cont", x - CONT_HW, NTAP_CONT[0], x + CONT_HW, NTAP_CONT[1], tech)

    # ---- labels and ports ---------------------------------------------------
    m1 = tech["Metal1"]
    pins = [
        ("I1", XG[0], 1590, "INPUT"),
        ("I0", XG[2], 1590, "INPUT"),
        ("I2", XG[3], 1590, "INPUT"),
        ("O0", 2000, 1170, "OUTPUT"),
        ("VDD", 2160, CELL_H, "POWER"),
        ("VSS", 2160, 0, "GROUND"),
    ]
    for pin, x, y, direction in pins:
        cell.add_shape(TextShape(m1, pin, Point(x, y), purpose="label"))
        cell.add_port(Port(pin, pin, m1, Rect.from_lbrt(x, y, x, y),
                           direction=direction))
    return cell


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else f"{CELL_NAME}.gds"
    generate(CELL_NAME, sg13g2_tech).write_gds(out)
    print(f"wrote {out}")
