#!/usr/bin/env bash
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Updated:                   2026-09-03
#  Description:               In-turn DRC/LVS oracle for the layout agent
# ================================================================
#
# The one command the model is given to grade its own work.  It sources
# pipeline.sh and runs the identical chain the host runs -- build GDS, DRC,
# LVS, report, evidence -- so the model's self-check and the host's grade
# cannot disagree.  It replaces the raw sak-drc.sh / sak-lvs.sh recipes the
# prompt used to hand out, whose report step silently produced no verdict, so
# a self-check was graded by a tool that wrote nothing and silence read as
# success.
#
# Two placement rules, both of which used to be silent failures:
#
#   * Everything must live inside the repository.  The verification container
#     mounts it at /foss/designs/aion_flow and sees nothing else, so a module
#     or work directory outside it can only ever produce "the tool wrote no
#     report".  That is detected here, before any container is started, and
#     reported as BLOCKED with the reason -- never as a clean result.
#
#   * The work directory must live OUTSIDE $BUILD_DIR/layout/, next to it in
#     $BUILD_DIR/selfcheck/iteration_<N>/.  The host builds the next evidence
#     packet from $BUILD_DIR/layout/iteration_<N>/, so a self-check writing its
#     own DRC and LVS reports in there put a second set of reports in the tree
#     the packet is assembled from: the model using the oracle corrupted the
#     evidence it would be shown next turn.
#
# Usage:
#   ./scripts/selfcheck.sh <MODULE.py> <WORKDIR> [<SPICE_NETLIST>]
#
# The cell name is the module's file stem.  The netlist is taken from the
# third argument, then $SPICE_NETLIST, then the netlist in this repository
# whose .subckt matches the cell name.
#
# Exit status:
#   0  clean   -- DRC and LVS both pass
#   1  dirty   -- the layout was checked and has violations or a mismatch
#   2  blocked -- the check could not be run (bad arguments, a path the
#                 container cannot see, a build failure, a tool that never
#                 produced a report)

set -euo pipefail

SELFCHECK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SELFCHECK_DIR}/.." && pwd)"
# shellcheck source=../pipeline.sh
source "${REPO_ROOT}/pipeline.sh"

EXIT_CLEAN=0
EXIT_DIRTY=1
EXIT_BLOCKED=2

# Where the container sees this repository.  Named in every placement error,
# because "outside the repository" on its own does not tell anyone why.
CONTAINER_MOUNT="/foss/designs/aion_flow"

usage () {
  cat <<EOF
Usage: ./scripts/selfcheck.sh <MODULE.py> <WORKDIR> [<SPICE_NETLIST>]

Runs the host's own verification chain on MODULE.py inside WORKDIR:
  build GDS -> Magic + KLayout DRC -> Netgen LVS -> report -> evidence packet

  MODULE.py       the cell generator to check; the cell name is its file stem
  WORKDIR         scratch directory for this round's artifacts (created, and
                  emptied per run by each step).  It must sit outside
                  \$BUILD_DIR/layout/ -- use \$BUILD_DIR/selfcheck/iteration_<N>
  SPICE_NETLIST   target netlist (default: \$SPICE_NETLIST, else the netlist
                  in this repository declaring .subckt <cell>)

Every path must live inside ${REPO_ROOT}: the verification container mounts
this repository at ${CONTAINER_MOUNT} and cannot see anything else.

Exit: ${EXIT_CLEAN} clean, ${EXIT_DIRTY} violations found, ${EXIT_BLOCKED} could not check.
EOF
}

note () {
  printf '[selfcheck] %s\n' "$*"
}

fail () {
  # Blocked is a *result the model has to notice*.  The reason goes to stderr,
  # and the verdict line to stdout as well, because a tool whose only output is
  # on a stream the reader is not looking at is indistinguishable from a tool
  # that found nothing wrong -- which is the entire bug this harness exists to
  # kill.
  local reason="$*"
  printf '[selfcheck] %s\n' "$reason" >&2
  printf '\n[selfcheck] RESULT: BLOCKED — %s\n' "$reason"
  printf '[selfcheck] Nothing was verified. This is NOT a clean result.\n'
  exit "$EXIT_BLOCKED"
}

# ---- argument handling ---------------------------------------------------

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit "$EXIT_CLEAN"
fi

