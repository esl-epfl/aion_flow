#!/bin/bash
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-08-25
#  Updated:                   2026-09-03
#  Description:               Deterministic AION layout pipeline steps
# ================================================================
#
# No LLM involvement here at all: these are the same commands every time, so
# there is nothing for an agent to decide and nothing that can loop.  Sourced
# by orchestrate.sh and by scripts/selfcheck.sh.
#
# Four invariants this file exists to hold:
#
#   1. A step fails loudly.  orchestrate.sh calls the chain as
#      `if ! run_deterministic_steps_for_current_iteration; then`, and a `!`
#      negation makes POSIX shells ignore `set -e` for the whole command --
#      including inside every function it calls.  So `set -e` can never be
#      trusted to stop the chain: every step checks the runner's exit status
#      explicitly, and returns non-zero itself.
#
#   2. A step succeeds only on evidence.  "The output file exists" is not
#      evidence when a `>` redirection created it, and a zero-byte file is not
#      evidence a tool ran -- a container killed mid-write leaves exactly that,
#      and it used to satisfy the DRC step.  Every artifact accepted as proof of
#      a completed step must be non-empty (`-size +0c`) and, where the tool
#      writes its own completion marker, must carry it.
#
#   3. A step is graded on what *this* run produced.  Each run directory is
#      emptied before the tool starts, so a stale report from an interrupted run
#      -- or one planted by the model, which has an edit tool and $BUILD_DIR --
#      cannot stand in for the report this run never got.  That replaces the old
#      `find -newer <stamp>` freshness test, which compared mtimes across two
#      filesystems and read "the tool finished inside the same second as the
#      stamp" as "the tool wrote nothing".
#
#   4. Discovery is canonical, never a tree walk.  sak-drc.sh / sak-lvs.sh write
#      <cell>.magic.drc/, <cell>.klayout.drc/ and <cell>.magic.lvs/ under the run
#      directory they are given; those directories, and only those, are read.
#      The same rule holds in aion_layout/verification.py and scripts/evidence.py
#      -- a whole-tree `find` is what let a planted report outrank the real one.
#
# Each step comes in a path-parameterised `_at` variant that reads no globals,
# so the host loop and the model-facing oracle (scripts/selfcheck.sh) execute
# byte-identical commands and cannot drift apart.  The state-driven wrappers
# resolve paths from STATE_FILE/BUILD_DIR/CELL_NAME/SPICE_NETLIST and delegate.

set -euo pipefail

# ---- environment --------------------------------------------------------

# Repository root: the directory holding this file.  Every path is resolved
# against it so the `_at` helpers behave the same from any working directory.
PIPELINE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Container entry point.  Overridable only so tests can substitute a stub.
PIPELINE_RUN_SCRIPT="${PIPELINE_RUN_SCRIPT:-${PIPELINE_ROOT}/scripts/docker_run.sh}"

# Host interpreter used for the evidence packet (needs klayout + aion_layout).
PIPELINE_PYTHON="${PIPELINE_PYTHON:-python3}"

# ---- temp files ---------------------------------------------------------
# Every temp file created here is registered and removed on exit *and* on a
# signal.  There was no trap at all: a Ctrl-C during a run left one stamp file
# and one evidence-stderr file behind per interrupted iteration.

PIPELINE_TMP_FILES=()
PIPELINE_TMP_FILE=""

pipeline_tmp_file () {
  # $1 = label.  Sets PIPELINE_TMP_FILE rather than printing the path: a
  # command substitution would run this in a subshell and the registration
  # would die with it, which is the whole point of the registry.
  local path
  path="$(mktemp "${TMPDIR:-/tmp}/aion-${1}.XXXXXX")" || return 1
  PIPELINE_TMP_FILES+=("$path")
  PIPELINE_TMP_FILE="$path"
}

