#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               The per-gate curriculum that narrows one model turn
# ================================================================

"""One narrow, answerable objective per model call, derived from the netlist.

Why a curriculum
----------------

The harness was rebuilt until the model could *see* the problem: ~9.5k tokens of
exact ground truth per iteration, every artifact recomputed from raw output,
nothing inferred from absence.  It still did not converge, and the measurement
says why -- the objective, not the evidence, is what the model cannot answer:

    Kimi-K2.7-Code, the whole-cell objective, the full 38 KB packet
      max_tokens=4000    66s   reasoning=16,945 ch  content=0
      max_tokens=16000  289s   reasoning=64,167 ch  content=0   finish=length

More completion budget bought more reasoning and never any output.  Better
evidence cannot rescue an objective that is not answerable in one turn.

So the loop stops asking for a finished cell.  It asks for one rung of a ladder:
place the gates; then get the device count right; then the taps; then the pins;
then the nets; then DRC.  Each rung is one narrow instruction with one measured
exit criterion, and the model is told only what that rung needs.

Nothing here may be specific to one cell
----------------------------------------

The user will generate other cells.  Every objective, every hint and every exit
criterion below is derived from the parsed netlist
(:class:`aion_layout.spice_parser.Subckt`) and the measured score
(:class:`score_iteration.Score`).  There is no coordinate literal, no cell name
and no device count written into this file; ``tests/test_scope_guards.py``
fails the build if one appears.

Exit criteria come from the score, not from a second opinion
------------------------------------------------------------

Every gate's exit test is a predicate over ``Score``, the same object
``scripts/ledger.py`` records and the same numbers ``report.txt`` is graded on.
A curriculum that measured progress its own way would eventually disagree with
the grader, and the model would be told it had passed a rung the harness still
counts as failed.

They also **fail closed**, exactly as the rest of the harness does: a gate whose
measurement is missing or degraded has *not* passed.  ``device_delta == 0`` is
true of an iteration whose LVS never ran, and treating that as progress is the
one bug this whole codebase exists to prevent.
"""

from __future__ import annotations

import argparse
import dataclasses as dc
import importlib.util
import json
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aion_layout.spice_parser import Mosfet, Subckt, parse_first_subckt  # noqa: E402


def _load_sibling(name: str):
    """Import a sibling ``scripts/*.py`` by location; ``scripts/`` is no package."""
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"aion_curriculum_{name}", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # Registered before execution: @dataclass resolves its own module out of
    # sys.modules while the class body runs.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_scorer = _load_sibling("score_iteration")
Score = _scorer.Score


# ---------------------------------------------------------------------------
# Evidence block indices, named so the ladder reads as intent rather than digits
# ---------------------------------------------------------------------------

BLOCK_OBJECTIVE = 0
BLOCK_NETLIST = 1
BLOCK_VERDICT = 2
BLOCK_MAGIC = 3
BLOCK_KLAYOUT = 4
BLOCK_NETGEN = 5
BLOCK_EXTRACTED = 6
BLOCK_LAYOUT_DIGEST = 7
BLOCK_BUILD_ERROR = 8
BLOCK_RULES = 9
BLOCK_API = 10
BLOCK_REFERENCE = 11

#: Blocks every gate carries.  [0] states the objective, [1] is the
#: specification, [2] is the verdict, [8] is the traceback when there is one --
#: a build error is never withheld, whatever rung the ladder is on.
ALWAYS: Tuple[int, ...] = (BLOCK_OBJECTIVE, BLOCK_NETLIST, BLOCK_VERDICT, BLOCK_BUILD_ERROR)

