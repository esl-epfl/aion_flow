# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-27 16:19:43
#  Updated:                   2026-08-27 16:21:32
#  Description:               AION Flow - Makefile
# ================================================================

include scripts/utils.mk

.PHONY: aion-opt-graph2verilog aion-opt-generate-cells aion-opt-rewrite \
        aion-opt-run-all aion-opt-lec aion-opt-sec aion-opt-clean \
        clean clean_aion_opt

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------
BUILD_DIR         ?= build
BUILD_DIR_OPT     ?= $(BUILD_DIR)/aion_opt
AION_OPT_DIR      := tools/aion_opt
PYTHONPATH        := $(AION_OPT_DIR):$(PYTHONPATH)
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
RTL               ?=
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
		--output-dir $(BUILD_DIR_OPT)
else
	PYTHONPATH=$(PYTHONPATH) $(AION_OPT) run-all \
		--input $(INPUT) \
		--cell-lib $(CELL_LIB) \
		--top $(TOP) \
		--output-dir $(BUILD_DIR_OPT) \
		--max-size $(MAX_SIZE) \
		--min-occurrences $(MIN_OCCURRENCES) \
		--area-factor $(AREA_FACTOR)
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
		--log-dir $(BUILD_DIR_OPT)/logs

aion-opt-sec: ## Run sequential equivalence check (SEC)
	@mkdir -p $(BUILD_DIR_OPT)/logs
	$(VERIFY_SCRIPT) sec \
		--rtl $(RTL) \
		--netlist $(NETLIST) \
		$(if $(LIB),--lib $(LIB)) \
		--log-dir $(BUILD_DIR_OPT)/logs

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
aion-opt-clean: ## Remove aion_opt build outputs
	rm -rf $(BUILD_DIR_OPT)

clean: ## Remove all build outputs
	rm -rf $(BUILD_DIR)
