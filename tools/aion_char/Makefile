# Custom (AION) standard-cell macros: generate and run exhaustive testbenches,
# and characterize custom cells into Liberty libraries.
#
# This Makefile pre-fills the ihp-sg13g2 paths so that in this repo a plain
# `make generate` / `make all` just works. All generated outputs land under
# $(BUILD_DIR_CHAR) (default: <repo-root>/build/aion_char).

MAKEFILE_DIR := $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
REPO_ROOT    := $(realpath $(MAKEFILE_DIR)/../..)

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
BUILD_DIR_CHAR ?= $(REPO_ROOT)/build/aion_char

# If a relative BUILD_DIR_CHAR was passed (e.g. from the root Makefile), resolve
# it against the repo root so it is unambiguous regardless of which directory
# the sub-make runs in.
_BUILD_DIR_CHAR_ABS := $(if $(filter /%,$(BUILD_DIR_CHAR)),$(BUILD_DIR_CHAR),$(REPO_ROOT)/$(BUILD_DIR_CHAR))

# ---------------------------------------------------------------------------
# PDK paths
# ---------------------------------------------------------------------------
PDK_ROOT ?= /foss/pdks
PDK      ?= ihp-sg13g2
STDCELL  := $(PDK_ROOT)/$(PDK)/libs.ref/sg13g2_stdcell
TECH     := $(PDK_ROOT)/$(PDK)/libs.tech

# Gold oracle: the `function` attributes of the standard cells.
LIB      ?= $(STDCELL)/lib/sg13g2_stdcell_typ_1p20V_25C.lib

# Simulation models for the standard cells.
CELL_V   ?= $(STDCELL)/verilog/sg13g2_stdcell.v $(STDCELL)/verilog/sg13g2_udp.v

# Transistor-level views and device models.
CELL_SP       ?= $(STDCELL)/spice/sg13g2_stdcell.spice
MODEL_LIB     ?= $(TECH)/ngspice/models/cornerMOSlv.lib
MODEL_SECTION ?= mos_tt
VDD           ?= 1.2

# ---------------------------------------------------------------------------
# Tool / package paths
# ---------------------------------------------------------------------------
AION_CHAR_DIR := $(MAKEFILE_DIR)
PYTHONPATH    := $(AION_CHAR_DIR):$(PYTHONPATH)

NETLIST       ?= $(MAKEFILE_DIR)aion_cells.v
TB_DIR        ?= $(_BUILD_DIR_CHAR_ABS)/tb
LIB_DIR       ?= $(_BUILD_DIR_CHAR_ABS)/lib
SELFCHECK_DIR ?= $(_BUILD_DIR_CHAR_ABS)/lib-selfcheck

GEN      := cd $(REPO_ROOT) && PYTHONPATH=$(PYTHONPATH) python3 -m aion_char generate
GEN_LIB  := cd $(REPO_ROOT) && PYTHONPATH=$(PYTHONPATH) python3 -m aion_char lib

# Optional raw-to-VCD converter for SPICE VCD output.
RAW2VCD  ?=

# Optional custom SPICE netlist and module restriction.
CUSTOM   ?=
MODULE   ?=

# Which testbench the waveform targets open.
TB       ?=

# Which layer to generate.
EMIT     ?= both

# ---------------------------------------------------------------------------
# Testbench generation flags
# ---------------------------------------------------------------------------
GEN_FLAGS := $(NETLIST) \
             --lib $(LIB) \
             $(addprefix --cell-verilog ,$(CELL_V)) \
             $(addprefix --cell-spice ,$(CELL_SP)) \
             --model-lib $(MODEL_LIB) --model-section $(MODEL_SECTION) --vdd $(VDD) \
             $(if $(RAW2VCD),--raw2vcd $(RAW2VCD),) \
             --emit $(EMIT) \
             $(addprefix --custom-netlist ,$(CUSTOM)) \
             $(addprefix --module ,$(MODULE)) \
             -o $(TB_DIR)

.DEFAULT_GOAL := help

help: ## Show this help message
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
.PHONY: help

# What tb/ was last generated from. EMIT=, MODULE= and CUSTOM= change *which*
# testbenches are emitted, so the signature is recorded and compared.
TB_STAMP := $(TB_DIR)/.generated
TB_SIG   := $(TB_DIR)/.gen_sig
GEN_SIG  := $(strip $(EMIT)|$(MODULE)|$(CUSTOM))

