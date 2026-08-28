# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-11 23:17:17
#  Updated:                   2026-08-28 11:19:58
#  Description:               Utils Makefile
# ================================================================

RTL_ROOT ?=

# ==============================================================================
# Color Definitions for Terminal Output
# ==============================================================================
C_RESET = \033[0m
C_BOLD  = \033[1m
C_CYAN  = \033[36m
C_GREEN = \033[32m
C_YELLO = \033[33m
C_MAGEN = \033[35m

.PHONY: help
help:
	@echo ""
	@echo "========================================================================"
	@echo "  AION Flow - Command Center"
	@echo "========================================================================"
	@awk 'BEGIN {FS = ":.*?## "; section=""} \
		/^[a-zA-Z_-]+:.*?##/ { \
			target=$$1; \
			if (target ~ /clean/) new="Clean"; \
			else if (target ~ /^aion-opt-/) new="AION Optimization"; \
			else if (target ~ /^aion-char-/) new="AION Characterization"; \
			else new="General"; \
			if (new != section) { section=new; printf "\n\033[1;34m%s\033[0m\n", section } \
			printf "  \033[36m%-28s\033[0m %s\n", target, $$2 \
		}' $(MAKEFILE_LIST)
	@echo ""

help_no_color:
	@awk 'BEGIN {FS = ":.*?## "; printf "  %-24s %s\n  %-24s %s\n", "COMMAND", "DESCRIPTION", "-------", "-----------"; section=""} \
		/^[a-zA-Z_-]+:.*?##/ { \
			target=$$1; \
			if (target ~ /clean/) new="Clean"; \
			else if (target ~ /^aion-opt-/) new="AION opt"; \
			else if (target ~ /^aion-char-/) new="AION char"; \
			else new="General"; \
			if (new != section) { section=new; printf "\n  ─── %s ──────────────────────────────────────────\n", section } \
			printf "  %-24s %s\n", target, $$2 \
		}' $(MAKEFILE_LIST)
	@echo ""

