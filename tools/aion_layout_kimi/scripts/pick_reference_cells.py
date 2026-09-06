#!/usr/bin/env python3
# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Host-side selection of a reference cell
# ================================================================

"""Rank the PDK standard cells by structural similarity to a target netlist.

Why this is host-side
---------------------

``context/`` holds 84 reference netlists and 83 matching generators: about
4 MB, roughly 794k tokens.  Pointing a model at it costs three times its whole
window to discover which one file it needed.  Ranking here is deterministic,
free, repeatable, and cannot blow the context budget -- and the winner is one
~1,700-token generator that shows the API and the tap/implant conventions in
use on a cell with the same shape as the target.

What it is *not*
----------------

The selected cell is a **different** cell than the target.  It is inlined as an
example of how the API is called, never as an answer: it does not implement the
target's topology, and a model that copies it verbatim fails LVS immediately.

Ranking features, per subcircuit
--------------------------------

``(n_nmos, n_pmos, n_ports, n_internal_nets, pun_depth, pdn_depth)`` where the
two depths are the longest series chain in the pull-up and pull-down networks --
the thing that decides how many transistors have to share a diffusion strip, and
therefore what the layout looks like.  Distance is the sum of absolute feature
differences, weighted so device counts dominate; ties break on the cell name so
the choice is stable across runs.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aion_layout.spice_parser import Mosfet, Subckt, parse_spice_file  # noqa: E402

#: Feature weights.  Device counts dominate because they set the cell's width
#: and the number of diffusion strips; the depths matter next because they
#: decide whether devices stack or sit side by side.
WEIGHTS: Dict[str, float] = {
    "n_nmos": 3.0,
    "n_pmos": 3.0,
    "n_ports": 1.0,
    "n_internal": 1.5,
    "pun_depth": 2.0,
    "pdn_depth": 2.0,
}

#: Byte cap on the inlined generator, so one large reference cannot crowd the
#: verification evidence out of the packet.
DEFAULT_MAX_BYTES = 8000


@dataclass(frozen=True)
class Features:
    """The structural fingerprint a cell is ranked on."""

    n_nmos: int
    n_pmos: int
    n_ports: int
    n_internal: int
    pun_depth: int
    pdn_depth: int

    def distance(self, other: "Features") -> float:
        """Return the weighted L1 distance between two fingerprints."""
        return (
            WEIGHTS["n_nmos"] * abs(self.n_nmos - other.n_nmos)
            + WEIGHTS["n_pmos"] * abs(self.n_pmos - other.n_pmos)
            + WEIGHTS["n_ports"] * abs(self.n_ports - other.n_ports)
            + WEIGHTS["n_internal"] * abs(self.n_internal - other.n_internal)
            + WEIGHTS["pun_depth"] * abs(self.pun_depth - other.pun_depth)
            + WEIGHTS["pdn_depth"] * abs(self.pdn_depth - other.pdn_depth)
        )

    def as_row(self) -> str:
        return (
            f"nmos={self.n_nmos} pmos={self.n_pmos} ports={self.n_ports} "
            f"internal={self.n_internal} pun_depth={self.pun_depth} "
            f"pdn_depth={self.pdn_depth}"
        )


def _rail_names(subckt: Subckt) -> Tuple[Optional[str], Optional[str]]:
    return subckt.vdd_net, subckt.vss_net


def _chain_depth(devices: Sequence[Mosfet], rail: Optional[str]) -> int:
    """Return the longest series run from any node back to ``rail``.

    Walks source/drain edges only.  A parallel network gives 1, a two-high
    stack gives 2, and so on.  Depth-limited and cycle-guarded because an
    extracted netlist is not guaranteed to be a tree.
    """
    if rail is None or not devices:
        return 0

    # adjacency over source/drain terminals
    edges: Dict[str, List[Tuple[str, str]]] = {}
    for d in devices:
        edges.setdefault(d.source, []).append((d.drain, d.name))
        edges.setdefault(d.drain, []).append((d.source, d.name))

    # Breadth-first hop count, not longest simple path.  Enumerating every
    # simple path is exponential -- it hung outright on a 900-device synthetic
    # netlist -- and it is also the wrong measure: what matters for the layout
    # is how many devices separate the rail from the furthest node, which is
    # the BFS eccentricity.  A three-high stack gives 3; three devices in
    # parallel give 1.  O(V+E).
    from collections import deque

    seen = {rail: 0}
    queue = deque([rail])
    best = 0
    while queue:
        node = queue.popleft()
        depth = seen[node]
        best = max(best, depth)
        for nxt, _dev in edges.get(node, ()):
            if nxt not in seen:
                seen[nxt] = depth + 1
                queue.append(nxt)
    return best


def features_of(subckt: Subckt) -> Features:
    """Return the structural fingerprint of ``subckt``."""
    vdd, vss = _rail_names(subckt)
    ports = set(subckt.pins)
    internal = {n for n in subckt.nets if n not in ports}
    return Features(
        n_nmos=len(subckt.nmos_devices),
        n_pmos=len(subckt.pmos_devices),
        n_ports=len(subckt.pins),
        n_internal=len(internal),
        pun_depth=_chain_depth(subckt.pmos_devices, vdd),
        pdn_depth=_chain_depth(subckt.nmos_devices, vss),
    )


@dataclass(frozen=True)
class Candidate:
    """One ranked reference cell."""

    name: str
    spice: Path
    generator: Optional[Path]
    features: Features
    distance: float


def rank_candidates(
    target: Subckt,
    spice_dir: Path,
    py_dir: Path,
) -> List[Candidate]:
    """Return every parsable reference cell, nearest first."""
    target_features = features_of(target)
    out: List[Candidate] = []

    for spice in sorted(spice_dir.glob("*.spice")):
        if spice.stem == target.name:
            continue  # never propose the target as its own example
        try:
            subckts = parse_spice_file(spice)
        except Exception:
            continue
        if not subckts:
            continue
        ref = subckts[0]
        generator = py_dir / f"{spice.stem}.py"
        feats = features_of(ref)
        out.append(
            Candidate(
                name=spice.stem,
                spice=spice,
                generator=generator if generator.is_file() else None,
                features=feats,
                distance=feats.distance(target_features),
            )
        )

    # Stable: distance first, then a generator existing at all, then the name.
    out.sort(key=lambda c: (c.distance, c.generator is None, c.name))
    return out


def pick(
    netlist: Path,
    context_dir: Path,
    require_generator: bool = True,
) -> Tuple[Optional[Candidate], Features, List[Candidate]]:
    """Return ``(winner, target_features, ranked)`` for ``netlist``."""
    subckts = parse_spice_file(netlist)
    if not subckts:
        raise ValueError(f"no subcircuit in {netlist}")
    target = subckts[0]

    ranked = rank_candidates(target, context_dir / "spice", context_dir / "py")
    winner: Optional[Candidate] = None
    for cand in ranked:
        if cand.generator is not None or not require_generator:
            winner = cand
            break
    return winner, features_of(target), ranked


def render_block(
    netlist: Path,
    context_dir: Path,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> str:
    """Return the reference-cell section for the evidence packet."""
    try:
        winner, target_features, ranked = pick(netlist, context_dir)
    except Exception as exc:
        return f"(not available: {type(exc).__name__}: {exc})"

    if winner is None or winner.generator is None:
        return (
            "(no reference cell available: "
            f"{len(ranked)} candidate(s) parsed, none with a generator under "
            f"{context_dir / 'py'})"
        )

    source = winner.generator.read_text(errors="replace")
    truncated = False
    if len(source.encode("utf-8")) > max_bytes:
        source = source.encode("utf-8")[:max_bytes].decode("utf-8", "ignore")
        source = source[: source.rfind("\n")] if "\n" in source else source
        truncated = True

    runners_up = ", ".join(
        f"{c.name} (d={c.distance:.1f})" for c in ranked[1:4] if c.generator
    )

    head = [
        f"target      : {target_features.as_row()}",
        f"selected    : {winner.name}  (distance {winner.distance:.1f})",
        f"             {winner.features.as_row()}",
        f"runners-up  : {runners_up or '(none)'}",
        f"ranked      : {len(ranked)} PDK cells, selected host-side by structural distance",
        "",
        "THIS IS A DIFFERENT CELL, NOT THE ANSWER.  It implements its own logic,",
        "not the target's.  It is here to show how the API is called on a cell of",
        "roughly this shape -- diffusion strips, gate placement, taps, rails,",
        "pins.  Copying it will fail LVS: the target's topology is in block [1].",
        "",
        f"--- {winner.generator.name} ---",
    ]
    tail = ["", f"(generator truncated at {max_bytes} bytes)"] if truncated else []
    return "\n".join(head + [source.rstrip()] + tail)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rank PDK standard cells by structural similarity to a netlist.",
    )
    parser.add_argument("netlist", help="Target SPICE netlist.")
    parser.add_argument(
        "--context-dir",
        default=str(ROOT / "context"),
        help="Directory holding spice/ and py/ (default: ./context).",
    )
    parser.add_argument("--top", type=int, default=10, help="How many to list.")
    parser.add_argument(
        "--block",
        action="store_true",
        help="Print the evidence-packet section instead of the ranking table.",
    )
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    args = parser.parse_args(argv)

    netlist = Path(args.netlist)
    context_dir = Path(args.context_dir)

    if args.block:
        print(render_block(netlist, context_dir, args.max_bytes))
        return 0

    winner, target_features, ranked = pick(netlist, context_dir)
    print(f"target: {netlist.name}")
    print(f"  {target_features.as_row()}")
    print()
    print(f"{'cell':<28} {'dist':>6}  gen  features")
    for cand in ranked[: args.top]:
        mark = "*" if winner is not None and cand.name == winner.name else " "
        gen = "yes" if cand.generator else "no "
        print(f"{mark}{cand.name:<27} {cand.distance:>6.1f}  {gen}  {cand.features.as_row()}")
    print()
    print(f"selected: {winner.name if winner else '(none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
