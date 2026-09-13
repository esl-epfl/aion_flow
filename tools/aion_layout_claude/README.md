# `aion_layout`

`aion_layout` takes an AION transistor-level SPICE `.subckt` — the output of
[`aion_minimizer`](../aion_minimizer/README.md) — and produces a DRC/LVS-clean
IHP SG13G2 standard cell with `gds`/`lef`/`lib`/`v`/`spice`/`cdl` views, measured
against the same logic built by abutting the PDK standard cells it replaces.

The bar is *smaller and faster than that row*, and the tool's last act is to say
whether the cell cleared it. On the shipped example it clears half: 45.5 % smaller,
28.6 % slower, `COMPARE: LOSS`. See [The comparison](#the-comparison).

A model draws the cell: it writes one Python generator and edits it until the
tools stop complaining. Every other step — DRC, LVS, PEX, area, characterization,
the view export and the comparison — is `make`, and stays `make`.

## Contents

- [Quick start](#quick-start)
- [The division of labour](#the-division-of-labour)
- [The flow, step by step](#the-flow-step-by-step)
- [The comparison](#the-comparison)
- [The exported views](#the-exported-views)
- [Project structure](#project-structure)
- [Fail closed](#fail-closed)
- [Known gaps](#known-gaps)

## Quick start

Everything runs from this directory, with the `iic-osic-tools` container up. The
`Makefile` defaults to the shipped worked example, so the first two commands take
no arguments at all:

```bash
cd tools/aion_layout_claude
make help          # every target, and the current value of every variable
make verify        # build + DRC + LVS, and the graded verdict
```

`make verify` builds `build/AION_inv_nand2_nor2_1/AION_inv_nand2_nor2_1.gds` from
`cells/AION_inv_nand2_nor2_1.py`, runs Magic DRC, KLayout DRC and Netgen LVS,
measures the footprint, and prints one verdict block. This is that block, as it
really comes out (one further line above it names the report file it wrote):

```
  cell        AION_inv_nand2_nor2_1
  Magic DRC   clean - 0 violation(s) (tool reported 0)
  KLayout DRC clean - 0 violation(s) (tool reported 0); completeness verified
    receipt matches: all 1 rule database(s) the run wrote were read
  LVS         clean - match_uniquely; devices 8/8; nets 9/9
    Circuits match uniquely.
    sg13_lv_nmos: layout 4 vs netlist 4
    sg13_lv_pmos: layout 4 vs netlist 4
  geometry    AION_inv_nand2_nor2_1: 2.880 x 3.780 um = 10.8864 um^2 (6 sites, from prBoundary)
RESULT: PASS
```

Every line is indented except the last. That is deliberate: exactly one line
starts at column 0 and it is the verdict, so no fragment of tool output can ever
be read as one. `grep '^RESULT:'` is a safe test, and so is the exit status —
**0 PASS/WIN, 1 FAIL/LOSS, 2 ERROR** (the step could not run), the same three
everywhere in the tool.

Once a cell passes, the rest of the flow is one command:

```bash
make flow          # verify, PEX, baseline, characterize both, export, compare
```

It ends in one `COMPARE:` line and exits 1 on a `LOSS`, so `make` reports
`Error 1` for a cell that is merely not better than the row it replaces. That is
the intended behaviour, not a broken run: the views are exported before the
comparison, so a losing cell still leaves a complete `final/` behind.

For any other cell, override the variables it needs:

```bash
make verify CELL=AION_foo_1 NETLIST=path/to/AION_foo_1_minimized.spice
make flow   CELL=AION_foo_1 NETLIST=path/to/AION_foo_1_minimized.spice \
            BASELINE=path/to/AION_foo.spice
```

**Where the outputs land.** Everything for one cell goes under
`$(BUILD_DIR)`, which is `build/<cell>/` by default:

```text
build/<cell>/
├── <cell>.gds              the layout
├── <cell>.png              make png only
├── <cell>.report.md        the verdict block above, as written
├── <cell>.evidence.md      make evidence
├── <cell>.compare.md/.json make compare
├── drc/                    Magic and KLayout reports, and the KLayout receipt
├── lvs/                    Netgen report and the extracted netlist
├── pex/<cell>_pex3.spice  the R+C extracted netlist
├── char/*.lib              Liberty, one file per corner
├── baseline/               the abutted row: gds, drc/, lvs/, pex/, char/
└── final/                  the exported views -- this is what ships
```

## The division of labour

```
  AION .subckt  ──►  make scaffold  ──►  cells/<cell>.py
                                              │
                                   ┌──────────┴──────────┐
                                   │   the model edits   │   ← the only hand step
                                   │      this file      │
                                   └──────────┬──────────┘
                                              │
      ┌──────────────────────────── make verify ────────────────────────────┐
      │  build GDS ─► Magic DRC ─► KLayout DRC ─► Netgen LVS ─► measure     │
      └────────────────────────────────┬────────────────────────────────────┘
                                       │  RESULT: PASS | FAIL | ERROR
                     FAIL  ──►  make evidence  ──►  back to the editor
                                       │  PASS
      ┌───────────────────────────── make flow ─────────────────────────────┐
      │  PEX ─► baseline: abut the PDK cells, DRC, LVS, PEX                 │
      │      ─► characterize both ─► export the views ─► compare            │
      └────────────────────────────────┬────────────────────────────────────┘
                                       │  COMPARE: WIN | LOSS
                              build/<cell>/final/
```

The model does exactly one thing: it writes `cells/<cell>.py`, a module exposing
`generate(name, tech) -> Cell`. It reads `make evidence` — eight titled blocks:
the target netlist, the verdict, DRC items with coordinates, the LVS digest, a
layout digest carrying the per-layer inventory and a cross-net overlap table
that names shorts by coordinate, the geometry, the design rules, and one PDK
cell as a worked example — then edits, and runs `make verify` again.
[`SKILL.md`](SKILL.md) is the instruction sheet it works from: the floorplan
method, the vertical skeleton, the rules that bite and their numbers.

**No verification, extraction, export or comparison step involves a model, and
none is meant to.** Those steps have exactly one right answer. Whether a Magic
report carries `[INFO] COUNT: 0`, whether the prBoundary is 2880 nm wide, whether
Netgen printed `Circuits match uniquely.` — a model asked those questions can
only agree with the file or disagree with it, and only the second outcome is new
information. Deciding *where to put a rectangle* is the opposite kind of problem:
there are many good answers, the search is over a floorplan, and a model is
genuinely useful. The boundary is drawn there and nowhere else.

The practical consequence is the one that matters next month: every graded step
re-runs with no model, no API key and no network. `make verify` and `make flow`
are plain `make`, and their exit statuses are the verdict.

## The flow, step by step

Every flow target is one call to `python3 -m aion_layout` and nothing else — the
CLI owns the logic, the `Makefile` owns the paths. A target that composed
several steps in shell would be a second implementation of the flow, free to
disagree with the one the CLI runs. (`help`, `test` and `clean` are not flow
targets and do not call it; `drc`, `lvs`, `pex` and `png` first rebuild the GDS,
because they list `gds` as a prerequisite.)

No `aion_layout` call is `@`-silenced, and nowhere in the file is a recipe line
prefixed with `-` or suffixed with `|| true`, so the command that produced a
result is readable above it and a non-zero status always stops the chain. The
only `@` lines are `help`'s own `echo`s and the input guards on `characterize`,
`compare` and `export`, which exist to *stop* a target, never to let one
continue: each is a `test -n` on a wildcard that must have matched something,
and each exits 2 with a message naming the target to run first.

`aion_layout` below is `python3 -m aion_layout`, and the `$(...)` are the
variables in the table further down. Three of them are discovered rather than
set: `PEX_SPICE` matches whatever the extractor named its netlist, and
`CANDIDATE_LIB` / `BASELINE_LIB` prefer the `typ` corner on both sides, because
a comparison whose two halves came from different corners would decide the
result by accident. Those are the three wildcards the guards above cover.

| Target | Command behind it | Produces | Where |
|---|---|---|---|
| `help` | — | every target, and the current value of every variable | stdout |
| `resize` | `aion_layout resize $(NETLIST) -o $(RESIZED) --cell $(CELL) --baseline $(BASELINE) --min-depth $(MIN_DEPTH) --report ...` | a NEW netlist whose series stacks are widened and folded, and the report saying what changed and why | `<cell>s.spice` and `build/<cell>/<cell>.resize.md` |
| `scaffold` | `aion_layout scaffold $(NETLIST) -o $(CELL_MODULE) --cell $(CELL)` | a starting generator that imports and runs | `cells/<cell>.py` |
| `gds` | `aion_layout build $(CELL_MODULE) --cell $(CELL) -o $(GDS)` | the layout | `build/<cell>/<cell>.gds` |
| `png` | the same, plus `--png $(PNG)` | a rendering of it | `build/<cell>/<cell>.png` |
| `drc` | `aion_layout drc $(GDS) -w $(BUILD_DIR)/drc --cell $(CELL)` | Magic and KLayout reports, and the KLayout receipt | `build/<cell>/drc/` |
| `lvs` | `aion_layout lvs $(GDS) $(NETLIST) --cell $(CELL) -w $(BUILD_DIR)/lvs` | the Netgen report and the extracted netlist | `build/<cell>/lvs/` |
| `verify` | `aion_layout verify $(CELL_MODULE) --cell $(CELL) --netlist $(NETLIST) -w $(BUILD_DIR) --report ...` | `RESULT: PASS\|FAIL\|ERROR`, plus everything `drc` and `lvs` produce | stdout and `build/<cell>/<cell>.report.md` |
| `evidence` | `aion_layout evidence --cell $(CELL) --netlist $(NETLIST) --gds $(GDS) --module $(CELL_MODULE) -o ...` | the packet the model reads between edits | `build/<cell>/<cell>.evidence.md` |
| `pex` | `aion_layout pex $(GDS) --cell $(CELL) -w $(PEX_DIR) --mode $(PEX_MODE)` | the extracted netlist (Magic; mode 3 = R+C by default) | `build/<cell>/pex/<cell>_pex<mode>.spice` |
| `baseline` | `aion_layout baseline $(BASELINE) -o $(BASELINE_DIR) --verify --pex --characterize` | the abutted PDK row, verified, extracted and characterized | `build/<cell>/baseline/` |
| `characterize` | `aion_layout characterize $(PEX_SPICE) --cell $(CELL) -o $(CHAR_DIR) --jobs $(JOBS) --area-gds $(GDS)` | Liberty, one file per corner | `build/<cell>/char/*.lib` |
| `compare` | `aion_layout compare --cell $(CELL) --baseline-cell $(BASELINE_CELL) --candidate-lib ... --baseline-lib ... --candidate-gds ... --baseline-gds ...` | `COMPARE: WIN\|LOSS`, and the report behind it | stdout and `build/<cell>/<cell>.compare.{md,json}` |
| `export` | `aion_layout export --cell $(CELL) --gds $(GDS) --spice $(NETLIST) --lib ... --pex-spice $(PEX_SPICE) -o $(FINAL_DIR)` | the six views, with the LEF checked | `build/<cell>/final/` |
| `flow` | `aion_layout flow $(NETLIST) --cell $(CELL) --module $(CELL_MODULE) --baseline $(BASELINE) -o $(BUILD_DIR) --corners $(CORNERS) --jobs $(JOBS) --pex-mode $(PEX_MODE)` | all of the above in order, stopping at the first hard failure | `build/<cell>/` |
| `test` | `python3 -m pytest tests/ -q` | the host-side suite: no container, no PDK, seconds | stdout |
| `clean` | `rm -rf $(BUILD_DIR)` | | |

### Variables

| Variable | Default | Meaning |
|---|---|---|
| `CELL` | `AION_inv_nand2_nor2_1` | the cell being built |
| `CELL_MODULE` | `cells/$(CELL).py` | the generator the model writes |
| `NETLIST` | `AION_inv_nand2_nor2_1_minimized.spice` | transistor-level truth for LVS and device widths |
| `BASELINE` | `AION_inv_nand2_nor2.spice` | the gate-level netlist of the PDK cells to beat |
| `BUILD_DIR` | `build/$(CELL)` | everything for one cell lands here |
| `RESIZED` | `$(CELL)s.spice` | where `resize` writes; it never edits `NETLIST` |
| `MIN_DEPTH` | `2` | `resize` leaves stacks this deep and shallower alone |
| `CORNERS` | `typ` | `typ`, or `all` to add slow and fast |
| `JOBS` | `8` | parallel ngspice runs during characterization |
| `PEX_MODE` | `3` | parasitic extraction: 1 C-decoupled, 2 C-coupled, 3 full RC. Applied to both sides of a comparison — see below |
| `DRIVER` | *(empty)* | characterize against this cell instead of an ideal ramp; must be non-inverting |
| `DRIVER_IN` / `DRIVER_OUT` | `A` / `X` | its pins, defaulted to an `sg13g2_buf_*` |

`python3 -m aion_layout <command> --help` documents every flag; the `Makefile`
uses a subset of them.

## The comparison

"Smaller and faster" is measured against the **abutted baseline**: the same
logic, built out of the PDK standard cells the AION cell replaces, placed in one
row with the cells abutted and the inter-cell nets jumpered in Metal2. It is not
an estimate — it is a real layout, and it goes through the identical chain: the
same two DRC decks, the same Netgen LVS, the same Magic PEX at the same
`PEX_MODE` (3, full RC, unless lowered), the same corners, the same slew and
load grid, and the same stimulus. Any difference the report shows is a
difference between two cells, not between two methods.

For the worked example:

| | |
|---|---|
| candidate | `AION_inv_nand2_nor2_1_minimized.spice` — 8 transistors, one `.subckt` |
| baseline | `AION_inv_nand2_nor2.spice` — `sg13g2_inv_1` + `sg13g2_nand2_1` + `sg13g2_nor2_1` |

The corners are IHP's, and the slew/load grid is the PDK's own NLDM index, so a
Liberty file from here reads next to IHP's in one STA run:

| corner | model section | VDD | temperature |
|---|---|---:|---:|
| `typ` | `mos_tt` | 1.20 V | 25 °C |
| `slow` | `mos_ss` | 1.08 V | 125 °C |
| `fast` | `mos_ff` | 1.32 V | −40 °C |

The grid is 7 x 7: input slews 0.0186 … 2.5074 ns, output loads 0.001 … 0.3 pF.
`CORNERS=typ` (the default) characterizes the first row only; `CORNERS=all` does
all three.

### Area

Measured, not estimated. The two bold rows are the ones the comparison uses, and
both come from `metrics.gds_boundary` reading the prBoundary out of the GDS that
`make flow` built. The `abutted row` line is measured out of the row `make
baseline` actually builds, not summed by hand.

| | width | height | area | sites | source |
|---|---:|---:|---:|---:|---|
| `AION_inv_nand2_nor2_1` | 2.88 um | 3.78 um | **10.8864 um²** | 6 | prBoundary |
| `sg13g2_inv_1` | 1.44 um | 3.78 um | 5.4432 um² | 3 | prBoundary |
| `sg13g2_nand2_1` | 1.92 um | 3.78 um | 7.2576 um² | 4 | power-rail span |
| `sg13g2_nor2_1` | 1.92 um | 3.78 um | 7.2576 um² | 4 | prBoundary |
| abutted row | 5.28 um | 3.78 um | **19.9584 um²** | 11 | prBoundary |

The three middle rows are listed for reference and are *not* how the baseline is
measured. Two of them come straight from `gds_boundary` on
`context/gds/sg13g2_*.gds`; the third cannot, because that GDS draws no
prBoundary and `gds_boundary` falls back to the bounding box and answers
`2.400 x 4.390 um ... (5 sites, from bbox)`. Its 1.92 um is the placement width
`baseline.py` derives from the power-rail span instead, and the reason that is
the defensible number is the second half of [Fail closed](#fail-closed).

The AION cell is **45.5 % smaller** — 6 sites against 11, five sites saved.
`make flow` prints those two measurements itself, in stages `[1/7]` and `[3/7]`:

```
  candidate: AION_inv_nand2_nor2_1: 2.880 x 3.780 um = 10.8864 um^2 (6 sites, from prBoundary)
  baseline: AION_inv_nand2_nor2: 5.280 x 3.780 um = 19.9584 um^2 (11 sites, from prBoundary)
```

Where those five sites come from is worth writing down, because it is what the
next cell's floorplan has to reproduce. Ordering the gates `I1, I1_bar, I0, I2`
chains all four pmos devices into one unbroken diffusion strip and all four nmos
devices into another:

```
   pmos nodes   I1_bar |  VDD  | net_p_0 | net_p_1 |  O0
   gates             I1     I1_bar     I0        I2
   nmos nodes   I1_bar |  VSS  |   O0    |   VSS   |  O0
```

`net_p_0` and `net_p_1` become shared diffusion: no wire, no contact, no column.
Four gates need five diffusion nodes at the 510 nm contacted pitch, which lands
on six sites. The abutted row spends eleven because each PDK cell pays for its
own diffusion ends, its own taps and its own boundary spacing, three times over.

### Delay

Measured. Both cells were extracted with Magic at the same `PEX_MODE` and
characterized with ngspice on the same grid and the same stimulus; the
comparison is read at its middle point, slew 0.3294 ns and load 0.0648 pF, at
`typ`. `flow` resolves both of those *once* and hands the same value to each
side, because a delay measured one way minus a delay measured another way is
not a difference between two cells.

| metric | candidate | baseline | unit | change | better |
| --- | ---: | ---: | :--- | ---: | :---: |
| placement area | 10.8864 | 19.9584 | um² | −45.5 % | yes |
| worst arc delay | 752.60 | 585.20 | ps | +28.6 % | **no** |
| mean arc delay | 519.31 | 436.35 | ps | +19.0 % | **no** |
| leakage power | 114.641 | 179.027 | pW | −36.0 % | yes |
| worst input capacitance | 0.00311 | 0.00315 | pF | −1.1 % | yes |

```
COMPARE: LOSS area -45.5% (10.886 vs 19.958 um2)  worst delay +28.6% (752.6 vs 585.2 ps)
```

**The worked example is smaller and slower, and it loses.** That is the honest
state of this cell, and the tool is built to report it rather than to find a
metric under which it wins.

The per-arc table says where the delay went, and it is not evenly spread:

| arc | candidate (ns) | baseline (ns) | change |
| --- | ---: | ---: | ---: |
| `I0->O0 fall` | 0.31077 | 0.32508 | −4.4 % |
| `I0->O0 rise` | 0.72895 | 0.58520 | +24.6 % |
| `I1->O0 fall` | 0.29333 | 0.31448 | −6.7 % |
| `I1->O0 rise` | 0.75260 | 0.56540 | +33.1 % |
| `I2->O0 fall` | 0.30721 | 0.30520 | +0.7 % |
| `I2->O0 rise` | 0.72300 | 0.52273 | +38.3 % |

Every falling arc is a wash or a small win; every rising arc is 25–38 % worse.
Rising means pulling `O0` up, and the netlist pulls it up through three pmos in
series — `XP1` → `XP2` → `XP3` — where the `sg13g2_nor2_1` it replaces has two.
Those series nodes, `net_p_0` and `net_p_1`, are exactly the ones the floorplan
merged into shared diffusion to save the five sites: they carry no contact and
no metal, so the pull-up current runs through diffusion for the whole stack.
The area win and the delay loss are the same decision, seen twice.

Routing cannot fix that, and it is worth being able to *prove* that rather than
assume it. Characterizing the same layout from the ideal netlist instead of the
extracted one separates the two causes in one run:

| arc | ideal | PEX | the layout's share |
| --- | ---: | ---: | ---: |
| `I0->O0 rise` | 723.9 ps | 728.9 ps | +5.1 ps |
| `I1->O0 rise` | 740.8 ps | 752.6 ps | +11.8 ps |
| `I2->O0 rise` | 714.0 ps | 723.0 ps | +9.0 ps |

The parasitics cost 1.3–11.8 ps against a 167 ps gap: **1.6 %**. The layout is
not the problem, and no amount of re-routing would have found that out.

### Resizing, and the win

The fix is device width, so it is a change to the netlist — which makes it an
explicit step rather than a layout decision. `make resize` widens every device
in a series stack deeper than `MIN_DEPTH`, folds it into fingers, and writes a
**new** netlist and a report; it never edits its input, because that file is
what LVS grades against. It takes the largest multiplier whose estimated area
still fits inside the abutted row, so it cannot buy speed by spending the area
win:

```
RESIZE: AION_inv_nand2_nor2_1 -> AION_inv_nand2_nor2_1s  x2 on 3 device(s), 7 columns, 9 sites, 16.330 um2 (budget 19.958)
```

`cells/AION_inv_nand2_nor2_1s.py` lays that netlist out. Folding a series chain
turns the pmos row into a **palindrome** around the output, so every internal
node appears twice and needs a strap — which is what its two Metal2 tracks are
for, and what its module docstring works through. It is DRC clean on both
engines and LVS-clean at 8/8 devices and 9/9 nets, and:

| metric | resized | baseline | unit | change | better |
| --- | ---: | ---: | :--- | ---: | :---: |
| placement area | 16.3296 | 19.9584 | um² | −18.2 % | yes |
| worst arc delay | 474.17 | 585.08 | ps | −19.0 % | yes |
| mean arc delay | 381.80 | 436.29 | ps | −12.5 % | yes |
| leakage power | 160.486 | 179.027 | pW | −10.4 % | yes |
| worst input capacitance | 0.00517 | 0.00315 | pF | +64.4 % | **no** |

```
COMPARE: WIN area -18.2% (16.330 vs 19.958 um2) worst delay -19.0% (474.2 vs 585.1 ps)
```

Smaller *and* faster, and the one number that got worse is the honest cost:
doubling the stacked devices doubles their gate area, so the cell presents 64 %
more input capacitance to whatever drives it. The report shows it rather than
leaving it to be discovered at block level.

The two cells are both kept, because they are a real trade and not a
before/after: `AION_inv_nand2_nor2_1` is 45 % smaller and 29 % slower,
`AION_inv_nand2_nor2_1s` is 18 % smaller and 19 % faster with a heavier input.
Which one a design wants is a question the comparison answers in ps and um²
rather than one the tool should decide.

Regenerate either table with `make flow`; it is written to
`build/<cell>/<cell>.compare.md` and `.compare.json`.

## The exported views

`make export` writes one directory of views, in the shape
[`output_constr.md`](output_constr.md) describes — a consumer discovers cells by
file stem, so `build/<cell>/final/<cell>.{gds,lef,lib,v,spice,cdl}` is what it
needs. One Liberty file is published as `<cell>.lib`; several are one per
corner and keep the names the characterizer gave them, because renaming them to
a single stem would either erase the corner or drop all but one — discovery then
groups them by directory, which `output_constr.md` allows.

| View | Extension | Required? | Used for |
|---|---|---|---|
| GDS | `.gds` | required | streamout |
| LEF | `.lef` | required | placement, routing blockages, pins |
| Liberty | `.lib` | required | STA and the resizer |
| Verilog | `.v` | recommended | gate-level simulation, before and after PnR |
| SPICE | `.spice` | recommended | LVS |
| CDL | `.cdl` | recommended | LVS |

### The four LEF checks

`output_constr.md` lists five conditions a place-and-route run refuses to start
on unless `LENIENT=1`, "because none of them fail until detailed placement
otherwise". `check_lef` has no lenient mode: it reports what `make pnr` would
find, and a cell that needs `LENIENT=1` is a cell to fix, not to wave through.
`exporters.check_lef` reports them as four fields — the two dimensional ones are
one measurement — and `export_all` builds and checks the LEF *before* it copies
any other view, so a cell the placer would reject leaves behind a quarantined
`<cell>.lef.rejected` and an error, never a directory that looks finished:

| `LefCheck` field | Condition | Why it matters |
|---|---|---|
| `cell_class` | `CLASS CORE ;` | anything else and OpenROAD treats the cell as a macro |
| `site` | `SITE CoreSite ;` | without it the cell has no row to sit in |
| `geometry` | height exactly 3.78 um, width an exact multiple of 0.48 um | one `CoreSite` row, on the site pitch |
| `pins` | `PIN VDD` and `PIN VSS` present | the PDN has nothing to strap otherwise |

Two of those are corrections, not polish. Magic's own `lef write` produces a
macro header like this one, captured from the worked example:

```
MACRO AION_inv_nand2_nor2_1
  CLASS BLOCK ;
  FOREIGN AION_inv_nand2_nor2_1 ;
  ORIGIN 0.000 0.000 ;
  SIZE 2.880 BY 3.780 ;
```

`CLASS BLOCK`, and no `SITE` line at all. Shipping that LEF unedited gives the
placer a hard macro where a standard cell was meant. The exporter rewrites both,
and `check_lef` is what proves it did rather than assuming. What `make flow`
prints for the worked example:

```
  lef check: ok
    class CORE, site CoreSite
    lef geometry: AION_inv_nand2_nor2_1: 2.880 x 3.780 um = 10.8864 um^2 (6 sites, from lef)
    pins: I1, I0, I2, O0, VDD, VSS
```

Each rewrite leaves its reason in the file, so nobody has to diff the LEF against
Magic's output to find out what changed:

```
# aion_layout: rewrote 'CLASS BLOCK ;' to 'CLASS CORE ;': magic reads no cell class
#   out of a GDS and defaults to BLOCK, which OpenROAD treats as a hard macro
# aion_layout: inserted 'SITE CoreSite ;' after SIZE: magic emits no SITE, and
#   without one the placer has no row to legalise the cell into
```

`export_lef` also cross-checks the `SIZE` line Magic wrote against the
prBoundary in the GDS and rejects the LEF if they disagree, because a published
LEF that describes a different cell from the GDS beside it is worse than no LEF
at all. And `make verify` applies the same size constraints straight off the
GDS, so a cell that is the wrong width is caught while iterating rather than at
export.

### The Verilog model

The `.v` is the only view that says what the cell **computes**, and it is the
one a gate-level simulation reads. It has to carry two things:

```verilog
`timescale 1ns / 10ps
`celldefine
module AION_inv_nand2_nor2_1 (
`ifdef USE_POWER_PINS
    inout VDD,
    inout VSS,
`endif
    output O0,
    input I0,
    input I1,
    input I2
);

  // Function
  assign O0 = ~I0 & I1 & ~I2;

  // Timing
  specify
    (I0 => O0) = (0.0, 0.0);
    (I1 => O0) = (0.0, 0.0);
    (I2 => O0) = (0.0, 0.0);
  endspecify

endmodule
`endcelldefine
```

**The function**, or the netlist that instantiates this cell drives `z` out of
it for the whole run, which reaches the testbench as `x` on a design that is
fine. **A `specify` path per timing arc**, because that is what an SDF's
`IOPATH` records attach to: a model with no `specify` block is annotated with
nothing and simulates at zero delay, and nothing complains, because the SDF
reader has no path to complain *about*. The delays in it are zero on purpose —
they are placeholders the SDF overwrites, exactly as in the PDK's own
`sg13g2_stdcell.v`.

One file serves every stage. `iverilog` keeps `specify` blocks only with
`-gspecify` (`-ginterconnect` for the SDF's wire delays, `-Ttyp` to pick the
triplet); Questa keeps them by default; Verilator drops them and ignores
`$sdf_annotate` outright, so a Verilator run is a function check at zero delay —
which is all Verilator ever is on a gate netlist, PDK cells included.

The function is **solved, not assumed**. `aion_layout.logic` reads the
transistor netlist the layout was drawn and LVS'd against and evaluates it one
input vector at a time: a node is 1 when conducting devices tie it to VDD and
nothing can tie it to VSS, and 0 for the mirror of that, repeated until every
gate-driven node in the cell has a level. That handles a merged AION cell,
whose second stage is gated by the first one's drain, with no assumption that
the netlist is one complementary gate or that its pull-up is series-parallel —
the SG13G2 MUXes, which pass data through transmission gates, solve too. The
result is minimised (Quine-McCluskey) and then re-evaluated against the truth
table it came from before it is written.

Then it is **checked against the Liberty**, which states the same fact by a
different route: `aion_char` measured `function` with an ngspice `.op` per input
vector. Two independent answers, and `export_all` refuses to publish the cell at
all when they differ — naming the vector where they first disagree, because at
that point one of the two views is wrong and neither can say which. When they
agree, the model records it:

```verilog
// AION_inv_nand2_nor2_1_typ_1p20V_25C.lib: pin O0 function agrees
```

A cell whose netlist has **no truth table** is refused rather than published
empty: feedback (a latch or a flop holds state), a node nothing drives in some
state (a tri-state output), a node tied to both rails, a device that is neither
an nmos nor a pmos. Each of those is reported by name and by the input vector
that exposed it. Such a cell needs a hand-written model; what it must not get is
the empty module that would elaborate and simulate as `x`.

The same rule as the LEF applies to everything after it: a publish that fails
here quarantines the views it had already written, rather than leaving a
directory holding a GDS, a Liberty and no model — discovery groups by stem, and
that directory is a cell somebody places.

## Project structure

```text
tools/aion_layout_claude/
├── README.md                       # this file
├── SKILL.md                        # the model-facing skill: how to draw a cell
├── Makefile                        # every target above; one CLI call each
├── pytest.ini                      # host-only by default: -m "not docker"
├── output_constr.md                # what a consumer requires of the views
├── ref_makefile_1.mk               # reference: the JKU analog flow's Makefile
├── AION_inv_nand2_nor2_1_minimized.spice   # worked example, transistor level
├── AION_inv_nand2_nor2.spice               # the same logic, three PDK cells
│
├── aion_layout/                    # the package; importable straight from here
│   ├── cli.py                      # every subcommand; the Makefile calls only this
│   ├── __main__.py                 # python3 -m aion_layout
│   ├── tech.py                     # SG13G2 layers, design rules, grid, cell frame
│   ├── primitives.py               # Point, Rect, transforms.  Nanometres.
│   ├── shapes.py                   # RectShape, PolygonShape, TextShape
│   ├── cell.py                     # Cell container, Port, GDS writer
│   ├── building_blocks.py          # diffusion, wells, poly, contacts, vias, taps,
│   │                               #   wires, pins, rails, whole transistors
│   ├── spice_parser.py             # SPICE .subckt -> Mosfet / Subckt
│   ├── netlist_view.py             # gate order, series chains, netlist summary
│   ├── auto_scaffold.py            # the gate placement scaffold.py wraps
│   ├── scaffold.py                 # netlist -> a starting cells/<cell>.py
│   ├── runner.py                   # the one place that runs a command
│   ├── verification.py             # DRC/LVS parsing, report discovery, receipts
│   ├── metrics.py                  # geometry from the GDS and from the LEF
│   ├── layout_metrics.py           # poly/active crossing count, from a GDS
│   ├── steps.py                    # build, render, drc, lvs, verify, the verdict
│   ├── baseline.py                 # abut the PDK cells into the comparison row
│   ├── characterize.py             # PEX, then ngspice over the corners
│   ├── liberty.py                  # read a .lib back: cells, arcs, functions, tables
│   ├── logic.py                    # what the netlist computes: switch-level truth
│   │                               #   table, minimised expression, .lib functions
│   ├── exporters.py                # the six views, and the LEF checks
│   ├── compare.py                  # candidate vs baseline, and the COMPARE: line
│   ├── evidence.py                 # the packet the model reads between edits
│   ├── router.py                   # manual routing helpers
│   ├── doc_generator.py            # markdown report for a verified cell
│   └── gds_to_python.py            # GDS -> a runnable generator
│
├── cells/                          # the generators.  The model edits these.
│   ├── AION_inv_nand2_nor2_1.py    # complete, verified worked example
│   └── _m2_probe.py                # a clean cell exercising the Metal2/Via1 helpers
│
├── scripts/
│   ├── docker_run.sh               # one command inside iic-osic-tools, from here
│   ├── hook_cell_check.py          # PostToolUse hook: advisory check on save
│   ├── gds_to_image.py             # GDS -> PNG
│   └── gds_to_python.py            # CLI for aion_layout.gds_to_python
│
├── context/                        # reference material, read-only
│   ├── py/sg13g2_*.py              # 83 PDK cells as generate() functions
│   ├── gds/sg13g2_*.gds            # 84 of them as GDS (one has no generator)
│   ├── spice/sg13g2_*.spice        # and 84 as netlists
│   └── drc/docs/*.md               # every numeric design rule, as tables
│
├── tests/
│   ├── conftest.py                 # fixtures; the committed reports stay read-only
│   ├── test_*.py                   # ten modules: the verdict surface, absence-is-
│   │                               #   not-clean, metrics, runner, spice_parser,
│   │                               #   scaffold, liberty, logic, exporters, compare
│   └── fixtures/                   # real clean and dirty DRC/LVS output, committed
│
└── build/                          # run output, one directory per cell
```

## Fail closed

The rule: **absent, empty, truncated, unparseable or merely
not-positively-confirmed evidence is not good evidence.** A missing report is an
error, never a pass. Every parser in `verification.py` and every measurement in
`metrics.py` follows it, and three places show what following it properly costs.

**The KLayout completeness receipt.** KLayout's DRC at `macro` level does not
necessarily write one database — it can write one `.lyrdb` per rule table. So
"merge every `.lyrdb` under the work directory, find zero items" has two causes
that look identical: the cell is clean, or a rule table never ran and its
database is not there to be read. `run_drc` therefore writes
`klayout.receipt.json` beside the databases *before* anything parses them,
naming the file set the run produced and the runner's exit status:

```json
{
  "version": 1,
  "tool": "klayout",
  "cell": "AION_inv_nand2_nor2_1",
  "exit_status": 0,
  "databases": [
    "AION_inv_nand2_nor2_1_AION_inv_nand2_nor2_1_full.lyrdb"
  ]
}
```

The merge grades itself against that receipt and reports `completeness` as one of
three values. `verified` — every named database was read, and only this one lets
a zero-item result be called clean. `degraded` — a database is missing, an
unnamed one appeared, or the runner exited something other than 0 (no
violations) or 1 (violations found). `unverified` — no receipt at all, which is
what a run predating receipts looks like, and which is *not* clean either. On
the worked example the verdict block says so out loud:

```
  KLayout DRC clean - 0 violation(s) (tool reported 0); completeness verified
    receipt matches: all 1 rule database(s) the run wrote were read
```

Deleting a database the receipt names is what this catches. Add a second name to
the `databases` list above, remove the file, and re-parse: without the receipt
the count would still be zero and the headline would still read `PASS`; with it,
`completeness` is `degraded`, `clean` is `False`, and the note says which file
went missing.

```
completeness degraded
1 of the 2 rule database(s) named by the receipt are missing:
'AION_inv_nand2_nor2_1_AION_inv_nand2_nor2_1_latchup.lyrdb'
```

Delete *every* database instead and the report does not degrade — it becomes
`available=False`, with `no *.lyrdb in the canonical <cell>.klayout.drc/
directory`. That is the same rule applied one step earlier: a run that left
nothing behind is not a clean run, it is a run nobody can grade.

**prBoundary versus bounding box.** `metrics.gds_boundary` measures the
placement footprint from the prBoundary layer (189/4). When a GDS draws none
there is a tempting fallback — the bounding box of every shape — and the numbers
it gives are not wrong, they are *a different measurement*. A standard cell's
NWell and implants deliberately overhang the boundary so an abutted neighbour
shares them, so the bbox charges a cell for geometry its neighbour also pays
for, and makes a cell look larger the better it abuts.

This is not hypothetical. The shipped `context/gds/sg13g2_nand2_1.gds` draws no
prBoundary:

```
sg13g2_nand2_1: 2.400 x 4.390 um = 10.5360 um^2 (5 sites, from bbox)
```

The cell is really 1.920 x 3.780 um — `context/py/sg13g2_nand2_1.py` sets exactly
that boundary. The 2.400 x 4.390 is its NWell overhang, and 5 sites is not even
a whole number of them. `baseline.py` hits this every time it places that cell,
and handles it by measuring something it can defend instead — the power-rail
span — and recording what it did:

```
  note: sg13g2_nand2_1: draws no prBoundary; placement width 1920 nm taken from
        the power rail span
```

So the fallback is taken, but never silently: the result is tagged
`source="bbox"`, carries a `problems` line saying what it is and what it is not,
and `allow_bbox_fallback=False` turns it into a `MetricsError` for
a caller that must not measure anything else — `make flow` grades the candidate
that way, so a cell with no boundary cannot reach the comparison at all. The
same call on a cell that draws its boundary:

```
AION_inv_nand2_nor2_1: 2.880 x 3.780 um = 10.8864 um^2 (6 sites, from prBoundary)
```

Same function, different `source`, and the report always says which.

**A port bound to nothing.** Mode 3 extraction runs Magic's `extresist`, which
splits a resistive net into segments and renames them — `VSS` becomes `VSS.t0`,
`VSS.n1`, and so on — and it can finish having bound the `.subckt` *port* to
none of them. The port is then declared and referenced nowhere, so every device
on that net is floating. On a ground rail that means no pull-down works and the
extracted cell drives its output to one rail for every input vector.

Nothing downstream notices on its own. LVS passes, because it runs a *different*
extraction with no resistance in it, where the net is whole — so the layout is
genuinely correct and genuinely verified. Characterization then measures the
broken netlist without complaint and writes a Liberty file whose function is
`O0 = 1` and which carries no timing arcs at all; the first error surfaces at
the comparison, an hour later, reading `baseline: ... publishes no timing arcs`
and pointing at the wrong artifact entirely.

Whether it happens is geometry, not correctness, which is what makes it nasty:

| baseline | width | port bound? |
|---|---|---|
| `mux2_1` + `inv_1` | 13 sites | yes — `R9 VSS.t3 VSS 1.85276` |
| `mux2_1` + `inv_2` | 14 sites | **no** — no resistor names `VSS` at all |

Those two rails are otherwise the same network, resistance for resistance. One
line is missing from the second, and it is the one that connects the cell to
ground.

So `run_pex` refuses to return a netlist whose `.subckt` declares a port nothing
in the body references, and names both the fix and the trap:

```
port(s) VSS are declared on the '.subckt reference_AION_mux2i_2' line and
referenced by nothing in it, so every device on those nets is floating and
the extracted cell does not compute its function.
   This is Magic's extresist renaming a split net's segments (VSS -> VSS.t0,
   VSS.n1, ...) without binding the port to any of them. LVS does not see it:
   it runs a non-RC extraction where the net is whole.
   Re-run with --pex-mode 2 (C-coupled), which skips extresist entirely and
   applies to both sides of a comparison, so the two halves stay the same
   measurement. What that costs is wire resistance; what it buys is a netlist
   whose rails are connected.
   Do NOT raise the extresist threshold instead: past the rail's own
   resistance it drops every R element from the netlist and silently turns
   full RC into C-only under a _pex3 file name.
```

The last paragraph is the point of the check. Raising `extresist threshold`
until the symptom disappears *works*, in the sense that the port comes back —
and it does so by switching resistance extraction off, taking the `R` elements
from twelve to zero while the file is still called `_pex3`. That is the failure
this whole section is about, wearing the costume of a fix.

`--pex-mode 2` is the honest way out, and it is defensible on its own terms
rather than merely convenient: in the characterization deck the rail port is
tied to ideal ground, and in silicon the rail is strapped by the power grid
along its whole length and abuts its neighbours on both sides. Feeding ground in
at a single label point through up to 474 Ω of rail is arguably *less* physical
than no rail resistance at all — characterizing with ideal rails is what vendor
libraries do. What it costs is the signal-net wire resistance, which is real and
is the reason mode 3 is still the default.

One consequence to hold on to: two cells extracted at different modes are not
comparable, and they end up in the same merged Liberty. Choose `PEX_MODE` per
library, not per cell.

This tool keeps `3` as its default, because a mined cell's own wire resistance
is the thing it exists to measure. The PDK-extension driver
(`scripts/pdk_cell.py` in `aion_chip`) sets `2` instead: every cell it builds is
graded against an *abutted PDK baseline*, which is the geometry that trips
`extresist`, and rail resistance is the parasitic those cells least want
modelled. See `PEX_MODE_DEFAULT` there for the argument in full.

## Known gaps

**The worked example loses.** `make flow` runs end to end and the answer is
`COMPARE: LOSS`: 45.5 % smaller, 28.6 % slower at the typical corner. The tool
is correct and the cell is not good enough, and those are different problems.
The cause is in the netlist rather than the layout — a three-deep pmos pull-up
against the NOR2's two — so the next move is `aion_minimizer`'s sizing or a
floorplan that contacts the internal series nodes, at the price of a site. See
[Delay](#delay). Nothing in this repository has yet produced a `COMPARE: WIN`.

**The technology description stops at Metal2, and so the measurements do.**
`tech.py` defines `Activ`, `NSD`, `PSD`, `NWell`, `PWell`, `GatPoly`, `Cont`,
`Via1`, `Metal1`, `Metal2` and `prBoundary` — nothing above.
`metrics.layer_inventory` iterates that table, so geometry on Metal3 and up is
invisible to it, and `metrics.routing_metals_used` searches `Metal1..Metal5` but
can only ever return the first two. A cell that drew Metal3 would be reported as
Metal1-only. Cells at this row height do not need Metal3, which is why it has
not bitten, but the silence is the wrong shape. Its `design_rules` are a curated
drawing guide over the same range, not the deck: the tables in
`context/drc/docs/{main,extra,precheck}_rules.md` are the authority, and the
values in `tech.py` are the ones you must *draw* rather than the smallest number
a rule mentions (the Via1 enclosures are the 50 nm endcap figures, not `V1.c`'s
10 nm — the comment there explains why).

**The Verilog model is combinational-only, and says so by refusing.**
`aion_layout.logic` solves a DC truth table, so a cell that holds state has no
model and `make export` stops instead of publishing one. That is the right
answer for every cell this tool has drawn — AION cells are merged combinational
gates — but a sequential AION cell would need a hand-written model and a
`specify` block with the timing checks that go with it, and nothing here writes
either. The refusal names the node and the input vector, which is at least the
information a hand-written model needs.

**The `specify` block carries plain module paths, not conditional ones.**
`(I0 => O0)` per arc, one delay pair each. A Liberty with state-dependent arcs
(`when : "..."` on a `timing()` group) publishes several delays for the same
pin pair, and the SDF then carries `COND` records that this model has no
`ifnone`/conditional paths to receive: the last matching annotation wins.
`aion_char` writes no `when`-qualified delay arcs today, so nothing is lost yet.

**Only one cell has ever been through the flow.** Everything in this README is
measured, and all of it is measured on `AION_inv_nand2_nor2_1`: three inputs,
one output, eight devices, Metal1 only. The Metal2 helpers have a DRC-clean
probe cell (`cells/_m2_probe.py`) but no cell in the flow uses them, and the
baseline builder has abutted exactly one row of exactly three PDK cells. Treat
every "it works" here as "it worked once, on this".

**KLayout DRC runs at `macro` level.** `verification.run_drc` invokes
`sak-drc.sh -d -b -l macro`. In the script's own words, `macro` "adds off-grid,
pin, and zero-area checks, skips chip-level density and antenna". A cell that is
clean here is clean *as a cell*; density and antenna are the block's problem and
are not checked. `regular` runs everything and is not wired to a target.

**Nothing containerised runs without the container.** DRC, LVS, PEX, the LEF
export and characterization all go through `scripts/docker_run.sh` into
`iic-osic-tools`. That is deliberate — one place knows the container name and
the mount — and it fails closed: a stopped container comes back as status 125
with `[container] ... is not running`, never as a skipped step. But there is no
host-only mode, so `make test` covers the parsers and the geometry and stops
where a tool would start.

**The scaffold is deliberately incomplete, and that is easy to misread.**
`make scaffold` emits a module that imports, runs and writes a GDS — and draws
no taps, no source/drain contacts and no routing. In `scaffold.py`'s own words:
"The emitted file is a *starting point*, never a cell. It will not pass DRC and
cannot pass LVS, and it says so about itself." The emitted docstring lists every
gap by name for exactly this reason. Expect the first `make verify` on a fresh
scaffold to fail, and read `make evidence` rather than treating the failure as a
bug.

**`make test` hides the number of tests that passed.** `pytest.ini` already
carries `-q` in `addopts` and the `test` recipe passes a second one, which takes
pytest to quiet level 2 and drops the summary line — so the target prints three
rows of dots and nothing else, and a suite that silently collected nothing would
look the same as one that passed. Run it as `python3 -m pytest tests/` (no flag;
`pytest.ini` supplies the `-q` and the `-m "not docker"` deselection) to get the
line that matters: `201 passed, 1 deselected in 2.93s`.

**`aion_layout/__init__.py` re-exports only `Layer`, `Tech` and `sg13g2_tech`.**
Every other module is imported by its full path, which is what the modules
themselves do, but it means `import aion_layout` tells a reader almost nothing
about what is in the package. This file is the index instead.

**`router.py`, `doc_generator.py` and `gds_to_python.py` are inherited and off
the flow.** They came from the earlier tool, they still import and run, and no
`make` target and no CLI subcommand calls any of them.