if (( $# < 2 || $# > 3 )); then
  usage >&2
  fail "expected 2 or 3 arguments, got $#"
fi

MODULE="$(pipeline_abspath "$1")"
WORKDIR="$(pipeline_abspath "$2")"
NETLIST_ARG="${3:-${SPICE_NETLIST:-}}"

# ---- placement: what the container can see -------------------------------

visibility_note () {
  # $1 = label, $2 = absolute host path.  Return 0 when the container can see
  # the path; otherwise explain, in full, why it cannot and return 1.  This
  # used to be a one-line "outside ..." message, and because $BUILD_DIR is what
  # puts a path outside the repository, the model's only feedback channel was
  # silently dead for the whole run whenever the operator chose a build
  # directory elsewhere -- with nothing said about the cause.
  local label="$1" path="$2"
  pipeline_in_repo "$path" && return 0

  printf '[selfcheck] the %s is outside this repository, so the container cannot see it:\n' "$label" >&2
  printf '[selfcheck]   %s\n' "$path" >&2
  printf '[selfcheck]   repository: %s\n' "$REPO_ROOT" >&2
  printf '[selfcheck] The verification container mounts the repository at %s and nothing else,\n' "$CONTAINER_MOUNT" >&2
  printf '[selfcheck] so sak-drc.sh and sak-lvs.sh would be handed a path that does not exist in\n' >&2
  printf '[selfcheck] there and would write no report at all.\n' >&2
  if [[ -n "${AION_BUILD_DIR:-}" ]] && ! pipeline_in_repo "$AION_BUILD_DIR"; then
    printf '[selfcheck] CAUSE: this run'"'"'s build directory is itself outside the repository:\n' >&2
    printf '[selfcheck]   BUILD_DIR = %s\n' "$AION_BUILD_DIR" >&2
    printf '[selfcheck] Every path derived from it is invisible to the container, so no self-check\n' >&2
    printf '[selfcheck] in this run can ever succeed. Report this: the run needs a build directory\n' >&2
    printf '[selfcheck] inside %s (for example %s/build).\n' "$REPO_ROOT" "$REPO_ROOT" >&2
  else
    printf '[selfcheck] Pass a path under %s instead.\n' "$REPO_ROOT" >&2
  fi
  return 1
}

require_visible () {
  # $1 = label, $2 = absolute host path.  A path the container cannot see can
  # only ever produce "the tool wrote no report", so it is BLOCKED here, before
  # a container is started, and never confused with a clean result.
  visibility_note "$1" "$2" && return 0
  fail "$1 is outside ${REPO_ROOT}: $2"
}

# Relative arguments are repository-relative, here and in orchestrate.sh alike.
# When one of them does not resolve to a file, say which convention resolved it
# rather than leaving a path the caller never typed in the error message.
if [[ ! -f "$MODULE" ]]; then
  pipeline_path_hint "$1"
  # A module that is missing *and* outside the repository is usually missing
  # because the build directory is outside it; say so rather than leaving the
  # systemic cause to be guessed from one absent file.
  visibility_note "module" "$MODULE" || true
  fail "cell generator not found: ${MODULE}"
fi
[[ -s "$MODULE" ]] || fail "cell generator is empty: ${MODULE}"
[[ "$MODULE" == *.py ]] || fail "cell generator must be a .py file: ${MODULE}"

require_visible "module" "$MODULE"
require_visible "workdir" "$WORKDIR"

# ---- placement: what the host grades -------------------------------------

CELL_HINT="$(basename "$MODULE" .py)"

suggested_workdir () {
  # The work directory the prompt hands out: $BUILD_DIR/selfcheck/iteration_<N>,
  # named for the iteration of the module being checked and deliberately not
  # under $BUILD_DIR/layout/.
  local base="${AION_BUILD_DIR:-${REPO_ROOT}/build}" iter parent
  parent="${MODULE%/*}"
  iter="${parent##*/}"
  case "$iter" in
    iteration_[0-9]*) ;;
    *) iter="$CELL_HINT" ;;
  esac
  printf '%s/selfcheck/%s\n' "$base" "$iter"
}

