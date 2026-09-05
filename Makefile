# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-27 16:19:43
#  Updated:                   2026-08-31 17:35:05
#  Description:               AION Flow - Makefile
# ================================================================

include scripts/utils.mk

REPO_ROOT := $(realpath .)

.PHONY: aion-opt-graph2verilog aion-opt-generate-cells aion-opt-rewrite \
        aion-opt-select-elite aion-opt-test aion-opt-complement-plan \
        aion-opt-run-all aion-opt-lec aion-opt-sec aion-opt-clean \
        aion-char-generate aion-char-verilator aion-char-icarus aion-char-sv \
        aion-char-spice aion-char-all aion-char-plot aion-char-wave-sv \
        aion-char-wave-spice aion-char-lib aion-char-lib-selfcheck \
        aion-char-lib-template aion-char-cells aion-char-verify-spice \
        aion-char-clean aion-char-clean-tb aion-char-clean-lib \
        aion-char-clean-build \
        split-spice-cells merge-spice-cells run-aion-minimizer-batch \
        aion-minimizer-run aion-minimizer-verify-spice aion-minimizer-clean \
        aion-minimizer-test \
        clean clean_aion_opt clean_aion_char clean_aion_minimizer \
        flow flow-opt

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------
BUILD_DIR         ?= build
BUILD_DIR_OPT     ?= $(BUILD_DIR)/aion_opt
BUILD_DIR_CHAR    ?= $(BUILD_DIR)/aion_char
BUILD_DIR_MIN     ?= $(BUILD_DIR)/aion_minimizer
AION_IN_DOCKER    ?= 0
export AION_IN_DOCKER
AION_OPT_DIR      := tools/aion_opt
AION_MIN_DIR      := tools/aion_minimizer

