# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               The evidence packet handed to the next iteration
# ================================================================

"""Everything a model needs to draw the next iteration, taken from artifacts.

This module decides whether the layout loop converges, so it is built around
one rule: **a coordinate beats a paragraph**.  "Metal1 has a short" costs an
iteration to localise.  "Metal1 nets O0 and I2 touch over (2.065,1.450)-(2.080,
1.790)" is a rectangle the model can move.  Every block here is written to that
standard, and the block that carries the most of it is the cross-net overlap
table.

Why the overlap table exists
----------------------------

Netgen says the layout and the schematic do not match, and Magic says nothing
at all, because a Metal1 short is not a design-rule violation -- two rectangles
that are supposed to be one net and two rectangles that were never supposed to
touch are the same geometry.  Only the *labels* tell them apart, and the tools
that read the labels report the consequence ("net count 9 vs 11") rather than
the cause.  So the cause is computed here, directly from the GDS: flood-fill a
Region per labelled net through the shapes it reaches, intersect the nets
pairwise, and print the rectangle where two of them meet.

Two connectivity decisions are worth stating because they are the difference
between a table that is right and one that reads plausibly:

* Shapes on one routing layer are connected when they **touch or overlap**.
  Abutting rectangles are how every generator in ``context/py/`` draws an L,
  so requiring overlap would split most real nets in two.
* Metal is joined across layers only by a via that **overlaps both** metals by
  a positive area.  A via that merely shares an edge with a metal is an
  enclosure violation whose electrical behaviour nobody should assert.
* Activ and GatPoly are *not* traversed.  A transistor's source and drain sit
  on one Activ polygon separated by a channel that is not in the geometry, so
  flood-filling diffusion would merge every node of a stack into one net and
  report shorts that do not exist.

Fail-closed, in a module that mostly prints
-------------------------------------------

A block whose source artifact is missing prints one line saying so.  It is
never simply absent, because an absent block reads as "no problem there" -- the
same failure as an exception handler that returns a clean grade.  For the same
reason every cap in this module states what it dropped: a silent cap reads as
"that is all of them".
"""

from __future__ import annotations

import dataclasses as dc
import importlib
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from . import layout_metrics, metrics
from .runner import TOOL_DIR
from .spice_parser import SpiceParseError, Subckt, parse_spice_file
from .tech import Tech, sg13g2_tech
from .verification import DrcReport, DrcViolation, LvsReport


class EvidenceError(RuntimeError):
    """Raised when a packet cannot be assembled from the inputs given."""


# ---------------------------------------------------------------------------
# Block identity
#
# Titles are constants because two things index on them: ``Evidence.block`` and
# the drop order.  A title typed twice is a title that will differ once.
# ---------------------------------------------------------------------------

BLOCK_NETLIST = "[1] TARGET NETLIST"
BLOCK_VERDICT = "[2] VERDICT"
BLOCK_DRC = "[3] DRC ITEMS"
BLOCK_LVS = "[4] LVS DIGEST"
BLOCK_LAYOUT = "[5] LAYOUT DIGEST"
BLOCK_GEOMETRY = "[6] GEOMETRY"
BLOCK_RULES = "[7] DESIGN RULES"
BLOCK_REFERENCE = "[8] REFERENCE CELL"

#: Presentation order.  The numbering in the titles is this order.
BLOCK_ORDER: Tuple[str, ...] = (
    BLOCK_NETLIST,
    BLOCK_VERDICT,
    BLOCK_DRC,
    BLOCK_LVS,
    BLOCK_LAYOUT,
    BLOCK_GEOMETRY,
    BLOCK_RULES,
    BLOCK_REFERENCE,
)

#: Most important first.  ``render(max_bytes=...)`` drops from the end of this.
#: The verdict leads because it is three lines and says what state the cell is
#: in; the reference cell trails because it is the largest block and the only
#: one whose content the model can look up for itself.
BLOCK_PRIORITY: Tuple[str, ...] = (
    BLOCK_VERDICT,
    BLOCK_NETLIST,
    BLOCK_DRC,
    BLOCK_LVS,
    BLOCK_LAYOUT,
    BLOCK_GEOMETRY,
    BLOCK_RULES,
    BLOCK_REFERENCE,
)

#: Violations printed per DRC category before the rest are counted instead.
MAX_VIOLATIONS_PER_CATEGORY = 8
#: Rectangles printed per shorted net pair before the rest are counted instead.
MAX_CONTACTS_PER_PAIR = 4
#: Bytes of ``context/py/<name>.py`` reproduced in the reference block.
MAX_REFERENCE_BYTES = 12000
#: Lines of the Netgen message reproduced in the LVS digest.
MAX_LVS_MESSAGE_LINES = 40

#: Indent applied to a rendered verdict.  ``steps.render_verdict`` emits a
#: ``RESULT:`` line at column 0; inside the packet that would look like the
#: packet's own verdict on itself to anything that greps for it.
_VERDICT_INDENT = "    "


# ---------------------------------------------------------------------------
# Cross-net connectivity
# ---------------------------------------------------------------------------

#: Layers a standard cell may route on, lowest first.
ROUTING_LAYERS: Tuple[str, ...] = (
    "Metal1",
    "Metal2",
    "Metal3",
    "Metal4",
    "Metal5",
)

#: ``(via layer, lower metal, upper metal)``.  Only entries whose three layers
#: exist in the technology are used, so this table may name more than SG13G2
#: has without the extraction changing.
VIA_STACK: Tuple[Tuple[str, str, str], ...] = (
    ("Via1", "Metal1", "Metal2"),
    ("Via2", "Metal2", "Metal3"),
    ("Via3", "Metal3", "Metal4"),
    ("Via4", "Metal4", "Metal5"),
)


@dc.dataclass(frozen=True)
class NetContact:
    """One place where two differently-labelled nets are connected."""

    layer: str
    net_a: str
    net_b: str
    rect_um: Tuple[float, float, float, float]
    #: ``overlap`` (positive area), ``touch`` (shared edge), ``via`` (through a
    #: via cut) or ``same shape`` (two labels on one polygon).
    kind: str

    @property
    def rect_str(self) -> str:
        x1, y1, x2, y2 = self.rect_um
        return f"({x1:.3f},{y1:.3f})-({x2:.3f},{y2:.3f})"

    def describe(self) -> str:
        return (
            f"{self.net_a} <-> {self.net_b}  on {self.layer}  "
            f"{self.rect_str}  [{self.kind}]"
        )


@dc.dataclass(frozen=True)
class NetShapes:
    """What one net owns on one layer."""

    net: str
    layer: str
    polygons: int
    area_um2: float
    bbox_um: Tuple[float, float, float, float]


