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
make verify  CELL=<cell> NETLIST=<netlist.spice>    # build + DRC + LVS + pin access + abutment + TritonRoute, one RESULT: line
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

| Layer    | `DIRECTION` | draw the port shape across  |
| -------- | ----------- | --------------------------- |
| `Metal1` | HORIZONTAL  | a `y = n * 420` nm line     |
| `Metal2` | VERTICAL    | an `x = n * 480` nm line    |

A port that covers no track, with no room beside it for a via to hang off onto, places
fine, routes globally fine, then aborts the entire design in detailed routing with
`DRT-0073 No access point`. That is a hard abort, not a DRC — nothing downgrades it, and
it costs an hour of flow to discover.

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

### Draw every port at least 210 nm across

Touching a track is not enough. The wire that runs onto the port still has to get *down*
to it, and every `ViaN` in `sg13g2_tech.lef` is a 190 nm cut enclosed by **290 x 210 nm**
on the metal below, in either orientation. A via may hang off the port — its enclosure
only has to overlap it — but only onto Metal1 that no other net comes within 180 nm of
(`M1.b`). In a squeezed channel there is no such Metal1, so the port itself has to hold
the via.

This is how the second attempt failed. `AION_a21oi_nor2_1`'s `O0` was grown to
`y = 1090 … 1270` to reach the track at `1260` — on the grid, and 180 nm across, so a via
still had nowhere to go and detailed routing still aborted on every instance of the cell.
That is 30 nm short, and it is the whole difference.

`M1.a` min width is 160 nm, so a port drawn at minimum width is **never** enough on its
own: widen it where the via goes. Same on Metal2 — `M2.a` min width is 200 nm, 10 nm under
the rule, so a minimum-width strap is fine as a wire and not as a port.

### Nothing may sit on the port's via landing

To the router, every shape in the LEF that is not this pin's `PORT` belongs to another
net: the cell's `OBS` and every other pin. `AION_nand2_o21ai_0` died on that. It routes
`O0` up to Metal2 correctly, but the label sits on the Metal1 end, and the strap was
exported as

```
OBS
  LAYER Metal2 ;
    RECT 1.835 0.950 2.035 2.650 ;   <- parked on top of PIN O0
```

— a legal-looking Metal1 port with an obstruction exactly where its `Via1` would go.

A `Cell` keys ports by name, so **a net gets one port rectangle**; you cannot label both
ends. So either put the port on the layer that has the room, with `draw_m2_pin` — the
strap then *is* the port — or keep Metal2 off the Metal1 port so the via up has somewhere
to land.

"Off" means **210 nm clear** (`M2.b`), not merely not overlapping: the via's Metal2 pad
(290 x 200 nm) is a Metal2 shape like any other. `AION_mux2i_1/I2` has another net's
Metal2 riser 15 nm beside each gate pad, and Metal1 of other nets crowding everywhere a via
could slide to — no access point, `DRT-0073`. `AION_mux2_0/I0` has a strap 5 nm to the
right of its port too, but free Metal1 on the left, and the router put its `Via1` 60 nm
off the port with the pad 265 nm clear of the strap: the first pin is unroutable, the
second routes on all 126 instances.

`make verify` writes the LEF with magic and grades it the way `make export` and `make pnr`
do, so an unreachable pin fails inside the `edit → verify` loop. What the check requires is
that **some `ViaN` overlaps the port with its Metal1 enclosure 180 nm clear of other nets'
Metal1 and its Metal2 pad 210 nm clear of other nets' Metal2**. Covering a track and being
210 nm across are the way to get there without thinking about it, not the rule itself.
All 283 signal pins of the PDK `sg13g2_stdcell` library pass.

### Then TritonRoute has the last word

