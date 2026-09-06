# `aion_opt`

`aion_opt` takes a post-synthesis gate-level netlist, finds groups of standard
cells that recur across the design, turns each recurring group into a new
Verilog cell, and rewrites the netlist to use those cells. What comes out is a
hierarchical netlist, an optional flat equivalent, the generated cell library,
a ranked *elite* subset of that library, and JSON/Markdown/HTML reports.

The generated cells are the input to the rest of the AION flow: `aion_char`
characterises them and `aion_minimizer` shrinks them at transistor level. Every
cell you keep is real work downstream, which is why the tool ranks them and can
hand you only the ones that pay for themselves — see
[Elite cell library](#elite-cell-library).

Outputs land under `build/aion_opt/` by default when driven from the root
`Makefile`.

## Quick start

```bash
make aion-opt-run-all                      # mine, rewrite, LEC (+ SEC if RTL is given)
make flow                                  # pattern extraction, stopping at LEC
make flow-opt                              # full + elite libraries, both LEC-checked
make aion-opt-test                         # unit and end-to-end tests
```

## Contents

- [How it works](#how-it-works)
- [Commands](#commands)
- [Elite cell library](#elite-cell-library)
- [Inverted inputs](#inverted-inputs)
- [Configuration flags](#configuration-flags)
- [Performance](#performance)
- [Flow runners](#flow-runners)
- [Module map](#module-map)
- [Tests](#tests)

## How it works

```
netlist.v ──yosys──> Yosys JSON ──> Circuit ──> signal-flow graph
                                                     │
                                          ESU subgraph enumeration
                                                     │
                                        canonical key per subgraph
                                                     │
                                   patterns = {key: [occurrences]}
                                                     │
                            greedy non-overlapping cover + reuse filter
                                          ┌──────────┴──────────┐
                                    cell generation        netlist rewrite
                                          │                      │
                            aion_cells.v / _elite.v        aion_netlist.v
                                                                 │
                                                                LEC
```

**1. Parse.** Verilog inputs are converted to Yosys JSON on demand and loaded
into an internal `Circuit` (instances, nets, ports). Cells absent from the
technology dictionary are skipped as black boxes.

**2. Build the graph.** Only *combinational* cells become graph nodes;
flip-flops, latches, clock gates, fill, decap, tap and antenna cells are
excluded. Drive-strength variants collapse onto one generic type
(`sg13g2_buf_1`, `sg13g2_buf_4`, `sg13g2_buf_16` → `sg13g2_buf`) so the same
logical pattern is recognised whatever the sizing.

**3. Enumerate.** Connected subgraphs of 2..`MAX_SIZE` cells are enumerated with
ESU (Wernicke's *enumerate-subgraphs*), which visits every connected subgraph
exactly once.

**4. Canonicalise.** Each subgraph is reduced to a canonical key that spells out
its cell types, its internal pin-to-pin edges, and its boundary pins. Two
occurrences share a key exactly when they are structurally interchangeable —
and therefore when one generated module can serve both. Because the boundary
pins are part of the key, two occurrences that share a key are guaranteed to
have the same port map.

**5. Cover.** Occurrences overlap heavily, so a greedy pass takes them in
decreasing order of saved area and keeps only disjoint ones. A pattern that
survives the cover fewer than `MIN_SELECTED` times is then dropped, its
instances are freed, and the cover is recomputed — see
[The reuse filter](#the-reuse-filter).

**6. Generate and rewrite.** One Verilog module per surviving pattern, and a
rewritten netlist that instantiates them.

**7. Verify.** LEC compares the rewritten netlist against the original; SEC
compares the flattened netlist against the RTL.

### The reuse filter

Mining requires a pattern to appear `MIN_OCCURRENCES` times, but the cover can
still leave it with a single non-overlapping site — a whole new cell to
characterise and minimise for one instantiation. `MIN_SELECTED` (default:
`MIN_OCCURRENCES`) closes that gap by re-checking the count *after* the cover
and iterating until the selection is stable.

On `tt_um_aion` with `MAX_SIZE=3, MIN_OCCURRENCES=2` this is the difference
between 472 cells covering 1320 sites and 277 cells covering 1253 — nearly half
the library removed for 5 % of the sites. Set `MIN_SELECTED=1` to keep the old
behaviour.

### Correctness properties

- **ESU exactness.** A frontier walk that grows a set one node at a time visits
  `{a,b,c}` once per insertion order, over-counting occurrences by up to
  `(k-1)!` and inflating the `MIN_OCCURRENCES` filter. ESU does not.
- **Boundary pins in the key.** Two occurrences with identical internal wiring
  but a different number of boundary inputs (a pin tied off, or left dangling)
  need different cells. Folding them together would silently produce a wrong
  netlist, so the key distinguishes them.
- **Determinism.** Node ids are assigned by sorted instance name and the cover
  breaks ties explicitly, so results do not depend on dictionary ordering or on
  `JOBS`. The test suite checks that `--jobs 1` and `--jobs 4` agree.

## Commands

Every command is reachable through the root `Makefile` and writes into
`BUILD_DIR`. `python -m aion_opt <command> --help` lists the full argument set.

### `aion-opt-generate-cells`

Mines patterns and writes one Verilog module per selected pattern, plus the
elite subset, the pattern report and the selection cache.

```bash
make aion-opt-generate-cells \
    INPUT=examples/full_flow/tt_um_aion.nl.v \
    TOP=tt_um_aion \
    MAX_SIZE=4 \
    MIN_OCCURRENCES=4 \
    MAX_OUTPUTS=1 \
    ELITE_COUNT=20
```

`MAX_OUTPUTS=1` restricts mining to single-output patterns, which is what the
downstream logic minimizer expects. It is also the cheapest way to keep large
`MAX_SIZE` values tractable.

Outputs:

| Output | Default | Contents |
|--------|---------|----------|
| `CELLS` | `$(BUILD_DIR)/aion_cells.v` | every generated cell |
| `ELITE_CELLS` | `$(BUILD_DIR)/aion_cells_elite.v` | the best `ELITE_COUNT` cells |
| `PATTERN_REPORT` | `$(BUILD_DIR)/pattern_report.json` | patterns found, selected and ranked |
| `SELECTION` | `$(BUILD_DIR)/work/selection.json` | mining result reused by `rewrite` |

### `aion-opt-rewrite`

Replaces occurrences with instances of the cells in `CELLS`. The cell library is
an **input**: `rewrite` reads it, matches its modules to the patterns it knows
about, and only substitutes occurrences for which a module exists. It never
regenerates or overwrites the file.

```bash
make aion-opt-generate-cells INPUT=... TOP=... BUILD_DIR=build/mydesign
make aion-opt-rewrite        INPUT=... TOP=... BUILD_DIR=build/mydesign
```

Point `CELLS` at `aion_cells_elite.v` — or at a hand-edited file — to rewrite
with a subset:

```bash
make aion-opt-rewrite CELLS=build/mydesign/aion_cells_elite.v \
                      REWRITE_NETLIST=build/mydesign/aion_netlist_elite.v
```

Outputs: `REWRITE_NETLIST` (hierarchical), `REWRITE_FLAT` (optional, PDK cells
only) and `REWRITE_REPORT{.json,.md,.html}`.

> **Matching.** Generated cells carry an embedded `// AION canonical_key: <key>`
> comment, so matching is fast and independent of module names — rename or
> delete modules freely. A library without those comments falls back to deriving
> the key from each module's structure through Yosys.

> **Mining once.** `rewrite` reuses the selection cache written by
> `generate-cells` when its fingerprint (input netlist, technology dictionary,
> top module and every mining parameter) still matches, which halves the runtime
> of a flow. It silently re-mines otherwise, so a stale cache can never produce a
> wrong netlist. `--no-cache` forces re-mining.

### `aion-opt-complement-plan`

Costs both options for every complemented cell input and writes the verdict.
See [Inverted inputs](#inverted-inputs).

```bash
make aion-opt-complement-plan CELL_INTERFACES=build/aion_minimizer/reports
```

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPLEMENT_PLAN` | `$(BUILD_DIR_OPT)/complement_plan.json` | Output plan; picked up by `generate-cells` when it exists |
| `CELL_INTERFACES` | `$(BUILD_DIR_MIN)/reports` | `aion_minimizer --report` files, or a directory of them |

Without `--interfaces` every input is costed but nothing is externalized: only
the minimizer knows which inputs actually need a complement.

### `aion-opt-select-elite`

Re-cuts an existing cell library to a different size or metric without
re-mining.

```bash
make aion-opt-select-elite ELITE_COUNT=10 ELITE_METRIC=occurrences \
                           ELITE_CELLS=build/mydesign/aion_cells_top10.v
```

### `aion-opt-run-all`

Mining, cell generation, hierarchical and flat rewriting, reports, LEC, and SEC
when existing RTL files are passed via `RTL=`.

```bash
make aion-opt-run-all INPUT=... TOP=... BUILD_DIR=build/mydesign
make aion-opt-run-all CONFIG=examples/aion_opt/aion_opt.yaml BUILD_DIR=build/pm32
```

### `aion-opt-graph2verilog`

Reads the netlist, builds the graph and emits an equivalent structural Verilog
netlist. A parser/emitter sanity check.

### `aion-opt-lec` / `aion-opt-sec`

Logical and sequential equivalence checks via `scripts/verify/run_lec_sec.py`,
which runs `kepler-formal` inside the EDA container.

### `cells-to-spice`

Converts generated cell modules into the gate-level SPICE that
`aion_minimizer` consumes. Supply-net names and the module prefix are
arguments.

```bash
python -m aion_opt cells-to-spice \
    --cells build/mydesign/aion_cells_elite.v \
    --gates tech/spice/sg13g2_stdcell.spice \
    --output-dir build/mydesign/spice
```

## Elite cell library

Every generated cell has to be characterised (`aion_char`) and minimised
(`aion_minimizer`) before it is worth anything, and that cost is per cell, not
per instantiation. Meanwhile the area savings are very unevenly distributed:
a handful of patterns account for most of the win.

`generate-cells` therefore ranks the selected patterns and writes the top
`ELITE_COUNT` of them to `ELITE_CELLS` — the same modules, byte-identical, just
fewer of them. Rewriting with that library leaves the remaining patterns as
ordinary standard cells.

On `tt_um_aion` (`MAX_SIZE=4, MIN_OCCURRENCES=4, MAX_OUTPUTS=1`):

| Library | Cells | Sites | Cells removed | Est. area saved | Of total area |
|---------|-------|-------|---------------|-----------------|---------------|
| all     | 122   | 1109  | 1205          | 3461.60         | 6.54 %        |
| elite   | 20    | 546   | 546           | 1561.11         | 2.95 %        |

Six times fewer cells to build, for 45 % of the area saving. `ELITE_METRIC`
picks how the ranking is done:

| Metric | Ranks by | Favours |
|--------|----------|---------|
| `saved-area` (default) | occurrences × per-occurrence saving | the biggest total win |
| `occurrences` | how often the cell is instantiated | small, ubiquitous cells |
| `saved-area-per-cell` | per-occurrence saving | large patterns, best return per cell built |

The elite cells are flagged in every report (`"elite": true` in JSON, a `*`
column in Markdown, an `ELITE` badge in HTML).

## Inverted inputs

`aion_minimizer` often needs a complemented copy of one of a cell's inputs: the
pull-up network of a static CMOS gate drives a plain POS literal `A` from
`A_bar`. The cell can build that inverter itself — two devices in **every**
instantiation — or take the complement on an extra `<port>_bar` port and leave
the job to the netlist that instantiates it.

Which is cheaper is not something the cell can know, so `aion_opt` decides it,
over the occurrences the cover actually selected:

- keeping the inverter inside costs `2 x occurrences` devices;
- pulling it out costs two devices per *distinct* driving net with no complement
  anywhere in the netlist, and nothing at all for the rest.

A complement is already there in two shapes: some inverter already reads the net
(its output is the complement), or the net is itself an inverter's output (that
inverter's input is the complement). Post-synthesis netlists are full of both,
which is what makes the trade worth making. An inverter that is itself about to
be absorbed into an AION cell does not count — its output net will not survive
the rewrite.

### The loop

```bash
make aion-opt-generate-cells                 # 1. cells, inverters still inside
python -m aion_opt cells-to-spice ...        # 2. gate-level SPICE per cell
python -m aion_minimizer run ... --report    # 3. which inputs need a complement
make aion-opt-complement-plan                # 4. decide, per cell and per input
make aion-opt-generate-cells                 # 5. cells, now with the extra ports
make aion-opt-rewrite                        # 6. netlist that drives them
make aion-opt-lec                            # 7. prove it
```

Step 4 prints its arithmetic:

```
AION_buf_xnor2_8.I0: external (9/24 sites already have it, 48 vs 30 devices)
AION_buf_xnor2_8.I1: external (2/24 sites already have it, 48 vs 38 devices)
AION_mux2_nand2_19.I0: internal (0/10 sites already have it, 20 vs 20 devices)
```

and writes `$(COMPLEMENT_PLAN)`, which both `generate-cells` and the minimizer
(`--inverted-inputs auto --external-inputs ...`) consume. On `tt_um_aion` with
`MAX_SIZE=4, MIN_OCCURRENCES=4, MAX_OUTPUTS=1`, 13 of 122 cells want a
complement and 12 ports are worth externalizing: 258 devices become 194.

### What the generated module looks like

```verilog
// AION canonical_key: ...
// AION complement_inputs: I2
module AION_buf_mux2_6 ( I0, I1, I2, O0, I2_bar);
  ...
  assign I2_int = ~I2_bar;
  sg13g2_mux2_1 g1 ( .A0(I0), .A1(I1), .S(I2_int), .X(w0) );
endmodule
```

The body reads `~I2_bar` rather than `I2` on purpose. The module is the
reference an equivalence check compares against, so wiring `I2_bar` to anything
but `~I2` has to make that check fail — and it does; `test_complement_flow.py`
asserts exactly that, by breaking one connection and requiring Yosys to reject
the result. The plain port stays in the interface because the generated
transistor cell still uses it.

The marker is part of the library, which is the authority on a module's
interface: `rewrite` reads it back to know which extra ports it owes a driver,
and it survives being sliced into an elite library.

`rewrite` then wires each `<port>_bar` to a complement the netlist already
carries, or inserts one inverter per net that has none:

```
[rewrite] 9 cell(s) take a complemented input on a port
[rewrite] Inserted 87 inverter(s) for complements the netlist did not already carry
```

The inverter cell is found in the technology dictionary by its function
(`!(A)`, exactly one input and one output — which is what rules out the
tri-state `einvn` cells), so no cell name is hard-coded.

The flat rewrite inlines the original PDK cells and never instantiates an AION
module, so it needs no complements and is unaffected.

### Proving it, and how to get that wrong

An equivalence check on this is only worth running if it can fail. Three ways
it silently cannot, all of them hit while building the check in
`test_complement_flow.py`:

- **`read_verilog -lib` blackboxes the PDK cells.** `equiv_make` then compares
  opaque boxes and proves everything, including a netlist with two mux inputs
  swapped. Read the real models from `tech/rtl/sg13g2_*_eqy.v`.
- **`equiv_induct` needs a SAT model for every flop**, so blackboxing the
  sequential cells makes it abort rather than prove. For a change that only
  touches combinational logic, `equiv_simple` alone is the right pass: it
  treats flop outputs as free variables, which is sound here because no AION
  pattern ever contains a sequential cell.
- **The PDK's behavioural flop models do not elaborate for formal.** For a
  design with flops the container path (`make aion-opt-lec`, kepler-formal) is
  the real gate.
- **`equiv_simple` alone is not enough on a sequential design.** Dropping
  `equiv_induct` to work around the flop models leaves points it cannot resolve
  locally — on `tt_um_aion`, 114 of 13252. Measured against a control, that
  number is *identical* for a correct netlist and for one with a deliberately
  mis-driven `<port>_bar`, so the recipe has no discriminating power there and
  neither confirms nor denies anything. It is sound on a purely combinational
  design, which is why the test fixture is one.
- **`yosys -q` hides `equiv_status`, and `equiv_status` without `-assert` exits
  0 whatever it found.** The two together turn the check into a no-op that
  always looks like a pass. Always pass `-assert`.

Whatever the recipe, run a **negative control**: break one `<port>_bar`
connection and require the check to reject it. Without that, a check that
passes tells you nothing. `test_complement_flow.py` does exactly this on a
purely combinational design, so it needs no flop model and runs from `make
aion-opt-test`.

## Configuration flags

Nothing is hard-coded. Every knob below is a Makefile variable, a CLI argument
and a YAML config key.

### Inputs

| Variable | CLI | Default | Description |
|----------|-----|---------|-------------|
| `INPUT` | `--input` | `examples/aion_opt/pm32.nl.v` | Input netlist (`.v`, `.sv` or Yosys `.json`) |
| `TOP` | `--top` | `pm32` | Top module name |
| `CELL_LIB` | `--cell-lib` | `tech/tech_dict/sg13g2_stdcell.json` | JSON technology dictionary |
| `BUILD_DIR` | — | `build` | Root of all outputs (`$(BUILD_DIR)/aion_opt`) |
| `CONFIG` | `--config` | (unset) | YAML config file |

### Mining and cover

| Variable | CLI | Default | Description |
|----------|-----|---------|-------------|
| `MAX_SIZE` | `--max-size` | `3` | Maximum standard cells per pattern (2..8) |
| `MIN_OCCURRENCES` | `--min-occurrences` | `2` | Minimum mined occurrences to keep a pattern |
| `MIN_SELECTED` | `--min-selected` | = `MIN_OCCURRENCES` | Minimum occurrences after the cover; `1` disables the reuse filter |
| `MAX_OUTPUTS` | `--max-outputs` | (no limit) | Cap on boundary outputs. `1` gives single-output cells |
| `MAX_INPUTS` | `--max-inputs` | (no limit) | Cap on boundary inputs |
| `AREA_FACTOR` | `--area-factor` | `0.85` | Assumed AION cell area relative to the cells it replaces |
| `JOBS` | `--jobs` | all cores | Mining workers. `0` = all cores, `1` = serial, negative = leave that many cores free |

### Cell library

| Variable | CLI | Default | Description |
|----------|-----|---------|-------------|
| `CELL_PREFIX` | `--cell-prefix` | `AION_` | Prefix of every generated module and instance |
| `ELITE_COUNT` | `--elite-count` | (all) | Size of the elite library |
| `ELITE_METRIC` | `--elite-metric` | `saved-area` | `saved-area`, `occurrences` or `saved-area-per-cell` |
| `COMPLEMENT_PLAN` | `--complement-plan` | (unset) | Plan from [`complement-plan`](#inverted-inputs); cells named in it take a complemented input on a port |
| `CELL_INTERFACES` | `--interfaces` | `$(BUILD_DIR_MIN)/reports` | `aion_minimizer --report` files consumed by `complement-plan` |

`CELL_PREFIX=MYLIB_` produces `MYLIB_nand2_nor2_0` modules and `_MYLIB_0_`
instances; the string appears nowhere else in the tool.

### Outputs

| Variable | Default | Used by |
|----------|---------|---------|
| `CELLS` | `$(BUILD_DIR_OPT)/aion_cells.v` | output of `generate-cells`; input of `rewrite` |
| `ELITE_CELLS` | `$(BUILD_DIR_OPT)/aion_cells_elite.v` | `generate-cells`, `select-elite` |
| `PATTERN_REPORT` | `$(BUILD_DIR_OPT)/pattern_report.json` | `generate-cells`, `select-elite` |
| `REWRITE_NETLIST` | `$(BUILD_DIR_OPT)/$(TOP)_optimized.v` | `rewrite` |
| `REWRITE_FLAT` | (unset) | `rewrite`, optional flat netlist |
| `REWRITE_REPORT` | `$(BUILD_DIR_OPT)/report` | `rewrite` (`.json` / `.md` / `.html`) |
| `SELECTION` | `$(BUILD_DIR_OPT)/work/selection.json` | shared by `generate-cells` and `rewrite` |
| `GRAPH2V_OUTPUT` | `$(BUILD_DIR_OPT)/$(TOP)_graph2verilog.v` | `graph2verilog` |
| `RUN_ALL_FLAT` | `$(BUILD_DIR_OPT)/$(TOP)_optimized_flat.v` | `run-all`, `sec` |

### Verification

| Variable | Default | Description |
|----------|---------|-------------|
| `REF` | `$(INPUT)` | Reference netlist for LEC |
| `MOD` | `$(REWRITE_NETLIST) $(CELLS)` | Modified netlist(s) for LEC |
| `RTL` | `examples/aion_opt/pm32.v examples/aion_opt/spm.v` | RTL sources for SEC |
| `NETLIST` | `$(RUN_ALL_FLAT)` | Synthesized netlist for SEC |
| `LIB` | script default | Liberty file for the formal tools |

### YAML config

```yaml
input_netlist: examples/full_flow/tt_um_aion.nl.v
cell_lib: tech/tech_dict/sg13g2_stdcell.json
top_module: tt_um_aion

max_pattern_size: 4
min_occurrences: 4
min_selected_occurrences: 4
max_outputs: 1
max_inputs: null
area_factor: 0.85
jobs: 0                    # 0 = every core

cell_prefix: AION_
elite_count: 20
elite_metric: saved-area
complement_plan: null       # or build/aion_opt/complement_plan.json

output_dir: build/aion_opt
```

Explicit command-line values always win over config values, and an unknown key
is an error rather than a silent no-op.

## Performance

`tt_um_aion` — 5177 instances, 5135 combinational nodes — on 20 cores:

| `MAX_SIZE` | `MAX_OUTPUTS` | Subgraphs | Patterns kept | Time | Peak RSS |
|-----------:|--------------:|----------:|--------------:|-----:|---------:|
| 3 | 1 | 67 k | 636 | 0.6 s | 60 MB |
| 4 | 1 | 379 k | 695 | 0.8 s | 60 MB |
| 5 | 1 | 2.4 M | 738 | 1.8 s | 60 MB |
| 6 | 1 | 17.0 M | 777 | 12.6 s | 60 MB |
| 4 | — | 379 k | 51 640 | 4.9 s | 336 MB |
| 5 | — | 2.4 M | 345 544 | 35.3 s | 2.2 GB |

For reference, the previous implementation took **46 s for `MAX_SIZE=3`** and
was not usable beyond that. Four changes account for the difference:

1. **Incident-edge indexing.** Classifying a candidate subgraph used to scan
   every pin edge in the design; it now looks only at the edges touching the
   candidate cells, which decouples the inner loop from the design size.
2. **Cheap canonicalisation.** Colour refinement plus memoisation replaced a
   brute-force search over all `n!` relabellings, which was run once per
   enumerated subgraph.
3. **ESU.** No duplicate visits, so no wasted canonicalisation.
4. **Parallel mining.** ESU partitions by root node; roots are striped across
   worker processes that inherit the read-only graph through `fork`, so nothing
   large is pickled and the merge is a dictionary union.

Memory, not time, is the limit at large `MAX_SIZE`. Every occurrence that
passes the filters is retained so it can be counted and covered, and the last
two rows show what that costs: the same 379 k and 2.4 M subgraphs, but two
orders of magnitude more surviving patterns once the boundary-output cap is
removed.

So set `MAX_OUTPUTS` (and `MAX_INPUTS`) whenever you push `MAX_SIZE` past 4.
They do not shrink the enumeration itself — adding a cell to a pattern can just
as easily *absorb* a boundary output as create one, so there is nothing sound to
prune on — but they are checked before canonicalisation, which is the expensive
part, and before anything is stored.

## Flow runners

Two runners in `examples/full_flow/` drive the Makefile targets:

- **`flow.py`** (`make flow`) — pattern extraction, rewrite and LEC. `FLOW_FULL`
  holds the complete pipeline including characterisation and minimisation;
  `FLOW` is the active, shorter definition that stops at the LEC gate.
- **`flow_opt.py`** (`make flow-opt`) — mines once, then rewrites and LEC-checks
  both the full and the elite libraries, and prints the trade-off between them.

Both expose the mining and elite knobs as module-level constants at the top of
the file.

## Module map

| Module | Responsibility |
|--------|----------------|
| `cli.py` | Argument parsing, config merging, command implementations |
| `config.py` | `AionOptConfig` dataclass, YAML loading, validation |
| `graph/circuit.py` | `Circuit` / `Instance` / `Net` model, indexed `bit -> net` lookup |
| `graph/builder.py` | Signal-flow graph, pin edges, per-instance edge index |
| `pattern/miner.py` | ESU enumeration, filters, parallel driver |
| `pattern/canonical.py` | Canonical labelling by colour refinement |
| `pattern/subgraph.py` | `Pattern` model, boundary splitting |
| `pattern/cover.py` | Greedy cover and the reuse re-filter |
| `cellgen/generator.py` | Verilog cell rendering, module and port naming |
| `io/cell_lib.py` | Technology dictionary, drive-strength collapsing |
| `io/cell_file.py` | Cell-library file format, canonical-key markers |
| `io/selection.py` | Selection cache shared between commands |
| `io/complements.py` | Inverter detection, complement availability, the plan |
| `io/rewriter.py` | Hierarchical and flat netlist rewriting, complement wiring |
| `io/netlist_writer.py` | Verilog emission |
| `io/yosys_json.py`, `io/verilog_to_json.py` | Yosys front end |
| `report/reporter.py` | JSON / Markdown / HTML reports, elite ranking |

## Tests

```bash
make aion-opt-test
# or
python -m pytest tools/aion_opt/tests -q
```

| File | Covers |
|------|--------|
| `test_miner.py` | ESU is exhaustive, duplicate-free, and independent of how roots are partitioned |
| `test_canonical.py` | Canonical keys are relabelling-invariant and structure-complete |
| `test_cover.py` | Disjointness, the reuse re-filter, determinism |
| `test_cell_lib.py` | Drive-strength collapsing, sequential/physical cell exclusion |
| `test_config.py` | YAML coverage and CLI precedence |
| `test_end_to_end.py` | Real CLI runs: cell format, elite subset, rewrite, cache reuse, custom prefix, `--jobs` invariance |
| `test_complements.py` | Inverter recognition, complement lookup (per bit, not per bus), the cost arithmetic |
| `test_cell_file_markers.py` | Both library markers, including through an elite slice |
| `test_complement_flow.py` | The whole inverted-input loop, Yosys-proved — and proved to reject a mis-driven port |

The end-to-end tests need Yosys on `PATH` and skip themselves otherwise. LEC and
SEC are not part of the suite because they need the EDA container; run
`make flow-opt` or `make aion-opt-run-all` for those gates.