@dc.dataclass(frozen=True)
class NetOverlapReport:
    """Per-layer net extraction, and every cross-net connection it found."""

    cell: str
    layers: Tuple[str, ...]
    nets: Tuple[NetShapes, ...]
    contacts: Tuple[NetContact, ...]
    #: ``(net, layer, x_um, y_um)`` for a label that sits on no shape.
    stray_labels: Tuple[Tuple[str, str, float, float], ...]
    #: ``(layer, bbox_um, polygon count)`` for a connected group with no label.
    unlabelled: Tuple[Tuple[str, Tuple[float, float, float, float], int], ...]
    #: ``(net, (bbox_um, ...))`` for a net whose shapes fall into more than one
    #: connected piece.  An open is as fatal as a short and reads identically
    #: in a per-net inventory, so it is named here rather than left to be
    #: inferred from a polygon count.
    split_nets: Tuple[Tuple[str, Tuple[Tuple[float, float, float, float], ...]], ...] = ()

    @property
    def clean(self) -> bool:
        """True when no two labelled nets are connected anywhere.

        Deliberately says nothing about :attr:`split_nets`: a net in two pieces
        is a different fault from a short, and collapsing the two into one flag
        would make the caller unable to tell which it has.
        """
        return not self.contacts


def cross_net_overlaps(
    gds_path: Path | str,
    cell_name: Optional[str] = None,
    tech: Optional[Tech] = None,
) -> NetOverlapReport:
    """Extract per-net geometry from ``gds_path`` and find the shorts.

    Raises :class:`EvidenceError` rather than returning an empty report for a
    GDS that cannot be read: "no cross-net overlaps" and "the file would not
    open" must never render as the same sentence.
    """
    tech = tech or sg13g2_tech
    path = Path(gds_path)
    if not path.is_file():
        raise EvidenceError(f"no GDS at {path}")
    try:
        import klayout.db as pya
    except Exception as exc:  # pragma: no cover - klayout is a hard dependency
        raise EvidenceError(f"klayout.db unavailable: {exc}") from exc

    layout = pya.Layout()
    try:
        layout.read(str(path))
    except Exception as exc:
        raise EvidenceError(f"cannot read {path.name}: {exc}") from exc
    top = _top_cell(layout, cell_name, path.name)
    dbu = layout.dbu

    # ---- 1. every drawn polygon on every routing layer, kept separate -------
    polys: List[Any] = []
    poly_layer: List[str] = []
    present: List[str] = []
    for name in ROUTING_LAYERS:
        layer = tech.get(name)
        if layer is None:
            continue
        index = layout.find_layer(*layer.gds_pair)
        if index is None:
            continue
        region = pya.Region(top.begin_shapes_rec(index))
        if region.is_empty():
            continue
        present.append(name)
        for poly in region.each():
            polys.append(poly)
            poly_layer.append(name)

    parent = list(range(len(polys)))
    # (lower index, upper index, kind, layer named in the report, rectangle
    # to quote).  A via edge quotes the cut itself rather than the metals'
    # shared footprint: the cut is the shape that has to move.
    edges: List[Tuple[int, int, str, str, Any]] = []

    # ---- 2. same-layer adjacency: touching counts --------------------------
    by_layer: Dict[str, List[int]] = {}
    for i, name in enumerate(poly_layer):
        by_layer.setdefault(name, []).append(i)
    for name, members in by_layer.items():
        boxes = {i: polys[i].bbox() for i in members}
        for a in range(len(members)):
            i = members[a]
            for b in range(a + 1, len(members)):
                j = members[b]
                if not boxes[i].touches(boxes[j]):
                    continue
                inter = pya.Region(polys[i]) & pya.Region(polys[j])
                if not inter.is_empty():
                    kind = "overlap"
                elif not pya.Region(polys[i]).interacting(pya.Region(polys[j])).is_empty():
                    kind = "touch"
                else:
                    continue
                _union(parent, i, j)
                edges.append((i, j, kind, name, _contact_box(polys[i], polys[j], pya)))

    # ---- 3. via adjacency: a via must overlap both metals by real area -----
    for via_name, lower, upper in VIA_STACK:
        via_layer = tech.get(via_name)
        if via_layer is None or lower not in by_layer or upper not in by_layer:
            continue
        index = layout.find_layer(*via_layer.gds_pair)
        if index is None:
            continue
        for cut in pya.Region(top.begin_shapes_rec(index)).each():
            cut_region = pya.Region(cut)
            low = [i for i in by_layer[lower] if not (cut_region & pya.Region(polys[i])).is_empty()]
            high = [i for i in by_layer[upper] if not (cut_region & pya.Region(polys[i])).is_empty()]
            if not low or not high:
                continue
            box = cut.bbox()
            for i in low:
                for j in high:
                    _union(parent, i, j)
                    edges.append((i, j, "via", via_name, box))

    # ---- 4. labels -> nets --------------------------------------------------
    nets_of: Dict[int, set] = {}
    stray: List[Tuple[str, str, float, float]] = []
    for name in present:
        layer = tech[name]
        members = by_layer.get(name, [])
        for text, x, y in _texts_on(layout, top, layer, pya):
            hits = [i for i in members if polys[i].inside(pya.Point(x, y))]
            if not hits:
                stray.append((text, name, x * dbu, y * dbu))
                continue
            for i in hits:
                nets_of.setdefault(i, set()).add(text)

    # ---- 5. one owner per polygon, by breadth-first search from the labels --
    # Growing every net through the whole shorted cluster would make each net's
    # Region the entire cluster, and the pairwise intersection would then be the
    # cluster: true, and useless.  Assigning each polygon to the nearest label
    # instead puts the reported rectangle exactly where the two nets meet.
    adjacency: Dict[int, List[int]] = {}
    for i, j, _kind, _where, _box in edges:
        adjacency.setdefault(i, []).append(j)
        adjacency.setdefault(j, []).append(i)

    owner: Dict[int, str] = {}
    contacts: List[NetContact] = []
    frontier: List[int] = []
    for i in sorted(nets_of):
        names = sorted(nets_of[i])
        owner[i] = names[0]
        frontier.append(i)
        for a in range(len(names)):
            for b in range(a + 1, len(names)):
                contacts.append(
                    NetContact(
                        layer=poly_layer[i],
                        net_a=names[a],
                        net_b=names[b],
                        rect_um=_box_um(polys[i].bbox(), dbu),
                        kind="same shape",
                    )
                )
    while frontier:
        nxt: List[int] = []
        for i in frontier:
            for j in adjacency.get(i, ()):
                if j not in owner:
                    owner[j] = owner[i]
                    nxt.append(j)
        frontier = nxt

    # ---- 6. every edge whose two ends belong to different nets -------------
    for _i, _j, kind, where, box in edges:
        a, b = owner.get(_i), owner.get(_j)
        if a is None or b is None or a == b:
            continue
        lo, hi = sorted((a, b))
        contacts.append(
            NetContact(
                layer=where, net_a=lo, net_b=hi, rect_um=_box_um(box, dbu), kind=kind
            )
        )

    # ---- 7. per-net inventory and unlabelled clusters -----------------------
    per_net: Dict[Tuple[str, str], List[Any]] = {}
    for i, poly in enumerate(polys):
        net = owner.get(i)
        if net is None:
            continue
        per_net.setdefault((net, poly_layer[i]), []).append(poly)
    nets: List[NetShapes] = []
    for (net, name), group in sorted(per_net.items()):
        region = pya.Region(group).merged()
        nets.append(
            NetShapes(
                net=net,
                layer=name,
                polygons=len(group),
                area_um2=region.area() * dbu * dbu,
                bbox_um=_box_um(region.bbox(), dbu),
            )
        )

    # A net's own islands are found over same-owner adjacency, never over the
    # union-find clusters: a short merges two nets into one cluster, and an
    # island count taken from that would report a broken net as whole.
    by_owner: Dict[str, List[int]] = {}
    for i in range(len(polys)):
        net = owner.get(i)
        if net is not None:
            by_owner.setdefault(net, []).append(i)
    split: List[Tuple[str, Tuple[Tuple[float, float, float, float], ...]]] = []
    for net, members in sorted(by_owner.items()):
        remaining = set(members)
        islands: List[Any] = []
        while remaining:
            seed = min(remaining)
            remaining.discard(seed)
            stack = [seed]
            group = [seed]
            while stack:
                k = stack.pop()
                for m in adjacency.get(k, ()):
                    if m in remaining and owner.get(m) == net:
                        remaining.discard(m)
                        stack.append(m)
                        group.append(m)
            islands.append(pya.Region([polys[k] for k in group]).merged().bbox())
        if len(islands) > 1:
            split.append((net, tuple(_box_um(b, dbu) for b in islands)))

    clusters: Dict[int, List[int]] = {}
    for i in range(len(polys)):
        clusters.setdefault(_find(parent, i), []).append(i)
    unlabelled: List[Tuple[str, Tuple[float, float, float, float], int]] = []
    for members in clusters.values():
        if any(m in owner for m in members):
            continue
        region = pya.Region([polys[m] for m in members]).merged()
        unlabelled.append(
            (poly_layer[members[0]], _box_um(region.bbox(), dbu), len(members))
        )

    return NetOverlapReport(
        cell=top.name,
        layers=tuple(present),
        nets=tuple(nets),
        contacts=tuple(sorted(_dedupe(contacts), key=_contact_key)),
        stray_labels=tuple(sorted(stray)),
        unlabelled=tuple(sorted(unlabelled)),
        split_nets=tuple(split),
    )