generate: ## Regenerate tb/sv and tb/spice from the netlist and the PDK
	@mkdir -p $(TB_DIR)
	$(GEN) $(GEN_FLAGS)
	@touch $(TB_STAMP) && printf '%s' '$(GEN_SIG)' > $(TB_SIG)
.PHONY: generate

$(TB_STAMP): $(NETLIST) $(AION_CHAR_DIR)/aion_char/tb_generator.py
	@$(MAKE) --no-print-directory -C $(MAKEFILE_DIR) generate

ensure-tb: $(TB_STAMP) ## Ensure tb/ is present and up-to-date
	@if [ "$(GEN_SIG)" != "$$(cat $(TB_SIG) 2>/dev/null)" ]; then \
		$(MAKE) --no-print-directory -C $(MAKEFILE_DIR) generate; \
	fi
.PHONY: ensure-tb

ENSURE_SV    = $(MAKE) --no-print-directory -C $(MAKEFILE_DIR) ensure-tb EMIT=sv
ENSURE_SPICE = $(MAKE) --no-print-directory -C $(MAKEFILE_DIR) ensure-tb EMIT=spice
ENSURE_BOTH  = $(MAKE) --no-print-directory -C $(MAKEFILE_DIR) ensure-tb EMIT=both

TB_MODULE      = $(if $(MODULE),$(MODULE),$(patsubst tb_%,%,$(TB)))
ENSURE_SV_TB    = $(ENSURE_SV) $(if $(TB),MODULE=$(TB_MODULE),)
ENSURE_SPICE_TB = $(ENSURE_SPICE) $(if $(TB),MODULE=$(TB_MODULE),)

verilator: ## Run the generated SystemVerilog testbenches with Verilator
	@$(ENSURE_SV)
	@$(MAKE) --no-print-directory -C $(TB_DIR)/sv verilator
.PHONY: verilator

icarus: ## Run the generated SystemVerilog testbenches with Icarus Verilog
	@$(ENSURE_SV)
	@$(MAKE) --no-print-directory -C $(TB_DIR)/sv icarus
.PHONY: icarus

sv: ## Run the SystemVerilog testbenches (Verilator + Icarus)
	@$(ENSURE_SV)
	@$(MAKE) --no-print-directory -C $(TB_DIR)/sv all
.PHONY: sv

spice: ## Run the transistor-level SPICE testbenches with ngspice
	@$(ENSURE_SPICE)
	@$(MAKE) --no-print-directory -C $(TB_DIR)/spice spice
.PHONY: spice

all: ## Run every testbench: SystemVerilog and SPICE
	@$(ENSURE_BOTH)
	@$(MAKE) --no-print-directory -C $(TB_DIR)/sv all
	@$(MAKE) --no-print-directory -C $(TB_DIR)/spice spice
.PHONY: all

plot: ## Open the analog waveforms in ngspice's own plotter (usage: make plot TB=tb_<module>)
	@$(ENSURE_SPICE_TB)
	@$(MAKE) --no-print-directory -C $(TB_DIR)/spice plot $(if $(TB),TB=$(TB),)
.PHONY: plot

wave-sv: ## Open a SystemVerilog waveform in GTKWave (usage: make wave-sv TB=tb_<module>)
	@$(ENSURE_SV_TB)
	@$(MAKE) --no-print-directory -C $(TB_DIR)/sv wave $(if $(TB),TB=$(TB),)
.PHONY: wave-sv

wave-spice: ## Open a SPICE waveform in GTKWave (usage: make wave-spice TB=tb_<module>)
	@$(ENSURE_SPICE_TB)
	@$(MAKE) --no-print-directory -C $(TB_DIR)/spice wave $(if $(TB),TB=$(TB),)
.PHONY: wave-spice

# ---------------------------------------------------------------------------
# Liberty characterization
# ---------------------------------------------------------------------------
LIB_TMPL ?= $(MAKEFILE_DIR)templates/sg13g2.lib.tmpl

# Default worked example.
LIB_SPICE ?= $(if $(CUSTOM),$(CUSTOM),$(REPO_ROOT)/examples/aion_char/aion_nand2_11_flat.spice)
LIB_CELL  ?= $(if $(MODULE),$(MODULE),AION_nand2_11)
LIB_NAME  ?= $(LIB_CELL)
AREA      ?=

