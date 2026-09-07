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

Note that this is a *necessary* condition, not a sufficient one — a port can
cover a track and still be unroutable once the neighbours' obstructions are
in play. It is the half that can be checked from the abstract alone.
