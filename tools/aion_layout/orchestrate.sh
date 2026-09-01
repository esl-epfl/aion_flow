#!/bin/bash
# orchestrate.sh — v3.2
#
# Deterministic pipeline steps (GDS gen, render, DRC, LVS, report) run as
# plain bash — no agent involved, so nothing there can hang on a tool
# permission prompt or loop on a repeated tool call.
#
# Usage:
#   ./orchestrate.sh <SPICE_NETLIST> <BUILD_DIR> [MAX_ITERATIONS]
#
# Requires: copilot-rcp.sh wrapper, jq, python3.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/pipeline.sh"

SPICE_NETLIST="${1:?Usage: orchestrate.sh <SPICE_NETLIST> <BUILD_DIR> [MAX_ITERATIONS]}"
BUILD_DIR="${2:?Usage: orchestrate.sh <SPICE_NETLIST> <BUILD_DIR> [MAX_ITERATIONS]}"
MAX_ITERATIONS="${3:-10}"
# MODEL="${MODEL:-openai/gpt-oss-120b}"
MODEL="${MODEL:-Qwen/Qwen3-VL-235B-A22B-Thinking}"

CEFPROVIDER_API_KEY="${CEFPROVIDER_API_KEY:?Set CEFPROVIDER_API_KEY in your environment (e.g. ~/.bashrc) before running orchestrate.sh}"
COPILOT_RCP="${COPILOT_RCP:?Set COPILOT_RCP to the path of your copilot-rcp.sh (e.g. in ~/.bashrc) before running orchestrate.sh}"

STATE_FILE="${BUILD_DIR}/layout/state.json"
MEMORY_FILE="${BUILD_DIR}/memory.md"
FIX_TIMEOUT="${FIX_TIMEOUT:-10m}"

CELL_NAME="$(grep -m1 -oP '(?<=\.subckt\s)\S+' "$SPICE_NETLIST")"
mkdir -p "${BUILD_DIR}/layout/iteration_0" "${BUILD_DIR}/layout/final"
touch "$MEMORY_FILE"

state_init "$CELL_NAME" "$MAX_ITERATIONS"

# Banner Helper Function
print_banner() {
    local fg_color="$1"
    local text="$2"
    local reset="\033[0m"
    local bold="\033[1m"
    echo -e "${bold}${fg_color}"
    echo "========================================================================"
    echo "  ${text}"
    echo "========================================================================"
    echo -e "${reset}"
}

print_banner "\033[36m" "AION LAYOUT ORCHESTRATION v3.2"
echo "Cell: $CELL_NAME | Netlist: $SPICE_NETLIST | Build dir: $BUILD_DIR | Max iter: $MAX_ITERATIONS | Model: $MODEL"
echo

