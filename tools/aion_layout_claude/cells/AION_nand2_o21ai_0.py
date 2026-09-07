#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Description:               NAND2 + O21AI standard-cell generator (IHP SG13G2)
# ================================================================

"""Generator for the AION_nand2_o21ai_0 standard cell.

    w0 = !(I0 & I1)                     NAND2, L = 130 nm
    O0 = !((I2 | I3) & w0)              O21AI, L = 150 nm

Ten devices, every one a single finger at the library's own widths
(nmos w = 740 nm, pmos w = 1120 nm), so both rows are unbroken-height
diffusion strips and the extracted widths match the netlist exactly.
The two sub-gates have different channel lengths, so the poly stripes are
drawn 130 nm wide for the I1/I0 gates and 150 nm wide for the w0/I3/I2
gates.

Floorplan.  The pmos network has an Euler circuit; the nmos network has
four odd-degree vertices (VSS, Xg1_net1, w0, O0) so it needs two trails
whatever the ordering, i.e. exactly one diffusion break.  The gate order
I1, I0, w0, I3, I2 chains all five pmos devices into one strip and splits
the nmos into 3 + 4 nodes:

    pmos nodes  VDD |  w0  |     VDD     |  O0  | Xg1_net14 | VDD
    gates            I1        I0    w0      I3         I2
    nmos nodes  VSS | Xg0_net1 | w0 ||| O0 | Xg1_net1 | VSS | Xg1_net1

(``|||`` is the diffusion break; the pmos node between the I0 and w0
gates is a single VDD node spanning both node columns N2 and N3.)
Xg1_net1 appears twice (it has degree three) and is strapped in the lower
Metal1 channel; Xg0_net1 and Xg1_net14 are pure shared-diffusion nodes and
need no contact at all.

Five gates plus one break need seven node columns.  Cnt.f (110 nm contact
to poly) with a 150 nm gate sets the contacted pitch at 530 nm, so the
nodes span 6 x 530 = 3180 nm; with the diffusion overhang that lands the
cell on 8 sites (3840 nm).

Routing.  Two nets cross the row gap.  w0 (pmos N1 drain, nmos N2 drain and
the g2 gate) uses the break column -- the only interior column with no gate
pad beside it -- and the upper Metal1 channel.  That leaves no Metal1 path
for O0 (nmos N3 up to pmos N4), because every other column is flanked by
gate pin pads and both cell edges are occupied by rail stubs, so O0 crosses
on one short Metal2 jumper with a Via1 at each end.

           _________________________ VDD rail _______________
   pmos    N0    N1    N2    N3    N4    N5    N6
                                [O0]==============            y 2310..2660
   upper    [w0]---------------------[w0]                     y 1970..2130
   pads    [I1]  [I0]        [w0]  [I3]  [I2]                 y 1450..1790
   lower                 [w0]  |M2| [Xg1_net1]-------         y 1090..1250
   nmos    N0    N1    N2  |||  N3    N4    N5    N6
           _________________________ VSS rail _______________
"""

from __future__ import annotations

import sys

from aion_layout.cell import Cell, Port
from aion_layout.primitives import Rect
from aion_layout.shapes import RectShape, TextShape
from aion_layout.tech import Layer, Tech, sg13g2_tech

CELL_NAME = "AION_nand2_o21ai_0"

# ------------------------------------------------------------- floorplan ---
SITE_W = 480
CELL_W = 3840                    # 8 sites
CELL_H = 3780

PITCH = 530                      # 110 + 160 + 110 + 150 (the L=150 gates)
XN = [330 + PITCH * k for k in range(7)]          # node centres N0..N6
XG = [                                            # gate centres g0..g4
    (XN[0] + XN[1]) // 2,        # I1
    (XN[1] + XN[2]) // 2,        # I0
    (XN[3] + XN[4]) // 2,        # w0   (the break sits between N2 and N3)
    (XN[4] + XN[5]) // 2,        # I3
    (XN[5] + XN[6]) // 2,        # I2
]

CONT_HW = 80
STUB_HW = 130                    # half width of a Metal1 stub over a contact
PAD_HW = 150                     # half width of a poly landing pad
M1_PAD_HW = 140                  # half width of a Metal1 pin pad
ACT_MARGIN = 190                 # diffusion overhang past the outer node
BREAK_HW = 150                   # diffusion end, half node, at the nmos break

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
POLY_Y = (410, 3375)

POLY_PAD_Y = (1500, 1800)
POLY_CONT_Y = (1570, 1730)

NCONT_Y = [(670, 830), (1010, 1170)]
PCONT_Y = [(2360, 2520), (2700, 2860)]