That rule is necessary, not sufficient: it accepts any via position that is legal, and
TritonRoute only tries some — tracks, half tracks, the pin centre, positions aligning the
enclosure with the pin. So `make verify` also places the LEF in an `N` and an `FS` row
between PDK cells and runs OpenROAD's `pin_access`, the stage that aborts step 7 with
`DRT-0073`. A reason starting `abstract (TritonRoute): PIN X:` means the router itself found
no way in, even if no static reason names the pin — give the via room where TritonRoute
looks: widen the port across a track, and clear the metal beside it on its layer and the
one above. Step 6 runs the same check again before it publishes the cell.

The LEF the router reads now declares your `Via1` cuts too (magic writes none; the
exporter adds them from the GDS). Before that, TritonRoute could not see a cell's own via
and dropped its access via right beside it: `AION_xnor2_1/I0` came back from step 7 as a
`V1.a` violation. With the cut declared it enters that pin on Metal2 instead — there is
nothing to draw differently for this.

The exporter also publishes any part of a signal pin's Metal2 within 565 nm of a rail
line as `OBS`, because the power grid's rail via pads sit there and the router must not
land beside them. You draw nothing differently for this either, but the checks read `OBS`
as another net. A reason naming an `OBS` Metal2 rectangle at `y < 565` (or `> 3215`) nm
may be your own pin's bar: then give that pin its access and its two ways up above the
band.

## Rail tap contacts go at `x = 160 + 480k`

Rows are placed **mirrored and abutted**, so a cell's VSS rail is the same silicon as the
VSS rail of the row below it. The tap `Cont` cuts of both cells land in one band, and they
have to be the *same rectangles*: either exactly on top of each other, or far enough
apart. Partly on top of each other is neither, and it is a DRC error in both decks.

Every one of the 2497 rail tap contacts across all 84 PDK `sg13g2_stdcell` cells sits at

```
x = 160 + 480k  ..  320 + 480k        one 160 nm cut per CoreSite, centred in it
```

with no exception. Put yours anywhere else and every abutment in the design is a
violation. The first two AION cells used `TAP_CONT_X = [150 + 430 * k ...]` and the placed
design came back with **10322 Magic and 2872 KLayout errors** — `Cnt.b`, `CntB.a1`, and
Magic's "this layer can't abut or partially overlap between subcells" — while both cells
were individually DRC-clean. The 480 − 430 = 50 nm beat is visible in the violation
widths: 50, 100, 150, 200, 250 and 300 nm, about 557 of each.

So for a cell `CELL_W` wide:

```python
TAP_CONT_X = [240 + 480 * k for k in range(CELL_W // 480)]   # contact centres
```

Nothing else lives in that band — the Metal1 rail and the tap Activ both span the full
cell width — so moving the contacts onto the grid is self-contained.

`make verify` checks this from the GDS. It is the same shape of problem as the two above:
invisible in a cell on its own, fatal once it has neighbours.

## Leave room for the power grid and the neighbour

Two more things a placed cell meets that a cell on its own never does. Both were found in
one step-7 run whose cells were all DRC-clean, LVS-clean and pin-access clean on their own.

**Metal2 and above stay 355 nm clear of both rails.** Wherever a vertical power strap
crosses a row — and it can cross anywhere along your cell — the PDN drops a via stack onto
the VDD and VSS rails. Its pads are centred on the rail line: 290 nm tall on Metal2 and
Metal4, 200 nm on Metal3, 620 nm on Metal5. So your metal has to keep the pad's half-height
plus the layer's spacing from `y = 0` and from `y = 3780`:

| layer | keep inside y (nm) |
|---|---|
| `Metal2`, `Metal4` | `355 … 3425` (145 + 210) |
| `Metal3` | `310 … 3470` (100 + 210) |
| `Metal5` | `520 … 3260` (310 + 210) |

Seven AION cells drew a horizontal Metal2 bar at `y = 110 … 310` to join two gate risers.
Where the bar overlapped the pad it **shorted the net to VSS: 130 nets in one chip**. Where
it came close without touching it was 111 `M2.b` errors. `AION_mux2_0` put its Metal2 at
`y = 200` and got the spacing errors only. Shift such a bar up so it starts at `y = 355` or
higher; it now crosses more of the Metal1 below it, so let `make verify` re-grade pin access
— and it now sits closer to whatever pin it wraps, so read the next section before you do.