request_fix() {
    local n src img next_mod summary prompt rc

    n="$(state_read '.current_iteration')"
    src="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.py"
    img="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.png"
    next_mod="${BUILD_DIR}/layout/iteration_$((n + 1))/${CELL_NAME}.py"
    mkdir -p "$(dirname "$next_mod")"
    summary="$(report_summary)"

    prompt=$(
        cat <<EOF
You are fixing a standard-cell layout generator. Below is the current DRC/LVS
result summary, and the full current Python source that generates the layout
via the AION layout API (see @GDS_PYTHON_API.md and @CLI_REFERENCE.md for the
API — read them if you need to, but nothing else in the repo).

---
### CRITICAL MANDATORY STEPS ###

1. **MEMORY READ (FIRST THING):**
   Before making any edits or analysis, read @${MEMORY_FILE} to review history, past mistakes, and decisions made in previous iterations.

2. **PYTHON COMPILATION VERIFICATION (MUST ITERATE UNTIL CLEAN):**
   After generating or editing ${next_mod}, you MUST run the bash command:
   \`python3 -m py_compile ${next_mod}\`
   If compilation fails or produces syntax errors, you MUST fix the syntax error in ${next_mod} and run the \`py_compile\` command again. Iterate until compilation returns exit status 0 without errors.

3. **MEMORY WRITE (LAST THING):**
   At the VERY END of your work (after ${next_mod} compiles cleanly), write and APPEND a new entry to @${MEMORY_FILE}. Your entry MUST include:
   - What you modified/fixed in this iteration.
   - Errors faced (DRC/LVS failures or syntax issues).
   - Lessons learned & specific details to pay attention to in upcoming steps.
---

You are also allowed to read the content of the @context folder, where you
can find a description of the DRC rules and the pdk std cells.

If you find any similarity between the current source and any of the files in @context, you can use them as reference, and take inspiration from them.

# Layout Debugging Strategy

When deciding what to modify, prioritize problems in this order:

1. **Incorrect transistor topology**
2. **Missing or incorrect source/drain connections**
3. **Missing contacts/vias**
4. **Missing power connections**
5. **Missing input/output connections**
6. **LVS connectivity mismatches**
7. **DRC shorts**
8. **DRC spacing violations**
9. **DRC enclosure violations**
10. **Other geometric/design-rule issues**
11. **Layout compactness and visual quality**

Do not optimize area before connectivity and verification are correct.

---

## First Iteration Special Rule

On iteration == 0, do not spend significant effort performing detailed DRC/LVS diagnosis. The automatically generated scaffold provides limited information.

Instead, focus on completing the obvious physical implementation: source connections, drain connections, transistor interconnect, missing devices, contacts, vias, input routing, output routing, power routing, topology implied by the SPICE netlist.

After the first iteration, use detailed DRC/LVS feedback to drive optimization.

---

# LVS Debugging

When LVS fails, determine whether the problem is:

### Missing connection
A net exists in SPICE but is disconnected in the layout. Fix the physical routing.

### Incorrect connection
Two nets are accidentally shorted. Fix the metal/poly/diffusion geometry.

### Missing device
A MOS device exists in SPICE but cannot be extracted from the layout. Check: active region, poly gate, source/drain geometry, contacts, layer combinations, transistor dimensions.

### Incorrect device parameters
Check the extracted transistor geometry against the SPICE instance. Do not alter the SPICE netlist to hide the mismatch.

---

# DRC Debugging

Use the exact DRC violation information to determine which geometry is incorrect. Typical fixes include: increasing spacing, enlarging enclosure, correcting via/contact placement, extending metal, moving poly, separating nets, correcting diffusion geometry, removing accidental overlaps, respecting minimum widths.

Prefer small, targeted modifications over completely redesigning the cell.

---

Rendered layout image for visual reference: @${img}

--- Verification summary (iteration ${n}) ---
${summary}

--- Current source (${src}) ---
$(cat "$src")
--- end source ---

you can find the drc rules here: @context:drc:

YOU SHOULD FOCUS FIRST ON LVS FAILURES, THEN DRC FAILURES, THEN OTHER ISSUES.

You can iterate at maximum 5 times in a session by running drc and lvs (work in a internal_iteration folder inside the main iteration folder)

To generate the gds, run
./scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/generate_cell.py <MODULE> <OUTPUT_GDS>"

To run the DRC, run
./scripts/docker_run.sh "cd tools/aion_layout && sak-drc.sh -d -b -l macro -w <DRC_RUN_DIR> <GDS_FILE>"

To run the LVS, run
./scripts/docker_run.sh "cd tools/aion_layout && sak-lvs.sh -d -b -w <LVS_RUN_DIR> -s <SPICE_NETLIST> -l <GDS_FILE> -c <CELL_NAME>"


Diagnose the failure(s) using the priority order above. Make the smallest
change that fixes the highest-priority problem — do not redesign the whole
cell.

Write the complete corrected Python file directly to:
${next_mod}

Test that ${next_mod} compiles via bash tool (\`python3 -m py_compile ${next_mod}\`). Fix any compilation/syntax errors and re-test until it compiles cleanly.

Do not modify ${src} or any other iteration's files. Once you have written ${next_mod}, verified it compiles cleanly, AND updated ${MEMORY_FILE}, stop — do not run any other commands.
EOF
    )

    print_banner "\033[33m" "REQUESTING FIX: ITERATION ${n} -> $((n + 1))"
    echo ">> Agent will write code directly to: ${next_mod}"
    echo ">> Agent will test compilation with python3 -m py_compile"
    echo ">> Agent will append iteration findings to: ${MEMORY_FILE}"
    echo

    timeout "$FIX_TIMEOUT" "$COPILOT_RCP" "$CEFPROVIDER_API_KEY" "$MODEL" -p "$prompt" \
        --allow-tool view \
        --allow-tool edit \
        --allow-tool bash \
        --deny-tool write-outside-workspace \
        --add-dir "$(dirname "$src")" \
        --add-dir "$(dirname "$next_mod")" \
        --add-dir "$BUILD_DIR"
    rc=$?

    echo

    if [[ $rc -ne 0 ]]; then
        echo "!! copilot exited with status $rc" >&2
        return 1
    fi

    if [[ ! -f "$next_mod" ]]; then
        echo "!! Agent finished but did not write ${next_mod}" >&2
        return 1
    fi

    # Host-side fallback safety assertion
    echo ">> Verifying final compilation state of ${next_mod}..."
    if ! python3 -m py_compile "$next_mod"; then
        echo "!! Syntax error: ${next_mod} failed final python compilation check!" >&2
        return 1
    fi
    echo ">> Compilation verified successfully."

    return 0
}

# ---- main loop -----------------------------------------------------------

for ((i = 0; i < MAX_ITERATIONS; i++)); do
    status="$(state_read '.status')"
    [[ "$status" == "verified_clean" || "$status" == "max_iterations_reached" ]] && break

    n="$(state_read '.current_iteration')"

    print_banner "\033[32m" "STARTING ITERATION ${n} / $((MAX_ITERATIONS - 1))"

    if [[ "$n" -eq 0 && ! -f "${BUILD_DIR}/layout/iteration_0/${CELL_NAME}.py" ]]; then
        echo "Generating initial scaffold..."
        step_generate_scaffold
    fi

    echo "Running deterministic pipeline (GDS -> render -> DRC -> LVS -> report)..."
    if ! run_deterministic_steps_for_current_iteration; then
        echo "!! A deterministic step failed outright (not a DRC/LVS violation — an actual command failure)." >&2
        state_write_atomic '.status = "blocked" | .last_error = "deterministic step failed, see stdout"'
        exit 1
    fi

    if report_passed; then
        print_banner "\033[32m" "SUCCESS: DRC AND LVS PASSED CLEANLY AT ITERATION ${n}"
        state_write_atomic '.status = "verified_clean"'
        break
    fi

    if [[ "$((n + 1))" -ge "$MAX_ITERATIONS" ]]; then
        print_banner "\033[31m" "MAX ITERATIONS (${MAX_ITERATIONS}) REACHED WITHOUT CLEAN RESULT"
        state_write_atomic '.status = "max_iterations_reached"'
        break
    fi

    if ! request_fix; then
        print_banner "\033[31m" "FIX REQUEST FAILED AT ITERATION ${n}"
        echo "!! Stopping execution. Inspect iteration ${n}'s report, image, and ${MEMORY_FILE}." >&2
        state_write_atomic '.status = "blocked" | .last_error = "fix request failed"'
        exit 1
    fi

    next_src="${BUILD_DIR}/layout/iteration_$((n + 1))/${CELL_NAME}.py"
    echo "Successfully generated and verified syntax for: $next_src"

    state_write_atomic ".current_iteration += 1 | .steps = {\"gds_generated\": false, \"rendered\": false, \"drc_done\": false, \"lvs_done\": false, \"report_generated\": false} | .last_result = \"$(report_summary | head -1 | tr -d '\"')\""
done

# ---- finalize (deterministic, no LLM) -------------------------------------

final_status="$(state_read '.status')"
if [[ "$final_status" == "verified_clean" || "$final_status" == "max_iterations_reached" ]]; then
    n="$(state_read '.current_iteration')"
    gds_last="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds"
    img_last="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.png"
    final_dir="${BUILD_DIR}/layout/final"
    mkdir -p "$final_dir"

    ./scripts/docker_run.sh "cd tools/aion_layout && sak-drc.sh -d -b -l macro -w ${final_dir}/drc ${gds_last}"
    ./scripts/docker_run.sh "cd tools/aion_layout && sak-lvs.sh -d -b -w ${final_dir}/lvs -s ${SPICE_NETLIST} -l ${gds_last} -c ${CELL_NAME}"
    ./scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/report_verification.py --cell ${CELL_NAME} --gds ${gds_last} --netlist ${SPICE_NETLIST} --runs-dir ${final_dir} --parse-only" >"${final_dir}/verification_report.txt"

    cp "$gds_last" "${final_dir}/${CELL_NAME}.gds"
    cp "$img_last" "${final_dir}/${CELL_NAME}.png"
    grep -A100 '^DRC:' "${final_dir}/verification_report.txt" | sed -n '/^LVS:/q;p' >"${final_dir}/drc_report.txt" || true
    grep -A100 '^LVS:' "${final_dir}/verification_report.txt" >"${final_dir}/lvs_report.txt" || true

    state_write_atomic '.status = "finalized"'

    print_banner "\033[35m" "ORCHESTRATION COMPLETE"
    echo "Cell: ${CELL_NAME}"
    echo "Iterations: $((n + 1))"
    echo "Status: ${final_status}"
    echo "Final Output: ${final_dir}/"
fi