def _contact_key(c: NetContact) -> Tuple:
    return (c.layer, c.net_a, c.net_b, c.rect_um, c.kind)


def _dedupe(contacts: Iterable[NetContact]) -> List[NetContact]:
    seen = set()
    out: List[NetContact] = []
    for c in contacts:
        key = _contact_key(c)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def _find(parent: List[int], i: int) -> int:
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def _union(parent: List[int], i: int, j: int) -> None:
    ri, rj = _find(parent, i), _find(parent, j)
    if ri != rj:
        parent[max(ri, rj)] = min(ri, rj)


def _contact_box(pa: Any, pb: Any, pya: Any) -> Any:
    """The rectangle where two same-layer polygons meet.

    An overlap has its own bounding box.  A pure edge contact intersects to
    nothing, and the intersection of the two *bounding boxes* is then the shared
    edge -- a degenerate rectangle, which is exactly the right answer for
    "where do these touch".
    """
    inter = pya.Region(pa) & pya.Region(pb)
    if not inter.is_empty():
        return inter.bbox()
    return pa.bbox() & pb.bbox()


def _box_um(box: Any, dbu: float) -> Tuple[float, float, float, float]:
    if box is None or box.empty():
        return (0.0, 0.0, 0.0, 0.0)
    return (box.left * dbu, box.bottom * dbu, box.right * dbu, box.top * dbu)


def _texts_on(layout: Any, top: Any, layer: Any, pya: Any) -> List[Tuple[str, int, int]]:
    """Return ``(text, x, y)`` in database units for one layer's label texts.

    Both the label datatype and the pin datatype are read, and so is the
    drawing datatype.  Generators differ: ``draw_pin`` writes a text on each of
    the first two, ``draw_power_rail`` leaves only the pin text
    ``Cell._insert_ports`` adds, and a GDS written elsewhere may put the name on
    the drawing layer.  Reading one datatype loses the rails on some cells and
    the signals on others.

    The walk is recursive, and the transformation is applied: a text placed in a
    subcell has to come back at its position in the top cell or it will be
    reported as sitting on no shape.
    """
    out: List[Tuple[str, int, int]] = []
    seen = set()
    for pair in (layer.label_pair, layer.pin_pair, layer.gds_pair):
        if pair is None:
            continue
        index = layout.find_layer(*pair)
        if index is None:
            continue
        for text in _each_text(top, index):
            key = (text.string, text.x, text.y)
            if key in seen:
                continue
            seen.add(key)
            out.append(key)
    return out


def _each_text(top: Any, index: int) -> List[Any]:
    """Every text on layer ``index`` at or below ``top``, in top coordinates."""
    out: List[Any] = []
    it = top.begin_shapes_rec(index)
    while not it.at_end():
        shape = it.shape()
        if shape.is_text():
            out.append(shape.text.transformed(it.trans()))
        it.next()
    return out


def _resolve_cell(path: Path, cell: str) -> Tuple[Optional[str], str]:
    """Return the cell name to measure, and a line naming what will be measured.

    Naming the cell explicitly is what lets the digest still describe a GDS
    that holds more than one top cell -- a real symptom of a generator that
    built two -- instead of refusing to measure it.  ``None`` falls back to the
    single-top rule the rest of the flow uses, so a GDS whose top carries a
    different name still reads.

    The note is never empty, and that is the point.  A digest that measures the
    only top cell in the file without saying which cell that was lets a GDS
    built under the wrong name be read as this cell's numbers -- the packet
    header says one name and the geometry belongs to another, with nothing in
    between to notice.
    """
    try:
        import klayout.db as pya

        layout = pya.Layout()
        layout.read(str(path))
    except Exception as exc:
        return None, f"cell:   UNKNOWN: {path.name} could not be opened ({type(exc).__name__}: {exc})"
    if layout.cell(cell) is not None:
        return cell, f"cell:   {cell}"
    tops = sorted(c.name for c in layout.top_cells())
    if len(tops) == 1:
        return None, (
            f"cell:   {tops[0]}   <- MISMATCH: {path.name} defines no cell named "
            f"{cell!r}; everything below describes {tops[0]!r} instead"
        )
    return None, (
        f"cell:   AMBIGUOUS: {path.name} defines no cell named {cell!r} and has "
        f"{len(tops)} top cells ({', '.join(tops) or '(none)'})"
    )


def _top_cell(layout: Any, cell_name: Optional[str], what: str) -> Any:
    if cell_name:
        cell = layout.cell(cell_name)
        if cell is None:
            raise EvidenceError(f"{what} has no cell named {cell_name!r}")
        return cell
    tops = layout.top_cells()
    if len(tops) != 1:
        names = ", ".join(sorted(c.name for c in tops)) or "(none)"
        raise EvidenceError(
            f"{what} has {len(tops)} top cells ({names}); name the one to read"
        )
    return tops[0]


# ---------------------------------------------------------------------------
# The packet
# ---------------------------------------------------------------------------


