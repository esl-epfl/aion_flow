<h1 align="center">AION Flow</h1>
<p align="center"><strong><em>AI-Based Standard Cells Generation</em></strong></p>

## Quick start

Set up the environment:

```bash
source env.sh
```

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
| `make aion-opt-run-all` | Full aion_opt flow end-to-end |
| `make aion-opt-graph2verilog` | Convert netlist to structural Verilog |
| `make aion-opt-generate-cells` | Mine patterns and emit AION cells |
| `make aion-opt-rewrite` | Rewrite netlist using generated cells |
| `make aion-opt-lec` | Logical equivalence check |
| `make aion-opt-sec` | Sequential equivalence check |
| `make aion-opt-clean` | Remove aion_opt build outputs |
| `make aion-char-generate` | Generate SV/SPICE testbenches for AION cells |
| `make aion-char-sv` | Run SystemVerilog testbenches |
| `make aion-char-spice` | Run SPICE testbenches |
| `make aion-char-all` | Run SV + SPICE testbenches |
| `make aion-char-lib` | Characterize a cell into Liberty `.lib` files |
| `make aion-char-verify-spice` | Verify a custom SPICE netlist for a cell |
| `make aion-char-clean` | Remove aion_char build outputs |
| `make aion-minimizer-run` | Minimize a gate-level SPICE netlist |
| `make aion-minimizer-verify-spice CELL=...` | Minimize and verify with aion_char SPICE |
| `make aion-minimizer-clean` | Remove aion_minimizer build outputs |
| `make clean` | Remove all build outputs |

## Flow overview

AION Flow is split into three tools. Each has its own directory, Makefile targets, and README with full usage details.

### Cluster extraction — `aion_opt`

The `aion_opt` tool (under `tools/aion_opt/`) takes a post-synthesis netlist, mines recurring combinational patterns, generates new structural Verilog cells, and rewrites the netlist to use them.

See [`tools/aion_opt/README.md`](tools/aion_opt/README.md) for commands, configuration flags, and YAML config.

### Cell validation and characterization — `aion_char`

The `aion_char` tool (under `tools/aion_char/`) validates the AION cells produced by `aion_opt` with exhaustive testbenches and characterizes them into Liberty libraries.

See [`tools/aion_char/README.md`](tools/aion_char/README.md) for commands and configuration flags.

### Gate-level SPICE minimization — `aion_minimizer`

The `aion_minimizer` tool (under `tools/aion_minimizer/`) takes a small gate-level SPICE netlist and merges the gate instances into a single optimized transistor-level SPICE netlist. It can also feed the result into `aion_char` for SPICE verification.

See [`tools/aion_minimizer/README.md`](tools/aion_minimizer/README.md) for commands and configuration flags.