CORNERS   ?= typ:mos_tt:1.20:25 slow:mos_ss:1.08:125 fast:mos_ff:1.32:-40
SLEWS     ?= 0.0186, 0.0966, 0.174, 0.3294, 0.6408, 1.263, 2.5074
LOADS     ?= 0.001, 0.0234, 0.039, 0.0648, 0.108, 0.18, 0.3

JOBS      ?= 8
VERIFY    ?= 1
KEEP      ?= 0

DRIVER     ?=
DRIVER_IN  ?= A
DRIVER_OUT ?= X

LIB_FLAGS := --cell $(LIB_CELL) --verilog $(NETLIST) $(if $(LIB),--lib $(LIB),) \
             $(addprefix --cell-verilog ,$(CELL_V)) \
             $(addprefix --cell-spice ,$(CELL_SP)) \
             --model-lib $(MODEL_LIB) \
             $(addprefix --corner ,$(CORNERS)) \
             --template $(LIB_TMPL) \
             --slews "$(SLEWS)" --loads "$(LOADS)" \
             --lib-name $(LIB_NAME) --jobs $(JOBS) \
             $(if $(AREA),--area $(AREA),) \
             $(if $(DRIVER),--driver-cell $(DRIVER) --driver-input $(DRIVER_IN) --driver-output $(DRIVER_OUT),) \
             $(if $(filter 0,$(VERIFY)),--no-verify,) \
             $(if $(filter 1,$(KEEP)),--keep-decks,) \
             -o $(LIB_DIR)

lib: ## Characterize a cell into one .lib per corner
	@mkdir -p $(LIB_DIR)
	$(GEN_LIB) $(LIB_SPICE) $(LIB_FLAGS)
.PHONY: lib

SELFCHECK_CELL ?= sg13g2_nand2_1

lib-selfcheck: ## Characterize a PDK cell and diff against the PDK's own .lib
	@mkdir -p $(SELFCHECK_DIR)
	cd $(REPO_ROOT) && PYTHONPATH=$(PYTHONPATH) python3 -m aion_char lib $(CELL_SP) \
		--cell $(SELFCHECK_CELL) --lib $(LIB) --model-lib $(MODEL_LIB) \
		--corner typ:mos_tt:1.20:25 --template $(LIB_TMPL) \
		--slews "$(SLEWS)" --loads "$(LOADS)" \
		--lib-name selfcheck --jobs $(JOBS) --compare-lib $(LIB) \
		$(if $(DRIVER),--driver-cell $(DRIVER) --driver-input $(DRIVER_IN) --driver-output $(DRIVER_OUT),) \
		$(if $(filter 1,$(KEEP)),--keep-decks,) \
		-o $(SELFCHECK_DIR)
	@echo
	@sed -n '/^## Comparison/,$$p' $(SELFCHECK_DIR)/char_report.md
.PHONY: lib-selfcheck

lib-template: ## Print the Liberty template used to build the libraries
	@cd $(REPO_ROOT) && PYTHONPATH=$(PYTHONPATH) python3 -m aion_char lib --template $(LIB_TMPL) --print-template
.PHONY: lib-template

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
GENERATED := $(TB_DIR) $(LIB_DIR) $(SELFCHECK_DIR)

clean: ## Delete everything generated: tb/, lib/ and lib-selfcheck/
	rm -rf $(GENERATED)
	@echo "removed: $(notdir $(GENERATED))"
.PHONY: clean

clean-tb: ## Delete only the generated tb/ directory
	rm -rf $(TB_DIR)
.PHONY: clean-tb

clean-lib: ## Delete only the generated Liberty directories
	rm -rf $(LIB_DIR) $(SELFCHECK_DIR)
.PHONY: clean-lib

clean-build: ## Delete only simulator build products, keep generated testbenches
	@[ -f $(TB_DIR)/sv/Makefile ] && $(MAKE) --no-print-directory -C $(TB_DIR)/sv clean || true
	@[ -f $(TB_DIR)/spice/Makefile ] && $(MAKE) --no-print-directory -C $(TB_DIR)/spice clean || true
.PHONY: clean-build