# Wrappers for aion_char targets: run directly inside the container, or invoke the
# shared Docker runner when called from the host.
AION_CHAR_DOCKER_PREFIX := $(if $(filter 1,$(AION_IN_DOCKER)),,./scripts/docker_run.sh ")
AION_CHAR_DOCKER_SUFFIX := $(if $(filter 1,$(AION_IN_DOCKER)),,")

AION_CHAR_DIR     := tools/aion_char
PYTHONPATH        := $(AION_OPT_DIR):$(AION_CHAR_DIR):$(AION_MIN_DIR):$(PYTHONPATH)
AION_OPT          := python3 -m aion_opt
AION_MIN          := python3 -m aion_minimizer
VERIFY_SCRIPT     := scripts/verify/run_lec_sec.py

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
INPUT             ?= examples/aion_opt/pm32.nl.v
TOP               ?= pm32
CELL_LIB          ?= tech/tech_dict/sg13g2_stdcell.json
AION_CHAR_NETLIST ?= $(REPO_ROOT)/examples/aion_char/aion_cells.v

# aion_minimizer inputs
AION_MIN_INPUT    ?= $(REPO_ROOT)/examples/aion_minimizer/AION_inv_nand2_nor2.spice
AION_MIN_GATES    ?= $(REPO_ROOT)/examples/aion_minimizer/sg13g2_stdcell.spice
AION_MIN_OUTPUT   ?= $(BUILD_DIR_MIN)/AION_inv_nand2_nor2_minimized.spice
AION_MIN_MODE     ?= transistor

# Convert host paths that are passed into the Docker container to the
# container-side mount point (/foss/designs/aion_flow/...).
AION_CHAR_NETLIST_ABS    := $(abspath $(AION_CHAR_NETLIST))
AION_CHAR_NETLIST_DOCKER := $(if $(filter 1,$(AION_IN_DOCKER)),$(AION_CHAR_NETLIST),$(subst $(REPO_ROOT),/foss/designs/aion_flow,$(AION_CHAR_NETLIST_ABS)))

# Allow NETLIST=... to override AION_CHAR_NETLIST when invoked from the flow.
AION_CHAR_NETLIST_FINAL  := $(if $(NETLIST),$(NETLIST),$(AION_CHAR_NETLIST))
AION_CHAR_NETLIST_FINAL_ABS    := $(abspath $(AION_CHAR_NETLIST_FINAL))
AION_CHAR_NETLIST_FINAL_DOCKER := $(if $(filter 1,$(AION_IN_DOCKER)),$(AION_CHAR_NETLIST_FINAL),$(subst $(REPO_ROOT),/foss/designs/aion_flow,$(AION_CHAR_NETLIST_FINAL_ABS)))

# ---------------------------------------------------------------------------
# Mining parameters
# ---------------------------------------------------------------------------
# MAX_SIZE        maximum number of standard cells per mined pattern
# MIN_OCCURRENCES minimum mined occurrences for a pattern to be kept
# MIN_SELECTED    minimum occurrences a pattern must still have after the
#                 non-overlapping cover (empty = same as MIN_OCCURRENCES,
#                 1 = keep single-use cells)
# MAX_OUTPUTS     cap on boundary outputs per pattern (empty = no limit)
# MAX_INPUTS      cap on boundary inputs per pattern (empty = no limit)
# AREA_FACTOR     assumed AION cell area relative to the cells it replaces
# JOBS            mining worker processes (empty = every available core)
MAX_SIZE          ?= 3
MIN_OCCURRENCES   ?= 2
MIN_SELECTED      ?=
AREA_FACTOR       ?= 0.85
MAX_OUTPUTS       ?=
MAX_INPUTS        ?=
JOBS              ?=
# COLLAPSE_STRENGTHS  1 (default) folds sg13g2_buf_1/_4/_16 onto one generic
#                     type; 0 treats every drive strength as its own cell
# ALLOW_OVERLAPPING   1 keeps every occurrence instead of a disjoint cover.
#                     Analysis only - generate-cells accepts it, rewrite does not.
COLLAPSE_STRENGTHS ?= 1
ALLOW_OVERLAPPING ?=

# ---------------------------------------------------------------------------
# Generated cell library
# ---------------------------------------------------------------------------
# CELL_PREFIX     prefix of every generated module (AION_ -> AION_nand2_nor2_0)
# ELITE_COUNT     size of the elite cell library (empty/0 = keep every cell)
# ELITE_METRIC    saved-area | occurrences | saved-area-per-cell
CELL_PREFIX       ?= AION_
ELITE_COUNT       ?=
ELITE_METRIC      ?= saved-area

# ---------------------------------------------------------------------------
# Output paths (per command)
# ---------------------------------------------------------------------------
GRAPH2V_OUTPUT    ?= $(BUILD_DIR_OPT)/$(TOP)_graph2verilog.v
CELLS             ?= $(BUILD_DIR_OPT)/aion_cells.v
ELITE_CELLS       ?= $(BUILD_DIR_OPT)/aion_cells_elite.v
PATTERN_REPORT    ?= $(BUILD_DIR_OPT)/pattern_report.json
REWRITE_NETLIST   ?= $(BUILD_DIR_OPT)/$(TOP)_optimized.v
REWRITE_FLAT      ?=
REWRITE_REPORT    ?= $(BUILD_DIR_OPT)/report
RUN_ALL_FLAT      ?= $(BUILD_DIR_OPT)/$(TOP)_optimized_flat.v
# Mining result shared between generate-cells and rewrite so the netlist is
# only mined once per flow.
SELECTION         ?= $(BUILD_DIR_OPT)/work/selection.json
COMPLEMENT_PLAN   ?= $(BUILD_DIR_OPT)/complement_plan.json
CELL_INTERFACES   ?= $(BUILD_DIR_MIN)/reports

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

# Mining/cover knobs shared by generate-cells, rewrite and run-all. Optional
# variables are only forwarded when set, so the CLI defaults stay in charge.
AION_OPT_MINE_ARGS := \
	--max-size $(MAX_SIZE) \
	--min-occurrences $(MIN_OCCURRENCES) \
	--area-factor $(AREA_FACTOR) \
	$(if $(MIN_SELECTED),--min-selected $(MIN_SELECTED)) \
	$(if $(MAX_OUTPUTS),--max-outputs $(MAX_OUTPUTS)) \
	$(if $(MAX_INPUTS),--max-inputs $(MAX_INPUTS)) \
	$(if $(JOBS),--jobs $(JOBS)) \
	$(if $(filter 0,$(COLLAPSE_STRENGTHS)),--no-collapse-strengths)

AION_OPT_ELITE_ARGS := \
	$(if $(ELITE_COUNT),--elite-count $(ELITE_COUNT)) \
	$(if $(ELITE_METRIC),--elite-metric $(ELITE_METRIC))

aion-opt-generate-cells: ## Mine patterns and generate AION cells
	@mkdir -p $(BUILD_DIR_OPT)/work
	PYTHONPATH=$(PYTHONPATH) $(AION_OPT) generate-cells \
		--input $(INPUT) \
		--cell-lib $(CELL_LIB) \
		--top $(TOP) \
		--work-dir $(BUILD_DIR_OPT)/work \
		--cell-prefix $(CELL_PREFIX) \
		$(AION_OPT_MINE_ARGS) \
		$(if $(ALLOW_OVERLAPPING),--allow-overlapping) \
		$(AION_OPT_ELITE_ARGS) \
		--output-cells $(CELLS) \
		$(if $(ELITE_CELLS),--output-elite-cells $(ELITE_CELLS)) \
		--output-report $(PATTERN_REPORT) \
		$(if $(SELECTION),--selection $(SELECTION)) \
		$(if $(wildcard $(COMPLEMENT_PLAN)),--complement-plan $(COMPLEMENT_PLAN))

aion-opt-complement-plan: ## Decide which complemented cell inputs come from outside the cell
	@mkdir -p $(dir $(COMPLEMENT_PLAN))
	PYTHONPATH=$(PYTHONPATH) $(AION_OPT) complement-plan \
		--input $(INPUT) \
		--cell-lib $(CELL_LIB) \
		--top $(TOP) \
		--work-dir $(BUILD_DIR_OPT)/work \
		--cell-prefix $(CELL_PREFIX) \
		$(AION_OPT_MINE_ARGS) \
		--cells $(CELLS) \
		$(if $(wildcard $(CELL_INTERFACES)),--interfaces $(CELL_INTERFACES)) \
		--output-plan $(COMPLEMENT_PLAN) \
		$(if $(SELECTION),--selection $(SELECTION))

aion-opt-select-elite: ## Cut an existing cell library down to ELITE_COUNT cells
	PYTHONPATH=$(PYTHONPATH) $(AION_OPT) select-elite \
		--cells $(CELLS) \
		--pattern-report $(PATTERN_REPORT) \
		$(AION_OPT_ELITE_ARGS) \
		--output-cells $(ELITE_CELLS)

aion-opt-rewrite: ## Rewrite netlist with generated cells
	@mkdir -p $(BUILD_DIR_OPT)/work
	PYTHONPATH=$(PYTHONPATH) $(AION_OPT) rewrite \
		--input $(INPUT) \
		--cell-lib $(CELL_LIB) \
		--top $(TOP) \
		--work-dir $(BUILD_DIR_OPT)/work \
		--cell-prefix $(CELL_PREFIX) \
		$(AION_OPT_MINE_ARGS) \
		--cells $(CELLS) \
		--output-netlist $(REWRITE_NETLIST) \
		$(if $(REWRITE_FLAT),--output-flat-netlist $(REWRITE_FLAT)) \
		--output-report $(REWRITE_REPORT) \
		$(if $(SELECTION),--selection $(SELECTION))

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
		--cell-prefix $(CELL_PREFIX) \
		$(AION_OPT_MINE_ARGS) \
		$(AION_OPT_ELITE_ARGS) \
		--rtl $(RTL)
endif

aion-opt-test: ## Run the aion_opt unit + end-to-end test suite
	PYTHONPATH=$(PYTHONPATH) python3 -m pytest $(AION_OPT_DIR)/tests -q

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
# Forward common aion_char variables into the sub-make. These are passed for every
# target so users can override LIB, CELL_V, CELL_SP, MODEL_LIB, VDD, MODULE, CUSTOM,
# RAW2VCD, TB, VIEWER, and characterization knobs from the repo root.
AION_CHAR_VARS := \
	BUILD_DIR_CHAR=$(BUILD_DIR_CHAR) \
	NETLIST=$(AION_CHAR_NETLIST_FINAL_DOCKER) \
	$(if $(LIB),LIB=$(LIB)) \
	$(if $(CELL_V),CELL_V="$(CELL_V)") \
	$(if $(CELL_SP),CELL_SP=$(CELL_SP)) \
	$(if $(MODEL_LIB),MODEL_LIB=$(MODEL_LIB)) \
	$(if $(MODEL_SECTION),MODEL_SECTION=$(MODEL_SECTION)) \
	$(if $(VDD),VDD=$(VDD)) \
	$(if $(MODULE),MODULE=$(MODULE)) \
	$(if $(CUSTOM),CUSTOM=$(subst $(REPO_ROOT),/foss/designs/aion_flow,$(abspath $(CUSTOM)))) \
	$(if $(RAW2VCD),RAW2VCD=$(RAW2VCD)) \
	$(if $(TB),TB=$(TB)) \
	$(if $(VIEWER),VIEWER=$(VIEWER)) \
	$(if $(CORNERS),CORNERS="$(CORNERS)") \
	$(if $(SLEWS),SLEWS="$(SLEWS)") \
	$(if $(LOADS),LOADS="$(LOADS)") \
	$(if $(JOBS),JOBS=$(JOBS)) \
	$(if $(AREA),AREA=$(AREA)) \
	$(if $(DRIVER),DRIVER=$(DRIVER)) \
	$(if $(DRIVER_IN),DRIVER_IN=$(DRIVER_IN)) \
	$(if $(DRIVER_OUT),DRIVER_OUT=$(DRIVER_OUT)) \
	$(if $(VERIFY),VERIFY=$(VERIFY)) \
	$(if $(KEEP),KEEP=$(KEEP))

aion-char-generate: ## Generate aion_char SV/SPICE testbenches
	@mkdir -p $(BUILD_DIR_CHAR)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) generate \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-verilator: ## Run aion_char Verilator testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) verilator \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-icarus: ## Run aion_char Icarus testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) icarus \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-sv: ## Run aion_char SystemVerilog testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) sv \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-spice: ## Run aion_char SPICE testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) spice \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-all: ## Run aion_char SV + SPICE testbenches
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) all \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-plot: ## Plot aion_char SPICE waveforms (TB=tb_<module>)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) plot \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-wave-sv: ## View aion_char SV waveforms (TB=tb_<module>, VIEWER=surfer|gtkwave)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) wave-sv \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-wave-spice: ## View aion_char SPICE waveforms (TB=tb_<module>, VIEWER=surfer|gtkwave)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) wave-spice \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-lib: ## Characterize a cell into Liberty .lib files
	@mkdir -p $(BUILD_DIR_CHAR)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) lib \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-lib-selfcheck: ## Self-check characterization against PDK .lib
	@mkdir -p $(BUILD_DIR_CHAR)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) lib-selfcheck \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-lib-template: ## Print the Liberty template
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) lib-template \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-cells: ## Show the AION cell Verilog path and list available cells
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) cells \
		$(AION_CHAR_VARS)$(AION_CHAR_DOCKER_SUFFIX)

