# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               A strict Liberty reader, for comparing two .lib files
# ================================================================

"""Liberty, read exactly as far as a delay comparison needs and no further.

The flow has to hold two libraries side by side -- the one ``tools/aion_char``
writes for the AION cell, and the PDK's own
``sg13g2_stdcell_typ_1p20V_25C.lib`` -- and answer whether one is faster than
the other.  That is a small question, and the part of Liberty it needs is
small: group headers, simple attributes, and ``index_1``/``index_2``/``values``
look-up tables.  A brace- and quote-aware tokenizer covers all of it, which is
why there is no third-party dependency here: the two producers this reader has
to satisfy are both known, both emit the same subset, and a dependency would
buy nothing but a version to pin.

**Every number handed out by this module is already in ns, pF and pW.**  The
scaling happens once, at parse time, from the library's own ``time_unit``,
``capacitive_load_unit`` and ``leakage_power_unit``.  This is the single most
important decision in the file: two libraries are only comparable if their
numbers mean the same thing, and a library that declares ``time_unit : "1ps"``
would otherwise look a thousand times faster than an identical one declaring
``"1ns"``.  ``Library.time_unit_ns`` and friends keep the factors so a caller
can get back to what the file literally said; nothing else in the flow should
need to.

Fail-closed choices worth knowing about:

* A library that declares no ``time_unit`` or no ``capacitive_load_unit`` is an
  error.  The Liberty standard has defaults, but a defaulted unit is a guess
  about what somebody meant, and a guess multiplied into every delay in the
  report is exactly the kind of quiet wrongness this flow exists to avoid.
* An attribute that is present but unparseable is an error, never a skip.
* ``area`` and ``cell_leakage_power`` are ``None`` when the cell does not state
  them, never ``0.0``.  Zero is a plausible measurement; ``None`` is not, and a
  caller that forgets to check gets a ``TypeError`` instead of a clean-looking
  report built on a number nobody measured.
* ``nom_voltage`` / ``nom_temperature`` / ``nom_process`` are read for the same
  reason the units are: a delay only means something alongside the PVT it was
  measured at, and a caller comparing two libraries has to be able to prove they
  share one.  They are ``None`` when the file is silent, never a default corner.

Timing groups that carry no ``cell_rise`` and no ``cell_fall`` -- setup/hold and
recovery/removal constraints on sequential cells -- are not delay arcs and are
not kept.  Combinational AION cells have none; a flip-flop's CLK->Q arc does
carry delay tables and is kept like any other.
"""

from __future__ import annotations

import dataclasses as dc
import re
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


class LibertyError(RuntimeError):
    """Raised when a Liberty file cannot be read, or says something it must not."""


# --------------------------------------------------------------------------------
# Units
# --------------------------------------------------------------------------------

#: Factor from one library time unit to nanoseconds.
_TIME_TO_NS = {"s": 1e9, "ms": 1e6, "us": 1e3, "ns": 1.0, "ps": 1e-3, "fs": 1e-6}
#: Factor from one library capacitance unit to picofarads.
_CAP_TO_PF = {"f": 1e12, "mf": 1e9, "uf": 1e6, "nf": 1e3, "pf": 1.0, "ff": 1e-3}
#: Factor from one library power unit to picowatts.
_POWER_TO_PW = {"w": 1e12, "mw": 1e9, "uw": 1e6, "nw": 1e3, "pw": 1.0, "fw": 1e-3}

_UNIT_RE = re.compile(r"^\s*([0-9]*\.?[0-9]*(?:[eE][+-]?[0-9]+)?)\s*([a-zA-Z]+)\s*$")


def _unit_factor(text: str, table: Dict[str, float], what: str, where: str) -> float:
    """Turn ``"1ns"`` / ``"1, pf"`` into the factor to the canonical unit."""
    match = _UNIT_RE.match(text.replace(",", " "))
    if match is None:
        raise LibertyError(f"{where}: cannot read {what} from {text!r}")
    mult = float(match.group(1)) if match.group(1) not in ("", ".") else 1.0
    suffix = match.group(2).lower()
    if suffix not in table:
        raise LibertyError(
            f"{where}: {what} {text!r} uses the unknown unit {suffix!r}; "
            f"known units are {', '.join(sorted(table))}"
        )
    return mult * table[suffix]