#: Byte budget for the whole packet at one rung.
#:
#: Chosen by measurement, and it is a compromise between two rules that pull
#: against each other.  The turn should be small -- that is the whole point.  But
#: the harness's first rule is that a measurement which arrives truncated is a
#: measurement the model cannot act on, and at 14,000 the LVS rungs were cutting
#: the Netgen digest and the layout digest's crossing table: the two things those
#: rungs are graded on.  18,000 leaves every evidence block whole at every rung
#: and lets the global squeeze fall where it was always meant to, on block [11],
#: the reference cell -- the only block that is not evidence about this run.
#: At 20,000 every rung of the fixture cell carries every measurement whole,
#: and only the `devices` rung -- the one that needs the netlist, the LVS
#: digest, the layout digest, the rules AND an example at once -- has to give
#: up the example.
#:
#: A rung therefore lands at roughly 4.5-6k prompt tokens rather than the 4k the
#: plan targeted.  That target was set when prompt size looked like the binding
#: constraint; it is not.  Measured against the gateway, the same model that
#: emitted zero content for a 9.9k-token whole-cell prompt emitted a working
#: module for a 4k-token rung -- and the difference that mattered was the
#: reasoning budget, not the byte count.  See MODEL_EFFORT in orchestrate.sh.
DEFAULT_GATE_BYTES = 20_000


# ---------------------------------------------------------------------------
# Fail-closed measurement guards
# ---------------------------------------------------------------------------

# These match by PREFIX, not against a list of known tags, and that is the whole
# point.  The first version enumerated the degradations it knew about, and the
# moment the scorer learned to emit a new one ("lvs-partial", for a Netgen
# report with no per-type device table) the guard did not know it and the rung
# passed on a report that says *** MISMATCH ***.  An enumerated allow-list of
# ways to be blind fails OPEN every time somebody discovers a new one.
#
# A tag naming an engine means that engine's numbers cannot be trusted.  Full
# stop, whatever the tag's suffix turns out to be.

#: Prefixes of degradation tags that mean "no DRC number was read".
_DRC_BLIND = ("magic-", "klayout-")

#: Prefixes that mean "no LVS number was read".
_LVS_BLIND = ("lvs-",)


def drc_measured(score: Score) -> bool:
    """True only when both DRC engines produced a trustworthy result."""
    return not any(tag.startswith(_DRC_BLIND) for tag in score.degraded)


def lvs_measured(score: Score) -> bool:
    """True only when Netgen produced a complete comparison this iteration."""
    if any(tag.startswith(_LVS_BLIND) for tag in score.degraded):
        return False
    return score.lvs_verdict != "no_final_result"


def crossings_measured(score: Score) -> bool:
    """True only when the GDS was read and the netlist gave a target."""
    return (
        getattr(score, "gate_crossings", None) is not None
        and getattr(score, "gate_crossings_required", None) is not None
    )


# ---------------------------------------------------------------------------
# One rung
# ---------------------------------------------------------------------------

@dc.dataclass(frozen=True)
class Gate:
    """One rung of the ladder: a narrow objective with a measured exit test."""

    #: Stable identifier, recorded in the ledger and accepted by ``AION_GATE``.
    key: str
    #: One line naming the rung, shown in the objective block's header.
    title: str
    #: The instruction, derived from the netlist.  No geometry, no cell literal.
    objective: str
    #: The rung is cleared when this returns True for the iteration's score.
    exit_test: Callable[[Score], bool]
    #: Human-readable statement of ``exit_test``, shown to the model.
    exit_text: str
    #: Evidence blocks this rung declares, beyond :data:`ALWAYS`.
    blocks: Tuple[int, ...] = ()
    #: Names kept in block [10]; everything else in the API surface is dropped.
    api_focus: Tuple[str, ...] = ()
    #: Byte budget for the packet at this rung.
    max_bytes: int = DEFAULT_GATE_BYTES

    @property
    def all_blocks(self) -> Tuple[int, ...]:
        return tuple(sorted(set(ALWAYS) | set(self.blocks)))

    def passed(self, score: Score) -> bool:
        """Fail closed: an exit test that raises has not been satisfied."""
        try:
            return bool(self.exit_test(score))
        except Exception:  # noqa: BLE001 - a broken predicate is not a pass
            return False


# ---------------------------------------------------------------------------
# Netlist-derived text fragments
# ---------------------------------------------------------------------------

def _join(names: Sequence[str], limit: int = 12) -> str:
    """Comma-join, stating the count rather than running on for a wide cell."""
    names = list(names)
    if not names:
        return "(none)"
    if len(names) <= limit:
        return ", ".join(names)
    return ", ".join(names[:limit]) + f", ... ({len(names)} total)"


def _gate_net_names(subckt: Subckt) -> List[str]:
    return sorted({d.gate for d in subckt.devices})


