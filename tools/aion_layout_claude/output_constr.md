# AI-generated standard cells

Drop the views of each custom cell in here. `make pnr` discovers them by file
stem and wires them into LibreLane as `EXTRA_LEFS`, `EXTRA_LIBS`, `EXTRA_GDS`,
`EXTRA_VERILOG_MODELS`, `EXTRA_SPICE_MODELS` and `EXTRA_CDLS`.

Any layout works — discovery is a recursive walk grouped by stem:

```
cells/foo.lef                      flat
cells/foo/foo.lef                  one directory per cell
cells/lef/foo.lef                  one directory per view
```

## Required per cell

| View    | Extensions                  | Used for                           |
| ------- | --------------------------- | ---------------------------------- |
| LEF     | `.lef`                      | placement, routing blockages, pins |
| Liberty | `.lib`                      | STA and the resizer                |
| GDS     | `.gds`, `.gds.gz`, `.gdsii` | streamout                          |

## Recommended

| View    | Extensions                      | Used for              |
| ------- | ------------------------------- | --------------------- |
| Verilog | `.v`, `.sv`                     | gate-level simulation |
| SPICE   | `.spice`, `.spi`, `.sp`, `.cir` | LVS                   |
| CDL     | `.cdl`                          | LVS                   |

## What the LEF must satisfy

`make pnr` refuses to start (unless `LENIENT=1`) if a cell breaks any of these,
because none of them fail until detailed placement otherwise:

- `CLASS CORE ;` — anything else makes OpenROAD treat the cell as a macro
- `SITE CoreSite ;`
- height exactly `3.78` um (one `CoreSite` row)
- width an exact multiple of `0.48` um (the `CoreSite` pitch)
- `PIN VDD` and `PIN VSS` present, so the PDN can strap it
- **every signal pin can be entered by a via** — some `ViaN` overlaps one of
  its routing-layer port rectangles with its enclosure, and keeps its metal
  shapes clear of every other net (the `OBS` and the other pins): 0.18 um on
  `Metal1`, 0.21 um on `Metal2`..`Metal5`. The via may hang off the port.
- **metal leaves room for the PDN's rail vias**: `Metal2` and `Metal4` inside
  `y = 0.355 .. 3.425` um, `Metal3` inside `0.310 .. 3.470`, `Metal5` inside
  `0.520 .. 3.260` — pins and `OBS` alike
- **metal leaves room for the neighbour**: every routing metal at least half its
  spacing from `x = 0` and from the cell width — 0.09 um on `Metal1`, 0.105 um
  on `Metal2`..`Metal5`. The `VDD`/`VSS` rails are exempt.
- **every signal pin has two ways up**: from the port, along free `Metal1` and
  `Metal2` and through a `Via1` wherever it clears the other nets, a `Via2` fits
  on at least two `Metal3` tracks `y = 0.42k` um

The two sections below are how to draw pins that meet the via rule without
thinking about it: put them on a track, and make them wide enough to hold the
via. Neither is the rule itself — TritonRoute reaches ports that miss the grid
or are 0.18 um across when the via has free metal to hang onto — but the pins
that failed in this flow were squeezed between other shapes, where there is
none.

## Put every signal pin on a routing track

This is the rule that does not fail at placement. A cell whose pin cannot be
reached places fine, routes globally fine, and then aborts the whole design in
detailed routing:

```
[ERROR DRT-0073] No access point for _AION_129_/O0 (AION_a21oi_nor2_1).
```

`DRT-0073` is a hard abort inside pin access, not a DRC checker — `LENIENT=1`
does not downgrade it.

The tracks come from `libs.tech/librelane/sg13g2_stdcell/tracks.info`: every
Metal has vertical lines at `x = n * 0.48` um and horizontal lines at
`y = n * 0.42` um. A wire runs *along* its layer's preferred `DIRECTION`
(`sg13g2_tech.lef`), so it can stop at any coordinate on that axis but is
pinned to a track on the other one:

