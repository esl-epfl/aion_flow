# `aion_char`

`aion_char` validates and characterizes the custom AION cells produced by `aion_opt`.

It provides two generators:

- **`tb_generator`** — exhaustive, self-checking SystemVerilog and SPICE testbenches for every cell in `aion_cells.v`.
- **`characterizer`** — ngspice-based Liberty characterization that produces one `.lib` file per process corner.

All generated outputs land under `build/aion_char/` by default.

## Quick start

Everything runs inside the EDA container — the PDK, cell models, and device models live under `/foss/pdks`.

```bash
# Generate testbenches and run both SV and SPICE simulations
./scripts/docker_run.sh "make aion-char-all"

# Or one layer at a time
./scripts/docker_run.sh "make aion-char-generate"   # write tb/
./scripts/docker_run.sh "make aion-char-sv"         # Verilator + Icarus
./scripts/docker_run.sh "make aion-char-spice"      # ngspice
```

## Available targets

| Target | Description |
|--------|-------------|
| `make aion-char-generate` | Generate `tb/sv` and `tb/spice` from `aion_cells.v` |
| `make aion-char-verilator` | Run SV testbenches with Verilator |
| `make aion-char-icarus` | Run SV testbenches with Icarus Verilog |
| `make aion-char-sv` | Run both SV simulators |
| `make aion-char-spice` | Run transistor-level SPICE testbenches |
| `make aion-char-all` | `sv` + `spice` |
| `make aion-char-plot` | Plot SPICE waveforms (`TB=tb_<module>`) |
| `make aion-char-wave-sv` | Open SV waveform in GTKWave (`TB=tb_<module>`) |
| `make aion-char-wave-spice` | Open SPICE waveform in GTKWave (`TB=tb_<module>`) |
| `make aion-char-lib` | Characterize a cell into `.lib` per corner |
| `make aion-char-lib-selfcheck` | Characterize a PDK cell and diff against its own `.lib` |
| `make aion-char-lib-template` | Print the Liberty template |
| `make aion-char-clean` | Remove all `build/aion_char/` outputs |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BUILD_DIR` | `build` | Root build directory |
| `BUILD_DIR_CHAR` | `$(BUILD_DIR)/aion_char` | Output directory for `aion_char` |
| `NETLIST` | `tools/aion_char/aion_cells.v` | Netlist under test |
| `LIB` | `.../sg13g2_stdcell_typ_1p20V_25C.lib` | Liberty oracle |
| `CELL_V` | PDK Verilog models | Standard-cell Verilog models |
| `CELL_SP` | PDK SPICE netlist | Standard-cell SPICE subcircuits |
| `MODEL_LIB` | PDK corner MOS lib | ngspice device-model library |
| `MODULE` | — | Restrict to one or more cell names |
| `CUSTOM` | — | Additional custom SPICE netlist for comparison |

### Worked example

A bare-transistor AION NAND2 example is provided under `examples/aion_char/`:

```bash
./scripts/docker_run.sh "make aion-char-lib"
```

This characterizes `AION_nand2_11` from `examples/aion_char/aion_nand2_11_flat.spice`.