@dc.dataclass(frozen=True)
class Evidence:
    """An ordered set of titled blocks, and the rules for shrinking it."""

    cell: str
    blocks: Tuple[Tuple[str, str], ...]

    def block(self, title: str) -> str:
        """Return one block's body.

        An unknown title raises rather than returning ``""``: an empty string
        would be indistinguishable from a block that genuinely had nothing to
        report, and callers act on that difference.
        """
        for name, body in self.blocks:
            if name == title:
                return body
        lowered = title.lower()
        hits = [b for n, b in self.blocks if lowered in n.lower()]
        if len(hits) == 1:
            return hits[0]
        raise EvidenceError(
            f"no block {title!r}; this packet has: "
            + ", ".join(n for n, _ in self.blocks)
        )

    def render(self, *, max_bytes: Optional[int] = None) -> str:
        """Render the packet, dropping whole blocks to fit ``max_bytes``.

        Blocks are dropped from the end of :data:`BLOCK_PRIORITY` and the drop
        is stated in the header.  Nothing is ever truncated mid-block: a packet
        that cannot fit says it does not fit.
        """
        kept = [name for name, _ in self.blocks]
        dropped: List[str] = []
        text = self._render(kept, dropped, over=0)
        if max_bytes is None or len(text.encode("utf-8")) <= max_bytes:
            return text

        order = [n for n in reversed(BLOCK_PRIORITY) if n in kept]
        order += [n for n in reversed(kept) if n not in BLOCK_PRIORITY]
        for name in order:
            if len(kept) == 1:
                break
            kept.remove(name)
            dropped.append(name)
            text = self._render(kept, dropped, over=0)
            if len(text.encode("utf-8")) <= max_bytes:
                return text
        over = len(text.encode("utf-8")) - max_bytes
        return self._render(kept, dropped, over=over)

    def _render(self, kept: Sequence[str], dropped: Sequence[str], over: int) -> str:
        rule = "=" * 72
        lines = [rule, f" EVIDENCE PACKET -- {self.cell}", rule]
        if dropped:
            lines += _wrap(
                "PACKET NOTE: over the byte budget; these blocks were dropped "
                "whole, in reverse priority order: " + ", ".join(dropped) + ".",
                width=72,
            )
        if over > 0:
            lines += _wrap(
                f"PACKET NOTE: still {over} bytes over the budget with only "
                f"{', '.join(kept)} left. Nothing was truncated mid-block; "
                "raise max_bytes to read the packet whole.",
                width=72,
            )
        for name, body in self.blocks:
            if name not in kept:
                continue
            lines += ["", f"---- {name} " + "-" * max(4, 66 - len(name)), ""]
            lines.append(body.rstrip("\n"))
        return "\n".join(lines) + "\n"


def build_evidence(
    *,
    cell: str,
    netlist: Path | str,
    gds: Optional[Path | str] = None,
    module: Optional[Path | str] = None,
    verdict: Any = None,
    reference_cell: Optional[str] = None,
    tech: Optional[Tech] = None,
    drc: Any = None,
    lvs: Optional[LvsReport] = None,
) -> Evidence:
    """Assemble the packet for one iteration of ``cell``.

    ``drc`` and ``lvs`` take reports the caller already parsed.  When they are
    not given the reports are looked for inside ``verdict``, whatever shape it
    has, so a caller that already carries a verdict need not unpack it: any
    :class:`~aion_layout.verification.DrcReport` or
    :class:`~aion_layout.verification.LvsReport` reachable through its
    attributes, lists or dicts is used.

    ``module`` is the path of the generator that wrote ``gds``.  It is recorded
    in the layout digest so the packet names the file to edit; the module is
    never imported, because importing model-written code to describe it is how
    a description becomes an execution.
    """
    if not cell or not str(cell).strip():
        raise EvidenceError("build_evidence needs the cell name")
    tech = tech or sg13g2_tech
    subckt, netlist_note = _load_subckt(netlist, cell)

    drc_reports = _as_drc_reports(drc)
    lvs_report = lvs
    if not drc_reports or lvs_report is None:
        found_drc, found_lvs = _harvest(verdict)
        drc_reports = drc_reports or found_drc
        lvs_report = lvs_report or found_lvs

    blocks: List[Tuple[str, str]] = [
        (BLOCK_NETLIST, _netlist_block(netlist, subckt, netlist_note)),
        (BLOCK_VERDICT, _verdict_block(verdict)),
        (BLOCK_DRC, _drc_block(drc_reports)),
        (BLOCK_LVS, _lvs_block(lvs_report)),
        (BLOCK_LAYOUT, _layout_block(gds, module, subckt, cell, tech)),
        (BLOCK_GEOMETRY, _geometry_block(gds, cell, tech)),
        (BLOCK_RULES, _rules_block(tech)),
        (BLOCK_REFERENCE, _reference_block(reference_cell)),
    ]
    ordered = {name: body for name, body in blocks}
    return Evidence(
        cell=str(cell),
        blocks=tuple((name, ordered[name]) for name in BLOCK_ORDER),
    )


# ---------------------------------------------------------------------------
# [1] TARGET NETLIST
# ---------------------------------------------------------------------------


def _load_subckt(
    netlist: Path | str, cell: str
) -> Tuple[Optional[Subckt], str]:
    """Return the subckt for ``cell``, and a note when it is not available."""
    path = Path(netlist)
    if not path.is_file():
        return None, f"MISSING: no netlist at {path}"
    try:
        subckts = parse_spice_file(path)
    except (SpiceParseError, OSError) as exc:
        return None, f"UNREADABLE: {path} -- {type(exc).__name__}: {exc}"
    if not subckts:
        return None, f"EMPTY: {path} declares no .subckt"
    for s in subckts:
        if s.name == cell:
            return s, ""
    first = subckts[0]
    return first, (
        f"NOTE: {path} declares no .subckt named {cell!r}; describing "
        f"{first.name!r}, the first of {len(subckts)}"
    )


def _netlist_block(netlist: Path | str, subckt: Optional[Subckt], note: str) -> str:
    if subckt is None:
        return note or f"MISSING: no usable netlist at {netlist}"
    lines: List[str] = [f"source: {netlist}"]
    if note:
        lines.append(note)
    lines += ["", "SUBCKT (verbatim)"]
    lines += ["  " + l for l in _subckt_text(netlist, subckt).splitlines()]

    lines += ["", f"DEVICES ({len(subckt.devices)})"]
    rows = [("name", "type", "W nm", "L nm", "ng", "m", "drain", "gate", "source", "bulk")]
    for d in subckt.devices:
        rows.append(
            (
                d.name,
                "nmos" if d.is_nmos else ("pmos" if d.is_pmos else d.model),
                f"{d.width_nm:g}",
                f"{d.length_nm:g}",
                str(d.fingers),
                str(d.multiplier),
                d.drain,
                d.gate,
                d.source,
                d.bulk,
            )
        )
    lines += _table(rows, indent="  ")

    pins = list(subckt.pins)
    roles = []
    for pin in pins:
        if pin == subckt.vdd_net:
            roles.append(f"{pin}(power)")
        elif pin == subckt.vss_net:
            roles.append(f"{pin}(ground)")
        elif pin == subckt.output_net:
            roles.append(f"{pin}(output)")
        elif pin in subckt.input_nets:
            roles.append(f"{pin}(input)")
        else:
            roles.append(f"{pin}(unclassified)")
    internal = sorted(subckt.nets - set(pins))
    unused = sorted(set(pins) - subckt.nets)
    lines += ["", f"PORTS ({len(pins)}): " + " ".join(roles)]
    lines.append(f"INTERNAL NETS ({len(internal)}): " + (" ".join(internal) or "(none)"))
    if unused:
        lines.append(
            "PORTS NO DEVICE TOUCHES: "
            + " ".join(unused)
            + "  <- these must still reach a label in the layout"
        )

    lines += ["", "NET FANOUT (device terminals on each net)"]
    fan = [("net", "kind", "total", "gate", "drain", "source", "bulk", "devices")]
    for net in sorted(subckt.nets):
        gate = sum(1 for d in subckt.devices if d.gate == net)
        drain = sum(1 for d in subckt.devices if d.drain == net)
        source = sum(1 for d in subckt.devices if d.source == net)
        bulk = sum(1 for d in subckt.devices if d.bulk == net)
        kind = "port" if net in pins else "internal"
        fan.append(
            (
                net,
                kind,
                str(gate + drain + source + bulk),
                str(gate),
                str(drain),
                str(source),
                str(bulk),
                " ".join(d.name for d in subckt.devices_on_net(net)),
            )
        )
    lines += _table(fan, indent="  ")
    return "\n".join(lines)


