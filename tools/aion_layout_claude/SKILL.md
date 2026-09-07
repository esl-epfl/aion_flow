---
name: aion-layout
description: Draw a DRC/LVS-clean IHP SG13G2 standard-cell layout for an AION transistor-level SPICE netlist, prove it is smaller and faster than the abutted PDK cells it replaces, and export gds/lef/lib/v/spice/cdl. Use when asked to lay out an AION cell, to fix DRC or LVS on one, or to produce its views.
---

# Drawing an AION standard cell

You draw the cell. The tool does everything else, and you must let it: DRC, LVS, PEX,
area measurement, characterization, the comparison and the view export are mechanical
steps with exactly one right answer, and running them by hand only adds variance. Every
one of them is a single command below.

Work in `tools/aion_layout_claude`. Everything here assumes that as the working directory
and `PYTHONPATH=.` (the `Makefile` sets it for you).

---

## The loop

```bash
make scaffold CELL=<cell> NETLIST=<netlist.spice>   # once: a starting generator
$EDITOR cells/<cell>.py                             # ← the only thing you do by hand
make verify  CELL=<cell> NETLIST=<netlist.spice>    # build + DRC + LVS, one RESULT: line
make evidence CELL=<cell> NETLIST=<netlist.spice>   # what to fix, with coordinates
```

Repeat `edit → verify → evidence` until `RESULT: PASS`. Then, once, the rest:

```bash
make flow CELL=<cell> NETLIST=<netlist.spice> BASELINE=<gate_level.spice>
```

which runs verify → PEX → build and verify the abutted baseline → characterize both →
compare → export, and ends in a `COMPARE:` line and `final/` full of views.

A generator is a module exposing `generate(name: str, tech: Tech) -> Cell`. Start from
`cells/AION_inv_nand2_nor2_1.py`; it is a complete, verified example. **All coordinates
are integers in nanometres.**

### Reading the evidence

`make evidence` prints blocks, and the two that matter most are:

- **`[5] LAYOUT DIGEST`** — the per-layer inventory and the **cross-net overlap table**.
  That table names a short by coordinates. If it lists a pair, you have a short there;
  there is nothing to interpret.
- **`[3] DRC ITEMS`** — every violation as `category bbox description`. Fix by category,
  not one box at a time: four `M1.d` items are usually one stub that is too small,
  repeated.

An LVS `Final result: Circuits match uniquely.` with 8/8 devices and 9/9 nets is the goal.
Anything else, read block `[4]`: `disconnected_nodes` names a net you drew but never
connected, and a device count short by one means a poly stripe is missing or does not
cross the diffusion.

---

## Floorplan first — this is what decides whether you win

Do not start placing rectangles. Decide, on paper, in this order:

**1. Which devices share diffusion.** Two devices sharing a source/drain node need no
wire, no contact and no column of their own. Order the gates so that the pull-up chain and
the pull-down chain each become one unbroken diffusion strip: this is a Euler path over
the series/parallel graph. `netlist_view.suggest_gate_order(subckt)` proposes one; check it
against the netlist yourself, because the ordering that merges the *pmos* row is not always
the one that merges the *nmos* row, and you want both.

Write the plan out as two rows of nodes and one row of gates, and put it in the module
docstring — it is the thing a reader needs and the thing you will need next iteration:

```
   pmos nodes   I1_bar |  VDD  | net_p_0 | net_p_1 |  O0
   gates             I1     I1_bar     I0        I2
   nmos nodes   I1_bar |  VSS  |   O0    |   VSS   |  O0
```

**2. How many columns.** N gates need N+1 diffusion nodes. The contacted poly pitch is
**510 nm** = 110 (`Cnt.f`, contact to poly) + 160 (contact) + 110 + 130 (poly width). So N
gates occupy `N × 510` nm of nodes, plus about 190 nm of diffusion overhang at each end.

**3. The width.** Round that up to a whole number of **480 nm** sites, and check the Metal1
you will need actually fits — the metal, not the diffusion, is usually what sets the width.
`Act.b` (210 nm active spacing) must still hold when the cell is abutted with a copy of
itself, so diffusion may not run to the boundary.

**4. Only then draw.** A cell that is one site too wide is a floorplan mistake, and no
amount of shape-nudging fixes it.

