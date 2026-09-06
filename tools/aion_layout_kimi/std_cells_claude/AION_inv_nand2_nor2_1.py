#!/usr/bin/env python3
# ================================================================
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Description:               INV + NOR3 standard-cell generator (IHP SG13G2)
# ================================================================

"""Generator for the AION_inv_nand2_nor2_1 standard cell.

Exposes ``generate(cell_name, tech) -> Cell`` so it can be driven by
``scripts/generate_cell.py`` (and therefore by ``make gds/drc/lvs/verify``).
Running the file directly writes the GDS without going through the Makefile.

The vertical stack (rail/tap/implant/well y coordinates, contact rows, poly
extension) is the shipped sg13g2 library's, so it is known DRC-good.  Metal1
is the only routing layer -- no Metal2, no Via1.

Netlist (AION_inv_nand2_nor2_1_minimized.spice) -- an inverter on I1 feeding
a NOR3, every device a single finger at the library's own widths:

    XP0 I1_bar  I1     VDD     VDD  pmos w=1.12u
    XN0 I1_bar  I1     VSS     VSS  nmos w=740n
    XP1 net_p_0 I1_bar VDD     VDD  pmos w=1.12u    series pull-up
    XP2 net_p_1 I0     net_p_0 VDD  pmos w=1.12u
    XP3 O0      I2     net_p_1 VDD  pmos w=1.12u
    XN1 O0      I0     VSS     VSS  nmos w=740n     parallel pull-down
    XN2 O0      I2     VSS     VSS  nmos w=740n
    XN3 O0      I1_bar VSS     VSS  nmos w=740n

w = 740 nm / 1120 nm are exactly the diffusion heights this cell height
allows, so both rows are a single unbroken diffusion strip and the extracted
widths match the netlist exactly -- no folding, no quantisation error.

Area.  The gate order I1, I1_bar, I0, I2 chains all four pmos devices into one
diffusion and all four nmos devices into another:

    pmos nodes   I1_bar | VDD | net_p_0 | net_p_1 | O0
    gates              I1     I1_bar    I0        I2
    nmos nodes   I1_bar | VSS |   O0    |   VSS   | O0

net_p_0 and net_p_1 are then shared diffusion and need no wire and no contact
at all.  Four gates need five diffusion nodes, every nmos node needs a
contact, and Cnt.f (contact 110 nm from poly) fixes the contacted pitch at
510 nm -- so 4 x 510 nm of nodes plus the diffusion overhang is the floor,
and the cell lands on 6 sites (2880 nm).

Routing.  Two nets have to cross the row gap: I1_bar (XP0/XN0 drains up to the
XP1/XN3 gate) and O0 (XP3 drain down to the XN1/XN2/XN3 drains).  At a 510 nm
pitch a 160 nm strip cannot pass a node column that has gate pin pads on both
sides, so both crossings are placed at the *outer* nodes and their risers step
outboard, past the end of the diffusion, where nothing is in the way:

           ___________________________ VDD rail ______________
   pmos     n0        n1        n2        n3        n4
   riser   |                                        |
   upper   +----------------[I1_bar]                |    y 1970..2130
   pads     [I1]      [I1_bar]  [I0]     [I2]       |    y 1450..1790
   lower              [O0]-----------------[O0]-----+    y 1090..1250
   nmos     n0        n1        n2        n3        n4
           ___________________________ VSS rail ______________
"""

from __future__ import annotations

import sys

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Point, Rect
from aion_layout.shapes import RectShape, TextShape
from aion_layout.tech import Layer, Tech, sg13g2_tech

CELL_NAME = "AION_inv_nand2_nor2_1"

# ------------------------------------------------------------- floorplan ---
SITE_W = 480
CELL_W = 2880                    # 6 sites
CELL_H = 3780

