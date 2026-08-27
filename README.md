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
| `make aion-opt-graph2verilog` | Convert netlist to structural Verilog |
| `make aion-opt-generate-cells` | Mine patterns and emit AION cells |
| `make aion-opt-rewrite` | Rewrite netlist using generated cells |
| `make aion-opt-run-all` | Full flow end-to-end |
| `make aion-opt-lec` | Logical equivalence check |
| `make aion-opt-sec` | Sequential equivalence check |
| `make aion-opt-clean` | Remove build outputs |

## Cluster extraction (`aion_opt`)

The `aion_opt` tool (under `tools/aion_opt/`) takes a post-synthesis netlist, mines recurring combinational patterns, generates new structural Verilog cells for those patterns, and rewrites the netlist to use them. The result is a hierarchical optimized netlist, a flat equivalent, the generated AION cell library, and reports.

### Commands

All commands are available through the root `Makefile` and write into `BUILD_DIR`.

#### `aion-opt-graph2verilog`

Reads the input netlist (Yosys JSON or Verilog), builds the internal circuit graph, and emits an equivalent structural Verilog netlist. Useful as a sanity check for the parser/emitter.

```bash
make aion-opt-graph2verilog INPUT=examples/aion_opt/pm32.nl.v TOP=pm32
```

Output: `$(GRAPH2V_OUTPUT)` (default: `$(BUILD_DIR)/$(TOP)_graph2verilog.v`)

#### `aion-opt-generate-cells`

Mines recurring combinational patterns and generates one Verilog module per selected pattern. The selection is greedy and non-overlapping; only patterns that save area according to `AREA_FACTOR` are kept.

```bash
make aion-opt-generate-cells \
    INPUT=examples/aion_opt/pm32.nl.v \
    TOP=pm32 \
    MAX_SIZE=3 \
    MIN_OCCURRENCES=2 \
    AREA_FACTOR=0.85
```

Outputs:
- `$(CELLS)` (default: `$(BUILD_DIR)/aion_cells.v`) — generated AION cell library
- `$(PATTERN_REPORT)` (default: `$(BUILD_DIR)/pattern_report.json`) — pattern mining report

#### `aion-opt-rewrite`

Rewrites the input netlist by replacing occurrences of the mined patterns with instances of the generated AION cells.

```bash
make aion-opt-rewrite \
    INPUT=examples/aion_opt/pm32.nl.v \
    TOP=pm32 \
    BUILD_DIR=build/pm32
```

Outputs:
- `$(REWRITE_NETLIST)` (default: `$(BUILD_DIR)/$(TOP)_optimized.v`) — hierarchical netlist using AION cells
- `$(REWRITE_REPORT).json`, `.md`, `.html` (default: `$(BUILD_DIR)/report`) — rewrite reports

> **How rewrite knows what to replace:** `aion-opt-rewrite` re-runs the graph construction and pattern mining on the input netlist (using the same `MAX_SIZE`, `MIN_OCCURRENCES`, and `AREA_FACTOR`), regenerates the AION cell modules, and then substitutes each selected occurrence with the matching regenerated cell. The `CELLS` variable therefore acts as an **output path** for the regenerated cell library, not as an input list of pre-generated cells.

#### `aion-opt-run-all`

Runs the complete flow in one shot: pattern mining, cell generation, hierarchical and flat netlist rewriting, reports, and LEC. SEC is run automatically if matching RTL files are found under the searched RTL directories.

```bash
make aion-opt-run-all \
    INPUT=examples/aion_opt/pm32.nl.v \
    TOP=pm32 \
    BUILD_DIR=build/pm32
```

You can also pass a YAML config; when `CONFIG` is set, the other arguments are read from the config file:

```bash
make aion-opt-run-all CONFIG=examples/aion_opt/aion_opt.yaml BUILD_DIR=build/pm32
```

Outputs in `$(BUILD_DIR)`:
- `aion_cells.v`
- `$(TOP)_optimized.v`
- `$(TOP)_optimized_flat.v`
- `report.json`, `report.md`, `report.html`
- `work/` — intermediate files (e.g. Verilog-to-Yosys-JSON conversion)
- `logs/` — LEC/SEC logs and artifacts

### Configuration flags

The following Makefile variables control the cluster-extraction flow:

| Variable | Default | Description |
|----------|---------|-------------|
| `INPUT` | `examples/aion_opt/pm32.nl.v` | Input netlist (`.v`, `.sv`, or Yosys `.json`) |
| `TOP` | `pm32` | Top module name |
| `CELL_LIB` | `tech/tech_dict/sg13g2_stdcell.json` | JSON technology dictionary used by `aion_opt` |
| `BUILD_DIR` | `build/aion_opt` | Directory for all outputs |
| `MAX_SIZE` | `3` | Maximum pattern size to mine (number of cells) |
| `MIN_OCCURRENCES` | `2` | Minimum occurrences for a pattern to be kept |
| `AREA_FACTOR` | `0.85` | Scaling factor for the generated AION cell area. Used to compute estimated area savings in reports and to score occurrences during greedy cover selection. |

Per-command output variables:

| Variable | Default | Used by |
|----------|---------|---------|
| `GRAPH2V_OUTPUT` | `$(BUILD_DIR)/$(TOP)_graph2verilog.v` | `graph2verilog` |
| `CELLS` | `$(BUILD_DIR)/aion_cells.v` | `generate-cells`, `rewrite`, `run-all` |
| `PATTERN_REPORT` | `$(BUILD_DIR)/pattern_report.json` | `generate-cells` |
| `REWRITE_NETLIST` | `$(BUILD_DIR)/$(TOP)_optimized.v` | `rewrite`, `run-all` |
| `REWRITE_REPORT` | `$(BUILD_DIR)/report` | `rewrite`, `run-all` |
| `RUN_ALL_FLAT` | `$(BUILD_DIR)/$(TOP)_optimized_flat.v` | `run-all`, `sec` |

Verification-specific variables (used by `aion-opt-lec` and `aion-opt-sec`):

| Variable | Default | Description |
|----------|---------|-------------|
| `REF` | `$(INPUT)` | Reference netlist for LEC |
| `MOD` | `$(REWRITE_NETLIST) $(CELLS)` | Modified netlist(s) for LEC |
| `RTL` | *(none)* | RTL source file(s) for SEC |
| `NETLIST` | `$(RUN_ALL_FLAT)` | Synthesized netlist for SEC |
| `LIB` | `tech/lib/sg13g2_stdcell_typ_1p20V_25C.lib` | Liberty timing library for formal checks (script default) |

### YAML config

You can also drive the CLI with a YAML config file. CLI/Makefile values override config values when both are provided.

```bash
python -m aion_opt run-all --config examples/aion_opt/aion_opt.yaml --output-dir build/pm32
```