aion-char-verify-spice: ## Verify a custom SPICE netlist for CELL (CELL=..., SPICE=...)
	$(AION_CHAR_DOCKER_PREFIX)$(MAKE) --no-print-directory -C $(AION_CHAR_DIR) verify-spice \
		$(AION_CHAR_VARS) \
		NETLIST=$(subst $(REPO_ROOT),/foss/designs/aion_flow,$(abspath $(NETLIST))) \
		MODULE=$(CELL) CUSTOM=$(subst $(REPO_ROOT),/foss/designs/aion_flow,$(abspath $(SPICE)))$(AION_CHAR_DOCKER_SUFFIX)

# ---------------------------------------------------------------------------
# SPICE split / merge helper
# ---------------------------------------------------------------------------
SPLIT_MERGE_SCRIPT := scripts/spice_split_merge.py

split-spice-cells: ## Split a SPICE file into one file per .subckt cell (INPUT=..., OUTPUT=...)
	@mkdir -p $(OUTPUT)
	python3 $(SPLIT_MERGE_SCRIPT) merge $(INPUT) -o $(OUTPUT)

merge-spice-cells: ## Merge SPICE files or a directory into one file (INPUTS=..., OUTPUT=...)
	@mkdir -p $(dir $(OUTPUT))
	python3 $(SPLIT_MERGE_SCRIPT) split $(INPUTS) -o $(OUTPUT)

