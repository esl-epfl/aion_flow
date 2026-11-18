<h1 align="center">AION Flow</h1>
<p align="center"><strong><em>AI-Based Standard Cells Generation</em></strong></p>

The tools AION runs between a synthesized netlist and a drawn standard cell.
Inside `aion_framework` this repository is a submodule and the framework drives the tools directly
(`python -m aion`); the Makefile here is for using them on their own.

## Quick start

Requirements: Python 3 with `tools/aion_opt/requirements.txt`,
`tools/aion_char/requirements.txt` and `sympy` + `networkx` for
aion_minimizer, Yosys on `PATH`, and the
`iic-osic-tools_shell_uid_1000` container for everything that needs the PDK
(aion_char, LEC/SEC, the layout tool). From the host, those targets enter the
container through `scripts/docker_run.sh`, which expects this checkout mounted
at `/foss/designs/aion_flow` (set `AION_IN_DOCKER=1` when already inside it).
The Makefile sets `PYTHONPATH` for the tools itself. `env.sh` is git-ignored:
keep any local setup there.

Run the full cluster-extraction flow:

```bash
make aion-opt-run-all
```

Outputs land under `build/aion_opt/` by default. Use `BUILD_DIR=` to redirect:

```bash
make aion-opt-run-all BUILD_DIR=build/pm32
```

Or drive it from a YAML config:

```bash
make aion-opt-run-all CONFIG=examples/aion_opt/aion_opt.yaml BUILD_DIR=build/pm32
```

## Available targets

| Target | Description |
|--------|-------------|
`make help` prints every target. The main ones:

| Target | Description |
|--------|-------------|
| `make aion-opt-run-all` | Full aion_opt flow end-to-end |
| `make aion-opt-graph2verilog` | Convert netlist to structural Verilog |
| `make aion-opt-generate-cells` | Mine patterns and emit AION cells |
| `make aion-opt-select-elite` | Cut an existing cell library down to `ELITE_COUNT` cells |
| `make aion-opt-rewrite` | Rewrite netlist using generated cells |
| `make aion-opt-complement-plan` | Decide which complemented cell inputs come from outside the cell |
| `make aion-opt-lec` | Logical equivalence check |
| `make aion-opt-sec` | Sequential equivalence check |
| `make aion-opt-test` | Run the aion_opt test suite |
| `make aion-opt-clean` | Remove aion_opt build outputs |
| `make aion-char-generate` | Generate SV/SPICE testbenches for AION cells |
| `make aion-char-sv` | Run SystemVerilog testbenches (`aion-char-verilator`, `aion-char-icarus` for one simulator) |
| `make aion-char-spice` | Run SPICE testbenches |
| `make aion-char-all` | Run SV + SPICE testbenches |
| `make aion-char-lib` | Characterize a cell into Liberty `.lib` files |
| `make aion-char-verify-spice CELL=... SPICE=...` | Verify a custom SPICE netlist for a cell |
| `make aion-char-clean` | Remove aion_char build outputs |
| `make aion-minimizer-run` | Minimize a gate-level SPICE netlist |
| `make run-aion-minimizer-batch INPUT_DIR=... OUTPUT_DIR=...` | Minimize every SPICE cell in a directory |
| `make aion-minimizer-verify-spice CELL=... SPICE=...` | Verify a minimized cell with aion_char SPICE |
| `make aion-minimizer-test` | Run the aion_minimizer test suite |
| `make aion-minimizer-clean` | Remove aion_minimizer build outputs |
| `make aion-layout-verify` | Build + DRC + LVS of a cell generator, one `RESULT:` line |
| `make aion-layout-flow` | Verify, PEX, baseline, characterize, export, compare |
| `make aion-layout-test` | Run the aion_layout host-side test suite |
| `make flow` / `make flow-opt` | The example runners in `examples/full_flow/` |
| `make clean` | Remove `BUILD_DIR` (default `build/`) |

The other `aion-layout-*` targets (`scaffold`, `gds`, `png`, `drc`, `lvs`,
`pin-access`, `pex`, `evidence`, `baseline`, `characterize`, `compare`,
`export`, `resize`, `clean`) forward to the same-named targets of
`tools/aion_layout_claude/Makefile`.

## Flow overview

AION Flow is split into four tools. Each has its own directory, Makefile targets, and README with full usage details.

### Cluster extraction — `aion_opt`

The `aion_opt` tool (under `tools/aion_opt/`) takes a post-synthesis netlist, mines recurring combinational patterns, generates new structural Verilog cells, and rewrites the netlist to use them.

See [`tools/aion_opt/README.md`](tools/aion_opt/README.md) for commands, configuration flags, and YAML config.

### Cell validation and characterization — `aion_char`

The `aion_char` tool (under `tools/aion_char/`) validates the AION cells produced by `aion_opt` with exhaustive testbenches and characterizes them into Liberty libraries.

See [`tools/aion_char/README.md`](tools/aion_char/README.md) for commands and configuration flags.

### Gate-level SPICE minimization — `aion_minimizer`

The `aion_minimizer` tool (under `tools/aion_minimizer/`) takes a small gate-level SPICE netlist and re-implements it as one transistor-level SPICE cell. It reads the Boolean function out of the PDK transistors, partitions the gate DAG into the cheapest set of complementary CMOS stages, sizes the devices, and can prove the result equivalent by exhaustive switch-level simulation.

Partitioning rather than always merging everything into one gate is what keeps XOR-heavy cells sane: a part that resynthesis cannot beat keeps its PDK cells, so **the result is never worse than the netlist it was given**.

See [`tools/aion_minimizer/README.md`](tools/aion_minimizer/README.md) for commands and configuration flags.

### Standard-cell layout — `aion_layout_claude`

The layout tool (under `tools/aion_layout_claude/`, Python package `aion_layout`) takes a transistor-level `.subckt` and a cell generator written by a model, and does everything mechanical: GDS build, Magic + KLayout DRC, Netgen LVS, PEX, an abutted PDK-cell baseline, Liberty characterization, the `gds`/`lef`/`lib`/`v`/`spice`/`cdl` export and the comparison against that baseline. [`SKILL.md`](tools/aion_layout_claude/SKILL.md) is what the drawing agent works from.

See [`tools/aion_layout_claude/README.md`](tools/aion_layout_claude/README.md).

`tools/aion_layout_kimi/` is an earlier, self-contained closed-loop harness that calls a model through a Copilot gateway (`orchestrate.sh`). No root Makefile target and nothing in `aion_framework` uses it; see its own [README](tools/aion_layout_kimi/README.md).

### Inverted inputs — across `aion_opt` and `aion_minimizer`

When a merged cell needs a complemented copy of one of its inputs, the inverter can live inside the cell or arrive on a `<port>_bar` port that the parent netlist drives. `aion_opt complement-plan` decides that per cell and per input by costing both options against the netlist the cells will actually be instantiated in.

See [Inverted inputs](tools/aion_opt/README.md#inverted-inputs) for the loop and the numbers.