M1_PAD_Y = (1450, 1790)          # gate pin pads
M1_UPPER = (1970, 2130)          # w0 channel, above the pads
M1_LOWER = (1090, 1250)          # Xg1_net1 strap, below the pads
M1_NVSS = (VSS_M1[1], 880)       # nmos VSS stub: rail up to the first contact
M1_NSIG = (620, M1_LOWER[1])     # nmos signal stub, both contact rows
M1_PSIG = (2310, 2910)           # pmos stub over both contact rows
M1_PVDD = (2310, VDD_M1[0])      # pmos VDD stub up to the rail

# One 160 nm cut per CoreSite, centred in it: the rail tap cuts of an abutted
# neighbour then land on exactly the same rectangles instead of partly on them.
TAP_CONT_X = [240 + SITE_W * k for k in range(CELL_W // SITE_W)]

# ------------------------------------------------- the O0 Metal2 jumper ----
V1_HW = 95                       # Via1 is exactly 190 nm
V1_X = 1935                      # inside the nmos N3 stub / pmos O0 bar
V1_YB = (1010, 1200)
V1_YT = (2400, 2590)
# The strap *is* the O0 port (see below), so it is drawn 220 nm wide: a port
# has to be at least 210 nm across for a ViaN landing, and M2.a's 200 nm
# minimum width is 10 nm short of that.
M2_X = (V1_X - 110, V1_X + 110)  # 220 nm wide, 15 nm side enclosure
M2_Y = (950, 2650)               # 50 nm endcap enclosure at both ends
# The O0 landing is stretched up to 1270 so the port covers the y = 1260 nm
# Metal1 routing track; 1450 - 1270 = 180 nm keeps M1.b to the gate pads.
M1_LAND_YB = (960, 1270)         # Metal1 landing (>= 50 nm Via1 endcap)
M1_LAND_YT = (2310, 2660)

# --------------------------------------------------------------- netlist ---
PNODES = ["VDD", "w0", "VDD", "VDD", "O0", "Xg1_net14", "VDD"]
NNODES = ["VSS", "Xg0_net1", "w0", "O0", "Xg1_net1", "VSS", "Xg1_net1"]
GATES = ["I1", "I0", "w0", "I3", "I2"]
PIN_GATE = {"I1": 0, "I0": 1, "I3": 3, "I2": 4}
GATE_L = {"I1": 130, "I0": 130, "w0": 150, "I3": 150, "I2": 150}
PIN_DIRECTION = {"I0": "INPUT", "I1": "INPUT", "I2": "INPUT", "I3": "INPUT",
                 "O0": "OUTPUT", "VDD": "POWER", "VSS": "GROUND"}

# nodes that get a contact.  Xg0_net1 (nmos N1) and Xg1_net14 (pmos N5) are
# pure shared-diffusion nodes; pmos N3 is the same VDD node as N2.
PCONT_NODES = [0, 1, 2, 4, 6]
NCONT_NODES = [0, 2, 3, 4, 5, 6]


def generate(cell_name: str = CELL_NAME, tech: Tech = sg13g2_tech) -> Cell:
    """Build the cell.  Signature required by scripts/generate_cell.py."""
    cell = Cell(cell_name, tech)

    activ = tech["Activ"]
    poly = tech["GatPoly"]
    cont = tech["Cont"]
    metal1 = tech["Metal1"]
    metal2 = tech["Metal2"]
    via1 = tech["Via1"]
    psd = tech["PSD"]
    nwell = tech["NWell"]
    prbnd = tech["prBoundary"]
    metal1_pin = Layer(name=f"{metal1.name}.pin",
                       gds_layer=metal1.gds_layer,
                       gds_datatype=metal1.pin_datatype)
    metal2_pin = Layer(name=f"{metal2.name}.pin",
                       gds_layer=metal2.gds_layer,
                       gds_datatype=metal2.pin_datatype)

    def box(layer: Layer, x1, y1, x2, y2) -> None:
        cell.add_shape(RectShape(layer, Rect.from_lbrt(x1, y1, x2, y2)))

    def pin(name: str, x1, y1, x2, y2) -> None:
        rect = Rect.from_lbrt(x1, y1, x2, y2)
        cell.add_shape(RectShape(metal1_pin, rect))
        cell.add_shape(TextShape(metal1, name, rect.center, purpose="label"))
        cell.add_port(Port(name=name, net=name, layer=metal1, rect=rect,
                           direction=PIN_DIRECTION[name]))

    def m2_pin(name: str, x1, y1, x2, y2) -> None:
        """Same as ``pin`` but on Metal2, where the O0 strap already is."""
        rect = Rect.from_lbrt(x1, y1, x2, y2)
        cell.add_shape(RectShape(metal2_pin, rect))
        cell.add_shape(TextShape(metal2, name, rect.center, purpose="label"))
        cell.add_port(Port(name=name, net=name, layer=metal2, rect=rect,
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
    box(activ, left, PACT[0], right, PACT[1])
    box(activ, left, NACT[0], XN[2] + BREAK_HW, NACT[1])       # nmos trail 1
    box(activ, XN[3] - BREAK_HW, NACT[0], right, NACT[1])      # nmos trail 2

    for gi, gx in enumerate(XG):
        half = GATE_L[GATES[gi]] // 2
        box(poly, gx - half, POLY_Y[0], gx + half, POLY_Y[1])
        box(poly, gx - PAD_HW, POLY_PAD_Y[0], gx + PAD_HW, POLY_PAD_Y[1])
        cuts(gx, [POLY_CONT_Y])

    # ------------------------------------------- source / drain contacts ---
    for i in PCONT_NODES:
        cuts(XN[i], PCONT_Y)
    for i in NCONT_NODES:
        # VSS nodes keep only the lower row, to stay clear of the strap.
        cuts(XN[i], NCONT_Y[:1] if NNODES[i] == "VSS" else NCONT_Y)

    # ------------------------------------------------------- Metal1 rails --
    for i in PCONT_NODES:
        if PNODES[i] == "VDD":
            box(metal1, XN[i] - STUB_HW, M1_PVDD[0], XN[i] + STUB_HW, M1_PVDD[1])
    for i in NCONT_NODES:
        if NNODES[i] == "VSS":
            box(metal1, XN[i] - STUB_HW, M1_NVSS[0], XN[i] + STUB_HW, M1_NVSS[1])

    # ------------------------------------------------------- gate pads -----
    for gi, gx in enumerate(XG):
        top = M1_UPPER[1] if GATES[gi] == "w0" else M1_PAD_Y[1]
        box(metal1, gx - M1_PAD_HW, M1_PAD_Y[0], gx + M1_PAD_HW, top)

    # ---- w0: pmos N1 drain, nmos N2 drain and the g2 gate ----------------
    box(metal1, XN[1] - STUB_HW, M1_UPPER[0], XN[1] + STUB_HW, M1_PSIG[1])
    box(metal1, XN[1] - STUB_HW, M1_UPPER[0], XG[2] + M1_PAD_HW, M1_UPPER[1])
    box(metal1, XN[2] - STUB_HW, M1_NSIG[0], XN[2] + STUB_HW, M1_NSIG[1])
    box(metal1, XN[2] + 55, M1_LOWER[0], XN[2] + 215, M1_UPPER[1])   # riser

    # ---- Xg1_net1: nmos N4 and N6, strapped in the lower channel ---------
    for i in (4, 6):
        box(metal1, XN[i] - STUB_HW, M1_NSIG[0], XN[i] + STUB_HW, M1_NSIG[1])
    box(metal1, XN[4] - STUB_HW, M1_LOWER[0], XN[6] + STUB_HW, M1_LOWER[1])

    # ---- O0: nmos N3 up to pmos N4 over one Metal2 jumper ----------------
    box(metal1, XN[3] - STUB_HW, M1_NSIG[0], XN[3] + STUB_HW, M1_NSIG[1])
    box(metal1, XN[3] - STUB_HW, M1_LAND_YB[0], XN[3] + STUB_HW + 30, M1_LAND_YB[1])
    box(metal1, XN[4] - STUB_HW, M1_PSIG[0], XN[4] + STUB_HW, M1_PSIG[1])
    box(metal1, XN[3] - STUB_HW, M1_LAND_YT[0], XN[4] + STUB_HW, M1_LAND_YT[1])
    box(via1, V1_X - V1_HW, V1_YB[0], V1_X + V1_HW, V1_YB[1])
    box(via1, V1_X - V1_HW, V1_YT[0], V1_X + V1_HW, V1_YT[1])
    box(metal2, M2_X[0], M2_Y[0], M2_X[1], M2_Y[1])

    # ------------------------------------------------------------- pins ---
    for name, gi in PIN_GATE.items():
        pin(name, XG[gi] - M1_PAD_HW, M1_PAD_Y[0], XG[gi] + M1_PAD_HW, M1_PAD_Y[1])
    # O0 is declared on the Metal2 strap, not on the Metal1 landing: `lef write
    # -pinonly` emits every unlabelled shape as OBS, so a Metal1 port would be
    # published with this cell's own Metal2 parked on its via landing.  The
    # strap spans x = 1920 nm, a Metal2 (vertical) routing track.
    m2_pin("O0", M2_X[0], M2_Y[0], M2_X[1], M2_Y[1])
    pin("VDD", 0, VDD_M1[0], CELL_W, VDD_M1[1])
    pin("VSS", 0, VSS_M1[0], CELL_W, VSS_M1[1])

    return cell


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else f"{CELL_NAME}.gds"
    generate().write_gds(out)
    assert CELL_W % SITE_W == 0
    print(f"wrote {out}  ({CELL_W} x {CELL_H} nm = {CELL_W // SITE_W} sites)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