### Device widths

Use the netlist's `w` exactly. In a 3780 nm row, `w=740 nm` (nmos) and `w=1120 nm` (pmos)
fit as single unbroken strips, which is why the PDK uses them: no folding, no fingers, and
the extracted `w` matches the netlist with no quantisation error. If a netlist asks for a
width that does not fit, fold it into `ng` fingers rather than shrinking it — LVS compares
widths.

---

## The vertical skeleton — known DRC-good, reuse it

Every cell in this row height shares this y-stack. It is the shipped library's, so it is
verified; copy it and vary only the x coordinates.

| what | y (nm) | note |
|---|---|---|
| VSS Metal1 rail | `-220 … 220` | 440 nm wide, centred on y=0 |
| p+ tap Activ | `-150 … 150` | substrate tie under the VSS rail |
| p+ tap Cont row | `-80 … 80` | |
| pSD (bottom) | `-180 … 180` | |
| nmos Activ | `590 … 1330` | W = 740 |
| nmos Cont rows | `670 … 830`, `1010 … 1170` | two rows per node |
| Metal1 lower channel | `1090 … 1250` | routing below the gate pads |
| gate pin pads (Metal1) | `1450 … 1790` | |
| poly landing pad | `1500 … 1800` | with its Cont at `1570 … 1730` |
| Metal1 upper channel | `1970 … 2130` | routing above the gate pads |
| pmos Activ | `2075 … 3195` | W = 1120 |
| pmos Cont rows | `2360 … 2520`, `2700 … 2860` | |
| NWell | `1750 … 4170` | overhangs the boundary; neighbours share it |
| pSD (top) | `1760 … 3600` | |
| n+ tap Activ | `3630 … 3930` | well tie under the VDD rail |
| n+ tap Cont row | `3700 … 3860` | |
| VDD Metal1 rail | `3560 … 4000` | |
| poly stripe | `410 … 3375` | ~180 nm extension past both diffusions |

The wells and implants deliberately overhang the prBoundary. That is correct: an abutted
neighbour shares them. Do not trim them to the boundary.

---

## Routing

**Metal1 first.** Between the gate pin pads (`1450 … 1790`) and each diffusion there is a
channel — `1090 … 1250` below and `1970 … 2130` above. Two nets can cross the row gap in
Metal1 without meeting if one uses the upper channel and the other the lower.

**A riser cannot pass a gated column.** At a 510 nm pitch, a vertical Metal1 strip cannot
squeeze past a node column that has gate pin pads on both sides: the pads are 280 nm wide
and 255 nm from the node centre, leaving less than the 180 nm `M1.b` spacing. Put row
crossings at the **outer** nodes and step the riser outboard, past the end of the
diffusion, where nothing is in the way.

**Metal2 is allowed, and it costs something.** Metal2 inside the cell is a routing
blockage the block-level router has to work around, and it is reported in the export. Use
it when it buys a site or breaks a crossing that Metal1 cannot, not by default. Most PDK
cells at drive 1 are Metal1-only, and so is the worked example.

When you do use it: `draw_via1`, `draw_via1_array`, `draw_m2_wire` and `draw_m2_pin` in
`aion_layout.building_blocks` size the landings from the rules for you and raise rather
than draw something illegal. `cells/_m2_probe.py` is a DRC-clean cell exercising all of
them — build it if you want a worked example of the geometry.

---

## Taps, or `LU.a` and `LU.b` forever

These two rules are not violated by geometry in the wrong place but by geometry that is
**missing**, so no amount of moving shapes fixes them:

- `LU.a` — every p-diffusion (the pmos active in the NWell) needs an n+ tap within range.
- `LU.b` — every n-diffusion (the nmos active in the substrate) needs a p+ tap within range.

A cell that draws no taps is infinitely far from one, and each rule fires once per
uncovered diffusion region — poly splits an active area into separate regions and each is
reported on its own, so the count tracks geometry, not device count.

Draw a tap row alongside each rail, at the y coordinates in the table above: an n+ tap in
the NWell tied to VDD, a p+ tap in the substrate tied to VSS. `draw_tap` does implant,
contact row, Metal1 landing, label and port in one call. The same addition gives the
extractor the bulk connection LVS wants, so one fix clears both.

