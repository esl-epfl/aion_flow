# AION_inv_nand2_nor2_1 — IHP SG13G2 standard cell

DRC- and LVS-clean layout of `../AION_inv_nand2_nor2_1_minimized.spice`,
routed in **Metal1 only** (no Metal2, no Via1).

| | |
|---|---|
| prBoundary | **2880 x 3780 nm** = 6 x 480 nm sites, cell height 3780 nm |
| Devices | 4 pmos w=1.12 um, 4 nmos w=740 nm, all single-finger, L=130 nm |
| Layers | Activ, GatPoly, Cont, Metal1 (+ pin 8/2, label 8/25), pSD, NWell |
| Magic DRC | clean (COUNT: 0) |
| KLayout DRC | clean (`-l macro`, 0 violations, receipt verified) |
| Netgen LVS | `Final result: Circuits match uniquely.` — 8/8 devices, 9/9 nets |

Extracted widths are `w=0.74u` / `w=1.12u`, i.e. exactly the netlist values —
740 nm and 1120 nm are precisely the diffusion heights a 3780 nm cell allows,
so nothing is folded and there is no quantisation error at all.

## Files

| file | what |
|---|---|
| `AION_inv_nand2_nor2_1.py` | the generator; exposes `generate(cell_name, tech) -> Cell` for `make`, and runs standalone too |
| `AION_inv_nand2_nor2_1.gds` | the layout |
| `AION_inv_nand2_nor2_1.png` | rendering via `scripts/gds_to_image.py` |
| `drc/` | Magic + KLayout DRC run directories |
| `lvs/` | Magic extraction + netgen run directory |
| `report.txt` | combined verdict from `scripts/report_verification.py` |

## Floorplan — why 6 sites

The cell is an inverter on `I1` feeding a NOR3.  Ordering the gates
`I1, I1_bar, I0, I2` chains all four pmos devices into one unbroken diffusion
and all four nmos devices into another:

```
   pmos nodes   I1_bar |  VDD  | net_p_0 | net_p_1 |  O0
   gates             I1     I1_bar     I0        I2
   nmos nodes   I1_bar |  VSS  |   O0    |   VSS   |  O0
```

`net_p_0` and `net_p_1` fall out as shared diffusion — no wire, no contact,
no column of their own.  Four gates need five diffusion nodes, every nmos node
needs a contact, and `Cnt.f` (contact 110 nm clear of poly) fixes the
contacted pitch at 510 nm: `110 + 160 + 110 + 130`.  So 4 x 510 = 2040 nm of
nodes is the floor, plus 190 nm of diffusion overhang and the Metal1 risers
below.  5 sites (2400 nm) does not hold it — the Metal1 alone spans 2500 nm,
and the diffusion would end 30 nm from the boundary, which breaks `Act.b`
(210 nm) the moment the cell is abutted.  **6 sites is the smallest legal
width**, against 8 for an abutted `sg13g2_inv_1` + `sg13g2_nor3_1`.

## Routing — Metal1 only

Two nets must cross the gap between the rows: `I1_bar` (XP0/XN0 drains up to
the XP1/XN3 gate) and `O0` (XP3 drain down to the XN1/XN2/XN3 drains).

At a 510 nm pitch a vertical strip cannot pass a node column that has gate pin
pads on both sides — the pads are 280 nm wide, 255 nm from the node centre,
which leaves less than the 180 nm Metal1 spacing on either side.  Both
crossings are therefore placed at the two **outer** nodes, and their risers
step outboard past the end of the diffusion, where nothing is in the way:

```
        ______________________ VDD rail _______________________
 pmos     n0        n1        n2        n3        n4
 riser   |                                         |
 upper   +-----------------[I1_bar]                 |   y 1970..2130
 pads     [I1]     [I1_bar]   [I0]      [I2]        |   y 1450..1790
 lower              [O0]------------------[O0]------+   y 1090..1250
 nmos     n0        n1        n2        n3        n4
        ______________________ VSS rail _______________________
```

The `I1_bar` channel runs *above* the pin pads and the `O0` channel *below*
them, so the two never meet.  To keep 180 nm off those channels the VSS stubs
use only the lower nmos contact row and the pmos contacts start at y = 2360.

## Verify with `make`

All three Makefile variables have to be given together.  `CELL_NAME` is derived
from `CELL_MODULE`, so overriding `CELL_NAME` alone makes `make` build the
*default* cell (`cells/sg13g2_nand2_1.py`) into this cell's GDS path and
overwrite it.  Set them once and the targets are short:

```sh
cd tools/aion_layout
export CELL_MODULE=std_cells_claude/AION_inv_nand2_nor2_1.py
export RUNS_DIR=std_cells_claude
export NETLIST=AION_inv_nand2_nor2_1_minimized.spice

make gds     # -> std_cells_claude/AION_inv_nand2_nor2_1.gds
make drc     # -> std_cells_claude/drc/    Magic + KLayout, both clean
make lvs     # -> std_cells_claude/lvs/    netgen, matches uniquely
```

(or spell them out per invocation:
`make drc CELL_MODULE=std_cells_claude/AION_inv_nand2_nor2_1.py RUNS_DIR=std_cells_claude`)

`make lvs` prints `KLayout LVS needs a CDL netlist but a SPICE netlist was
provided, running Magic+Netgen LVS only` -- that is sak-lvs.sh's own choice,
not a failure.

### `make verify` cannot pass — a Makefile gap, not a layout problem

`scripts/report_verification.py` refuses to call a zero-violation KLayout run
clean unless it finds `klayout.receipt.json` in the KLayout DRC run directory.
That receipt is written by `pipeline_write_klayout_receipt` in `pipeline.sh`,
and the Makefile's `drc` target calls `sak-drc.sh` directly instead, so the
receipt is never produced -- for any cell, not just this one.  `make verify`
therefore always ends in
`KLayout : DEGRADED ... completeness: UNVERIFIED` / `RESULT: FAIL`.

To get the verdict today, run DRC/LVS through the pipeline steps (identical
tool commands, plus the receipt) and then the report:

```sh
bash -c 'source ./pipeline.sh
  step_drc_at std_cells_claude/AION_inv_nand2_nor2_1.gds std_cells_claude/drc
  step_lvs_at std_cells_claude/AION_inv_nand2_nor2_1.gds std_cells_claude/lvs \
              AION_inv_nand2_nor2_1_minimized.spice AION_inv_nand2_nor2_1'

python3 scripts/report_verification.py --cell AION_inv_nand2_nor2_1 \
  --gds std_cells_claude/AION_inv_nand2_nor2_1.gds \
  --netlist AION_inv_nand2_nor2_1_minimized.spice \
  --runs-dir std_cells_claude --parse-only      # -> RESULT: PASS
```

`report.txt` is the output of exactly that.

## Render

```sh
./scripts/docker_run.sh "cd tools/aion_layout && \
  python3 scripts/gds_to_image.py std_cells_claude/AION_inv_nand2_nor2_1.gds \
          std_cells_claude/AION_inv_nand2_nor2_1.png --width 1400 --height 1700"
```
