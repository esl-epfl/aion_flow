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

Instances whose name matches `RSZ_DONT_TOUCH_RX` (`^ai_.*` by default, see
`implementation/config.json`) are hidden from the resizer, so it will not size
or buffer them away.