def _internal_nets(subckt: Subckt) -> List[str]:
    ports = set(subckt.pins)
    return sorted(n for n in subckt.nets if n not in ports)


#: Devices the `devices` rung lists individually before it summarises instead.
#:
#: Block [0] is deliberately exempt from every byte cap and from TRIM_ORDER --
#: an instruction that arrives truncated is worse than no instruction -- so it
#: has to be bounded where it is GENERATED.  Unbounded, a 120-device cell
#: produced a 7.8 KB objective and a 900-device one would produce ~60 KB: the
#: turn's whole budget spent restating a table block [1] already carries in full.
MAX_DEVICES_LISTED = 12


def _device_line(d: Mosfet) -> str:
    kind = "nmos" if d.is_nmos else ("pmos" if d.is_pmos else d.model)
    return (
        f"{d.name}: {kind} W={d.width_nm:g}nm L={d.length_nm:g}nm "
        f"D={d.drain} G={d.gate} S={d.source} B={d.bulk}"
    )


def tie_nets(subckt: Subckt) -> Tuple[Optional[str], Optional[str]]:
    """Return ``(n_well_tie, substrate_tie)``, derived from the device bulks.

    NOT from ``Subckt.vdd_net``/``vss_net``.  Those match the literal pin names
    ``VDD`` and ``VSS``, so a cell whose rails are called ``VPWR``/``VGND`` --
    which is most of them outside this one PDK -- reports no rails at all.  The
    ``taps`` rung would then silently vanish from that cell's ladder while the
    latch-up rules still fired, leaving the ``drc`` rung holding an objective it
    has not been told how to meet.

    A MOSFET's bulk terminal names the region its channel sits in: every PMOS
    bulk is the n-well, every NMOS bulk is the substrate.  That is topology, it
    is in every netlist, and it does not depend on what anybody named the rail.
    A cell whose devices disagree about their own bulk has no single region to
    tie, so it returns ``None`` rather than guessing.
    """
    n_bulks = {d.bulk for d in subckt.pmos_devices}
    p_bulks = {d.bulk for d in subckt.nmos_devices}
    n_tie = next(iter(n_bulks)) if len(n_bulks) == 1 else None
    p_tie = next(iter(p_bulks)) if len(p_bulks) == 1 else None
    return n_tie, p_tie


def _widths_by_type(subckt: Subckt) -> str:
    rows = []
    for label, devices in (("nmos", subckt.nmos_devices), ("pmos", subckt.pmos_devices)):
        if not devices:
            continue
        widths = sorted({d.width_nm for d in devices})
        lengths = sorted({d.length_nm for d in devices})
        rows.append(
            f"{len(devices)} {label}: W in {{{', '.join(f'{w:g}' for w in widths)}}} nm, "
            f"L in {{{', '.join(f'{l:g}' for l in lengths)}}} nm"
        )
    return "; ".join(rows) or "(no MOSFETs in this netlist)"


# ---------------------------------------------------------------------------
# The ladder
# ---------------------------------------------------------------------------

def _gate_build() -> Gate:
    return Gate(
        key="build",
        title="the module must build",
        objective=(
            "The module for the previous iteration did not import, did not define\n"
            "generate(cell_name, tech), or raised while drawing. Nothing about the\n"
            "layout can be measured until it builds.\n"
            "\n"
            "Do ONE thing this turn: make the module import and return a Cell.\n"
            "Read the traceback in block [8], fix exactly what it names, and change\n"
            "nothing else. Do not improve the layout, do not add geometry -- a\n"
            "module that builds and draws too little is progress; one that does not\n"
            "build is not measurable at all."
        ),
        exit_test=lambda s: bool(s.buildable),
        exit_text="the module imports, generate(cell_name, tech) returns a Cell, and a GDS is written",
        blocks=(BLOCK_API,),
        api_focus=("Cell", "Rect", "Point", "Tech", "Layer"),
    )


