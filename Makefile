# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-27 16:19:43
#  Updated:                   2026-08-27 18:08:09
#  Description:               AION Flow - Makefile
# ================================================================

include scripts/utils.mk

.PHONY: aion-opt-graph2verilog aion-opt-generate-cells aion-opt-rewrite \
        aion-opt-run-all aion-opt-lec aion-opt-sec aion-opt-clean \
        aion-char-generate aion-char-verilator aion-char-icarus aion-char-sv \
        aion-char-spice aion-char-all aion-char-plot aion-char-wave-sv \
        aion-char-wave-spice aion-char-lib aion-char-lib-selfcheck \
        aion-char-lib-template aion-char-clean aion-char-clean-tb \
        aion-char-clean-lib aion-char-clean-build \
        clean clean_aion_opt clean_aion_char

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------
BUILD_DIR         ?= build
BUILD_DIR_OPT     ?= $(BUILD_DIR)/aion_opt
BUILD_DIR_CHAR    ?= $(BUILD_DIR)/aion_char
AION_IN_DOCKER    ?= 0
export AION_IN_DOCKER
AION_OPT_DIR      := tools/aion_opt

# Wrappers for aion_char targets: run directly inside the container, or invoke the
# shared Docker runner when called from the host.
AION_CHAR_DOCKER_PREFIX := $(if $(filter 1,$(AION_IN_DOCKER)),,./scripts/docker_run.sh ")
AION_CHAR_DOCKER_SUFFIX := $(if $(filter 1,$(AION_IN_DOCKER)),,")
AION_CHAR_DIR     := tools/aion_char
PYTHONPATH        := $(AION_OPT_DIR):$(AION_CHAR_DIR):$(PYTHONPATH)
AION_OPT          := python3 -m aion_opt
VERIFY_SCRIPT     := scripts/verify/run_lec_sec.py

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
INPUT             ?= examples/aion_opt/pm32.nl.v
TOP               ?= pm32
CELL_LIB          ?= tech/tech_dict/sg13g2_stdcell.json

# ---------------------------------------------------------------------------
# Mining parameters
# ---------------------------------------------------------------------------
MAX_SIZE          ?= 3
MIN_OCCURRENCES   ?= 2
AREA_FACTOR       ?= 0.85

# ---------------------------------------------------------------------------
# Output paths (per command)
# ---------------------------------------------------------------------------
GRAPH2V_OUTPUT    ?= $(BUILD_DIR_OPT)/$(TOP)_graph2verilog.v
CELLS             ?= $(BUILD_DIR_OPT)/aion_cells.v
PATTERN_REPORT    ?= $(BUILD_DIR_OPT)/pattern_report.json
REWRITE_NETLIST   ?= $(BUILD_DIR_OPT)/$(TOP)_optimized.v
REWRITE_REPORT    ?= $(BUILD_DIR_OPT)/report
RUN_ALL_FLAT      ?= $(BUILD_DIR_OPT)/$(TOP)_optimized_flat.v

# ---------------------------------------------------------------------------
# Config file support
# ---------------------------------------------------------------------------
CONFIG            ?=

# ---------------------------------------------------------------------------
# Verification inputs
# ---------------------------------------------------------------------------
REF               ?= $(INPUT)
MOD               ?= $(REWRITE_NETLIST) $(CELLS)
RTL               ?= examples/aion_opt/pm32.v examples/aion_opt/spm.v
NETLIST           ?= $(RUN_ALL_FLAT)
LIB               ?=

# ---------------------------------------------------------------------------
# aion_opt subcommands
# ---------------------------------------------------------------------------
aion-opt-graph2verilog: ## Convert input netlist to structural Verilog
	@mkdir -p $(BUILD_DIR_OPT)/work
	PYTHONPATH=$(PYTHONPATH) $(AION_OPT) graph2verilog \
		--input $(INPUT) \
		--cell-lib $(CELL_LIB) \
		--top $(TOP) \
		--work-dir $(BUILD_DIR_OPT)/work \
		--output $(GRAPH2V_OUTPUT)

aion-opt-generate-cells: ## Mine patterns and generate AION cells
	@mkdir -p $(BUILD_DIR_OPT)/work
	PYTHONPATH=$(PYTHONPATH) $(AION_OPT) generate-cells \
		--input $(INPUT) \
		--cell-lib $(CELL_LIB) \
		--top $(TOP) \
		--work-dir $(BUILD_DIR_OPT)/work \
		--max-size $(MAX_SIZE) \
		--min-occurrences $(MIN_OCCURRENCES) \
		--area-factor $(AREA_FACTOR) \
		--output-cells $(CELLS) \
		--output-report $(PATTERN_REPORT)

aion-opt-rewrite: ## Rewrite netlist with generated cells
	@mkdir -p $(BUILD_DIR_OPT)/work
	PYTHONPATH=$(PYTHONPATH) $(AION_OPT) rewrite \
		--input $(INPUT) \
		--cell-lib $(CELL_LIB) \
		--top $(TOP) \
		--work-dir $(BUILD_DIR_OPT)/work \
		--cells $(CELLS) \
		--output-netlist $(REWRITE_NETLIST) \
		--output-report $(REWRITE_REPORT) \
		--max-size $(MAX_SIZE) \
		--min-occurrences $(MIN_OCCURRENCES) \
		--area-factor $(AREA_FACTOR)

aion-opt-run-all: ## Run the full aion_opt flow end-to-end
	@mkdir -p $(BUILD_DIR_OPT)/work
ifneq ($(CONFIG),)
	PYTHONPATH=$(PYTHONPATH) $(AION_OPT) run-all \
		--config $(CONFIG) \
		--output-dir $(BUILD_DIR_OPT) \
		--rtl $(RTL)
else
	PYTHONPATH=$(PYTHONPATH) $(AION_OPT) run-all \
		--input $(INPUT) \
		--cell-lib $(CELL_LIB) \
		--top $(TOP) \
		--output-dir $(BUILD_DIR_OPT) \
		--max-size $(MAX_SIZE) \
		--min-occurrences $(MIN_OCCURRENCES) \
		--area-factor $(AREA_FACTOR) \
		--rtl $(RTL)
endif

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
aion-opt-lec: ## Run logical equivalence check (LEC)
	@mkdir -p $(BUILD_DIR_OPT)/logs
	$(VERIFY_SCRIPT) lec \
		--ref $(REF) \
		--mod $(MOD) \
		$(if $(LIB),--lib $(LIB)) \
		$(if $(filter 1,$(AION_IN_DOCKER)),--in-docker) \
		--log-dir $(BUILD_DIR_OPT)/logs

aion-opt-sec: ## Run sequential equivalence check (SEC)
	@mkdir -p $(BUILD_DIR_OPT)/logs
	$(VERIFY_SCRIPT) sec \
		--rtl $(RTL) \
		--netlist $(NETLIST) \
		$(if $(LIB),--lib $(LIB)) \
		$(if $(filter 1,$(AION_IN_DOCKER)),--in-docker) \
		--log-dir $(BUILD_DIR_OPT)/logs

# ---------------------------------------------------------------------------
# aion_char subcommands
# ---------------------------------------------------------------------------
aion-char-generate: ## Generate aion_char SV/SPICE testbenches
	@mkdir -p $(BUILD_DIR_CHAR)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) generate \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-verilator: ## Run aion_char Verilator testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) verilator \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-icarus: ## Run aion_char Icarus testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) icarus \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-sv: ## Run aion_char SystemVerilog testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) sv \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-spice: ## Run aion_char SPICE testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) spice \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-all: ## Run aion_char SV + SPICE testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) all \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-plot: ## Plot aion_char SPICE waveforms (TB=tb_<module>)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) plot \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-wave-sv: ## View aion_char SV waveforms in GTKWave (TB=tb_<module>)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) wave-sv \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-wave-spice: ## View aion_char SPICE waveforms in GTKWave (TB=tb_<module>)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) wave-spice \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-lib: ## Characterize a cell into Liberty .lib files
	@mkdir -p $(BUILD_DIR_CHAR)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) lib \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-lib-selfcheck: ## Self-check characterization against PDK .lib
	@mkdir -p $(BUILD_DIR_CHAR)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) lib-selfcheck \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-lib-template: ## Print the Liberty template
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) lib-template \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
aion-opt-clean: ## Remove aion_opt build outputs
	rm -rf $(BUILD_DIR_OPT)

aion-char-clean: ## Remove aion_char build outputs
	rm -rf $(BUILD_DIR_CHAR)

aion-char-clean-tb: ## Remove aion_char generated testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) clean-tb \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-clean-lib: ## Remove aion_char generated Liberty libraries
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) clean-lib \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-clean-build: ## Remove aion_char simulator build products only
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) clean-build \
		BUILD_DIR_CHAR=$(BUILD_DIR_CHAR)$(AION_CHAR_DOCKER_SUFFIX)

clean: ## Remove all build outputs
	rm -rf $(BUILD_DIR)

clean_aion_opt: ## Alias for aion-opt-clean
	$(MAKE) aion-opt-clean

clean_aion_char: ## Alias for aion-char-clean
	$(MAKE) aion-char-clean