# G11: the containment test below is a glob on the path as typed.  A symlink
# defeats it — `ln -s $BUILD_DIR/layout/iteration_1 $BUILD_DIR/selfcheck/link`
# was accepted and wrote drc/, lvs/ and report.txt straight into the graded
# iteration tree, at the canonical report paths, which is exactly the
# corruption this guard exists to prevent.  Test the resolved path; keep the
# path as typed for the messages so the operator sees what they wrote.
WORKDIR_RESOLVED="$(readlink -m -- "$WORKDIR" 2>/dev/null || printf '%s' "$WORKDIR")"

case "$WORKDIR_RESOLVED" in
  */layout/iteration_[0-9]*)
    printf '[selfcheck] the work directory is inside the graded iteration tree:\n' >&2
    printf '[selfcheck]   %s\n' "$WORKDIR" >&2
    printf '[selfcheck] The host assembles the next evidence packet from that tree, so the DRC and\n' >&2
    printf '[selfcheck] LVS reports this check is about to write would show up in it as a second,\n' >&2
    printf '[selfcheck] foreign set of results — the oracle would corrupt the evidence you are\n' >&2
    printf '[selfcheck] shown next turn.\n' >&2
    printf '[selfcheck] Use this instead:\n' >&2
    printf '[selfcheck]   ./scripts/selfcheck.sh %s %s\n' "$MODULE" "$(suggested_workdir)" >&2
    fail "work directory must not be under \$BUILD_DIR/layout/: ${WORKDIR}"
    ;;
esac

CELL="$CELL_HINT"
case "$CELL" in
  [A-Za-z_]*) ;;
  *) fail "cell name '${CELL}' (the module stem) is not a valid identifier" ;;
esac
case "$CELL" in
  *[!A-Za-z0-9_]*) fail "cell name '${CELL}' (the module stem) contains characters the tools reject" ;;
esac

# Locate the netlist declaring this cell.  orchestrate.sh does not export
# SPICE_NETLIST, so the two-argument form the prompt shows has to find it.
find_netlist_for_cell () {
  local cell="$1" dir candidate
  for dir in "${AION_BUILD_DIR:-}" "$REPO_ROOT" "${REPO_ROOT}/cells" "${REPO_ROOT}/tests/fixtures"; do
    [[ -n "$dir" && -d "$dir" ]] || continue
    while IFS= read -r candidate; do
      if grep -qE "^[[:space:]]*\.subckt[[:space:]]+${cell}([[:space:]]|$)" "$candidate" 2>/dev/null; then
        printf '%s\n' "$candidate"
        return 0
      fi
    done < <(find "$dir" -maxdepth 2 -type f \
               \( -name '*.spice' -o -name '*.cdl' -o -name '*.sp' \) 2>/dev/null | sort)
  done
  return 1
}

if [[ -n "$NETLIST_ARG" ]]; then
  NETLIST="$(pipeline_abspath "$NETLIST_ARG")"
elif ! NETLIST="$(find_netlist_for_cell "$CELL")"; then
  fail "no netlist declaring '.subckt ${CELL}' found; pass it as the third argument"
fi

if [[ ! -s "$NETLIST" ]]; then
  [[ -n "$NETLIST_ARG" ]] && pipeline_path_hint "$NETLIST_ARG"
  fail "netlist not found or empty: ${NETLIST}"
fi
require_visible "netlist" "$NETLIST"

mkdir -p "$WORKDIR" || fail "cannot create workdir: ${WORKDIR}"
LOG_DIR="${WORKDIR}/logs"
mkdir -p "$LOG_DIR"

GDS="${WORKDIR}/${CELL}.gds"
DRC_DIR="${WORKDIR}/drc"
LVS_DIR="${WORKDIR}/lvs"
REPORT="${WORKDIR}/report.txt"
BUILD_ERR="${WORKDIR}/build_error.txt"

# ---- budget --------------------------------------------------------------

report_budget () {
  # A DEADLINE file holds one epoch second: the wall-clock instant this turn
  # ends.  The model gets 5 self-check rounds inside that budget and each
  # round costs real time, so tell it what is left.
  local file candidate deadline now left
  file=""
  for candidate in "${AION_DEADLINE_FILE:-}" \
                   "${AION_BUILD_DIR:+${AION_BUILD_DIR}/layout/deadline.epoch}" \
                   "${WORKDIR}/DEADLINE" \
                   "$(dirname "$WORKDIR")/DEADLINE" \
                   "$(dirname "$WORKDIR")/deadline.epoch"; do
    if [[ -n "$candidate" && -s "$candidate" ]]; then
      file="$candidate"
      break
    fi
  done
  [[ -n "$file" ]] || return 0

  deadline="$(tr -d '[:space:]' < "$file")"
  case "$deadline" in
    '' | *[!0-9]*)
      note "budget: ignoring ${file}, it does not hold an epoch second ('${deadline}')"
      return 0 ;;
  esac

  now="$(date +%s)"
  left=$(( deadline - now ))
  if (( left > 0 )); then
    note "budget: ${left}s left in this turn (${file})"
  else
    note "budget: EXHAUSTED ${left#-}s ago (${file}) — write your module now, do not start another round"
  fi
}