| Layer    | `DIRECTION` | Draw a pin on it across  |
| -------- | ----------- | ------------------------ |
| `Metal1` | HORIZONTAL  | a `y = n * 0.42` line    |
| `Metal2` | VERTICAL    | an `x = n * 0.48` line   |
| `Metal3` | HORIZONTAL  | a `y = n * 0.42` line    |
| `Metal4` | VERTICAL    | an `x = n * 0.48` line   |
| `Metal5` | HORIZONTAL  | a `y = n * 0.42` line    |

So a `Metal1` port must be tall enough, and placed such that a multiple of
0.42 falls inside it. `Metal1` minimum width is 0.16 um and minimum spacing is
0.18 um, which leaves a 0.16-tall port only 10 nm of slack against a 0.42
pitch — a port squeezed into a channel between two other `Metal1` shapes will
miss the grid unless it was placed against the track deliberately. Both AION
cells drawn in the first pass did exactly that, topping out at `y = 1.250`
with the track at `y = 1.260`.

Two ways out when the port cannot grow where it sits:

- move the neighbouring `Metal1` so the port can reach the track, the way the
  PDK cells do (`sg13g2_a21oi_1`'s `Y` is a multi-rect stub spanning
  `y = 0.72 .. 3.16`, crossing six tracks)
- drop a `Via1` and put the port on `Metal2` instead, where the rule becomes
  an `x = n * 0.48` line

Cells are cheaper to check than to re-route: `make verify` and `make export`
grade pin access on the LEF magic writes, and `make pnr` refuses to start. All
283 signal pins of the PDK `sg13g2_stdcell` library pass.

## Covering a track is not enough: the via has to land

Growing a port until it just touches a track is how the second pass failed.
`AION_a21oi_nor2_1`'s `O0` came back as `RECT 2.150 1.090 2.550 1.270` — it
does contain the track at `y = 1.260`, and detailed routing still aborted with
`DRT-0073` on every instance of the cell. A wire that runs onto a port still
has to get *down* to it, and 0.18 um leaves nowhere to put the via.

Every `ViaN` (N = 1..4) in `sg13g2_tech.lef` is a 0.19 um cut enclosed by
**0.29 x 0.21 um on the metal below**, in either orientation. The enclosure
may hang off the port — `sg13g2_nand4_1`'s `A` relies on that, its widest port
`RECT` being 0.275 um — but only onto `Metal1` no other net comes within
0.18 um of, and a port squeezed into a channel has none. So:

> draw a port `RECT` at least **0.21 um across in both directions**.

That is 0.05 um more than the `Metal1` minimum width, so a port drawn at
minimum width is never enough on its own — it has to be widened where the via
goes, which is what the PDK cells do (`sg13g2_inv_1`'s `Y` is 0.23 um across
and 2.565 um long, crossing six tracks).

## Nothing may sit where the via lands

To the router, every shape in the LEF that is not the pin's own `PORT`
belongs to another net — the `OBS` and every other pin. `AION_nand2_o21ai_0`
failed on that. It routes `O0` up to `Metal2` correctly, but the label is on
the `Metal1` end, and the strap came out as

```
OBS
  LAYER Metal2 ;
    RECT 1.835 0.950 2.035 2.650 ;   <- sits exactly on top of PIN O0
```

and the router had a legal-looking `Metal1` port with an obstruction parked
where its via would have gone.

A `Cell` keys its ports by name, so **a net gets exactly one port rectangle**
— labelling both ends is not something the model can express. The two ways
out are therefore:

- declare the port on the layer where the metal has the room, so the strap
  *is* the port: `cell.add_port(Port("O0", "O0", tech["Metal2"], strap))` —
  note that a strap drawn at the `Metal2` minimum width of 0.20 um is 10 nm
  under the landing-pad rule above, so draw it 0.21 um wide when it is a port
- keep the upper metal off the port, so the via up has somewhere to go