def _gate_gates(subckt: Subckt) -> Gate:
    nets = _gate_net_names(subckt)
    n_dev = len(subckt.devices)
    return Gate(
        key="gates",
        title="one poly gate per transistor",
        objective=(
            f"This netlist has {n_dev} transistors driven by {len(nets)} distinct gate\n"
            f"nets: {_join(nets)}.\n"
            "A transistor exists in the layout where a GatPoly shape crosses an Activ\n"
            "shape. Block [7] lists every such crossing; the host counts them in the\n"
            "written GDS and compares against the netlist.\n"
            "\n"
            "Do ONE thing this turn: make the number of poly/active crossings equal\n"
            f"{n_dev}, one per transistor, with each crossing on the gate net the\n"
            "netlist names. Every gate net above must gate at least one crossing --\n"
            "including any net that is internal to the cell rather than a port.\n"
            "\n"
            "Do not fix DRC, do not add taps, do not reroute Metal1. Later rungs do\n"
            "those; this turn is graded only on the crossing count."
        ),
        exit_test=lambda s: crossings_measured(s)
        and s.gate_crossings == s.gate_crossings_required,
        exit_text=f"the written GDS contains exactly {n_dev} GatPoly-over-Activ regions",
        blocks=(BLOCK_LAYOUT_DIGEST, BLOCK_RULES, BLOCK_REFERENCE, BLOCK_API),
        api_focus=(
            "draw_poly_gate", "draw_diffusion", "draw_well", "draw_transistor",
            "Cell", "Rect", "Point",
        ),
    )


def _device_listing(subckt: Subckt) -> str:
    """Up to :data:`MAX_DEVICES_LISTED` devices, then a pointer to block [1]."""
    devices = subckt.devices
    lines = [f"  {_device_line(d)}" for d in devices[:MAX_DEVICES_LISTED]]
    if len(devices) > MAX_DEVICES_LISTED:
        lines.append(
            f"  ... and {len(devices) - MAX_DEVICES_LISTED} more. The complete "
            "device table is block [1]; it is the specification, and this is a "
            "sample of it rather than a different list."
        )
    return "\n".join(lines)


def _gate_devices(subckt: Subckt) -> Gate:
    return Gate(
        key="devices",
        title="every device extractable, with the right W and L",
        objective=(
            "The crossings are there, but extraction does not yet recover the same\n"
            "devices the netlist declares. A crossing becomes an extractable device\n"
            "only when it sits in the right implant, in the right well, with source\n"
            "and drain diffusion on both sides of the poly.\n"
            "\n"
            f"The netlist requires: {_widths_by_type(subckt)}.\n"
            "\n"
            "Device by device:\n"
            + _device_listing(subckt)
            + "\n\n"
            "Do ONE thing this turn: make the extracted device count per type match\n"
            "the netlist, with each channel's width and length as stated above. Block\n"
            "[5] gives the per-type layout-vs-schematic counts the host grades on.\n"
            "\n"
            "Do not chase DRC or net connectivity yet."
        ),
        exit_test=lambda s: lvs_measured(s) and s.device_delta == 0,
        exit_text="Netgen reports the same device count per type in layout and schematic",
        blocks=(BLOCK_NETGEN, BLOCK_LAYOUT_DIGEST, BLOCK_RULES, BLOCK_REFERENCE, BLOCK_API),
        api_focus=(
            "draw_transistor", "draw_diffusion", "draw_poly_gate", "draw_well",
            "draw_contact", "Cell", "Rect",
        ),
    )


def _gate_taps(subckt: Subckt) -> Gate:
    n_tie, p_tie = tie_nets(subckt)
    wanted = [
        f"n-implant inside the n-well, tied to {n_tie}" if n_tie else "",
        f"p-implant in the substrate, tied to {p_tie}" if p_tie else "",
    ]
    wanted_text = "\n".join(f"  - {w}" for w in wanted if w)
    return Gate(
        key="taps",
        title="well and substrate taps on the rails",
        objective=(
            "The layout has no body contact, so the latch-up rules fire: every well\n"
            "and every substrate region must be tied to the net its devices name as\n"
            "their bulk.\n"
            "\n"
            "This cell needs:\n"
            f"{wanted_text}\n"
            "\n"
            "A tap is a diffusion contact in the SAME-type implant as the region it\n"
            "ties, contacted up to Metal1 and merged into that net.\n"
            "\n"
            "Do ONE thing this turn: add the taps, using draw_tap, and connect each\n"
            "to its rail. Derive their position and size from the rails and active\n"
            "bands your own generator already computes; do not paste coordinates.\n"
            "\n"
            "Blocks [3] and [4] list the violations by rule and coordinate. Leave\n"
            "every other DRC rule alone this turn."
        ),
        exit_test=lambda s: drc_measured(s)
        and not any(rule.startswith("LU.") for rule in s.drc_by_rule),
        exit_text="no LU.* (latch-up) violation is reported by Magic or KLayout",
        blocks=(BLOCK_MAGIC, BLOCK_KLAYOUT, BLOCK_RULES, BLOCK_LAYOUT_DIGEST, BLOCK_API),
        api_focus=("draw_tap", "draw_power_rail", "draw_well", "draw_contact", "Rect"),
    )