_SUBCKT_START = re.compile(r"^\s*\.subckt\s+(\S+)", re.IGNORECASE)
_SUBCKT_END = re.compile(r"^\s*\.ends\b", re.IGNORECASE)


def _subckt_text(netlist: Path | str, subckt: Subckt) -> str:
    """Return the ``.subckt ... .ends`` lines verbatim, or say why not."""
    try:
        text = Path(netlist).read_text(errors="replace")
    except OSError as exc:  # pragma: no cover - _load_subckt read it already
        return f"(cannot re-read {netlist}: {exc})"
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        match = _SUBCKT_START.match(line)
        if match and match.group(1) == subckt.name:
            start = i
            break
    if start is None:
        return f"(no .subckt {subckt.name} line found in {netlist})"
    for j in range(start, len(lines)):
        if _SUBCKT_END.match(lines[j]):
            return "\n".join(lines[start : j + 1])
    return "\n".join(lines[start:]) + "\n(no .ends: the netlist is truncated)"


# ---------------------------------------------------------------------------
# [2] VERDICT
# ---------------------------------------------------------------------------


def _verdict_block(verdict: Any) -> str:
    if verdict is None:
        return "MISSING: no verdict was supplied; this packet says nothing about pass/fail."
    try:
        steps = importlib.import_module("aion_layout.steps")
    except Exception as exc:
        return (
            f"UNAVAILABLE: a verdict was supplied ({type(verdict).__name__}) but "
            f"aion_layout.steps could not be imported ({type(exc).__name__}: {exc}), "
            "so it could not be re-rendered. It is NOT shown -- treat the cell's "
            "state as unknown."
        )
    render = getattr(steps, "render_verdict", None)
    if render is None:
        return (
            "UNAVAILABLE: aion_layout.steps defines no render_verdict(); the "
            "verdict could not be re-rendered and is NOT shown."
        )
    try:
        text = render(verdict)
    except Exception as exc:
        return (
            f"FAILED: steps.render_verdict raised {type(exc).__name__}: {exc}. "
            "The verdict is NOT shown -- treat the cell's state as unknown."
        )
    if not isinstance(text, str) or not text.strip():
        return (
            "EMPTY: steps.render_verdict returned nothing renderable "
            f"({type(text).__name__}); the verdict is NOT shown."
        )
    body = "\n".join(_VERDICT_INDENT + l for l in text.rstrip().splitlines())
    return "recomputed by steps.render_verdict, indented one level:\n" + body


# ---------------------------------------------------------------------------
# [3] DRC ITEMS
# ---------------------------------------------------------------------------


def _as_drc_reports(drc: Any) -> Tuple[DrcReport, ...]:
    """Normalise the ``drc=`` argument, refusing anything it cannot read.

    Dropping an unrecognised value would leave the block saying "no DRC report
    was supplied" to a caller that supplied one, which is the fail-open shape
    this module exists to avoid.  ``None`` entries inside a sequence are the
    one thing skipped rather than refused: ``steps.Verdict`` legitimately holds
    ``None`` for a tool that did not run, and that absence is reported by the
    verdict itself.
    """
    if drc is None:
        return ()
    if isinstance(drc, DrcReport):
        return (drc,)
    if isinstance(drc, (list, tuple)):
        rejected = sorted(
            {type(r).__name__ for r in drc if r is not None and not isinstance(r, DrcReport)}
        )
        if rejected:
            raise EvidenceError(
                "drc= holds " + ", ".join(rejected) + " where a DrcReport was "
                "expected; refusing to report it as no DRC report at all"
            )
        return tuple(r for r in drc if isinstance(r, DrcReport))
    raise EvidenceError(
        f"drc= must be a DrcReport or a sequence of them, not "
        f"{type(drc).__name__}"
    )


def _harvest(verdict: Any) -> Tuple[Tuple[DrcReport, ...], Optional[LvsReport]]:
    """Pull every DRC/LVS report reachable from ``verdict``.

    ``steps.Verdict`` is written by another module and may hold its reports in
    a field, a tuple or a dict.  Reaching for a fixed attribute name would make
    this block silently empty the day that name changes, and an empty DRC block
    reads as a clean one.
    """
    drc: List[DrcReport] = []
    lvs: List[LvsReport] = []
    seen: set = set()

    def walk(obj: Any, depth: int) -> None:
        if obj is None or depth > 4 or len(drc) + len(lvs) > 16:
            return
        if id(obj) in seen:
            return
        seen.add(id(obj))
        if isinstance(obj, DrcReport):
            drc.append(obj)
            return
        if isinstance(obj, LvsReport):
            lvs.append(obj)
            return
        if isinstance(obj, dict):
            for value in obj.values():
                walk(value, depth + 1)
            return
        if isinstance(obj, (list, tuple, set, frozenset)):
            for value in obj:
                walk(value, depth + 1)
            return
        if dc.is_dataclass(obj) and not isinstance(obj, type):
            for field in dc.fields(obj):
                walk(getattr(obj, field.name, None), depth + 1)
            return
        for name in getattr(obj, "__dict__", {}):
            if not name.startswith("_"):
                walk(getattr(obj, name, None), depth + 1)

    walk(verdict, 0)
    return tuple(drc), (lvs[0] if lvs else None)