# ---- step runner ---------------------------------------------------------

# Run one pipeline step with its output captured, so the container's very
# verbose logs do not swamp the evidence packet.  On failure the tail of the
# log is printed: the model has to see why, not just that.
#   $1 = label, $2 = log file, $3.. = command
run_step () {
  local label="$1" log="$2" rc=0
  shift 2
  # `rc=$?` inside `if ! cmd; then` would read the *negation's* status, which
  # is always 0 — the step would report "exit 0" and the caller would treat a
  # failure as a success.  Capture the status directly.
  "$@" > "$log" 2>&1 || rc=$?
  if (( rc != 0 )); then
    printf '[selfcheck] %s FAILED (exit %d) — last 40 lines of %s:\n' "$label" "$rc" "$log"
    strip_ansi < "$log" | tail -n 40 | sed 's/^/    | /'
    return "$rc"
  fi
  note "${label} ok (log: ${log})"
}

# Print the evidence packet, then leave.  Called on every exit path that has
# artifacts worth showing.
emit_evidence () {
  local build_err="${1:-}"
  echo
  step_evidence_at "$NETLIST" "$WORKDIR" "$CELL" "$MODULE" "$build_err" || true
}

# A step that could not run is never a pass.  Same shape as fail(), but after
# the evidence packet, and on both streams for the same reason.
blocked () {
  echo
  printf '[selfcheck] RESULT: BLOCKED — %s\n' "$*"
  printf '[selfcheck] Nothing was verified. This is NOT a clean result.\n'
  printf '[selfcheck] RESULT: BLOCKED — %s\n' "$*" >&2
  exit "$EXIT_BLOCKED"
}

# ---- run -----------------------------------------------------------------

note "cell    : ${CELL}"
note "module  : ${MODULE}"
note "netlist : ${NETLIST}"
note "workdir : ${WORKDIR}"
report_budget

if ! run_step "GDS build" "${LOG_DIR}/gds.log" step_generate_gds_at "$MODULE" "$GDS"; then
  strip_ansi < "${LOG_DIR}/gds.log" > "$BUILD_ERR" || true
  emit_evidence "$BUILD_ERR"
  blocked "the module did not build, so nothing was verified."
fi
rm -f "$BUILD_ERR"

run_step "Magic+KLayout DRC" "${LOG_DIR}/drc.log" step_drc_at "$GDS" "$DRC_DIR" || {
  emit_evidence
  blocked "sak-drc.sh produced no complete DRC report (see ${LOG_DIR}/drc.log)."
}

run_step "Netgen LVS" "${LOG_DIR}/lvs.log" step_lvs_at "$GDS" "$LVS_DIR" "$NETLIST" "$CELL" || {
  emit_evidence
  blocked "sak-lvs.sh produced no complete netgen report (see ${LOG_DIR}/lvs.log)."
}

run_step "Report" "${LOG_DIR}/report.log" \
  step_report_at "$GDS" "$WORKDIR" "$NETLIST" "$CELL" "$REPORT" || {
  emit_evidence
  blocked "no PASS/FAIL verdict could be produced; see ${REPORT}."
}

emit_evidence

echo
echo "===== VERDICT (${REPORT}) ====="
if grep -q '^Cell:' "$REPORT"; then
  sed -n '/^Cell:/,$p' "$REPORT"
else
  cat "$REPORT"
fi
echo "===== END VERDICT ====="
echo

report_budget

if report_passed_at "$REPORT"; then
  note "RESULT: PASS — DRC and LVS are both clean. Stop editing and write your module."
  exit "$EXIT_CLEAN"
fi

note "RESULT: FAIL — fix the highest-priority defect above, then check again."
exit "$EXIT_DIRTY"