# --------------------------------------------------------------------------------
# Tokenizer and parser
# --------------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""(?P<cont>\\\r?\n)
      | (?P<ws>[ \t\r\n]+)
      | (?P<block>/\*.*?\*/)
      | (?P<line>//[^\n]*)
      | (?P<str>"[^"]*")
      | (?P<punct>[(){}:;,])
      | (?P<word>[^ \t\r\n(){}:;,"]+)""",
    re.VERBOSE | re.DOTALL,
)

#: One token: (kind, raw text, 1-based line).  ``kind`` is 'str', 'punct' or 'word'.
_Token = Tuple[str, str, int]


def _unquote(text: str) -> str:
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1]
    return text


def _tokenize(text: str, where: str) -> List[_Token]:
    tokens: List[_Token] = []
    line = 1
    pos = 0
    end = len(text)
    while pos < end:
        match = _TOKEN_RE.match(text, pos)
        if match is None:
            raise LibertyError(f"{where}:{line}: cannot tokenize at {text[pos:pos + 40]!r}")
        kind = match.lastgroup
        raw = match.group()
        if kind in ("str", "punct", "word"):
            tokens.append((kind, raw, line))
        line += raw.count("\n")
        pos = match.end()
    return tokens


@dc.dataclass
class _Group:
    """One ``name (args) { ... }`` block, kept in the shape the builders want.

    ``attrs`` holds ``name : value ;`` with the value already unquoted, and a
    list per name because Liberty lets an attribute repeat (``leakage_power``
    conditions, for instance).  ``complex_attrs`` holds ``name (a, b) ;`` with
    the argument tokens *raw*: whether an argument was quoted is the only thing
    that distinguishes a ``values`` table's rows from a single flat row.
    """

    type: str
    args: Tuple[str, ...]
    attrs: Dict[str, List[str]]
    complex_attrs: Dict[str, List[Tuple[str, ...]]]
    groups: Tuple["_Group", ...]

    def attr(self, name: str) -> Optional[str]:
        got = self.attrs.get(name)
        return got[-1] if got else None

    def sub(self, type_: str) -> List["_Group"]:
        return [g for g in self.groups if g.type == type_]


def _parse_statements(
    tokens: Sequence[_Token], i: int, where: str, inside_group: bool
) -> Tuple[Dict[str, List[str]], Dict[str, List[Tuple[str, ...]]], List[_Group], int]:
    attrs: Dict[str, List[str]] = {}
    complex_attrs: Dict[str, List[Tuple[str, ...]]] = {}
    groups: List[_Group] = []
    count = len(tokens)

    while i < count:
        kind, text, line = tokens[i]
        if kind == "punct" and text == "}":
            if inside_group:
                return attrs, complex_attrs, groups, i + 1
            raise LibertyError(f"{where}:{line}: '}}' with no group open")
        if kind == "punct" and text == ";":
            i += 1
            continue
        if kind != "word":
            raise LibertyError(
                f"{where}:{line}: expected an attribute or group name, found {text!r}"
            )
        name = text
        i += 1
        if i >= count:
            raise LibertyError(f"{where}:{line}: file ends after {name!r}")

        if tokens[i][0] == "punct" and tokens[i][1] == ":":
            i += 1
            values: List[str] = []
            while i < count and not (tokens[i][0] == "punct" and tokens[i][1] in ";}"):
                values.append(_unquote(tokens[i][1]))
                i += 1
            if i < count and tokens[i][1] == ";":
                i += 1
            attrs.setdefault(name, []).append(" ".join(values))
            continue

        if tokens[i][0] == "punct" and tokens[i][1] == "(":
            i += 1
            args: List[str] = []
            while i < count and not (tokens[i][0] == "punct" and tokens[i][1] == ")"):
                if tokens[i][0] == "punct" and tokens[i][1] == ",":
                    i += 1
                    continue
                args.append(tokens[i][1])
                i += 1
            if i >= count:
                raise LibertyError(f"{where}:{line}: unterminated '(' after {name!r}")
            i += 1
            if i < count and tokens[i][0] == "punct" and tokens[i][1] == "{":
                sub_attrs, sub_complex, sub_groups, i = _parse_statements(
                    tokens, i + 1, where, True
                )
                groups.append(
                    _Group(name, tuple(args), sub_attrs, sub_complex, tuple(sub_groups))
                )
            else:
                if i < count and tokens[i][0] == "punct" and tokens[i][1] == ";":
                    i += 1
                complex_attrs.setdefault(name, []).append(tuple(args))
            continue

        raise LibertyError(
            f"{where}:{line}: {name!r} is followed by {tokens[i][1]!r}, "
            "which is neither ':' nor '('"
        )

    if inside_group:
        raise LibertyError(f"{where}: file ends inside an unclosed group")
    return attrs, complex_attrs, groups, i


# --------------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------------


@dc.dataclass(frozen=True)
class Table:
    """A non-linear delay model look-up table, in ns against ns and pF.

    ``index_1`` is input slew in ns, ``index_2`` output load in pF, and
    ``values[i][j]`` the entry at ``(index_1[i], index_2[j])``.  A one-
    dimensional table has an empty ``index_2`` and a single row indexed by
    ``index_1``; ``at()`` then ignores the load it is given.
    """

    index_1: Tuple[float, ...]
    index_2: Tuple[float, ...]
    values: Tuple[Tuple[float, ...], ...]

    def __post_init__(self) -> None:
        if not self.values or not self.values[0]:
            raise LibertyError("look-up table has no values")
        width = len(self.values[0])
        if any(len(row) != width for row in self.values):
            raise LibertyError(
                "look-up table is ragged: rows of "
                + ", ".join(str(len(r)) for r in self.values)
            )
        if not self.index_1:
            raise LibertyError("look-up table has no index_1")
        for axis, name in ((self.index_1, "index_1"), (self.index_2, "index_2")):
            if any(b <= a for a, b in zip(axis, axis[1:])):
                raise LibertyError(f"{name} is not strictly increasing: {axis}")
        if self.index_2:
            if len(self.values) != len(self.index_1) or width != len(self.index_2):
                raise LibertyError(
                    f"look-up table is {len(self.values)}x{width} but its indices are "
                    f"{len(self.index_1)}x{len(self.index_2)}"
                )
        else:
            if len(self.values) != 1 or width != len(self.index_1):
                raise LibertyError(
                    f"one-dimensional look-up table is {len(self.values)}x{width} "
                    f"but index_1 has {len(self.index_1)} points"
                )

    @staticmethod
    def _bracket(axis: Tuple[float, ...], x: float) -> Tuple[int, float]:
        """Return ``(lower index, fraction)``, clamped to the ends of ``axis``."""
        if len(axis) == 1:
            return 0, 0.0
        if x <= axis[0]:
            return 0, 0.0
        if x >= axis[-1]:
            return len(axis) - 2, 1.0
        lo = 0
        hi = len(axis) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if axis[mid] <= x:
                lo = mid
            else:
                hi = mid
        return lo, (x - axis[lo]) / (axis[lo + 1] - axis[lo])

    def at(self, slew: float, load: float) -> float:
        """Bilinear interpolation, clamped to the characterized grid.

        Clamping means a point outside the grid returns the edge value rather
        than an extrapolation.  That is the conventional reading of an NLDM
        table, but it is also a value nobody measured, so callers that pick
        their own operating point should ask ``contains()`` first and say so.
        """
        i, ti = self._bracket(self.index_1, slew)
        if not self.index_2:
            row = self.values[0]
            if len(self.index_1) == 1:
                return row[0]
            return row[i] * (1.0 - ti) + row[i + 1] * ti
        j, tj = self._bracket(self.index_2, load)
        if len(self.index_1) == 1:
            row = self.values[0]
            if len(self.index_2) == 1:
                return row[0]
            return row[j] * (1.0 - tj) + row[j + 1] * tj
        if len(self.index_2) == 1:
            return self.values[i][0] * (1.0 - ti) + self.values[i + 1][0] * ti
        v00 = self.values[i][j]
        v01 = self.values[i][j + 1]
        v10 = self.values[i + 1][j]
        v11 = self.values[i + 1][j + 1]
        return (
            v00 * (1.0 - ti) * (1.0 - tj)
            + v10 * ti * (1.0 - tj)
            + v01 * (1.0 - ti) * tj
            + v11 * ti * tj
        )

    def contains(self, slew: float, load: float) -> bool:
        """True when ``(slew, load)`` is inside the characterized grid."""
        if not (self.index_1[0] <= slew <= self.index_1[-1]):
            return False
        if not self.index_2:
            return True
        return self.index_2[0] <= load <= self.index_2[-1]

    @property
    def mid_index_1(self) -> float:
        """The middle slew grid point, in ns."""
        return self.index_1[len(self.index_1) // 2]

    @property
    def mid_index_2(self) -> Optional[float]:
        """The middle load grid point in pF, or ``None`` for a 1-D table."""
        if not self.index_2:
            return None
        return self.index_2[len(self.index_2) // 2]

    @property
    def mid(self) -> float:
        """The value at the middle grid point -- an actual entry, not a fit."""
        i = len(self.index_1) // 2
        if not self.index_2:
            return self.values[0][i]
        return self.values[i][len(self.index_2) // 2]


# --------------------------------------------------------------------------------
# Cells and library
# --------------------------------------------------------------------------------


@dc.dataclass(frozen=True)
class TimingArc:
    """One ``timing ()`` group that carries delay, in ns.

    An arc is identified by more than its two pins.  ``when`` separates the
    arcs a cell publishes between the same pins under different side-input
    conditions, and ``timing_type`` separates the pair a tri-state cell
    publishes on its enable pin -- SG13G2's ``ebufn``/``einvn`` give
    ``TE_B->Z`` twice, once ``three_state_enable`` and once
    ``three_state_disable``.  Both go into ``label()``, because two arcs that
    share a label would look like a match across libraries when they are not.
    Ordinary combinational arcs keep the plain ``'A->Y rise'`` label.
    """

    related_pin: str
    output_pin: str
    sense: str
    cell_rise: Optional[Table]
    cell_fall: Optional[Table]
    rise_transition: Optional[Table]
    fall_transition: Optional[Table]
    when: str = ""
    timing_type: str = "combinational"

    def label(self, edge: str) -> str:
        """``'A->Y rise'``, widened only as far as uniqueness demands."""
        base = f"{self.related_pin}->{self.output_pin} {edge}"
        if self.timing_type and self.timing_type != "combinational":
            base = f"{base} [{self.timing_type}]"
        return f"{base} @{self.when}" if self.when else base

    def table(self, edge: str) -> Optional[Table]:
        if edge == "rise":
            return self.cell_rise
        if edge == "fall":
            return self.cell_fall
        raise LibertyError(f"unknown edge {edge!r}; expected 'rise' or 'fall'")


@dc.dataclass(frozen=True)
class LibCell:
    """One ``cell`` group: its footprint claim, its pins and its delay arcs.

    ``area`` and ``leakage`` are ``None`` when the cell does not state them.
    ``area`` is the value the Liberty file *claims*; the flow's area verdict
    comes from :mod:`aion_layout.metrics` instead, and this one is only ever
    used to check that the two agree.
    """

    name: str
    area: Optional[float]
    leakage: Optional[float]
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    arcs: Tuple[TimingArc, ...]
    input_caps: Dict[str, float]


@dc.dataclass(frozen=True)
class Library:
    """A whole ``.lib``, with every number already scaled to ns / pF / pW."""

    name: str
    path: Path
    time_unit_ns: float
    cap_unit_pf: float
    cells: Dict[str, LibCell]
    leakage_unit_pw: float = 1.0
    #: ``nom_voltage`` in volts, ``nom_temperature`` in Celsius and
    #: ``nom_process``, or ``None`` where the library does not state one.  A
    #: delay only means anything alongside the PVT it was measured at, so a
    #: comparison has to be able to check that two libraries share one.
    nom_voltage: Optional[float] = None
    nom_temperature: Optional[float] = None
    nom_process: Optional[float] = None
    #: ``default_operating_conditions``, for naming the corner in a report.
    operating_conditions: str = ""

    def pvt_label(self) -> str:
        """``'1.2 V, 25 C, process 1'`` -- as much of it as the file states."""
        parts = []
        if self.nom_voltage is not None:
            parts.append(f"{self.nom_voltage:g} V")
        if self.nom_temperature is not None:
            parts.append(f"{self.nom_temperature:g} C")
        if self.nom_process is not None:
            parts.append(f"process {self.nom_process:g}")
        if self.operating_conditions:
            parts.append(self.operating_conditions)
        return ", ".join(parts) or "(no operating conditions stated)"

    def cell(self, name: str) -> LibCell:
        """Return one cell, or say which cells the library actually has."""
        got = self.cells.get(name)
        if got is None:
            known = sorted(self.cells)
            shown = ", ".join(known[:12]) + (" ..." if len(known) > 12 else "")
            raise LibertyError(
                f"{self.path.name} has no cell {name!r}; it defines "
                f"{len(known)} cells: {shown or '(none)'}"
            )
        return got


# --------------------------------------------------------------------------------
# Building the tree into a Library
# --------------------------------------------------------------------------------

_DELAY_TABLES = ("cell_rise", "cell_fall", "rise_transition", "fall_transition")


def _floats(args: Sequence[str], where: str, what: str) -> Tuple[float, ...]:
    """Read ``("0.1, 0.2")`` or ``(0.1, 0.2)`` into a tuple of floats."""
    flat = ",".join(_unquote(a) for a in args)
    out: List[float] = []
    for piece in flat.split(","):
        piece = piece.strip()
        if not piece:
            continue
        try:
            out.append(float(piece))
        except ValueError as exc:
            raise LibertyError(f"{where}: {what} holds {piece!r}, which is not a number") from exc
    return tuple(out)


def _rows(args: Sequence[str], where: str) -> Tuple[Tuple[float, ...], ...]:
    """Read a ``values`` argument list into rows.

    A quoted argument is one row -- that is how both producers write a 2-D
    table.  With nothing quoted the whole argument list is a single row, which
    is how a 1-D table is sometimes spelled.
    """
    quoted = [a for a in args if a.startswith('"')]
    if quoted:
        return tuple(_floats([a], where, "values") for a in quoted)
    return (_floats(args, where, "values"),)


def _table(
    group: _Group,
    templates: Dict[str, Tuple[Tuple[float, ...], Tuple[float, ...]]],
    *,
    time_ns: float,
    cap_pf: float,
    value_scale: float,
    where: str,
) -> Table:
    """Build a :class:`Table`, taking indices from the lu_table_template if absent."""
    tmpl_indices = templates.get(group.args[0] if group.args else "", ((), ()))

    if "index_1" in group.complex_attrs:
        index_1 = _floats(group.complex_attrs["index_1"][-1], where, "index_1")
    else:
        index_1 = tmpl_indices[0]
    if "index_2" in group.complex_attrs:
        index_2 = _floats(group.complex_attrs["index_2"][-1], where, "index_2")
    else:
        index_2 = tmpl_indices[1]

    if "values" not in group.complex_attrs:
        raise LibertyError(f"{where}: {group.type} group carries no values")
    values = _rows(group.complex_attrs["values"][-1], where)

    if not index_1:
        raise LibertyError(
            f"{where}: {group.type} states no index_1 and its template "
            f"{group.args[0] if group.args else '(unnamed)'!r} does not either"
        )

    try:
        return Table(
            index_1=tuple(v * time_ns for v in index_1),
            index_2=tuple(v * cap_pf for v in index_2),
            values=tuple(tuple(v * value_scale for v in row) for row in values),
        )
    except LibertyError as exc:
        raise LibertyError(f"{where}: {group.type}: {exc}") from exc


def _build_arcs(
    pin_name: str,
    pin_group: _Group,
    templates: Dict[str, Tuple[Tuple[float, ...], Tuple[float, ...]]],
    *,
    time_ns: float,
    cap_pf: float,
    where: str,
) -> List[TimingArc]:
    arcs: List[TimingArc] = []
    for timing in pin_group.sub("timing"):
        related = (timing.attr("related_pin") or "").split()
        if not related:
            raise LibertyError(f"{where}: a timing group on pin {pin_name} names no related_pin")
        tables: Dict[str, Optional[Table]] = {}
        for kind in _DELAY_TABLES:
            found = timing.sub(kind)
            tables[kind] = (
                _table(
                    found[-1],
                    templates,
                    time_ns=time_ns,
                    cap_pf=cap_pf,
                    value_scale=time_ns,
                    where=f"{where}: {related[0]}->{pin_name}",
                )
                if found
                else None
            )
        if tables["cell_rise"] is None and tables["cell_fall"] is None:
            # A constraint arc (setup/hold/recovery), not a delay arc.
            continue
        for pin in related:
            arcs.append(
                TimingArc(
                    related_pin=pin,
                    output_pin=pin_name,
                    sense=timing.attr("timing_sense") or "",
                    cell_rise=tables["cell_rise"],
                    cell_fall=tables["cell_fall"],
                    rise_transition=tables["rise_transition"],
                    fall_transition=tables["fall_transition"],
                    when=timing.attr("when") or "",
                    timing_type=timing.attr("timing_type") or "combinational",
                )
            )
    return arcs


def _number(group: _Group, name: str, where: str) -> Optional[float]:
    """A simple numeric attribute: absent gives ``None``, malformed is fatal."""
    raw = group.attr(name)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError as exc:
        raise LibertyError(f"{where}: {name} is {raw!r}, which is not a number") from exc


def _build_cell(
    group: _Group,
    templates: Dict[str, Tuple[Tuple[float, ...], Tuple[float, ...]]],
    *,
    time_ns: float,
    cap_pf: float,
    leak_pw: float,
    where: str,
) -> LibCell:
    if not group.args:
        raise LibertyError(f"{where}: a cell group has no name")
    name = _unquote(group.args[0])
    scope = f"{where}: cell {name}"

    inputs: List[str] = []
    outputs: List[str] = []
    caps: Dict[str, float] = {}
    arcs: List[TimingArc] = []

    for pin in group.sub("pin"):
        if not pin.args:
            raise LibertyError(f"{scope}: a pin group has no name")
        pin_name = _unquote(pin.args[0])
        direction = (pin.attr("direction") or "").lower()
        if direction in ("input", "inout"):
            inputs.append(pin_name)
            cap = _number(pin, "capacitance", f"{scope}: pin {pin_name}")
            if cap is not None:
                caps[pin_name] = cap * cap_pf
        if direction in ("output", "inout"):
            outputs.append(pin_name)
        if direction not in ("input", "output", "inout", "internal"):
            raise LibertyError(
                f"{scope}: pin {pin_name} declares direction "
                f"{pin.attr('direction')!r}, which is not a pin direction"
            )
        arcs.extend(
            _build_arcs(pin_name, pin, templates, time_ns=time_ns, cap_pf=cap_pf, where=scope)
        )

    leakage = _number(group, "cell_leakage_power", scope)
    return LibCell(
        name=name,
        area=_number(group, "area", scope),
        leakage=None if leakage is None else leakage * leak_pw,
        inputs=tuple(inputs),
        outputs=tuple(outputs),
        arcs=tuple(arcs),
        input_caps=caps,
    )


def read_liberty(path: Path | str) -> Library:
    """Read one ``.lib`` into a :class:`Library`, in ns, pF and pW.

    Missing, empty and unparseable files are all errors, as is a library that
    does not say what its time or capacitance units are.
    """
    path = Path(path)
    if not path.is_file():
        raise LibertyError(f"no Liberty file at {path}")
    if path.stat().st_size == 0:
        raise LibertyError(f"{path} is empty")

    where = path.name
    tokens = _tokenize(path.read_text(errors="replace"), where)
    if not tokens:
        raise LibertyError(f"{path} holds no Liberty statements")
    _, _, groups, _ = _parse_statements(tokens, 0, where, False)

    libraries = [g for g in groups if g.type == "library"]
    if len(libraries) != 1:
        raise LibertyError(
            f"{where}: expected exactly one 'library' group, found {len(libraries)}"
        )
    library = libraries[0]
    name = _unquote(library.args[0]) if library.args else ""
    if not name:
        raise LibertyError(f"{where}: the library group has no name")

    time_raw = library.attr("time_unit")
    if time_raw is None:
        raise LibertyError(
            f"{where}: the library declares no time_unit; refusing to guess "
            "the scale of every delay in the file"
        )
    time_ns = _unit_factor(time_raw, _TIME_TO_NS, "time_unit", where)

    cap_args = library.complex_attrs.get("capacitive_load_unit")
    if not cap_args:
        raise LibertyError(
            f"{where}: the library declares no capacitive_load_unit; refusing "
            "to guess the scale of every load index in the file"
        )
    cap_pf = _unit_factor(
        " ".join(_unquote(a) for a in cap_args[-1]),
        _CAP_TO_PF,
        "capacitive_load_unit",
        where,
    )

    leak_raw = library.attr("leakage_power_unit")
    leak_pw = (
        1.0 if leak_raw is None
        else _unit_factor(leak_raw, _POWER_TO_PW, "leakage_power_unit", where)
    )

    templates: Dict[str, Tuple[Tuple[float, ...], Tuple[float, ...]]] = {}
    for tmpl in library.sub("lu_table_template"):
        if not tmpl.args:
            continue
        templates[_unquote(tmpl.args[0])] = (
            _floats(tmpl.complex_attrs.get("index_1", [()])[-1], where, "index_1"),
            _floats(tmpl.complex_attrs.get("index_2", [()])[-1], where, "index_2"),
        )

    cells: Dict[str, LibCell] = {}
    for group in library.sub("cell"):
        built = _build_cell(
            group, templates, time_ns=time_ns, cap_pf=cap_pf, leak_pw=leak_pw, where=where
        )
        if built.name in cells:
            raise LibertyError(f"{where}: cell {built.name} is defined twice")
        cells[built.name] = built
    if not cells:
        raise LibertyError(f"{where}: the library defines no cells")

    return Library(
        name=name,
        path=path,
        time_unit_ns=time_ns,
        cap_unit_pf=cap_pf,
        cells=cells,
        leakage_unit_pw=leak_pw,
        nom_voltage=_number(library, "nom_voltage", where),
        nom_temperature=_number(library, "nom_temperature", where),
        nom_process=_number(library, "nom_process", where),
        operating_conditions=library.attr("default_operating_conditions") or "",
    )


# --------------------------------------------------------------------------------
# Reading delays out of a cell
# --------------------------------------------------------------------------------


def first_delay_table(cell: LibCell) -> Table:
    """The first ``cell_rise``/``cell_fall`` table on the cell, in arc order.

    This is what fixes the default operating point, so it must be picked the
    same way every time: arcs keep the order the Liberty file lists them in,
    and rise is looked at before fall.
    """
    for arc in cell.arcs:
        for edge in ("rise", "fall"):
            table = arc.table(edge)
            if table is not None:
                return table
    raise LibertyError(f"cell {cell.name} has no cell_rise or cell_fall table")


def delay_grid(cell: LibCell) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
    """The ``(slew, load)`` grid the cell was characterized on, in ns and pF."""
    table = first_delay_table(cell)
    return table.index_1, table.index_2


def default_operating_point(cell: LibCell) -> Tuple[float, float]:
    """The middle grid point of :func:`first_delay_table`, as ``(slew, load)``."""
    table = first_delay_table(cell)
    load = table.mid_index_2
    if load is None:
        raise LibertyError(
            f"cell {cell.name} is characterized against slew only; there is no "
            "load axis to pick an operating point on"
        )
    return table.mid_index_1, load


def _resolve_point(
    cell: LibCell, slew: Optional[float], load: Optional[float]
) -> Tuple[float, float]:
    if slew is not None and load is not None:
        return slew, load
    default_slew, default_load = default_operating_point(cell)
    return (
        default_slew if slew is None else slew,
        default_load if load is None else load,
    )


def arc_delays(
    cell: LibCell, *, slew: Optional[float] = None, load: Optional[float] = None
) -> Dict[str, float]:
    """Every delay the cell publishes at one operating point, in ns.

    Keys are ``'A->Y rise'``-shaped labels; both edges of every arc appear.
    """
    if not cell.arcs:
        raise LibertyError(f"cell {cell.name} publishes no timing arcs")
    slew, load = _resolve_point(cell, slew, load)
    out: Dict[str, float] = {}
    for arc in cell.arcs:
        for edge in ("rise", "fall"):
            table = arc.table(edge)
            if table is None:
                continue
            label = arc.label(edge)
            if label in out:
                raise LibertyError(
                    f"cell {cell.name} publishes two arcs labelled {label!r}; "
                    "they cannot be told apart and so cannot be compared"
                )
            out[label] = table.at(slew, load)
    if not out:
        raise LibertyError(
            f"cell {cell.name} publishes timing arcs but none carries a "
            "cell_rise or cell_fall table"
        )
    return out


def worst_arc_delay(
    cell: LibCell, *, slew: Optional[float] = None, load: Optional[float] = None
) -> Tuple[float, str]:
    """The slowest arc at one operating point: ``(ns, 'A->Y rise')``."""
    delays = arc_delays(cell, slew=slew, load=load)
    label = max(delays, key=lambda k: (delays[k], k))
    return delays[label], label


def mean_arc_delay(
    cell: LibCell, *, slew: Optional[float] = None, load: Optional[float] = None
) -> float:
    """The mean over every rise and fall delay the cell publishes, in ns."""
    return statistics.fmean(arc_delays(cell, slew=slew, load=load).values())


__all__ = [
    "LibCell",
    "Library",
    "LibertyError",
    "Table",
    "TimingArc",
    "arc_delays",
    "default_operating_point",
    "delay_grid",
    "first_delay_table",
    "mean_arc_delay",
    "read_liberty",
    "worst_arc_delay",
]