def _drc_block(reports: Sequence[DrcReport]) -> str:
    if not reports:
        return (
            "MISSING: no DRC report was supplied. Nothing here says the layout "
            "is rule-clean -- an empty DRC block is not a clean one."
        )
    lines: List[str] = []
    for report in reports:
        lines.append(f"--- {report.tool} ---")
        lines.append(
            f"clean={report.clean}  available={report.available}  "
            f"items={report.error_count}  tool count={report.reported_count}  "
            f"degraded={report.degraded}"
        )
        if report.completeness:
            lines.append(f"completeness={report.completeness}: {report.completeness_note}")
        if report.missing_databases:
            lines.append(
                "databases promised and not found: "
                + ", ".join(report.missing_databases)
            )
        if report.unparsed_files:
            lines.append(f"report files that could not be parsed: {report.unparsed_files}")
        if report.unavailable_reason:
            lines.append(f"unavailable: {report.unavailable_reason}")
        if report.location_note:
            lines.append(f"location: {report.location_note}")
        if not report.violations:
            lines += ["(no violation rows)", ""]
            continue

        grouped: Dict[str, List[DrcViolation]] = {}
        for v in report.violations:
            grouped.setdefault(v.category, []).append(v)
        lines.append(f"{len(report.violations)} rows in {len(grouped)} categories:")
        for category in sorted(grouped):
            items = grouped[category]
            lines.append(f"  {category}  ({len(items)})")
            for v in items[:MAX_VIOLATIONS_PER_CATEGORY]:
                text = " ".join((v.description or v.message or "").split())
                lines.append(f"    {v.category} {v.bbox_str} {text}")
            if len(items) > MAX_VIOLATIONS_PER_CATEGORY:
                lines.append(
                    f"    ... {len(items) - MAX_VIOLATIONS_PER_CATEGORY} more "
                    f"{category} rows not shown (of {len(items)})"
                )
        lines.append("")
    return "\n".join(lines).rstrip()


# ---------------------------------------------------------------------------
# [4] LVS DIGEST
# ---------------------------------------------------------------------------


