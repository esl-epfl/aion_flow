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
- **every signal pin covers a routing track** — see below
- **every signal pin has room for a via to land on it** — see below

## Every signal pin must cover a routing track

This is the one that does not fail at placement. A cell whose pin misses the
grid places fine, routes globally fine, and then aborts the whole design in
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

| Layer    | `DIRECTION` | A pin on it must contain |
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

Cells are cheaper to check than to re-route: `make export` grades this and
refuses to publish, and `make pnr` refuses to start. All 283 signal pins of
the PDK `sg13g2_stdcell` library satisfy it.

## Covering a track is not enough: the via has to land

Growing a port until it just touches a track is how the second pass failed.
`AION_a21oi_nor2_1`'s `O0` came back as `RECT 2.150 1.090 2.550 1.270` — it
does contain the track at `y = 1.260`, and detailed routing still aborted with
`DRT-0073` on every instance of the cell. A wire that runs onto a port still
has to get *down* to it, and 0.18 um leaves nowhere to put the via.

Every `ViaN` (N = 1..4) in `sg13g2_tech.lef` is a 0.19 um cut enclosed by
**0.29 x 0.21 um on the metal below**, in either orientation. The long side
lies along the wire and may hang off the end of the port onto the rest of the
net — `sg13g2_nand4_1`'s `A` relies on that, its widest port `RECT` being
0.275 um. The short side may not. So:

> a port `RECT` must be at least **0.21 um across in both directions**.

That is 0.05 um more than the `Metal1` minimum width, so a port drawn at
minimum width is never enough on its own — it has to be widened where the via
goes, which is what the PDK cells do (`sg13g2_inv_1`'s `Y` is 0.23 um across
and 2.565 um long, crossing six tracks).

## Nothing may sit where the via lands

`make export` runs `lef write -hide -pinonly`, which writes **only the
labelled rectangle as a `PORT` and every other shape as `OBS`** — the rest of
the port's own net included. `AION_nand2_o21ai_0` failed on that. It routes
`O0` up to `Metal2` correctly, but the label is on the `Metal1` end, so the
strap came out as

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

## What is checked, and where

`make verify` grades the ports a generator declares, the metal it draws over
them **and its rail tap contacts**, so a cell can be fixed inside the drawing
loop; `make export` grades the LEF magic actually wrote and refuses to publish;
`make pnr` refuses to start. All 283 signal pins and all 2497 rail tap contacts
of the PDK `sg13g2_stdcell` library pass all of it.

These are *necessary* conditions, not sufficient ones — a port can satisfy
every one of them and still be unroutable once the neighbouring instances'
obstructions are in play. They are the half that can be checked from the
abstract alone, and the half that has actually taken this flow down.