def _gate_shorts(subckt: Subckt) -> Gate:
    """Split out of the old `pins` rung, and split by measurement.

    That rung asked for two different jobs at once -- unmerge the shorted nets
    AND label every port -- and it was measurably too broad: the same model that
    answered the `gates` rung in 24,684 characters of reasoning spent 42,914 on
    this one and emitted no code at all, at a 12,000-token budget.

    ``disconnected`` and ``unmatched_pins`` are separate fields on ``Score``, so
    the split is not a guess about what is easier; each half has its own
    measurement and its own exit criterion.
    """
    return Gate(
        key="shorts",
        title="no two nets merged into one node",
        objective=(
            "Extraction found nodes it could not attach to any net of block [1].\n"
            "\n"
            "There are exactly two ways to produce one, and they need opposite\n"
            "edits, so establish which one you have BEFORE changing anything:\n"
            "\n"
            "  A SHORT -- two nets drawn as one piece of metal, so the node that\n"
            "    results matches neither. Block [7]'s cross-net overlap table names\n"
            "    each one, with the overlapping rectangle. FIX: separate them.\n"
            "\n"
            "  A BREAK -- one net drawn in two pieces that never meet, so a terminal\n"
            "    ends up on a node with nothing else on it. This is what you have if\n"
            "    that table reads '(none found)'. FIX: connect them.\n"
            "\n"
            "Block [6] is the netlist the tools extracted, and it settles it: find\n"
            "the unattached node there and look at what is on it. Terminals that\n"
            "block [1] puts on two different nets means a short. One lonely terminal,\n"
            "or none, means a break.\n"
            "\n"
            "You do not have to compute a route. router.connect_ports(port_a,\n"
            "port_b, layer) draws the wire between two Ports for you, and\n"
            "router.draw_via_stack changes layer; block [10] has both signatures.\n"
            "cell.ports is a dict, so the ports you already drew are addressable.\n"
            "\n"
            "Do ONE thing this turn: make that node attach. Fix the single worst one\n"
            "if there are several -- a later turn gets the rest, and one correct edit\n"
            "scores better than several speculative ones.\n"
        ),
        exit_test=lambda s: lvs_measured(s) and s.disconnected == 0,
        exit_text="Netgen reports no disconnected node",
        blocks=(BLOCK_NETGEN, BLOCK_EXTRACTED, BLOCK_LAYOUT_DIGEST, BLOCK_API),
        api_focus=(
            "draw_wire", "connect_ports", "draw_via_stack",
            "draw_metal_wire", "draw_contact", "draw_pin", "Port", "Rect", "Cell",
        ),
    )


def _gate_pins(subckt: Subckt) -> Gate:
    return Gate(
        key="pins",
        title="every port present and matched",
        objective=(
            f"This cell has {len(subckt.pins)} ports: {_join(subckt.pins)}.\n"
            "Extraction could not match some of them. A port exists for the tools\n"
            "only when a Metal1 shape carries a label on the pin layer AND that\n"
            "shape is electrically connected to the devices the netlist puts on\n"
            "that net.\n"
            "\n"
            "Do ONE thing this turn: give every port above a labelled Metal1 pin\n"
            "that reaches its own devices. Block [5] names which ports failed to\n"
            "match; those are the only ones to work on.\n"
            "\n"
            "The nets are already unmerged -- that was the previous rung -- so do\n"
            "not move existing geometry unless a pin cannot be placed without it."
        ),
        exit_test=lambda s: lvs_measured(s) and s.unmatched_pins == 0,
        exit_text="Netgen reports no unmatched port",
        blocks=(BLOCK_NETGEN, BLOCK_LAYOUT_DIGEST, BLOCK_API),
        api_focus=(
            "draw_pin", "draw_wire", "connect_ports", "draw_metal_wire",
            "draw_contact", "draw_via_stack", "Port", "Cell", "Rect",
        ),
    )