"Off" means **0.21 um clear**, not merely not overlapping: the via's `Metal2`
pad is a `Metal2` shape like any other. `AION_mux2i_1/I2` has another net's
`Metal2` riser 15 nm beside each of its gate pads, with other nets' `Metal1`
everywhere a via could slide to, and detailed routing finds no access point.
`AION_mux2_0/I0` has a strap 5 nm beside its port as well, but free `Metal1`
on the other side: the router puts its `Via1` 60 nm off the port, the pad
0.265 um from the strap, and routes every instance.

## Rail tap contacts go at `x = 160 + 480k`

Rows are placed mirrored and abutted, so a cell's VSS rail is the same silicon as
the VSS rail of the row below it, and the tap `Cont` cuts of both cells land in
one band. They have to be the *same rectangles* — coincident, or far enough
apart. Partly on top of each other is neither.

All 2497 rail tap contacts of all 84 PDK `sg13g2_stdcell` cells sit at
`x = 160 + 480k .. 320 + 480k`: one 160 nm cut per `CoreSite`, centred in it, no
exception. `AION_a21oi_nor2_1` and `AION_nand2_o21ai_0` used `150 + 430k`, and
the placed design came back with 10322 Magic and 2872 KLayout errors (`Cnt.b`,
`CntB.a1`, and "this layer can't abut or partially overlap between subcells")
with both cells individually DRC-clean.

```python
TAP_CONT_X = [240 + 480 * k for k in range(CELL_W // 480)]   # contact centres
```

## Metal2 stays out of the rail via band

Wherever a vertical `TopMetal1` power strap crosses a row, the PDN drops a via
stack onto the `VDD` and `VSS` rails, and a strap can cross anywhere along a
cell. The pads are centred on the rail line — measured in step 7's GDS,
`VIA_via1_2_2200_440_1_5_410_410` and up:

| Layer              | Pad height | Keep out, from each rail line |
| ------------------ | ---------- | ----------------------------- |
| `Metal2`, `Metal4` | 0.29 um    | 0.145 + 0.21 = **0.355 um**   |
| `Metal3`           | 0.20 um    | 0.100 + 0.21 = **0.310 um**   |
| `Metal5`           | 0.62 um    | 0.310 + 0.21 = **0.520 um**   |

Seven AION cells (`AION_xnor2_1`, `_xnor2_4`, `_xnor2_xor2_2/7/9`, `_xor2_5`,
`_xor2_8`) joined two gate risers with a `Metal2` bar at `y = 0.110 .. 0.310`.
The placed chip came back with **130 nets shorted to VGND** — every overlap of a
bar with a pad — and 111 `M2.b` / 4 `M2.a` errors where they came close without
touching. `AION_mux2_0`, at `y = 0.200`, got only the spacing errors. Every one
of those cells was DRC- and LVS-clean on its own. No PDK cell draws `Metal2`
anywhere near a rail.

## Metal keeps half its spacing from the side edges

A cell abutted to the left or right is held to half the spacing on its side, so
yours has to keep the other half: **0.09 um** of `Metal1`, **0.105 um** of
`Metal2`..`Metal5`, from `x = 0` and from `x = width`. `AION_xnor2_xor2_7`'s
`O1` ran to `x = 7.670` in a 7.680 um cell and the placed chip had 50 `M1.b`
errors against the PDK cells beside it; the PDK library keeps at least 0.105 um.
The `VDD`/`VSS` rail rectangles are exempt — they run edge to edge to join the
neighbour's — but a supply stub leaving the rail is not.

## Every signal pin has two ways up

A wire of the pin's net may run on `Metal1` and `Metal2` wherever its centre is
spacing plus half its width clear of every other net's metal — 0.26 um on
`Metal1`, 0.31 um on `Metal2` — and along the pin's own metal, and may change
layer through a `Via1` wherever both of the via's metal shapes clear the other
nets. From everything reachable that way, a `Via2` (its `Metal2` enclosure
0.29 x 0.21 um, 0.21 um clear of other nets) has to fit on **at least two**
distinct `Metal3` tracks `y = 0.42k` um. A gap exactly one wire wide between two
shapes is not followed, and pins drawn on `Metal3` or above are not graded.