# ---------------------------------------------------------------------------
# aion_minimizer batch helper
# ---------------------------------------------------------------------------
MINIMIZER_BATCH_SCRIPT := scripts/run_aion_minimizer_batch.py

run-aion-minimizer-batch: ## Batch-minimize SPICE cells (INPUT_DIR=..., OUTPUT_DIR=..., GATES=...)
	@mkdir -p $(OUTPUT_DIR)
	PYTHONPATH=$(PYTHONPATH) python3 $(MINIMIZER_BATCH_SCRIPT) \
		$(INPUT_DIR) $(OUTPUT_DIR) \
		$(addprefix --gates ,$(GATES)) \
		$(if $(MODE),--mode $(MODE),) \
		$(if $(WN),--wn $(WN),) \
		$(if $(WP),--wp $(WP),) \
		$(if $(L),--l $(L),) \
		$(if $(MAX_INPUTS),--max-inputs $(MAX_INPUTS),) \
		$(if $(VERIFY),--verify,) \
		$(if $(VERIFY_SPICE),--verify-spice,) \
		$(if $(NETLIST),--netlist $(NETLIST),) \
		$(if $(BUILD_DIR),--build-dir $(BUILD_DIR),) \
		$(if $(filter 0,$(AION_IN_DOCKER)),--docker-runner ./scripts/docker_run.sh,)