def _gate_nets(subckt: Subckt) -> Gate:
    internal = _internal_nets(subckt)
    return Gate(
        key="nets",
        title="the layout implements the netlist exactly",
        objective=(
            "Every device is there and every port matches, but the connectivity is\n"
            "not yet the netlist's. LVS passes only when the layout's graph is the\n"
            "schematic's graph.\n"
            "\n"
            f"Ports: {_join(subckt.pins)}\n"
            f"Internal nets ({len(internal)}): {_join(internal)}\n"
            "\n"
            "Block [1] carries the fanout table -- for each net, the exact device\n"
            "terminals that must be on it. Block [6] is what the tools extracted.\n"
            "Diff them: a net in [6] that merges two nets of [1] is a short, and a\n"
            "net of [1] split across two nets of [6] is a missing wire.\n"
            "\n"
            "Do ONE thing this turn: fix the connectivity differences, working from\n"
            "the shorts first. Do not redesign the placement -- it already passes the\n"
            "device rung, and a redesign restarts the ladder."
        ),
        # The guard is redundant today -- an unread LVS reports
        # "no_final_result" -- and it is here so that stays true by construction
        # rather than by the default value of a field somebody may change.
        exit_test=lambda s: lvs_measured(s) and s.lvs_verdict == "match_uniquely",
        exit_text="Netgen's final result is match_uniquely",
        blocks=(BLOCK_NETGEN, BLOCK_EXTRACTED, BLOCK_LAYOUT_DIGEST, BLOCK_API),
        api_focus=(
            "draw_wire", "connect_ports", "draw_via_stack", "draw_metal_wire",
            "draw_contact", "draw_pin", "Port", "Rect",
        ),
    )


def _gate_drc() -> Gate:
    return Gate(
        key="drc",
        title="clear the remaining design-rule violations",
        objective=(
            "The layout implements the netlist. What is left is geometry.\n"
            "\n"
            "Blocks [3] and [4] list every remaining violation with its rule name and\n"
            "coordinates; block [9] gives the numeric value each rule enforces.\n"
            "\n"
            "Do ONE thing this turn: fix the violations, largest rule class first,\n"
            "WITHOUT changing connectivity. Grow a shape rather than move it wherever\n"
            "both would work -- moving a shape is how a cleared LVS comes back broken,\n"
            "and connectivity outranks geometry in the score."
        ),
        exit_test=lambda s: drc_measured(s) and s.drc_violations == 0,
        exit_text="Magic and KLayout report no violation",
        blocks=(BLOCK_MAGIC, BLOCK_KLAYOUT, BLOCK_RULES, BLOCK_API),
        api_focus=("Rect", "draw_metal_wire", "draw_contact", "draw_tap", "Cell"),
    )


def gates(subckt: Subckt) -> List[Gate]:
    """Derive the ladder for ``subckt``.

    The ladder is shorter for a cell that cannot fail a rung: a netlist with no
    devices has nothing to gate, and one with no rails cannot be told to tap
    them.  A rung that could never fail is not a rung -- it is a place the loop
    would sit claiming progress it did not make.
    """
    ladder: List[Gate] = [_gate_build()]

    if subckt.devices:
        ladder.append(_gate_gates(subckt))
        ladder.append(_gate_devices(subckt))

    # A tap has to be tied to something.  With no derivable bulk net there is no
    # net to tie it to and the objective would name one that does not exist --
    # but ONE tie is enough: an NMOS-only cell still needs its substrate tied.
    if any(tie_nets(subckt)):
        ladder.append(_gate_taps(subckt))

    # Shorts before pins: a merged net makes ports unmatchable, so labelling
    # them first is work that the next measurement undoes.
    if subckt.devices:
        ladder.append(_gate_shorts(subckt))

    if subckt.pins:
        ladder.append(_gate_pins(subckt))

    if subckt.devices:
        ladder.append(_gate_nets(subckt))

    ladder.append(_gate_drc())
    return ladder