def _lvs_block(report: Optional[LvsReport]) -> str:
    if report is None:
        return (
            "MISSING: no LVS report was supplied. Nothing here says the layout "
            "implements the netlist."
        )
    lines = [
        f"tool={report.tool}  clean={report.clean}  verdict={report.verdict}",
    ]
    if report.location_note:
        lines.append(f"location: {report.location_note}")
    if report.net_counts:
        layout_n, schematic_n = report.net_counts
        flag = "" if layout_n == schematic_n else "   <- MISMATCH"
        lines.append(f"nets:    layout {layout_n} vs schematic {schematic_n}{flag}")
    else:
        lines.append("nets:    not reported")
    if report.device_total:
        layout_n, schematic_n = report.device_total
        flag = "" if layout_n == schematic_n else "   <- MISMATCH"
        lines.append(f"devices: layout {layout_n} vs schematic {schematic_n}{flag}")
    else:
        lines.append("devices: total not reported")

    if report.device_counts:
        rows = [("model", "layout", "schematic", "")]
        for model in sorted(report.device_counts):
            layout_n, schematic_n = report.device_counts[model]
            rows.append(
                (
                    model,
                    str(layout_n),
                    str(schematic_n),
                    "" if layout_n == schematic_n else "<- MISMATCH",
                )
            )
        lines += ["", "DEVICE COUNTS BY MODEL"] + _table(rows, indent="  ")

    if report.disconnected_nodes:
        lines += ["", f"DISCONNECTED NODES ({len(report.disconnected_nodes)})"]
        lines += ["  " + n for n in report.disconnected_nodes]
    if report.unmatched_pins:
        lines += ["", f"UNMATCHED PINS ({len(report.unmatched_pins)})"]
        lines += [f"  {a} <-> {b}" for a, b in report.unmatched_pins]

    message = (report.message or "").rstrip()
    if message:
        body = message.splitlines()
        lines += ["", "NETGEN MESSAGE"]
        lines += ["  " + l for l in body[:MAX_LVS_MESSAGE_LINES]]
        if len(body) > MAX_LVS_MESSAGE_LINES:
            lines.append(
                f"  ... {len(body) - MAX_LVS_MESSAGE_LINES} further message "
                f"lines not shown (of {len(body)})"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# [5] LAYOUT DIGEST
# ---------------------------------------------------------------------------


def _layout_block(
    gds: Optional[Path | str],
    module: Optional[Path | str],
    subckt: Optional[Subckt],
    cell: str,
    tech: Tech,
) -> str:
    if gds is None:
        return "MISSING: no GDS was supplied; nothing about the drawn layout is known."
    path = Path(gds)
    if not path.is_file():
        return f"MISSING: no GDS at {path}; nothing about the drawn layout is known."

    named, cell_note = _resolve_cell(path, cell)
    lines = [f"gds:    {path}"]
    lines.append(f"module: {module if module else '(not supplied)'}")
    lines.append(cell_note)

    try:
        inventory = metrics.layer_inventory(path, named, tech)
    except Exception as exc:
        # Deliberately broad.  klayout raises a bare RuntimeError for a GDS
        # that is empty or truncated -- exactly what a generator that died
        # mid-write leaves behind -- and letting that escape would replace the
        # packet the model reads to fix the file with a traceback.
        inventory = {}
        lines.append(
            f"LAYER INVENTORY UNAVAILABLE: {type(exc).__name__}: {exc}"
        )
    if inventory:
        rows = [("layer", "gds", "polys", "area um2", "bbox um")]
        for name in sorted(inventory):
            stat = inventory[name]
            box = stat.bbox_um or (0.0, 0.0, 0.0, 0.0)
            rows.append(
                (
                    name,
                    f"{stat.gds_pair[0]}/{stat.gds_pair[1]}",
                    str(stat.polygons),
                    f"{stat.area_um2:.4f}",
                    f"({box[0]:.3f},{box[1]:.3f})-({box[2]:.3f},{box[3]:.3f})",
                )
            )
        lines += ["", "LAYER INVENTORY"] + _table(rows, indent="  ")

    lines += ["", "GATE COUNT"]
    crossings = layout_metrics.count_gate_crossings(path, tech, named)
    expected = len(subckt.devices) if subckt else None
    if crossings.count is None:
        lines.append(f"  UNMEASURED: {crossings.reason}")
    elif expected is None:
        lines.append(
            f"  {crossings.count} GatPoly-over-Activ regions drawn; "
            "no netlist to compare against"
        )
    else:
        flag = "matches the netlist" if crossings.count == expected else "<- MISMATCH"
        lines.append(
            f"  {crossings.count} GatPoly-over-Activ regions drawn vs "
            f"{expected} devices in the netlist: {flag}"
        )

    lines += ["", "LABELS AND PORTS"]
    lines += _label_lines(path, named, tech)

    lines += ["", "CROSS-NET OVERLAP TABLE"]
    lines += _overlap_lines(path, named, tech)
    return "\n".join(lines)


def _label_lines(path: Path, cell: Optional[str], tech: Tech) -> List[str]:
    """Every text in the GDS with its layer, datatype purpose and coordinate."""
    try:
        import klayout.db as pya
    except Exception as exc:  # pragma: no cover
        return [f"  UNAVAILABLE: klayout.db: {exc}"]
    layout = pya.Layout()
    try:
        layout.read(str(path))
        top = _top_cell(layout, cell, path.name)
    except Exception as exc:
        return [f"  UNAVAILABLE: {type(exc).__name__}: {exc}"]
    dbu = layout.dbu

    rows = [("text", "layer", "purpose", "gds", "x um", "y um")]
    for name, layer in sorted(tech.layers.items()):
        for purpose, pair in (
            ("label", layer.label_pair),
            ("pin", layer.pin_pair),
            ("drawing", layer.gds_pair),
        ):
            if pair is None:
                continue
            index = layout.find_layer(*pair)
            if index is None:
                continue
            for text in _each_text(top, index):
                rows.append(
                    (
                        text.string,
                        name,
                        purpose,
                        f"{pair[0]}/{pair[1]}",
                        f"{text.x * dbu:.3f}",
                        f"{text.y * dbu:.3f}",
                    )
                )
    if len(rows) == 1:
        return [
            "  NONE: the GDS carries no text at all. Extraction cannot name a "
            "single net, so LVS cannot match and every port is unreachable."
        ]
    return _table(sorted(rows[:1]) + sorted(rows[1:]), indent="  ")


def _overlap_lines(path: Path, cell: Optional[str], tech: Tech) -> List[str]:
    try:
        report = cross_net_overlaps(path, cell, tech)
    except Exception as exc:  # broad: see _layout_block
        return [f"  UNAVAILABLE: {type(exc).__name__}: {exc}"]

    lines = [
        "  connectivity: same-layer shapes that touch or overlap, plus metals "
        "a via overlaps",
        "  on both sides. Activ/GatPoly are not traversed (a stack shares one "
        "diffusion).",
        f"  routing layers with geometry: {', '.join(report.layers) or '(none)'}",
    ]
    if report.nets:
        rows = [("net", "layer", "polys", "area um2", "bbox um")]
        for n in report.nets:
            rows.append(
                (
                    n.net,
                    n.layer,
                    str(n.polygons),
                    f"{n.area_um2:.4f}",
                    f"({n.bbox_um[0]:.3f},{n.bbox_um[1]:.3f})-"
                    f"({n.bbox_um[2]:.3f},{n.bbox_um[3]:.3f})",
                )
            )
        lines += ["", "  NETS AS DRAWN"] + _table(rows, indent="    ")
    else:
        lines.append("  NO LABELLED NET GEOMETRY: no text sits on any routing shape.")

    if report.split_nets:
        lines += ["", f"  NETS DRAWN IN MORE THAN ONE PIECE ({len(report.split_nets)})"]
        for net, boxes in report.split_nets:
            lines.append(
                f"    {net} is {len(boxes)} disconnected island(s) -- nothing "
                "joins them, so extraction sees one net per island:"
            )
            for box in boxes[:MAX_CONTACTS_PER_PAIR]:
                lines.append(
                    f"      ({box[0]:.3f},{box[1]:.3f})-({box[2]:.3f},{box[3]:.3f})"
                )
            if len(boxes) > MAX_CONTACTS_PER_PAIR:
                lines.append(
                    f"      ... {len(boxes) - MAX_CONTACTS_PER_PAIR} more "
                    f"island(s) not shown (of {len(boxes)})"
                )

    if report.stray_labels:
        lines += ["", f"  LABELS ON NO SHAPE ({len(report.stray_labels)})"]
        for text, layer, x, y in report.stray_labels:
            lines.append(
                f"    {text} on {layer} at ({x:.3f},{y:.3f}) -- extraction "
                "will not attach this name to any net"
            )
    if report.unlabelled:
        lines += ["", f"  UNLABELLED SHAPE GROUPS ({len(report.unlabelled)})"]
        for layer, box, count in report.unlabelled:
            lines.append(
                f"    {layer} {count} polygon(s) "
                f"({box[0]:.3f},{box[1]:.3f})-({box[2]:.3f},{box[3]:.3f}) "
                "-- an internal net, or a wire that reaches nothing"
            )

    lines.append("")
    if not report.contacts:
        lines.append(
            "  CROSS-NET OVERLAPS: none. No two differently-labelled nets touch "
            "on any routing layer."
        )
        return lines

    grouped: Dict[Tuple[str, str], List[NetContact]] = {}
    for c in report.contacts:
        grouped.setdefault((c.net_a, c.net_b), []).append(c)
    lines.append(
        f"  CROSS-NET OVERLAPS: {len(report.contacts)} across "
        f"{len(grouped)} net pair(s) -- each one is a short."
    )
    for pair in sorted(grouped):
        items = grouped[pair]
        lines.append(f"    {pair[0]} <-> {pair[1]}  ({len(items)} place(s))")
        for c in items[:MAX_CONTACTS_PER_PAIR]:
            lines.append(f"      {c.layer} {c.rect_str} [{c.kind}]")
        if len(items) > MAX_CONTACTS_PER_PAIR:
            lines.append(
                f"      ... {len(items) - MAX_CONTACTS_PER_PAIR} more place(s) "
                f"not shown (of {len(items)})"
            )
    return lines


# ---------------------------------------------------------------------------
# [6] GEOMETRY
# ---------------------------------------------------------------------------


def _geometry_block(gds: Optional[Path | str], cell: str, tech: Tech) -> str:
    if gds is None:
        return "MISSING: no GDS was supplied; the placement footprint is unknown."
    path = Path(gds)
    if not path.is_file():
        return f"MISSING: no GDS at {path}; the placement footprint is unknown."
    named, cell_note = _resolve_cell(path, cell)
    lines: List[str] = [cell_note]
    try:
        geometry = metrics.gds_boundary(path, named, tech)
    except Exception as exc:  # broad: see _layout_block
        return cell_note + f"\nUNMEASURED: {type(exc).__name__}: {exc}"
    lines.append(geometry.describe())
    lines.append(
        f"sites: {geometry.sites:.4f} x {metrics.SITE_WIDTH_UM} um   "
        f"row height: {metrics.ROW_HEIGHT_UM} um   "
        f"row legal: {geometry.row_legal}"
    )
    if geometry.problems:
        lines.append("problems:")
        lines += [f"  - {p}" for p in geometry.problems]
    try:
        used = metrics.routing_metals_used(path, named, tech)
    except Exception as exc:  # broad: see _layout_block
        lines.append(f"routing metals: UNMEASURED ({type(exc).__name__}: {exc})")
    else:
        lines.append("routing metals used: " + (", ".join(used) or "(none)"))
        above = [m for m in used if m != "Metal1"]
        if above:
            lines.append(
                "  " + ", ".join(above) + " inside a standard cell is a routing "
                "blockage the block router has to work around"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# [7] DESIGN RULES
#
# The layer table is generated from ``tech.design_rules`` so it cannot drift
# from the technology the generator draws against.  The rules below it are the
# ones ``tech`` does not carry; they are quoted from context/drc/docs/ with
# their rule names, and every derived number is computed from the tech widths
# rather than typed, so only the published constants can ever be stale.
# ---------------------------------------------------------------------------

#: ``(rule, layer, minimum area in um^2)`` -- context/drc/docs/main_rules.md.
_AREA_RULES: Tuple[Tuple[str, str, float], ...] = (
    ("M1.d", "Metal1", 0.09),
    ("M2.d", "Metal2", 0.144),
)
#: ``(rule, layer, exact size in um)`` -- a cut that is neither wider nor
#: narrower than this value.
_EXACT_SIZE_RULES: Tuple[Tuple[str, str, float], ...] = (
    ("Cnt.a", "Cont", 0.16),
    ("V1.a", "Via1", 0.19),
)
#: ``(rule, description, minimum in um)`` -- enclosures ``tech`` omits.
_ENCLOSURE_RULES: Tuple[Tuple[str, str, float], ...] = (
    ("M1.c1", "Metal1 endcap enclosure of Via1", 0.05),
    ("V1.c1", "Via1 endcap enclosure by Metal1", 0.05),
    ("M2.c", "Metal2 enclosure of Via1 (all sides)", 0.005),
    ("M2.c1", "Metal2 endcap enclosure of Via1", 0.05),
)
#: ``(rule, layer, minimum spacing in um)`` for the via cuts.
_SPACING_RULES: Tuple[Tuple[str, str, float], ...] = (("V1.b", "Via1", 0.22),)


def _rules_block(tech: Tech) -> str:
    rules = tech.design_rules
    lines = [f"technology: {tech.name}   database unit: {tech.db_unit} m"]

    widths = rules.get("min_width_nm", {})
    spacing = rules.get("min_spacing_nm", {})
    enclosure = rules.get("min_enclosure_nm", {})
    vias = rules.get("via_size_nm", {})
    names = sorted(set(widths) | set(spacing) | set(enclosure) | set(vias))
    rows = [("layer", "min width", "min space", "via size", "encloses (nm)")]
    for name in names:
        encl = enclosure.get(name, {})
        rows.append(
            (
                name,
                _nm(widths.get(name)),
                _nm(spacing.get(name)),
                _nm(vias.get(name)),
                ", ".join(f"{k} {v:g}" for k, v in sorted(encl.items())) or "-",
            )
        )
    lines += ["", "FROM tech.design_rules (nm)"] + _table(rows, indent="  ")

    pairs = rules.get("min_spacing_nm_pairs", {})
    if pairs:
        lines.append("  pairwise spacing: " + ", ".join(
            f"{a}-{b} {v:g}" for (a, b), v in sorted(pairs.items())
        ))
    scalars = [
        (k, v) for k, v in sorted(rules.items()) if isinstance(v, (int, float))
    ]
    if scalars:
        lines.append("  " + ", ".join(f"{k} {v:g}" for k, v in scalars))
    gate = rules.get("min_gate_width_nm", {})
    if gate:
        lines.append(
            "  min gate width: " + ", ".join(f"{k} {v:g}" for k, v in sorted(gate.items()))
        )

    lines += [
        "",
        "NOT CARRIED BY tech -- context/drc/docs/ (um)",
        "  area rules bite first: a minimum-width strip has a minimum length.",
        "  tech.min_enclosure_nm already carries the ENDCAP value for each cut;",
        "  the all-sides rule below is the smaller published number, not a licence",
        "  to draw the landing smaller.",
    ]
    rows = [("rule", "layer", "min area um2", "at min width", "min length um")]
    for rule, layer_name, area in _AREA_RULES:
        width_nm = widths.get(layer_name)
        if width_nm:
            width_um = width_nm / 1000.0
            rows.append(
                (rule, layer_name, f"{area:g}", f"{width_um:g} um", f"{area / width_um:.4g}")
            )
        else:
            rows.append((rule, layer_name, f"{area:g}", "unknown", "unknown"))
    lines += _table(rows, indent="  ")

    rows = [("rule", "applies to", "value um", "kind")]
    for rule, layer_name, value in _EXACT_SIZE_RULES:
        rows.append((rule, layer_name, f"{value:g}", "exact: min AND max"))
    for rule, layer_name, value in _SPACING_RULES:
        rows.append((rule, layer_name, f"{value:g}", "minimum spacing"))
    for rule, what, value in _ENCLOSURE_RULES:
        rows.append((rule, what, f"{value:g}", "minimum enclosure"))
    lines += [""] + _table(rows, indent="  ")
    return "\n".join(lines)


def _nm(value: Optional[float]) -> str:
    return "-" if value is None else f"{value:g}"


# ---------------------------------------------------------------------------
# [8] REFERENCE CELL
# ---------------------------------------------------------------------------


def _reference_block(reference_cell: Optional[str]) -> str:
    if not reference_cell:
        return "NOT REQUESTED: no reference cell was named."
    if "/" in reference_cell or "\\" in reference_cell or reference_cell.startswith("."):
        return (
            f"REFUSED: {reference_cell!r} is not a bare cell name; the reference "
            "block only reads context/py/<name>.py"
        )
    path = TOOL_DIR / "context" / "py" / f"{reference_cell}.py"
    if not path.is_file():
        return f"MISSING: no reference generator at {path}"
    try:
        text = path.read_text(errors="replace")
    except OSError as exc:
        return f"UNREADABLE: {path}: {exc}"
    header = f"source: context/py/{reference_cell}.py  ({len(text)} bytes)"
    encoded = text.encode("utf-8")
    if len(encoded) <= MAX_REFERENCE_BYTES:
        return header + "\n\n" + text.rstrip()
    cut = encoded[:MAX_REFERENCE_BYTES].decode("utf-8", "ignore")
    cut = cut[: cut.rfind("\n")] if "\n" in cut else cut
    return (
        header
        + f"\nTRUNCATED to the first {MAX_REFERENCE_BYTES} bytes; "
        + f"{len(encoded) - MAX_REFERENCE_BYTES} bytes not shown.\n\n"
        + cut.rstrip()
        + "\n... (truncated)"
    )


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _table(rows: Sequence[Sequence[str]], *, indent: str = "") -> List[str]:
    """Render ``rows`` (the first is the header) as aligned columns."""
    if not rows:
        return []
    width = max(len(r) for r in rows)
    padded = [list(r) + [""] * (width - len(r)) for r in rows]
    sizes = [max(len(str(r[c])) for r in padded) for c in range(width)]
    header = padded[0]
    out: List[str] = []
    for i, row in enumerate(padded):
        cells = [str(v).ljust(sizes[c]) for c, v in enumerate(row)]
        out.append((indent + "  ".join(cells)).rstrip())
        if i == 0:
            # A column with no heading gets no rule, so an annotation column
            # ("<- MISMATCH") does not grow a dashed header out of nothing.
            rule = [("-" if str(header[c]) else " ") * sizes[c] for c in range(width)]
            out.append((indent + "  ".join(rule)).rstrip())
    return out


def _wrap(text: str, *, width: int = 72) -> List[str]:
    out: List[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}" if line else word
        if line and len(candidate) > width:
            out.append(line)
            line = word
        else:
            line = candidate
    if line:
        out.append(line)
    return out


__all__ = [
    "BLOCK_DRC",
    "BLOCK_GEOMETRY",
    "BLOCK_LAYOUT",
    "BLOCK_LVS",
    "BLOCK_NETLIST",
    "BLOCK_ORDER",
    "BLOCK_PRIORITY",
    "BLOCK_REFERENCE",
    "BLOCK_RULES",
    "BLOCK_VERDICT",
    "Evidence",
    "EvidenceError",
    "NetContact",
    "NetOverlapReport",
    "NetShapes",
    "ROUTING_LAYERS",
    "VIA_STACK",
    "build_evidence",
    "cross_net_overlaps",
]