---

## Pins and labels — LVS matches on these

Every port of the `.subckt` needs a Metal1 (or Metal2) **label text** on the shape that
carries the net, and a `Port` on the `Cell` with the right direction. Netgen matches by
name: a missing label is a failed pin match, not a subtle timing issue. Internal nets need
no label. Put the label inside the shape it names, or the extractor may attach it to the
wrong net.

### Every port must cover a routing track

LVS only cares that the label is on the right net. The **router** cares where the shape
is, and it is stricter than it looks. Tracks
(`libs.tech/librelane/sg13g2_stdcell/tracks.info`) run at `x = n * 480` nm and
`y = n * 420` nm on every Metal. A wire runs *along* its layer's preferred direction, so
it stops anywhere on that axis but is pinned to a track on the other one:

| Layer    | `DIRECTION` | the port shape must contain |
| -------- | ----------- | --------------------------- |
| `Metal1` | HORIZONTAL  | a `y = n * 420` nm line     |
| `Metal2` | VERTICAL    | an `x = n * 480` nm line    |

A port that covers no track places fine, routes globally fine, then aborts the entire
design in detailed routing with `DRT-0073 No access point`. That is a hard abort, not a
DRC — nothing downgrades it, and it costs an hour of flow to discover.

This is easy to get wrong on an **output** port squeezed between two other Metal1 shapes.
`M1.a` min width is 160 nm and `M1.b` min spacing is 180 nm, so a port in a 520 nm channel
has exactly 160 nm of room and 10 nm of slack against the 420 nm pitch. The first two AION
cells both failed here: their `O0` topped out at `y = 1250` with the track at `y = 1260`.

So place the port **against a track deliberately**, do not let it fall where the channel
happens to leave room. Pick the track first, then draw the shape across it. If the port
cannot grow where it sits, move the neighbouring Metal1 (the PDK cells do this — the `Y`
of `sg13g2_a21oi_1` is a multi-rect stub from `y = 720` to `y = 3160`, crossing six
tracks) or drop a `Via1` and put the port on Metal2, where the rule becomes an
`x = n * 480` line.

`make export` checks this and refuses to publish, and `make pnr` refuses to start. All 283
signal pins of the PDK `sg13g2_stdcell` library satisfy it.

---

## Fix in this order

Connectivity before geometry, always. Do not optimise area before LVS matches.

1. Wrong transistor topology — the netlist says something the layout does not implement
2. Missing or wrong source/drain connections
3. Missing contacts or vias
4. Missing power connections
5. Missing input/output connections
6. LVS connectivity mismatches
7. DRC shorts (the cross-net overlap table names them)
8. DRC spacing
9. DRC enclosure
10. Everything else geometric
11. Compactness

Prefer small targeted edits over a redraw, and keep the parts that already verify. Every
edit should have a reason you could write in one line: *"LVS says O0 is disconnected from
the XP3 drain → add the Metal1 riser at n4"*.

---

## Rules that bite, with their numbers

| rule | value (um) | what it catches |
|---|---|---|
| `M1.a` / `M1.b` | width 0.16 / space 0.18 | Metal1 too thin, two stubs too close |
| `M1.d` | area 0.09 | a Metal1 stub that is legal in both dimensions but too small |
| `M2.a` / `M2.b` | width 0.20 / space 0.21 | |
| `M2.d` | area 0.144 | **a 0.2 um Metal2 wire must be ≥ 0.72 um long** |
| `V1.a` / `V1.b` | Via1 exactly 0.19 / space 0.22 | Via1 has a max width too, not just a min |
| `M1.c1` / `V1.c1` | 0.05 | Metal1 endcap enclosure of Via1 |
| `M2.c` / `M2.c1` | 0.005 / 0.05 | Metal2 enclosure of Via1, sides vs endcap |
| `Cnt.a` / `Cnt.f` | Cont exactly 0.16 / 0.11 to poly | `Cnt.f` is what sets the 510 nm pitch |
| `Act.a` / `Act.b` | width 0.24 / space 0.21 | `Act.b` must hold across an abutment |
| `Gat.a` / `Gat.b` | width 0.13 / space 0.18 | |
| `LU.a` / `LU.b` | — | missing taps, see above |