# ---------------------------------------------------------------------------
# aion_minimizer subcommands
# ---------------------------------------------------------------------------
aion-minimizer-run: ## Minimize a gate-level SPICE netlist into a transistor-level netlist
	@mkdir -p $(BUILD_DIR_MIN)
	PYTHONPATH=$(PYTHONPATH) $(AION_MIN) run \
		$(AION_MIN_INPUT) \
		--gates $(AION_MIN_GATES) \
		--mode $(AION_MIN_MODE) \
		--verify \
		-o $(AION_MIN_OUTPUT)

aion-minimizer-verify-spice: ## Run aion-char-verify-spice on a minimized cell (requires CELL=..., SPICE=...)
ifndef CELL
	$(error CELL is required. Use: make aion-minimizer-verify-spice CELL=<existing_aion_cell_name>)
endif
ifndef SPICE
	$(error SPICE is required. Use: make aion-minimizer-verify-spice CELL=... SPICE=...)
endif
	$(MAKE) --no-print-directory aion-char-verify-spice \
		CELL=$(CELL) \
		SPICE=$(SPICE)

aion-minimizer-test: ## Run the aion_minimizer test suite
	PYTHONPATH=$(PYTHONPATH) python3 -m pytest $(AION_MIN_DIR)/tests -q

aion-minimizer-clean: ## Remove aion_minimizer build outputs
	rm -rf $(BUILD_DIR_MIN)

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

clean_aion_minimizer: ## Alias for aion-minimizer-clean
	$(MAKE) aion-minimizer-clean

flow: ## Run the full flow
	python examples/full_flow/flow.py

flow-opt: ## Run the optimization-only flow (mine -> elite -> rewrite -> LEC)
	python examples/full_flow/flow_opt.py