PITCH = 510                      # contacted poly pitch: 110 + 160 + 110 + 130
XN = [420, 930, 1440, 1950, 2460]        # diffusion node centres n0..n4
XG = [x + PITCH // 2 for x in XN[:-1]]   # gate centres g0..g3

CONT_HW = 80
STUB_HW = 130                    # half width of a Metal1 stub over a contact
POLY_HW = 65
PAD_HW = 150                     # half width of a poly landing pad
M1_PAD_HW = 140                  # half width of a Metal1 pin pad
ACT_MARGIN = 190                 # diffusion overhang past the outer node
RISER_HW = 80                    # half width of an outboard row-crossing riser
RISER_DX = 230                   # its offset from the outer node centre

# ------------------------------------------------------------ y skeleton ---
VSS_M1 = (-220, 220)
VDD_M1 = (CELL_H - 220, CELL_H + 220)
PTAP_ACT = (-150, 150)
NTAP_ACT = (3630, 3930)
PTAP_CONT = (-80, 80)
NTAP_CONT = (3700, 3860)
PSD_BOT = (-180, 180)
PSD_TOP = (1760, 3600)
NWELL_Y = (1750, 4170)

NACT = (590, 1330)               # nmos diffusion, W = 740  (netlist exact)
PACT = (2075, 3195)              # pmos diffusion, W = 1120 (netlist exact)
POLY_Y = (410, 3375)             # gate stripe, 180 nm extension past both rows

POLY_PAD_Y = (1500, 1800)
POLY_CONT_Y = (1570, 1730)

NCONT_Y = [(670, 830), (1010, 1170)]
PCONT_Y = [(2360, 2520), (2700, 2860)]

M1_PAD_Y = (1450, 1790)          # gate pin pads
M1_UPPER = (1970, 2130)          # I1_bar channel, above the pads
M1_LOWER = (1090, 1250)          # O0 channel, below the pads
M1_NVSS = (VSS_M1[1], 880)       # nmos VSS stub: rail up to the first contact
M1_NSIG = (620, M1_LOWER[1])     # nmos signal stub
M1_PSIG = (2310, 2910)           # pmos stub over both contact rows
M1_PVDD = (2310, VDD_M1[0])      # pmos VDD stub up to the rail

TAP_CONT_X = [150 + 430 * k for k in range(7)]

# --------------------------------------------------------------- netlist ---
# node index -> net, per row.  Both chains fall out of the gate order.
PNODES = ["I1_bar", "VDD", "net_p_0", "net_p_1", "O0"]
NNODES = ["I1_bar", "VSS", "O0", "VSS", "O0"]
GATES = ["I1", "I1_bar", "I0", "I2"]
PIN_GATE = {"I1": 0, "I0": 2, "I2": 3}   # gate index carrying an external pin
PIN_DIRECTION = {"I0": "INPUT", "I1": "INPUT", "I2": "INPUT",
                 "O0": "OUTPUT", "VDD": "POWER", "VSS": "GROUND"}


def generate(cell_name: str = CELL_NAME, tech: Tech = sg13g2_tech) -> Cell:
    """Build the cell.  Signature required by scripts/generate_cell.py."""
    cell = Cell(cell_name, tech)

    activ = tech["Activ"]
    poly = tech["GatPoly"]
    cont = tech["Cont"]
    metal1 = tech["Metal1"]
    psd = tech["PSD"]
    nwell = tech["NWell"]
    prbnd = tech["prBoundary"]
    # Pin rectangles live on Metal1's pin datatype; RectShape needs a Layer
    # for that pair, so derive one rather than hard-coding 8/2.
    metal1_pin = Layer(name=f"{metal1.name}.pin",
                       gds_layer=metal1.gds_layer,
                       gds_datatype=metal1.pin_datatype)

    def box(layer: Layer, x1, y1, x2, y2) -> None:
        cell.add_shape(RectShape(layer, Rect.from_lbrt(x1, y1, x2, y2)))

    def pin(name: str, x1, y1, x2, y2) -> None:
        rect = Rect.from_lbrt(x1, y1, x2, y2)
        cell.add_shape(RectShape(metal1_pin, rect))
        cell.add_shape(TextShape(metal1, name, rect.center, purpose="label"))
        cell.add_port(Port(name=name, net=name, layer=metal1, rect=rect,
                           direction=PIN_DIRECTION[name]))

    def cuts(xc, rows) -> None:
        for y0, y1 in rows:
            box(cont, xc - CONT_HW, y0, xc + CONT_HW, y1)

    # ------------------------------------------- boundary, well, implants --
    cell.set_boundary(Rect.from_lbrt(0, 0, CELL_W, CELL_H))
    box(prbnd, 0, 0, CELL_W, CELL_H)
    box(nwell, -240, NWELL_Y[0], CELL_W + 240, NWELL_Y[1])
    box(psd, -70, PSD_BOT[0], CELL_W + 70, PSD_BOT[1])
    box(psd, -70, PSD_TOP[0], CELL_W + 70, PSD_TOP[1])

    # ------------------------------------------------- rails, taps, wells --
    box(activ, 0, PTAP_ACT[0], CELL_W, PTAP_ACT[1])
    box(activ, 0, NTAP_ACT[0], CELL_W, NTAP_ACT[1])
    box(metal1, 0, VSS_M1[0], CELL_W, VSS_M1[1])
    box(metal1, 0, VDD_M1[0], CELL_W, VDD_M1[1])
    for xc in TAP_CONT_X:
        cuts(xc, [PTAP_CONT, NTAP_CONT])

    # -------------------------------------------- diffusion and the gates --
    left, right = XN[0] - ACT_MARGIN, XN[-1] + ACT_MARGIN
    box(activ, left, NACT[0], right, NACT[1])
    box(activ, left, PACT[0], right, PACT[1])
    for gx in XG:
        box(poly, gx - POLY_HW, POLY_Y[0], gx + POLY_HW, POLY_Y[1])
        box(poly, gx - PAD_HW, POLY_PAD_Y[0], gx + PAD_HW, POLY_PAD_Y[1])
        cuts(gx, [POLY_CONT_Y])

    # ------------------------------------------- source / drain contacts ---
    for i, xc in enumerate(XN):
        # VSS nodes keep only the lower row, to stay 180 nm off the O0 channel.
        cuts(xc, NCONT_Y[:1] if NNODES[i] == "VSS" else NCONT_Y)
        if PNODES[i] not in ("net_p_0", "net_p_1"):
            cuts(xc, PCONT_Y)            # the series nodes need no contact

    # ------------------------------------------------------- Metal1 stubs --
    for i, xc in enumerate(XN):
        if NNODES[i] == "VSS":
            box(metal1, xc - STUB_HW, M1_NVSS[0], xc + STUB_HW, M1_NVSS[1])
        if PNODES[i] == "VDD":
            box(metal1, xc - STUB_HW, M1_PVDD[0], xc + STUB_HW, M1_PVDD[1])

    # gate pin pads; the I1_bar pad reaches up into the upper channel
    for gi, gx in enumerate(XG):
        y1 = M1_UPPER[1] if GATES[gi] == "I1_bar" else M1_PAD_Y[1]
        box(metal1, gx - M1_PAD_HW, M1_PAD_Y[0], gx + M1_PAD_HW, y1)

    # ---- I1_bar: XP0/XN0 drains at n0 -> the XP1/XN3 gate at g1 -----------
    x0 = XN[0]
    riser_l = (x0 - RISER_DX, x0 - RISER_DX + 2 * RISER_HW)
    box(metal1, riser_l[0], M1_NSIG[0], x0 + STUB_HW, M1_NSIG[1])     # nmos node
    box(metal1, riser_l[0], M1_NSIG[1], riser_l[1], M1_UPPER[0])      # riser
    box(metal1, riser_l[0], M1_UPPER[0],                              # channel
        XG[1] + M1_PAD_HW, M1_UPPER[1])
    box(metal1, x0 - STUB_HW, M1_UPPER[0], x0 + STUB_HW, M1_PSIG[1])  # pmos node

    # ---- O0: XP3 drain at n4 -> XN1/XN2/XN3 drains at n2 and n4 ----------
    x4 = XN[-1]
    riser_r = (x4 + RISER_DX - 2 * RISER_HW, x4 + RISER_DX)
    box(metal1, XN[2] - STUB_HW, M1_LOWER[0], riser_r[1], M1_LOWER[1])
    box(metal1, XN[2] - STUB_HW, M1_NSIG[0], XN[2] + STUB_HW, M1_NSIG[1])
    box(metal1, x4 - STUB_HW, M1_NSIG[0], riser_r[1], M1_NSIG[1])
    box(metal1, riser_r[0], M1_NSIG[1], riser_r[1], M1_PSIG[0])
    box(metal1, x4 - STUB_HW, M1_PSIG[0], riser_r[1], M1_PSIG[1])

    # ------------------------------------------------------------- pins ---
    for name, gi in PIN_GATE.items():
        pin(name, XG[gi] - M1_PAD_HW, M1_PAD_Y[0], XG[gi] + M1_PAD_HW, M1_PAD_Y[1])
    pin("O0", XN[3] - PAD_HW, M1_LOWER[0], XN[3] + PAD_HW, M1_LOWER[1])
    pin("VDD", 0, VDD_M1[0], CELL_W, VDD_M1[1])
    pin("VSS", 0, VSS_M1[0], CELL_W, VSS_M1[1])

    return cell


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else f"{CELL_NAME}.gds"
    generate().write_gds(out)
    assert CELL_W % SITE_W == 0
    print(f"wrote {out}  ({CELL_W} x {CELL_H} nm = {CELL_W // SITE_W} sites)")
    print(f"  nmos W = {NACT[1] - NACT[0]} nm (netlist 740 nm), "
          f"pmos W = {PACT[1] - PACT[0]} nm (netlist 1120 nm), 1 finger each")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