def current_gate(subckt: Subckt, score: Score) -> Gate:
    """Return the first rung whose exit test the score does not satisfy.

    Walking from the bottom every time is what makes progress monotonic without
    keeping any state: after a regression the loop resumes at the rung that
    broke rather than at the one it had reached, and there is no stored "current
    gate" that can drift away from what the artifacts actually show.

    When every rung passes the layout is clean and the loop breaks before asking
    for a fix; the last rung is returned so callers always get a ``Gate``.
    """
    ladder = gates(subckt)
    for gate in ladder:
        if not gate.passed(score):
            return gate
    return ladder[-1]


def ladder_status(subckt: Subckt, score: Score) -> List[Tuple[Gate, bool]]:
    """Return every rung with whether the score clears it."""
    return [(gate, gate.passed(score)) for gate in gates(subckt)]


def gate_by_key(subckt: Subckt, key: str) -> Optional[Gate]:
    """Return the rung named ``key``, or ``None`` when this cell has no such rung."""
    return next((g for g in gates(subckt) if g.key == key), None)


# ---------------------------------------------------------------------------
# The objective block
# ---------------------------------------------------------------------------

def _measured_lines(gate: Gate, score: Score) -> List[str]:
    """State the numbers this rung is graded on, and nothing else.

    Only the current rung's own measurement is shown.  Reporting the whole score
    here is how a narrow objective becomes a wide one again: the model reads the
    other numbers and starts working on them.
    """
    out: List[str] = []
    if gate.key == "build":
        out.append(f"buildable            : {'yes' if score.buildable else 'NO'}")
    elif gate.key == "gates":
        got = getattr(score, "gate_crossings", None)
        need = getattr(score, "gate_crossings_required", None)
        reason = getattr(score, "gate_crossings_reason", "") or ""
        out.append(
            "poly/active crossings: "
            + (f"{got}" if got is not None else f"NOT MEASURED ({reason or 'no GDS'})")
            + (f"   required: {need}" if need is not None else "   required: unknown")
        )
    elif gate.key == "devices":
        out.append(f"device count delta   : {score.device_delta} (layout vs schematic, summed per type)")
    elif gate.key == "taps":
        lu = {r: n for r, n in score.drc_by_rule.items() if r.startswith("LU.")}
        out.append(
            "latch-up violations  : "
            + (", ".join(f"{r}={n}" for r, n in sorted(lu.items())) if lu else "none")
        )
    elif gate.key == "pins":
        out.append(f"disconnected nodes   : {score.disconnected}")
        out.append(f"unmatched ports      : {score.unmatched_pins}")
    elif gate.key == "nets":
        out.append(f"LVS final result     : {score.lvs_verdict}")
        out.append(f"net count delta      : {score.net_delta}")
    elif gate.key == "drc":
        out.append(f"DRC violations       : {score.drc_violations}")
        if score.drc_by_rule:
            out.append(
                "  by rule            : "
                + ", ".join(f"{r}={n}" for r, n in sorted(score.drc_by_rule.items()))
            )
    if score.degraded:
        out.append(
            "UNMEASURED           : " + ", ".join(sorted(set(score.degraded)))
            + "   (an unmeasured rung has NOT passed)"
        )
    return out


def objective_block(gate: Gate, subckt: Subckt, score: Score) -> str:
    """Return the body of block [0]: the one thing to do this turn."""
    ladder = gates(subckt)
    position = next((i for i, g in enumerate(ladder) if g.key == gate.key), 0) + 1

    cleared = [g.key for g in ladder[: position - 1]]
    remaining = [g.key for g in ladder[position:]]

    lines = [
        f"RUNG {position} OF {len(ladder)}: {gate.key} -- {gate.title}",
        "",
        "The cell is built one rung at a time. This turn is graded on this rung",
        "only; the rungs after it are somebody else's turn and working on them now",
        "spends the budget without moving the score.",
        "",
        f"  cleared   : {', '.join(cleared) if cleared else '(none yet)'}",
        f"  THIS TURN : {gate.key}",
        f"  still to do: {', '.join(remaining) if remaining else '(none -- this is the last rung)'}",
        "",
        "--- what to do ---",
        gate.objective,
        "",
        "--- measured now, for this rung ---",
    ]
    lines.extend("  " + line for line in _measured_lines(gate, score))
    lines.extend(
        [
            "",
            f"PASSES WHEN: {gate.exit_text}.",
            "",
            "Write the complete corrected module. Change as little as possible: an",
            "edit that clears this rung and breaks an earlier one scores worse than",
            "no edit at all, and the loop will send you back down the ladder.",
        ]
    )
    return "\n".join(lines)