The full numeric tables are in `context/drc/docs/{main,extra,precheck}_rules.md`, and
`make evidence` block `[7]` prints the ones the framework knows, generated from `tech.py`
so they cannot drift.

---

## Winning the comparison

The cell is measured against the **abutted baseline**: the same logic built from the PDK
standard cells it replaces, placed in one row and jumpered in Metal2, run through the
identical DRC/LVS/PEX/characterization chain. `make baseline` builds it; `make compare`
prints one `COMPARE:` line.

Area is the prBoundary — the placement footprint, not the shape bounding box. You win on
area by merging diffusion (fewer columns) and by not spending a site on routing you could
have done in a channel. You win on delay because the merged cell drops the internal wires,
contacts and junction area that the abutted chain spends between its cells; every column
you remove removes some of that too, so the two usually improve together.

### When it says LOSS

First find out *where* the loss is, because the two causes have different fixes and only
one of them is yours.

Look at the per-arc table in the comparison report. If the fall arcs and the rise arcs are
both slow, or the loss tracks the wire lengths, it is the layout. If one sense is slow and
the other is not, suspect the netlist: a series stack of N devices has N times the
on-resistance of a single one, and the abutted chain it is being compared against never
stacks more than two.

Separate them with one command — characterize the *ideal* netlist, with no parasitics at
all, and compare that to the PEX numbers:

```bash
make characterize CELL=<cell> NETLIST=<the transistor netlist, not the PEX one> \
     BUILD_DIR=build/_ideal CORNERS=typ
```

If ideal and PEX agree to a few per cent, the layout is not the problem and no amount of
re-routing will help. On the worked example that difference was 1.3–11.8 ps against a
167 ps gap: 1.6%.

Then the fix is device sizing, and it is an explicit step:

```bash
make resize CELL=<cell> NETLIST=<netlist> BASELINE=<gate-level netlist>
```

`resize` finds the devices in a series stack deeper than `MIN_DEPTH`, widens them, folds
them into fingers, and writes a **new** netlist and a report. It never edits the input:
the netlist is what LVS grades against, so resizing produces a differently named cell.
It picks the largest multiplier whose estimated area still fits inside the abutted row —
a cell that is faster but no longer smaller has spent the only advantage it had — and if
no multiplier fits it says so rather than quietly changing nothing and reporting success.

Then lay out the resized cell. Folding changes the floorplan: a series chain of N-finger
devices lays out as a **palindrome** around its output node, so every internal node
appears twice and needs a strap, and the gate pairs at the outer columns do too. That is
what the two Metal2 tracks in `cells/AION_inv_nand2_nor2_1s.py` are for, and its module
docstring works the whole thing through.

If the loss really is the layout: recount the columns and re-derive the gate order. It is
almost never the routing.

---

## Hard rules

- **Never modify the netlist.** It is the source of truth for connectivity and for device
  widths. Fix the layout.
- **Never hand-edit a GDS, a report, or anything under a run directory.** They are
  evidence. If a verdict looks wrong, it is the layout or a real tool bug, and both are
  worth finding.
- **Never mark something clean that was not positively confirmed clean.** A missing report,
  an empty one, a KLayout run with no receipt: all of them mean *unknown*, and the tool
  will tell you so. Do not argue with it.
- **The cell must stay row-legal**: height exactly 3780 nm, width an exact multiple of
  480 nm, `PIN VDD` and `PIN VSS` present. `make verify` checks it and `make export`
  refuses to publish a cell that fails it.
- **Every signal port must cover a routing track**: a Metal1 port needs a `y = n * 420` nm
  line inside it, a Metal2 port an `x = n * 480` nm line. Miss it and detailed routing
  kills the whole design with `DRT-0073`, long after this cell looked finished.
  `make export` refuses to publish a cell that fails it.
- **The Verilog model is solved from the netlist, not written by you.** `make export`
  derives the cell's function from the transistor netlist, checks it against the
  `function` the characterizer measured in SPICE, and refuses to publish anything when
  the two disagree or when the netlist has no truth table (feedback, a node nothing
  drives). A refusal there is a real finding about the cell — do not work around it.