pipeline_cleanup_tmp () {
  # Safe to call more than once, and safe to call from another script's trap.
  local path
  (( ${#PIPELINE_TMP_FILES[@]} > 0 )) || return 0
  for path in "${PIPELINE_TMP_FILES[@]}"; do
    [[ -n "$path" ]] && rm -f -- "$path"
  done
  PIPELINE_TMP_FILES=()
  return 0
}

pipeline_install_traps () {
  # Install cleanup traps, but never replace one the sourcing script already
  # owns: orchestrate.sh restores its state.json snapshot from an EXIT trap and
  # silently overwriting it would put the anti-tamper guard back to sleep.  A
  # script that installs its own trap must call pipeline_cleanup_tmp from it.
  local sig
  for sig in EXIT INT TERM HUP; do
    [[ -z "$(trap -p "$sig")" ]] || continue
    if [[ "$sig" == "EXIT" ]]; then
      trap 'pipeline_cleanup_tmp' EXIT
    else
      # Clean up, restore the default disposition, then re-raise, so the shell
      # still dies from the signal instead of swallowing it.
      trap "pipeline_cleanup_tmp; trap - ${sig}; kill -${sig} \$\$" "$sig"
    fi
  done
}
pipeline_install_traps

# ---- small helpers ------------------------------------------------------

strip_ansi () {
  # Drop CSI escape sequences.  docker_run.sh prints a coloured banner into
  # stdout, so every captured artifact is contaminated with them and the model
  # is shown this text verbatim.
  LC_ALL=C sed -E $'s/\x1b\\[[0-9;?]*[ -\\/]*[@-~]//g'
}

pipeline_abspath () {
  # Print $1 as an absolute, normalised host path (a relative path is
  # repository-relative).  Normalising is not cosmetic: "build", "build/" and
  # "./build" name one directory but three strings, and the string is what
  # every prefix test, every container path and the `rm -rf` guard below
  # actually see.  Symlinks are deliberately *not* resolved -- that would move
  # a path out from under the repository prefix test.
  local path="$1" part
  local -a out=()
  case "$path" in
    /*) ;;
    *)  path="${PIPELINE_ROOT}/${path}" ;;
  esac
  local IFS='/'
  for part in $path; do
    case "$part" in
      '' | '.') continue ;;
      '..') (( ${#out[@]} > 0 )) && unset 'out[${#out[@]}-1]' ;;
      *) out+=("$part") ;;
    esac
  done
  printf '/%s\n' "${out[*]}"
}

pipeline_relpath () {
  # Print $1 as a repository-relative path.  The container mounts the
  # repository, not the host filesystem, so an absolute host path means
  # nothing inside it.
  local path
  path="$(pipeline_abspath "$1")"
  case "$path" in
    "${PIPELINE_ROOT}/"*) printf '%s\n' "${path#"${PIPELINE_ROOT}/"}" ;;
    "${PIPELINE_ROOT}")   printf '.\n' ;;
    *)                    printf '%s\n' "$path" ;;
  esac
}

pipeline_in_repo () {
  # True when $1 is inside the repository, i.e. visible to the container.
  local path
  path="$(pipeline_abspath "$1")"
  [[ "$path" == "${PIPELINE_ROOT}" || "$path" == "${PIPELINE_ROOT}/"* ]]
}

# ---- path convention ----------------------------------------------------
# One rule, everywhere: a relative path is *repository*-relative, because the
# repository is the only thing the container can see.  orchestrate.sh used to
# resolve its own argv against the caller's working directory instead, so
# `orchestrate.sh net.spice build` from any other directory wrote the scaffold
# and state.json under $PWD while every step looked for them under the
# repository, and the run died on "cell generator missing or empty" naming a
# path nobody typed.  orchestrate.sh now resolves through pipeline_abspath like
# everything else; where a path is still missing, the message says which
# convention resolved it, so the failure names the real problem.

pipeline_path_hint () {
  # $1 = a path as the caller supplied it.  Print the resolution convention
  # when it is the likely cause of the "missing or empty" failure just
  # reported, and nothing at all otherwise.
  case "$1" in
    /*) return 0 ;;
  esac
  [[ "$PWD" != "$PIPELINE_ROOT" ]] || return 0
  echo "pipeline: '$1' is relative, so it was resolved against the repository root ${PIPELINE_ROOT}, not your working directory ${PWD}." >&2
  echo "pipeline: pass absolute paths, or run from ${PIPELINE_ROOT}." >&2
}

# ---- artifact discovery -------------------------------------------------
# Directory names the container tools write under a run directory.  Mirrored
# from aion_layout.verification.{MAGIC_DRC,KLAYOUT_DRC,MAGIC_LVS}_DIR_SUFFIX;
# if one side ever changes, the other must change with it.
PIPELINE_MAGIC_DRC_DIR_SUFFIX='magic.drc'
PIPELINE_KLAYOUT_DRC_DIR_SUFFIX='klayout.drc'
PIPELINE_MAGIC_LVS_DIR_SUFFIX='magic.lvs'

# Magic ends every report it finishes with its own count trailer, and netgen
# ends every completed comparison with "Final result:".  These are the tools'
# positive statements that they ran to the end; a report without one was
# truncated, and truncation must never read as "nothing to report".  Same
# markers as verification._MAGIC_COUNT_RE / _LVS_FINAL_MARKER -- change both.
PIPELINE_MAGIC_COUNT_RE='^[[:space:]]*\[INFO\][[:space:]]*COUNT:[[:space:]]*[0-9]+'
PIPELINE_NETGEN_FINAL_MARKER='Final result:'

# Set by pipeline_drc_artifacts_ok / pipeline_lvs_artifacts_ok to say what was
# missing, so the caller decides whether that is worth printing.
PIPELINE_ARTIFACT_REASON=""

pipeline_find_artifact () {
  # $1 = directory, $2.. = globs.  Prints the first non-empty regular file
  # matching a glob *directly* inside $1, or returns 1.
  #
  # Non-empty and non-recursive are both deliberate.  The old version was
  # `find -type f -name` over the whole tree with no size test, so a zero-byte
  # .rpt left by an OOM-killed container counted as proof DRC had run, and any
  # writable subdirectory could plant a file that satisfied the step.
  local dir="$1" pattern found
  shift
  [[ -d "$dir" ]] || return 1
  for pattern in "$@"; do
    found="$(find "$dir" -maxdepth 1 -type f -name "$pattern" -size +0c -print -quit 2>/dev/null || true)"
    if [[ -n "$found" ]]; then
      printf '%s\n' "$found"
      return 0
    fi
  done
  return 1
}

pipeline_canonical_dir () {
  # $1 = run directory (host), $2 = cell name, $3 = directory suffix.
  # Print <run>/<cell>.<suffix> when it exists; failing that, the single
  # <run>/*.<suffix> directory when there is exactly one.  Two candidates is an
  # ambiguity, not a preference -- picking the first sorted match is precisely
  # how a planted directory wins -- so it is reported and nothing is chosen.
  local run_dir="$1" cell="$2" suffix="$3" exact candidate
  local -a candidates=()
  exact="${run_dir}/${cell}.${suffix}"
  if [[ -d "$exact" ]]; then
    printf '%s\n' "$exact"
    return 0
  fi
  for candidate in "${run_dir}"/*."${suffix}"; do
    [[ -d "$candidate" ]] && candidates+=("$candidate")
  done
  if (( ${#candidates[@]} == 1 )); then
    printf '%s\n' "${candidates[0]}"
    return 0
  fi
  if (( ${#candidates[@]} > 1 )); then
    echo "pipeline: ${#candidates[@]} *.${suffix} directories under ${run_dir} and none is ${cell}.${suffix}: ${candidates[*]}" >&2
    echo "pipeline: refusing to guess which one the tool wrote" >&2
  fi
  return 1
}

pipeline_drc_artifacts_ok () {
  # $1 = DRC run directory (host), $2 = cell name.
  # True only when *both* DRC tools left a complete report where they write it:
  # Magic's *.magic.drc.rpt carrying its own count trailer, and at least one
  # non-empty KLayout database.  Accepting either one alone is what let a run
  # killed between the two tools be recorded as a finished DRC step.
  local drc_dir="$1" cell="$2" magic_dir klayout_dir rpt
  PIPELINE_ARTIFACT_REASON=""
  if [[ ! -d "$drc_dir" ]]; then
    PIPELINE_ARTIFACT_REASON="no DRC run directory at ${drc_dir}"
    return 1
  fi
  if ! magic_dir="$(pipeline_canonical_dir "$drc_dir" "$cell" "$PIPELINE_MAGIC_DRC_DIR_SUFFIX")"; then
    PIPELINE_ARTIFACT_REASON="no ${cell}.${PIPELINE_MAGIC_DRC_DIR_SUFFIX}/ directory under ${drc_dir}"
    return 1
  fi
  if ! rpt="$(pipeline_find_artifact "$magic_dir" '*.magic.drc.rpt')"; then
    PIPELINE_ARTIFACT_REASON="no non-empty *.magic.drc.rpt in ${magic_dir}"
    return 1
  fi
  if ! grep -qE "$PIPELINE_MAGIC_COUNT_RE" "$rpt"; then
    PIPELINE_ARTIFACT_REASON="${rpt} carries no '[INFO] COUNT:' trailer, so Magic never finished writing it (if the report format changed, update PIPELINE_MAGIC_COUNT_RE here and _MAGIC_COUNT_RE in aion_layout/verification.py together)"
    return 1
  fi
  if ! klayout_dir="$(pipeline_canonical_dir "$drc_dir" "$cell" "$PIPELINE_KLAYOUT_DRC_DIR_SUFFIX")"; then
    PIPELINE_ARTIFACT_REASON="Magic reported but no ${cell}.${PIPELINE_KLAYOUT_DRC_DIR_SUFFIX}/ directory under ${drc_dir}: KLayout did not run"
    return 1
  fi
  if ! pipeline_find_artifact "$klayout_dir" '*.lyrdb' >/dev/null; then
    PIPELINE_ARTIFACT_REASON="no non-empty *.lyrdb in ${klayout_dir}: KLayout wrote no rule database"
    return 1
  fi
  return 0
}

pipeline_lvs_artifacts_ok () {
  # $1 = LVS run directory (host), $2 = cell name.
  # True only when netgen left a report carrying its own "Final result:" line.
  local lvs_dir="$1" cell="$2" magic_lvs report
  PIPELINE_ARTIFACT_REASON=""
  if [[ ! -d "$lvs_dir" ]]; then
    PIPELINE_ARTIFACT_REASON="no LVS run directory at ${lvs_dir}"
    return 1
  fi
  if ! magic_lvs="$(pipeline_canonical_dir "$lvs_dir" "$cell" "$PIPELINE_MAGIC_LVS_DIR_SUFFIX")"; then
    PIPELINE_ARTIFACT_REASON="no ${cell}.${PIPELINE_MAGIC_LVS_DIR_SUFFIX}/ directory under ${lvs_dir}"
    return 1
  fi
  if ! report="$(pipeline_find_artifact "$magic_lvs" '*.lvs.out' '*.lvs.log')"; then
    PIPELINE_ARTIFACT_REASON="no non-empty *.lvs.out or *.lvs.log in ${magic_lvs}"
    return 1
  fi
  if ! grep -qF "$PIPELINE_NETGEN_FINAL_MARKER" "$report"; then
    PIPELINE_ARTIFACT_REASON="${report} carries no '${PIPELINE_NETGEN_FINAL_MARKER}' line, so netgen never finished the comparison"
    return 1
  fi
  return 0
}

pipeline_clear_run_dir () {
  # $1 = run directory (absolute host path), $2 = label for messages.
  # Empty it, so the step that follows is graded only on files that run wrote.
  # Neither step used to clear anything -- a report planted or left behind
  # survived into the next run and was there to be discovered.
  #
  # This deletes a directory tree, so it refuses anything that does not look
  # like a tool's own run directory rather than trusting its caller.
  local dir="$1" label="$2" entry rest
  local -a parts=()

  case "$dir" in
    /*) ;;
    *)  echo "pipeline: refusing to clear ${label} directory '${dir}': not an absolute path" >&2
        return 1 ;;
  esac
  case "$dir" in
    */ | *//* | */./* | */../* | */.. )
        echo "pipeline: refusing to clear ${label} directory '${dir}': path is not normalised" >&2
        return 1 ;;
  esac
  if [[ -L "$dir" ]]; then
    echo "pipeline: refusing to clear ${label} directory '${dir}': it is a symlink" >&2
    return 1
  fi
  rest="${dir#/}"
  IFS='/' read -r -a parts <<< "$rest"
  if (( ${#parts[@]} < 3 )); then
    echo "pipeline: refusing to clear ${label} directory '${dir}': too close to the filesystem root" >&2
    return 1
  fi
  # Never a directory something else owns: the repository itself, the home
  # directory, or any ancestor of either.
  local guard
  for guard in "$PIPELINE_ROOT" "${HOME:-}"; do
    [[ -n "$guard" ]] || continue
    if [[ "$guard" == "$dir" || "$guard" == "$dir"/* ]]; then
      echo "pipeline: refusing to clear ${label} directory '${dir}': it contains ${guard}" >&2
      return 1
    fi
  done
  # A DRC or LVS run directory holds tool output and nothing else.  Anything
  # here means the caller passed the wrong directory -- an iteration directory,
  # say, whose generator and GDS this would delete.
  for entry in "$dir"/*.py "$dir"/*.gds "$dir"/*.png "$dir"/state.json "$dir"/report.txt; do
    [[ -e "$entry" ]] || continue
    echo "pipeline: refusing to clear ${label} directory '${dir}': it holds ${entry##*/}, which no DRC/LVS run writes" >&2
    return 1
  done

  if [[ -e "$dir" ]] && ! rm -rf -- "$dir"; then
    echo "pipeline: cannot clear ${label} directory ${dir}" >&2
    return 1
  fi
  if ! mkdir -p -- "$dir"; then
    echo "pipeline: cannot create ${label} directory ${dir}" >&2
    return 1
  fi
  # Positive confirmation.  An rm that silently failed would otherwise leave
  # the stale report exactly where the step is about to go looking for it.
  if [[ -n "$(ls -A "$dir" 2>/dev/null || true)" ]]; then
    echo "pipeline: ${label} directory ${dir} is not empty after clearing it" >&2
    return 1
  fi
}

pipeline_docker () {
  # Run one shell command inside the IIC-OSIC container.  Always from the
  # repository root: docker_run.sh derives the container working directory
  # from $PWD, so the caller's cwd must not leak into the container path.
  ( cd "$PIPELINE_ROOT" && "$PIPELINE_RUN_SCRIPT" "$1" )
}

pipeline_python () {
  # Run one aion_layout entry point inside the container.
  pipeline_docker "cd tools/aion_layout && PYTHONPATH=/foss/designs/aion_flow/tools/aion_layout python3 $1"
}

# A report is only a report once it carries a verdict.  An ERROR verdict means
# report_verification.py could not verify anything, which is not a result.
PIPELINE_VERDICT_RE='^RESULT:[[:space:]]*(PASS|FAIL)[[:space:]]*$'

# ---- state.json helpers -------------------------------------------------

state_read () {
  # $1 = jq filter
  jq -r "$1" "$STATE_FILE"
}

state_write_atomic () {
  # $1 = jq filter that transforms current state into new state
  local tmp
  tmp="$(mktemp "${STATE_FILE}.XXXXXX")" || return 1
  PIPELINE_TMP_FILES+=("$tmp")
  if ! jq "$1" "$STATE_FILE" > "$tmp"; then
    rm -f "$tmp"
    echo "pipeline: state update failed, state left unchanged: $1" >&2
    return 1
  fi
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

pipeline_iteration () {
  # Print the current iteration number, or fail loudly.  A silently empty
  # iteration number used to build paths like ".../iteration_/cell.gds".
  local n
  if ! n="$(state_read '.current_iteration' 2>/dev/null)"; then
    echo "pipeline: cannot read .current_iteration from '${STATE_FILE:-<unset>}'" >&2
    return 1
  fi
  case "$n" in
    '' | null | *[!0-9]*)
      echo "pipeline: invalid .current_iteration: '${n}'" >&2
      return 1 ;;
  esac
  printf '%s\n' "$n"
}

state_demote () {
  # $1 = step key, $2 = why the artifacts do not support it.
  # Clear a "true" flag the evidence on disk does not support, and say so: a
  # flag surviving on no evidence is how a run killed mid-step skipped the very
  # step it never finished.
  local key="$1" reason="$2"
  [[ "$(state_read ".steps.${key}")" == "true" ]] || return 0
  echo "pipeline: state says ${key}=true but ${reason}; re-running that step" >&2
  state_write_atomic ".steps.${key} = false"
}

# Self-healing check: don't trust a "true" flag if the artifacts it implies are
# not all there — this is what protects the next run from a previous invocation
# getting killed mid-step.  The checks mirror the ones the steps themselves
# make, so a flag can only survive on the *complete* evidence.  Accepting a
# partial set here is how a run killed between Magic and KLayout came back,
# skipped DRC, and had its FAIL attributed to data it never collected.
state_reconcile () {
  local n iter_dir gds img drc_dir lvs_dir report
  n="$(pipeline_iteration)" || return 1
  iter_dir="${BUILD_DIR}/layout/iteration_${n}"
  gds="${iter_dir}/${CELL_NAME}.gds"
  img="${iter_dir}/${CELL_NAME}.png"
  drc_dir="${iter_dir}/drc"
  lvs_dir="${iter_dir}/lvs"
  report="${iter_dir}/report.txt"

  [[ -s "$gds" ]] || state_demote gds_generated "there is no non-empty GDS at ${gds}"
  [[ -s "$img" ]] || state_demote rendered "there is no non-empty PNG at ${img}"
  pipeline_drc_artifacts_ok "$drc_dir" "$CELL_NAME" \
    || state_demote drc_done "$PIPELINE_ARTIFACT_REASON"
  pipeline_lvs_artifacts_ok "$lvs_dir" "$CELL_NAME" \
    || state_demote lvs_done "$PIPELINE_ARTIFACT_REASON"
  if [[ ! -f "$report" ]] || ! grep -qE "$PIPELINE_VERDICT_RE" "$report"; then
    state_demote report_generated "${report} carries no PASS/FAIL verdict"
  fi
}

# ---- path-parameterised steps -------------------------------------------
# These read no globals.  Paths may be absolute (inside the repository) or
# repository-relative; anything outside the repository is invisible to the
# container and is rejected by the caller, not silently mangled here.

step_generate_scaffold_at () {
  # $1 = SPICE netlist, $2 = python cell generator to write
  local netlist module module_host
  netlist="$(pipeline_relpath "$1")"
  module="$(pipeline_relpath "$2")"
  module_host="$(pipeline_abspath "$2")"

  mkdir -p "$(dirname "$module_host")"
  if ! pipeline_python "scripts/generate_from_netlist.py ${netlist} -o ${module} --summary"; then
    echo "pipeline: generate_from_netlist.py failed for ${netlist}" >&2
    pipeline_path_hint "$1"
    return 1
  fi
  if [[ ! -s "$module_host" ]]; then
    echo "pipeline: no scaffold written to ${module_host}" >&2
    pipeline_path_hint "$2"
    return 1
  fi
}

step_generate_gds_at () {
  # $1 = python cell generator, $2 = GDS to produce
  local module gds module_host gds_host
  module="$(pipeline_relpath "$1")"
  gds="$(pipeline_relpath "$2")"
  module_host="$(pipeline_abspath "$1")"
  gds_host="$(pipeline_abspath "$2")"

  if [[ ! -s "$module_host" ]]; then
    echo "pipeline: cell generator missing or empty: ${module_host}" >&2
    pipeline_path_hint "$1"
    return 1
  fi
  mkdir -p "$(dirname "$gds_host")"
  rm -f "$gds_host"   # never let a stale GDS pass for a fresh build

  if ! pipeline_python "scripts/generate_cell.py ${module} ${gds}"; then
    echo "pipeline: generate_cell.py failed for ${module}" >&2
    return 1
  fi
  if [[ ! -s "$gds_host" ]]; then
    echo "pipeline: generate_cell.py wrote no GDS to ${gds_host}" >&2
    return 1
  fi
}

step_render_at () {
  # $1 = GDS, $2 = PNG to produce
  local gds img gds_host img_host
  gds="$(pipeline_relpath "$1")"
  img="$(pipeline_relpath "$2")"
  gds_host="$(pipeline_abspath "$1")"
  img_host="$(pipeline_abspath "$2")"

  if [[ ! -s "$gds_host" ]]; then
    echo "pipeline: render input GDS missing or empty: ${gds_host}" >&2
    pipeline_path_hint "$1"
    return 1
  fi
  mkdir -p "$(dirname "$img_host")"
  rm -f "$img_host"

  if ! pipeline_python "scripts/gds_to_image.py ${gds} ${img} --width 1600 --height 1200"; then
    echo "pipeline: gds_to_image.py failed for ${gds}" >&2
    return 1
  fi
  if [[ ! -s "$img_host" ]]; then
    echo "pipeline: gds_to_image.py wrote no PNG to ${img_host}" >&2
    return 1
  fi
}

step_drc_at () {
  # $1 = GDS, $2 = DRC run directory
  local gds drc_dir gds_host drc_host cell rc=0
  gds="$(pipeline_relpath "$1")"
  drc_dir="$(pipeline_relpath "$2")"
  gds_host="$(pipeline_abspath "$1")"
  drc_host="$(pipeline_abspath "$2")"
  cell="$(basename "$gds_host")"
  cell="${cell%.gds}"

  if [[ ! -s "$gds_host" ]]; then
    echo "pipeline: DRC input GDS missing or empty: ${gds_host}" >&2
    pipeline_path_hint "$1"
    return 1
  fi
  # Emptied, not just created: a report left here by an earlier run — or put
  # here by anything else — must not be able to answer for this one.
  pipeline_clear_run_dir "$drc_host" "DRC" || return 1

  pipeline_docker "cd tools/aion_layout && sak-drc.sh -d -b -l macro -w ${drc_dir} ${gds}" || rc=$?

  # sak-drc.sh exits ERR_DRC=1 when it finds violations: that is a *result*,
  # and it has to reach the model.  Every larger status is a tool error
  # (ERR_FILE_NOT_FOUND=2 ... ERR_NO_VAR=8) and must stop the run.
  if (( rc > 1 )); then
    echo "pipeline: sak-drc.sh failed (exit ${rc}) on ${gds}" >&2
    return 1
  fi
  # Exit 1 is only a result if both tools actually reported.  A non-zero exit
  # with an incomplete or truncated report is a killed run, and a killed run
  # that reports nothing must never be read as a clean one.
  if ! pipeline_drc_artifacts_ok "$drc_host" "$cell"; then
    echo "pipeline: sak-drc.sh (exit ${rc}) left no usable DRC evidence under ${drc_host}" >&2
    echo "pipeline: ${PIPELINE_ARTIFACT_REASON}" >&2
    return 1
  fi

  pipeline_write_klayout_receipt "${drc_host}/${cell}.klayout.drc" "$rc"
}

# Record what the KLayout half of the DRC run actually produced.
#
# Without this, "at least one non-empty .lyrdb" is the whole completeness
# check, and deleting a single rule database deletes a whole rule table from
# the verdict while the headline still reads clean — measured on the committed
# fixtures: removing the one latchup database turned "FAIL - 1 violation
# across 31 rule databases" into "PASS - 0 violations across 30".  The graders
# (aion_layout/verification.py, scripts/evidence.py) read this file back and
# refuse to call a zero-item result clean unless it matches.
#
# Absence is deliberately not fatal: a run that predates receipts, or any
# other caller, grades as "completeness UNVERIFIED", which reports the items
# it did find but can never be confirmed clean.
pipeline_write_klayout_receipt () {
  # $1 = <cell>.klayout.drc directory, $2 = sak-drc.sh exit status
  local dir="$1" rc="$2" tmp
  [[ -d "$dir" ]] || return 0
  tmp="$(mktemp "${dir}/.receipt.XXXXXX")" || return 0
  {
    printf '{\n  "version": 1,\n  "exit_status": %d,\n  "databases": [' "$rc"
    local first=1 f
    for f in "$dir"/*.lyrdb; do
      [[ -e "$f" ]] || continue
      (( first )) || printf ','
      first=0
      printf '\n    "%s"' "$(basename "$f")"
    done
    (( first )) || printf '\n  '
    printf ']\n}\n'
  } >"$tmp"
  mv -f "$tmp" "${dir}/klayout.receipt.json"
}

step_lvs_at () {
  # $1 = GDS, $2 = LVS run directory, $3 = SPICE netlist, $4 = cell name
  local gds lvs_dir netlist cell gds_host lvs_host netlist_host rc=0
  gds="$(pipeline_relpath "$1")"
  lvs_dir="$(pipeline_relpath "$2")"
  netlist="$(pipeline_relpath "$3")"
  cell="$4"
  gds_host="$(pipeline_abspath "$1")"
  lvs_host="$(pipeline_abspath "$2")"
  netlist_host="$(pipeline_abspath "$3")"

  if [[ ! -s "$gds_host" ]]; then
    echo "pipeline: LVS input GDS missing or empty: ${gds_host}" >&2
    pipeline_path_hint "$1"
    return 1
  fi
  if [[ ! -s "$netlist_host" ]]; then
    echo "pipeline: LVS reference netlist missing or empty: ${netlist_host}" >&2
    pipeline_path_hint "$3"
    return 1
  fi
  pipeline_clear_run_dir "$lvs_host" "LVS" || return 1

  pipeline_docker "cd tools/aion_layout && sak-lvs.sh -d -b -w ${lvs_dir} -s ${netlist} -l ${gds} -c ${cell}" || rc=$?

  # sak-lvs.sh exits ERR_LVS_MISMATCH=1 on a mismatch: a result, not a
  # failure.  Anything above 1 means netgen never ran to completion.
  if (( rc > 1 )); then
    echo "pipeline: sak-lvs.sh failed (exit ${rc}) on ${gds}" >&2
    return 1
  fi
  if ! pipeline_lvs_artifacts_ok "$lvs_host" "$cell"; then
    echo "pipeline: sak-lvs.sh (exit ${rc}) left no usable netgen evidence under ${lvs_host}" >&2
    echo "pipeline: ${PIPELINE_ARTIFACT_REASON}" >&2
    return 1
  fi
}

step_report_at () {
  # $1 = GDS, $2 = work directory holding drc/ and lvs/, $3 = SPICE netlist,
  # $4 = cell name, $5 = report file to write
  local gds work_dir netlist cell report report_host rc=0
  gds="$(pipeline_relpath "$1")"
  work_dir="$(pipeline_relpath "$2")"
  netlist="$(pipeline_relpath "$3")"
  cell="$4"
  report="$(pipeline_relpath "$5")"
  report_host="$(pipeline_abspath "$5")"

  mkdir -p "$(dirname "$report_host")"

  # ANSI is stripped on the way in: docker_run.sh colours its banner and this
  # file is grepped for the verdict and read by humans.
  pipeline_python "scripts/report_verification.py --cell ${cell} --gds ${gds} --netlist ${netlist} --runs-dir ${work_dir} --parse-only" \
    | strip_ansi > "$report_host" || rc=$?

  # report_verification.py exits 0 = PASS, 1 = FAIL, 2 = could not verify.
  # Only a PASS/FAIL line counts as a report: the file existing proves nothing,
  # the `>` redirection created it before the command even ran.
  if ! grep -qE "$PIPELINE_VERDICT_RE" "$report_host"; then
    echo "pipeline: report_verification.py (exit ${rc}) produced no PASS/FAIL verdict in ${report_host}" >&2
    echo "pipeline: last lines of the report follow" >&2
    tail -n 15 "$report_host" >&2 || true
    return 1
  fi
  # A verdict from a run that also reported a tool error is not a verdict: the
  # contract is one status per outcome, so the two disagreeing means something
  # printed a line that looks like one.
  if (( rc > 1 )); then
    echo "pipeline: report_verification.py exited ${rc} (could not verify) yet ${report_host} carries a verdict line:" >&2
    grep -E "$PIPELINE_VERDICT_RE" "$report_host" >&2 || true
    echo "pipeline: refusing to grade this iteration on it" >&2
    return 1
  fi
  printf '%s\n' "$report"
}

step_evidence_at () {
  # $1 = SPICE netlist, $2 = iteration directory, $3 = cell name,
  # $4 = python cell generator, $5 = optional build-error file.
  # Prints the evidence packet on stdout.  This is what the model is shown,
  # so it must never print nothing: on failure it prints why.
  local netlist iter_dir cell module build_err err packet rc=0
  netlist="$(pipeline_abspath "$1")"
  iter_dir="$(pipeline_abspath "$2")"
  cell="$3"
  module="${4:-}"
  build_err="${5:-}"

  local -a args=(--netlist "$netlist" --iter-dir "$iter_dir" --cell "$cell")
  if [[ -n "$module" ]]; then
    args+=(--module "$(pipeline_abspath "$module")")
  fi
  if [[ -n "$build_err" ]]; then
    args+=(--build-error-file "$(pipeline_abspath "$build_err")")
  fi

  # Registered, so an interrupt between here and the rm still cleans up.
  pipeline_tmp_file "evidence-err" || return 1
  err="$PIPELINE_TMP_FILE"
  packet="$( cd "$PIPELINE_ROOT" && "$PIPELINE_PYTHON" scripts/evidence.py "${args[@]}" 2>"$err" )" || rc=$?

  if (( rc != 0 )) || [[ -z "$packet" ]]; then
    # An empty summary is the bug this whole file exists to fix; say what
    # went wrong instead, on stdout, where the caller is looking.
    echo "===== EVIDENCE UNAVAILABLE ====="
    echo "scripts/evidence.py exited ${rc} for cell ${cell}"
    echo "  netlist  : ${netlist}"
    echo "  iter-dir : ${iter_dir}"
    echo "--- stderr ---"
    cat "$err" || true
    echo "===== END EVIDENCE UNAVAILABLE ====="
    rm -f "$err"
    return 1
  fi

  rm -f "$err"
  printf '%s\n' "$packet" | strip_ansi
}

report_passed_at () {
  # $1 = report file.  Only an explicit PASS verdict passes; a missing file,
  # an empty file and a "could not verify" verdict all read as "not passed".
  [[ -f "$1" ]] || return 1
  grep -qE '^RESULT:[[:space:]]*PASS[[:space:]]*$' "$1"
}

# ---- state-driven wrappers ----------------------------------------------
# Thin: resolve paths from the globals orchestrate.sh sets, delegate, and
# record the step in state.json only after the `_at` variant returned 0.

step_generate_scaffold () {
  step_generate_scaffold_at "$SPICE_NETLIST" \
    "${BUILD_DIR}/layout/iteration_0/${CELL_NAME}.py"
}

step_generate_gds () {
  local n
  n="$(pipeline_iteration)" || return 1
  step_generate_gds_at "${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.py" \
                       "${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds" || return 1
  state_write_atomic '.steps.gds_generated = true'
}

step_render () {
  local n
  n="$(pipeline_iteration)" || return 1
  step_render_at "${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds" \
                 "${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.png" || return 1
  state_write_atomic '.steps.rendered = true'
}

step_drc () {
  local n
  n="$(pipeline_iteration)" || return 1
  step_drc_at "${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds" \
              "${BUILD_DIR}/layout/iteration_${n}/drc" || return 1
  state_write_atomic '.steps.drc_done = true'
}

step_lvs () {
  local n
  n="$(pipeline_iteration)" || return 1
  step_lvs_at "${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds" \
              "${BUILD_DIR}/layout/iteration_${n}/lvs" \
              "$SPICE_NETLIST" "$CELL_NAME" || return 1
  state_write_atomic '.steps.lvs_done = true'
}

step_report () {
  local n
  n="$(pipeline_iteration)" || return 1
  step_report_at "${BUILD_DIR}/layout/iteration_${n}/${CELL_NAME}.gds" \
                 "${BUILD_DIR}/layout/iteration_${n}" \
                 "$SPICE_NETLIST" "$CELL_NAME" \
                 "${BUILD_DIR}/layout/iteration_${n}/report.txt" >/dev/null || return 1
  state_write_atomic '.steps.report_generated = true'
}

pipeline_base_iteration () {
  # The iteration the model is asked to work FROM, which is not always the
  # newest one.  When an iteration scores worse than the best seen, the loop
  # rejects it and branches from the best instead: advancing from a regression
  # is an unfiltered random walk, and the better version is then lost for good.
  # Falls back to the current iteration, so a run with no .base_iteration --
  # every run before this key existed -- behaves exactly as it did.
  local base
  base="$(state_read '.base_iteration // empty' 2>/dev/null || true)"
  case "$base" in
    '' | null | *[!0-9]*) pipeline_iteration ;;
    *) printf '%s\n' "$base" ;;
  esac
}

step_evidence () {
  # $1 = optional build-error file (orchestrate.sh passes the traceback from a
  # rejected module here so the model sees why its last attempt would not build)
  local n iter_dir build_err
  n="$(pipeline_base_iteration)" || return 1
  iter_dir="${BUILD_DIR}/layout/iteration_${n}"
  build_err="${1:-${AION_BUILD_ERROR_FILE:-}}"
  [[ -z "$build_err" && -s "${iter_dir}/build_error.txt" ]] && build_err="${iter_dir}/build_error.txt"
  [[ -s "$build_err" ]] || build_err=""
  step_evidence_at "$SPICE_NETLIST" "$iter_dir" "$CELL_NAME" \
                   "${iter_dir}/${CELL_NAME}.py" "$build_err"
}

# ---- verdict ------------------------------------------------------------

# Pure text parsing — no LLM needed to know pass/fail.
report_passed () {
  local n
  n="$(pipeline_iteration)" || return 1
  report_passed_at "${BUILD_DIR}/layout/iteration_${n}/report.txt"
}

report_summary () {
  # What the model is actually shown.  This used to grep report.txt for
  # ^(DRC|LVS|RESULT): and for violation|mismatch|...; against the real
  # artifacts both greps matched nothing and the entire payload injected into
  # the prompt was three characters, "---".  It now emits the labelled,
  # byte-capped evidence packet built from the raw artifacts.
  #   $1 = optional build-error file, forwarded to the packet.
  step_evidence "${1:-}" || true
}

run_deterministic_steps_for_current_iteration () {
  # orchestrate.sh calls this as `if ! run_deterministic_steps_...`, which
  # disables errexit inside every function below.  Hence the explicit
  # `|| return 1` after each step: without it, a failed step falls through to
  # the next one and the chain reports success.
  if [[ ! -f "${STATE_FILE:-}" ]]; then
    echo "pipeline: STATE_FILE '${STATE_FILE:-<unset>}' does not exist" >&2
    return 1
  fi
  state_reconcile || return 1

  if [[ "$(state_read '.steps.gds_generated')" != "true" ]]; then
    step_generate_gds || return 1
  fi
  if [[ "$(state_read '.steps.rendered')" != "true" ]]; then
    step_render || return 1
  fi
  if [[ "$(state_read '.steps.drc_done')" != "true" ]]; then
    step_drc || return 1
  fi
  if [[ "$(state_read '.steps.lvs_done')" != "true" ]]; then
    step_lvs || return 1
  fi
  if [[ "$(state_read '.steps.report_generated')" != "true" ]]; then
    step_report || return 1
  fi
}