OBJECTIVE_TITLE = "OBJECTIVE FOR THIS TURN (the only thing graded)"


# ---------------------------------------------------------------------------
# CLI -- used by orchestrate.sh, and by hand when inspecting a ladder
# ---------------------------------------------------------------------------

def _resolve(netlist: Path, cell: Optional[str]) -> Subckt:
    from aion_layout.spice_parser import parse_spice_file

    subckts = parse_spice_file(netlist)
    if not subckts:
        raise SystemExit(f"no subcircuit in {netlist}")
    if cell:
        match = next((s for s in subckts if s.name == cell), None)
        if match is not None:
            return match
    return subckts[0]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect the gate ladder for a netlist.")
    parser.add_argument("--netlist", required=True)
    parser.add_argument("--cell", default=None)
    parser.add_argument("--iter-dir", default=None, help="Score this iteration and pick the rung.")
    parser.add_argument("--gate", default=None, help="Force a rung by key.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--print", dest="what", choices=("key", "ladder", "objective", "blocks"),
        default="ladder",
    )
    args = parser.parse_args(argv)

    subckt = _resolve(Path(args.netlist), args.cell)
    ladder = gates(subckt)

    if args.iter_dir:
        score = _scorer.score_iteration(
            Path(args.iter_dir), args.cell or subckt.name, Path(args.netlist)
        )
    else:
        # No iteration to read: an all-zero score would read as "everything
        # passes", so start from the bottom of the ladder instead.
        score = _scorer.unmeasured_score()

    gate = gate_by_key(subckt, args.gate) if args.gate else current_gate(subckt, score)
    if gate is None:
        print(
            f"no rung named {args.gate!r} for {subckt.name}; this cell's ladder is: "
            + ", ".join(g.key for g in ladder),
            file=sys.stderr,
        )
        return 2

    if args.json:
        print(json.dumps(
            {
                "cell": subckt.name,
                "ladder": [g.key for g in ladder],
                "gate": gate.key,
                "title": gate.title,
                "blocks": list(gate.all_blocks),
                "max_bytes": gate.max_bytes,
                "status": {g.key: passed for g, passed in ladder_status(subckt, score)},
            },
            indent=2,
        ))
        return 0

    if args.what == "key":
        print(gate.key)
    elif args.what == "blocks":
        print(",".join(str(b) for b in gate.all_blocks))
    elif args.what == "objective":
        print(objective_block(gate, subckt, score))
    else:
        for g, passed in ladder_status(subckt, score):
            mark = "PASS" if passed else ("HERE" if g.key == gate.key else "    ")
            print(f"  [{mark}] {g.key:<8} {g.title}")
    return 0


__all__ = [
    "ALWAYS",
    "BLOCK_API",
    "BLOCK_BUILD_ERROR",
    "BLOCK_EXTRACTED",
    "BLOCK_KLAYOUT",
    "BLOCK_LAYOUT_DIGEST",
    "BLOCK_MAGIC",
    "BLOCK_NETGEN",
    "BLOCK_NETLIST",
    "BLOCK_OBJECTIVE",
    "BLOCK_REFERENCE",
    "BLOCK_RULES",
    "BLOCK_VERDICT",
    "DEFAULT_GATE_BYTES",
    "OBJECTIVE_TITLE",
    "Gate",
    "crossings_measured",
    "current_gate",
    "drc_measured",
    "gate_by_key",
    "gates",
    "ladder_status",
    "tie_nets",
    "lvs_measured",
    "main",
    "objective_block",
]


if __name__ == "__main__":
    sys.exit(main())