After the rail rule moved their `Metal2` bars from `y = 0.11` to `0.36` um,
`AION_xor2_5` (I0, I2), `AION_xor2_8` (I0) and `AION_xnor2_xor2_9` (I1) each
boxed an inner pin between the pin beside it (a U of `Metal2`) and an
obstruction bar at `y = 1.97` um, with a `Via2` fitting on `y = 1.26` only.
Step 7's detailed routing plateaued at ~415 violations — `Metal2` shorts through
the neighbour's bar — for 60+ iterations at every die size, with 433 of the 498
markers at iteration 10 on those three cells. On the same placement, the
abstracts with the bars at `0.11` um (a second track at `y = 0.84`) routed to 0
violations by iteration 8. Lifting the obstruction bar to `y = 1.995` opens
`y = 1.68` and satisfies both rules. All 283 signal pins of the PDK library reach
eight tracks.

## What is checked, and where

`make verify` grades the ports a generator declares, the metal it draws over
them, **its rail tap contacts, the metal it leaves near the rails and the
side edges, and the ways up out of every pin**, so a cell can be fixed inside the
drawing loop; `make export` grades the LEF magic actually wrote and refuses to
publish; `make pnr` refuses to start. All 283 signal pins and all 2497 rail tap
contacts of the PDK `sg13g2_stdcell` library pass all of it, and all 84 of its
cells pass the rail band and side-edge rules.

Pin access is also graded by **TritonRoute itself**. `make verify` places the
LEF in an `N` and an `FS` row between two `sg13g2_inv_1` and runs OpenROAD's
`pin_access` — the stage that aborts step 7 with `DRT-0073` — and step 6 runs
it again (`make pin-access`) on the exported LEF before copying the cell into
`implementation/cells/`. On the cells published so far it agrees with step 7:
every pin of the ten mined cells is reached, and `AION_mux2i_1/I2` and
`AION_mux2i_2/I2` are not.

## Via cuts are in the LEF

Magic's `lef write` emits no cut layers, so the exporter reads every
`Via1`..`Via4` cut out of the GDS and writes it into the LEF — into a pin's
`PORT` when that pin covers it on both metals, into `OBS` otherwise — and
refuses a LEF whose cut count differs from the GDS. Without them TritonRoute
landed an access `Via1` on a track crossing 0.19 um from the cell's own on
`AION_xnor2_1/I0` and `AION_xnor2_xor2_2/I0`, and the merged cuts were `V1.a`
in the placed chip. With them declared, `pin_access` enters both pins on
Metal2, and no preferred Metal1 access via of the ten mined cells comes within
`V1.b` of a cell cut.

## Pin metal near the rails is published as obstruction

The exporter also writes the part of every signal pin's `Metal2` within
**0.565 um** of a rail line (the Metal3 track at `y = 0.42` plus half a 0.29 um
Via2 enclosure) to `OBS`, and keeps the rest in the pin. Nothing is redrawn and
the metal is still the pin's net; the router just does not land there. Under a
power strap the PDN puts a 0.29 um `Metal2` via pad on the rail line, and a
router wire or `Via2` on a pin bar at `y = 0.355 .. 0.555` reaches within 0.17 um
of it. After the rail rule lifted the xor/xnor bars to 0.355, that was all 14
violations step 7's detailed routing never cleared: 13 of 164 such bars under a
strap failed, none of the 1264 elsewhere. Swapped onto the same placement,
abstracts split this way routed to 0 violations by iteration 7, and the unsplit
ones stayed at 23. Because a check here reads `OBS` as another net, a problem
can name an `OBS` rectangle in that band that is really your own pin's metal.

These are *necessary* conditions, not sufficient ones — a port can satisfy
every one of them and still be unroutable once the neighbouring instances'
obstructions are in play. They are the half that can be checked from the
abstract alone, and the half that has actually taken this flow down.
