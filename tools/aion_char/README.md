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
| `make aion-char-wave-sv` | Open SV waveform in Surfer (`TB=tb_<module>`, `VIEWER=gtkwave` for GTKWave) |
| `make aion-char-wave-spice` | Open SPICE waveform in Surfer (`TB=tb_<module>`, `VIEWER=gtkwave` for GTKWave) |
| `make aion-char-lib` | Characterize a cell into `.lib` per corner |
| `make aion-char-lib-selfcheck` | Characterize a PDK cell and diff against its own `.lib` |
| `make aion-char-lib-template` | Print the Liberty template |
| `make aion-char-cells` | Show the AION cell Verilog path and list available cells |
| `make aion-char-verify-spice` | Verify a custom SPICE netlist for one cell (`MODULE=...`, `SPICE=...`) |
| `make aion-char-clean` | Remove all `build/aion_char/` outputs |
| `make aion-char-clean-tb` | Remove only generated testbenches |
| `make aion-char-clean-lib` | Remove only generated Liberty libraries |
| `make aion-char-clean-build` | Remove only simulator build products |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BUILD_DIR` | `build` | Root build directory |
| `BUILD_DIR_CHAR` | `$(BUILD_DIR)/aion_char` | Output directory for `aion_char` |
| `NETLIST` | `examples/aion_char/aion_cells.v` | Netlist under test |
| `LIB` | `.../sg13g2_stdcell_typ_1p20V_25C.lib` | Liberty oracle |
| `CELL_V` | PDK Verilog models | Standard-cell Verilog models |
| `CELL_SP` | PDK SPICE netlist | Standard-cell SPICE subcircuits |
| `MODEL_LIB` | PDK corner MOS lib | ngspice device-model library |
| `MODEL_SECTION` | `mos_tt` | Corner section in `MODEL_LIB` |
| `VDD` | `1.2` | Supply voltage |
| `MODULE` | — | Restrict generation/simulation to one or more cell names |
| `CUSTOM` | — | Additional custom SPICE netlist for comparison |
| `CELL` | — | Cell name for `aion-char-verify-spice` |
| `SPICE` | — | Custom SPICE netlist path for `aion-char-verify-spice` |
| `VIEWER` | `surfer` | Waveform viewer for `wave-sv`/`wave-spice` (`gtkwave` or `surfer`) |
| `RAW2VCD` | `scripts/raw2vcd.py` | rawfile-to-VCD converter |
| `CORNERS` | `typ:... slow:... fast:...` | Characterization corners |
| `SLEWS` | 7 values | Input slews for characterization |
| `LOADS` | 7 values | Output loads for characterization |
| `JOBS` | `8` | Parallel jobs for characterization |
| `AREA` | — | Cell area override for `.lib` |
| `DRIVER` / `DRIVER_IN` / `DRIVER_OUT` | — | Optional driver cell for characterization |
| `VERIFY` | `1` | Set to `0` to skip Liberty verification |
| `KEEP` | `0` | Set to `1` to keep ngspice decks |
| `AION_IN_DOCKER` | `0` | Set to `1` when already inside the EDA container |

### Worked examples

A bare-transistor AION NAND2 example is provided under `examples/aion_char/`:

```bash
# Characterize AION_nand2_11 from the example SPICE netlist
./scripts/docker_run.sh "make aion-char-lib"
```

Verify a custom SPICE netlist against the generated testbench for a specific cell:

```bash
./scripts/docker_run.sh "make aion-char-verify-spice CELL=AION_nand2_11 SPICE=examples/aion_char/aion_nand2_11_flat.spice"
```

List the cells available in the current netlist:

```bash
make aion-char-cells
```