**Every metal keeps half its spacing from the left and right edges**: Metal1 90 nm, Metal2
and up 105 nm, so `x = 90 … CELL_W − 90` on Metal1. The cell abutted beside yours only keeps
the other half. `AION_xnor2_xor2_7` ran its `O1` output to `x = 7670` in a 7680 nm cell and
got 50 `M1.b` errors against the PDK cells placed next to it. The VDD/VSS rails are the
exception: they run edge to edge on purpose, to join the neighbour's. A supply *stub* is
not exempt — `x = 90` applies to it too.

`make verify` grades both on the LEF magic writes, as `make export` and `make pnr` do. All 84
PDK `sg13g2_stdcell` cells pass both.

## Give every pin two ways up

A pin the router can *reach* can still be one it cannot get *out of*. Follow a wire of the
pin's net from its port along free Metal1 and Metal2 — its centre `spacing + width/2` clear of
every other net (Metal1 260 nm, Metal2 310 nm), through a `Via1` wherever both of its metal
shapes clear the other nets — and count the Metal3 tracks `y = n * 420` nm on which a `Via2`
fits: Metal2 enclosure 290 × 210 nm, 210 nm clear of other nets' Metal2. **Every signal pin
needs at least two.**

After the bars above were lifted to `y = 355`, `AION_xor2_5` (I0, I2), `AION_xor2_8` (I0) and
`AION_xnor2_xor2_9` (I1) each had an inner pin in a box: below it the U-shaped Metal2 of the
pin beside it, its bar now at `y = 360 … 560`; above it an obstruction bar at `y = 1970`. The
bar's new height took the Via2 off `y = 840`, leaving `y = 1260` as the only way up.
Detailed routing **stalled at ~400 Metal2 shorts for 60+ iterations, at every die size** — it
kept shorting through the neighbour's bar. The same placement with the bars back at `y = 110`
(two tracks) routed to zero. DRC, LVS and pin access are clean on every one of these cells.

`make verify` reports it as `PIN X can put a Via2 on 1 Metal3 track …`, names the track the
pin has and, for each track next to it, the shape that keeps the via off. To fix it, open a
second track:

- move that shape — in `AION_xor2_5`, lifting the obstruction bar from `y = 1970` to `1995`
  opens `y = 1680` (`1680 + 105 + 210 = 1995`) and keeps the U bar out of the rail band; or
- run the pin's own Metal2 out of the box, so its wire is not walled in at all.

A slot exactly one wire wide (Metal1 `180 + 160 + 180 = 520` nm between two shapes) does not
count as a way out. Pins drawn on Metal3 or above are not graded. All 283 signal pins of the
PDK library reach eight tracks.

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
- **Leave the rail via band and the side edges free**: Metal2 inside `y = 355 … 3425` nm
  (Metal3 `310 … 3470`, Metal5 `520 … 3260`), and every metal at least half its spacing
  from the left and right edges — 90 nm on Metal1, 105 nm above — rails excepted. Miss it
  and the placed design shorts nets to VSS under the power grid's vias or fails spacing
  against its neighbours, while this cell verifies clean on its own. `make export` refuses
  to publish a cell that fails it.
- **Give every signal pin a Via2 on at least two Metal3 tracks**, reachable from the pin
  along free Metal1 and Metal2. A pin boxed in by other nets' Metal2 with one track out
  stalls detailed routing at hundreds of shorts, however long it runs. `make export` refuses
  to publish a cell that fails it.
- **The Verilog model is solved from the netlist, not written by you.** `make export`
  derives the cell's function from the transistor netlist, checks it against the
  `function` the characterizer measured in SPICE, and refuses to publish anything when
  the two disagree or when the netlist has no truth table (feedback, a node nothing
  drives). A refusal there is a real finding about the cell — do not work around it.
