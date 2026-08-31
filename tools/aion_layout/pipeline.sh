#!/bin/bash
# pipeline.sh — deterministic AION layout pipeline steps.
# No LLM involvement here at all: these are the same commands every time,
# so there is nothing for an agent to decide and nothing that can loop.
# Sourced by orchestrate.sh.

set -euo pipefail

# ---- state.json helpers -----------------------------------------------

state_read () {
  # $1 = jq filter
  jq -r "$1" "$STATE_FILE"
}

state_write_atomic () {
  # $1 = jq filter that transforms current state into new state
  local tmp
  tmp="$(mktemp "${STATE_FILE}.XXXXXX")"
  jq "$1" "$STATE_FILE" > "$tmp"
  mv -f "$tmp" "$STATE_FILE"   # atomic on same filesystem — no torn writes
}

state_init () {
  local cell="$1" max_iter="$2"
  if [[ ! -f "$STATE_FILE" ]]; then
    cat > "$STATE_FILE" <<EOF
{
  "cell_name": "${cell}",
  "current_iteration": 0,
  "max_iterations": ${max_iter},
  "steps": {"gds_generated": false, "rendered": false, "drc_done": false, "lvs_done": false, "report_generated": false},
  "last_result": null,
  "last_error": null,
  "status": "in_progress"
}
EOF
  fi
}

# Self-healing check: don't trust a "true" flag if the file it implies
# doesn't actually exist — this is what protects the next run from a
# previous invocation getting killed mid-step.
state_reconcile () {
  local n gds img drc_dir lvs_dir report
  n="$(state_read '.current_iteration')"
  gds="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds"
  img="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.png"
  drc_dir="${BUILD_DIR}/layout/iteration_${n}/drc"
  lvs_dir="${BUILD_DIR}/layout/iteration_${n}/lvs"
  report="${BUILD_DIR}/layout/iteration_${n}/report.txt"

  [[ -f "$gds" ]]                     || state_write_atomic '.steps.gds_generated = false'
  [[ -f "$img" ]]                     || state_write_atomic '.steps.rendered = false'
  [[ -d "$drc_dir" && -n "$(ls -A "$drc_dir" 2>/dev/null)" ]] || state_write_atomic '.steps.drc_done = false'
  [[ -d "$lvs_dir" && -n "$(ls -A "$lvs_dir" 2>/dev/null)" ]] || state_write_atomic '.steps.lvs_done = false'
  [[ -f "$report" ]]                  || state_write_atomic '.steps.report_generated = false'
}

# ---- pipeline steps -----------------------------------------------------

step_generate_scaffold () {
  # iteration 0 only
  local mod="${BUILD_DIR}/layout/iteration_0/${CELL_NAME}.py"
  ./scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/generate_from_netlist.py ${SPICE_NETLIST} -o ${mod} --summary"
}

step_generate_gds () {
  local n mod gds
  n="$(state_read '.current_iteration')"
  mod="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.py"
  gds="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds"

  ./scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/generate_cell.py ${mod} ${gds}"

  [[ -f "$gds" ]] || { echo "GDS was not produced" >&2; return 1; }
  state_write_atomic '.steps.gds_generated = true'
}

step_render () {
  local n gds img
  n="$(state_read '.current_iteration')"
  gds="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds"
  img="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.png"

  ./scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/gds_to_image.py ${gds} ${img} --width 1600 --height 1200"

  [[ -f "$img" ]] || { echo "PNG was not produced" >&2; return 1; }
  state_write_atomic '.steps.rendered = true'
}

step_drc () {
  local n gds drc_dir
  n="$(state_read '.current_iteration')"
  gds="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds"
  drc_dir="${BUILD_DIR}/layout/iteration_${n}/drc"
  mkdir -p "$drc_dir"

  ./scripts/docker_run.sh "cd tools/aion_layout && sak-drc.sh -d -b -l macro -w ${drc_dir} ${gds}"

  [[ -n "$(ls -A "$drc_dir" 2>/dev/null)" ]] || { echo "DRC produced no output" >&2; return 1; }
  state_write_atomic '.steps.drc_done = true'
}

step_lvs () {
  local n gds lvs_dir
  n="$(state_read '.current_iteration')"
  gds="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds"
  lvs_dir="${BUILD_DIR}/layout/iteration_${n}/lvs"
  mkdir -p "$lvs_dir"

  ./scripts/docker_run.sh "cd tools/aion_layout && sak-lvs.sh -d -b -w ${lvs_dir} -s ${SPICE_NETLIST} -l ${gds} -c ${CELL_NAME}"

  [[ -n "$(ls -A "$lvs_dir" 2>/dev/null)" ]] || { echo "LVS produced no output" >&2; return 1; }
  state_write_atomic '.steps.lvs_done = true'
}

step_report () {
  local n gds report
  n="$(state_read '.current_iteration')"
  gds="${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds"
  report="${BUILD_DIR}/layout/iteration_${n}/report.txt"

  ./scripts/docker_run.sh "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 scripts/report_verification.py --cell ${CELL_NAME} --gds ${gds} --netlist ${SPICE_NETLIST} --runs-dir ${BUILD_DIR}/layout/iteration_${n} --parse-only" > "$report"

  [[ -f "$report" ]] || { echo "Report was not produced" >&2; return 1; }
  state_write_atomic '.steps.report_generated = true'
}

# Pure text parsing — no LLM needed to know pass/fail.
report_passed () {
  local n report
  n="$(state_read '.current_iteration')"
  report="${BUILD_DIR}/layout/iteration_${n}/report.txt"
  [[ -f "$report" ]] || return 1
  grep -q '^RESULT: *PASS' "$report"
}

report_summary () {
  local n report
  n="$(state_read '.current_iteration')"
  report="${BUILD_DIR}/layout/iteration_${n}/report.txt"
  grep -E '^(DRC|LVS|RESULT):' "$report" || true
  echo "---"
  grep -iE 'violation|mismatch|disconnect|short|missing' "$report" | head -30
}

run_deterministic_steps_for_current_iteration () {
  state_reconcile
  [[ "$(state_read '.steps.gds_generated')" == "true" ]]     || step_generate_gds
  [[ "$(state_read '.steps.rendered')" == "true" ]]          || step_render
  [[ "$(state_read '.steps.drc_done')" == "true" ]]          || step_drc
  [[ "$(state_read '.steps.lvs_done')" == "true" ]]          || step_lvs
  [[ "$(state_read '.steps.report_generated')" == "true" ]]  || step_report
}
