# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-06
#  Description:               What the drawn netlist computes, solved not assumed
# ================================================================

"""The boolean function of a transistor netlist, solved rather than assumed.

Every other view the flow publishes is *structure*: the GDS is polygons, the
LEF is a footprint, the SPICE and the CDL are devices and nodes.  Exactly one
view has to state what the cell **computes** in a language a simulator will
act on, and that is the Verilog model.  A gate-level netlist that instantiates
a cell whose module body is empty still elaborates, still links, still runs --
and drives ``z`` out of every one of that cell's outputs for the whole
simulation, which arrives at the testbench as ``x`` and is read as a design
bug.  So the function cannot be left out, and it must not be guessed.

It is solved here, from the same transistor netlist LVS graded the layout
against, by a DC switch-level analysis: for one input vector, a node is 1 when
a chain of conducting devices ties it to VDD and no chain can tie it to VSS,
and 0 for the mirror of that.  Resolving the vector one node at a time and
repeating until nothing moves handles a multi-stage cell -- the AION cells are
*several* gates merged into one layout, and the second stage cannot be
evaluated before the first one has a value -- with no assumption anywhere that
the netlist is one complementary gate, that the pull-up is series-parallel, or
that the cell has a single output.

Three things this deliberately refuses to do, all for the same reason:

* A node that never resolves is an error, not an ``x``.  It means feedback
  (the cell has state, and a truth table is the wrong model for it) or a node
  nothing drives in that state (a pass-gate output at high impedance).  Both
  are real properties of the netlist, and both make the Verilog model this
  module exists to feed a lie.
* A node tied to both rails at once is an error.  It is a fight, and whichever
  value SPICE would settle on is a ratio, not a logic level.
* A device whose model is neither an nmos nor a pmos is an error rather than
  an ignored line.  A device that is silently dropped changes the function and
  says nothing.

The expression handed out is minimised (Quine-McCluskey primes, then essential
primes and a greedy cover of the rest) and then **re-evaluated against the
truth table it came from** before it is returned, because a minimiser bug that
produces a plausible-looking wrong expression is exactly the failure this whole
module exists to prevent.  Whichever of the function and its complement spells
with fewer literals wins, so a NOR comes out as ``~(A | B)`` rather than as the
four-cube sum of products that is the same thing.

:func:`parse_boolean` reads the *other* statement of the same fact -- the
``function`` attribute of the Liberty file, which ``aion_char`` measured with
ngspice rather than derived -- so that the two can be compared.  They are
produced by different tools from different inputs by different methods, and
:mod:`aion_layout.exporters` refuses to publish a cell whose two answers
disagree.
"""

from __future__ import annotations

import dataclasses as dc
import re
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from .spice_parser import Mosfet, Subckt


class LogicError(RuntimeError):
    """Raised when a netlist has no truth table, or none that can be trusted."""


#: Above this the exhaustive solve stops being a second and starts being a
#: coffee break; no standard cell in this flow comes close.  It is a refusal
#: with a number in it rather than a hang.
MAX_INPUTS = 12

#: A cube of a sum-of-products: one entry per input, ``None`` for "don't care".
Cube = Tuple[Optional[int], ...]


# ---------------------------------------------------------------------------
# The truth table
# ---------------------------------------------------------------------------


@dc.dataclass(frozen=True)
class TruthTable:
    """Every output of a cell, over every input vector.

    ``rows[i]`` holds one value per name in ``outputs``, for the input vector
    whose bits are ``inputs`` read most-significant first: vector ``i`` gives
    ``inputs[j]`` the value ``(i >> (len(inputs) - 1 - j)) & 1``.
    """

    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    rows: Tuple[Tuple[int, ...], ...]

    def __post_init__(self) -> None:
        expected = 1 << len(self.inputs)
        if len(self.rows) != expected:
            raise LogicError(
                f"a truth table over {len(self.inputs)} inputs has {expected} rows, "
                f"not {len(self.rows)}"
            )

    def vector(self, index: int) -> Dict[str, int]:
        """The input assignment of row ``index``."""
        last = len(self.inputs) - 1
        return {name: (index >> (last - j)) & 1 for j, name in enumerate(self.inputs)}

    def column(self, output: str) -> Tuple[int, ...]:
        """The value of one output over every input vector."""
        try:
            at = self.outputs.index(output)
        except ValueError:
            raise LogicError(
                f"{output!r} is not an output of this cell; it has "
                + (", ".join(self.outputs) or "(none)")
            ) from None
        return tuple(row[at] for row in self.rows)

    def support(self, output: str) -> Tuple[str, ...]:
        """The inputs ``output`` actually depends on, in declaration order.

        This is the arc list: an input the output does not respond to has no
        timing arc in the Liberty either, and a ``specify`` path for it would
        be a path no SDF record ever annotates.
        """
        column = self.column(output)
        last = len(self.inputs) - 1
        real: List[str] = []
        for j, name in enumerate(self.inputs):
            bit = 1 << (last - j)
            if any(column[i] != column[i ^ bit] for i in range(len(column))):
                real.append(name)
        return tuple(real)

    def sense(self, output: str, pin: str) -> str:
        """``positive_unate``, ``negative_unate`` or ``non_unate`` for one arc.

        The same three words the Liberty ``timing_sense`` uses, so the two can
        be read side by side.
        """
        column = self.column(output)
        try:
            j = self.inputs.index(pin)
        except ValueError:
            raise LogicError(f"{pin!r} is not an input of this cell") from None
        bit = 1 << (len(self.inputs) - 1 - j)
        rises = falls = False
        for low in range(len(column)):
            if low & bit:
                continue
            if column[low | bit] > column[low]:
                rises = True
            elif column[low | bit] < column[low]:
                falls = True
        if rises and falls:
            return "non_unate"
        if falls:
            return "negative_unate"
        return "positive_unate"

    def expression(self, output: str, *, style: str = "verilog") -> str:
        """The minimised expression for one output, in ``verilog`` or ``liberty``."""
        return render(*minimal_cover(self.column(output), self.inputs), style=style)

    def disagrees_at(self, expression: str, output: str) -> Optional[int]:
        """Return the first vector index where ``expression`` differs, or None."""
        function = parse_boolean(expression, known=self.inputs)
        column = self.column(output)
        for index, value in enumerate(column):
            if function(self.vector(index)) != value:
                return index
        return None


# ---------------------------------------------------------------------------
# Solving the netlist
# ---------------------------------------------------------------------------


def _rails(subckt: Subckt) -> Tuple[str, str]:
    vdd, vss = subckt.vdd_net, subckt.vss_net
    missing = [name for name, net in (("VDD", vdd), ("VSS", vss)) if net is None]
    if missing:
        raise LogicError(
            f"{subckt.name} has no {' and no '.join(missing)} pin, so no node in it "
            f"can be given a logic level; its pins are: {', '.join(subckt.pins)}"
        )
    return vdd, vss  # type: ignore[return-value]


def _classify_ports(
    subckt: Subckt,
    vdd: str,
    vss: str,
    *,
    declared: Optional[Mapping[str, str]] = None,
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """Split the signal pins into inputs and outputs.

    Without ``declared`` the split is read off the topology: a pin a device
    only ever *gates* is an input; a pin wired to a channel terminal is driven
    by the cell and is an output.  That rule is exact for static CMOS and wrong
    for anything with a pass gate, where a steered *input* arrives on a channel
    terminal exactly as the output does -- on a transmission-gate mux every
    signal pin looks like an output and the cell has no inputs left to sweep.

    ``declared`` is the cell's own statement of which is which, keyed by pin
    name with ``"input"``/``"output"`` values (case-insensitive); supplies may
    appear and are ignored.  It is checked against the pins, never trusted
    blind: a name it does not mention falls back to the topology rule, so a
    partial map degrades instead of losing a port.
    """
    gates = {d.gate for d in subckt.devices}
    channels = {d.drain for d in subckt.devices} | {d.source for d in subckt.devices}
    said = {
        name: role.lower()
        for name, role in (declared or {}).items()
        if role.lower() in ("input", "output")
    }
    unknown = sorted(set(said) - set(subckt.pins))
    if unknown:
        raise LogicError(
            f"{subckt.name}: the declared directions name {', '.join(unknown)}, "
            f"which {subckt.name} does not have as a pin; its pins are: "
            + ", ".join(subckt.pins)
        )
    inputs: List[str] = []
    outputs: List[str] = []
    for pin in subckt.pins:
        if pin in (vdd, vss):
            continue
        role = said.get(pin)
        if role == "output" and pin not in channels:
            raise LogicError(
                f"{subckt.name}: {pin} is declared an output, but no device in the "
                "cell has a drain or a source on it -- nothing drives it, so it "
                "cannot be one. A declaration may settle what the topology leaves "
                "open; it may not overrule what the topology settles"
            )
        if role == "input":
            inputs.append(pin)
        elif role == "output":
            outputs.append(pin)
        elif pin in channels:
            outputs.append(pin)
        elif pin in gates:
            inputs.append(pin)
        else:
            raise LogicError(
                f"{subckt.name} declares the pin {pin!r} that no device connects to; "
                "a port nothing drives and nothing reads is not a port"
            )

    def blamed(role: str) -> str:
        """Name the declared pins of ``role``, so a bad map is not a mystery."""
        named = [pin for pin in subckt.pins if said.get(pin) == role]
        if not named:
            return ""
        return f" (the declared directions call {', '.join(named)} an {role})"

    if not outputs:
        raise LogicError(
            f"{subckt.name} has no output pin: no signal pin is wired to a drain or "
            "a source, so the cell drives nothing" + blamed("input")
        )
    if not inputs:
        raise LogicError(
            f"{subckt.name} has no input pin: no signal pin gates a device, so the "
            "cell has a constant function and no timing arc" + blamed("output")
        )
    if len(inputs) > MAX_INPUTS:
        raise LogicError(
            f"{subckt.name} has {len(inputs)} inputs; this solver is exhaustive and "
            f"stops at {MAX_INPUTS} ({1 << MAX_INPUTS} vectors)"
        )
    return tuple(inputs), tuple(outputs)


def _conducts(device: Mosfet, gate_value: int, subckt_name: str) -> bool:
    if device.is_nmos:
        return gate_value == 1
    if device.is_pmos:
        return gate_value == 0
    raise LogicError(
        f"{subckt_name} instantiates {device.name} with model {device.model!r}, which "
        "is neither an nmos nor a pmos; a device this solver cannot switch would be "
        "silently dropped from the function"
    )


def _adjacency(
    devices: Sequence[Mosfet],
    values: Mapping[str, int],
    *,
    definite: bool,
    subckt_name: str,
) -> Dict[str, List[str]]:
    """Channel connections that conduct (``definite``) or might (``not definite``)."""
    adjacency: Dict[str, List[str]] = {}
    for device in devices:
        gate = values.get(device.gate)
        if gate is None:
            if definite:
                continue
        elif not _conducts(device, gate, subckt_name):
            continue
        adjacency.setdefault(device.drain, []).append(device.source)
        adjacency.setdefault(device.source, []).append(device.drain)
    return adjacency


def _sources_reached(
    start: str, adjacency: Mapping[str, List[str]], sources: Set[str]
) -> Set[str]:
    """Which sources ``start`` is tied to; a source is a terminal, never a waypoint.

    Walking *through* VDD would find a path out of every pull-up network into
    every other one, and report a node as tied to both rails whenever any two
    gates in the cell happened to be conducting.

    ``sources`` is the two rails plus the cell's input pins.  An input belongs
    there for the same reason a rail does: it is held at a level by something
    outside the cell, so a channel path that arrives at one has found a driver
    and has no business continuing through it.  On a cell whose inputs are all
    gates this is inert -- no channel path can reach a pin that sits on no
    channel terminal -- and on a pass gate it is the whole difference between a
    solvable node and one that "settles at no level".
    """
    seen = {start}
    stack = [start]
    hit: Set[str] = set()
    while stack:
        net = stack.pop()
        for neighbour in adjacency.get(net, ()):
            if neighbour in seen:
                continue
            seen.add(neighbour)
            if neighbour in sources:
                hit.add(neighbour)
                continue
            stack.append(neighbour)
    return hit


def _solve_vector(
    subckt: Subckt,
    values: Dict[str, int],
    unresolved: List[str],
    vdd: str,
    vss: str,
    sources: Set[str],
) -> Dict[str, int]:
    """Give every node in ``unresolved`` a level, or say why none can be given.

    ``sources`` are the nodes held at a level from outside the network being
    solved: the two rails, and the input pins.  A node takes a level when every
    source it could possibly reach agrees on one, which for a complementary
    gate is the familiar "tied to VDD and no path to VSS" and for a
    transmission gate is "tied to whatever the pass gate is steering".
    """
    pending = list(unresolved)
    while pending:
        sure = _adjacency(subckt.devices, values, definite=True, subckt_name=subckt.name)
        maybe = _adjacency(subckt.devices, values, definite=False, subckt_name=subckt.name)
        progressed = False
        for node in list(pending):
            # Every source is a rail or an input pin, so all of them already
            # have a level in ``values``: it is the level that matters here,
            # not which source carries it.
            tied = {values[s] for s in _sources_reached(node, sure, sources)}
            could = {values[s] for s in _sources_reached(node, maybe, sources)}
            if len(tied) > 1:
                raise LogicError(
                    f"{subckt.name}: {node} is tied to both a 0 and a 1 at once for the "
                    f"input vector {_spell(values, subckt)}; whatever SPICE settles "
                    "on there is a resistive divider, not a logic level"
                )
            if len(tied) != 1 or not could <= tied:
                continue
            values[node] = tied.pop()
            pending.remove(node)
            progressed = True
        if not progressed:
            raise LogicError(
                f"{subckt.name}: {', '.join(sorted(pending))} settle at no level for the "
                f"input vector {_spell(values, subckt)}. Either the cell has feedback and "
                "holds state -- a truth table is the wrong model for it, and it needs a "
                "hand-written Verilog model -- or nothing drives the node in that state, "
                "which a static CMOS cell may not do"
            )
    return values


def _spell(values: Mapping[str, int], subckt: Subckt) -> str:
    """``I0=0 I1=1 I2=0`` for the pins only, so an error names the vector."""
    return " ".join(f"{pin}={values[pin]}" for pin in subckt.pins if pin in values)


def truth_table(
    subckt: Subckt, *, directions: Optional[Mapping[str, str]] = None
) -> TruthTable:
    """Solve ``subckt`` over every input vector.

    Every net that gates a device has to be resolved on the way, not only the
    output pins: in a merged AION cell the gate of the second stage is the
    drain of the first, and there is no order to evaluate them in that does not
    discover it.  A pass gate adds a second reason -- the node a transmission
    gate steers is neither a pin nor a gate of anything the topology can order
    -- and it is resolved the same way, by repeating until nothing moves.

    ``directions`` names each pin ``"input"`` or ``"output"``.  Pass it for any
    cell whose inputs are not all gate terminals: see :func:`_classify_ports`.
    """
    vdd, vss = _rails(subckt)
    inputs, outputs = _classify_ports(subckt, vdd, vss, declared=directions)
    gated = {d.gate for d in subckt.devices}
    internal = sorted(gated - set(inputs) - {vdd, vss} - set(outputs))
    wanted = list(outputs) + internal
    sources = {vdd, vss} | set(inputs)

    rows: List[Tuple[int, ...]] = []
    last = len(inputs) - 1
    for index in range(1 << len(inputs)):
        values: Dict[str, int] = {vdd: 1, vss: 0}
        for j, name in enumerate(inputs):
            values[name] = (index >> (last - j)) & 1
        solved = _solve_vector(subckt, values, wanted, vdd, vss, sources)
        rows.append(tuple(solved[out] for out in outputs))

    return TruthTable(inputs=inputs, outputs=outputs, rows=tuple(rows))


# ---------------------------------------------------------------------------
# Minimisation
# ---------------------------------------------------------------------------


def _merge(a: Cube, b: Cube) -> Optional[Cube]:
    """Two cubes differing in exactly one literal, merged; else None."""
    difference = -1
    for i, (x, y) in enumerate(zip(a, b)):
        if x == y:
            continue
        if x is None or y is None or difference >= 0:
            return None
        difference = i
    if difference < 0:
        return None
    return a[:difference] + (None,) + a[difference + 1 :]


def _covers(cube: Cube, minterm: int, width: int) -> bool:
    last = width - 1
    return all(bit is None or bit == ((minterm >> (last - i)) & 1) for i, bit in enumerate(cube))


def _primes(width: int, minterms: Set[int]) -> List[Cube]:
    """Every prime implicant of ``minterms``, by Quine-McCluskey."""
    last = width - 1
    current: Set[Cube] = {
        tuple((m >> (last - i)) & 1 for i in range(width)) for m in minterms
    }
    primes: Set[Cube] = set()
    while current:
        by_ones: Dict[int, List[Cube]] = {}
        for cube in current:
            by_ones.setdefault(sum(1 for bit in cube if bit == 1), []).append(cube)
        merged: Set[Cube] = set()
        used: Set[Cube] = set()
        for ones, group in by_ones.items():
            for a in group:
                for b in by_ones.get(ones + 1, ()):
                    combined = _merge(a, b)
                    if combined is not None:
                        merged.add(combined)
                        used.add(a)
                        used.add(b)
        primes |= current - used
        current = merged
    return sorted(
        primes,
        key=lambda cube: (
            sum(bit is not None for bit in cube),
            tuple(-1 if bit is None else bit for bit in cube),
        ),
    )


def _cover(width: int, minterms: Set[int]) -> List[Cube]:
    """A small sum of products covering exactly ``minterms``.

    Essential primes first -- those are forced -- then the cheapest remaining
    prime per still-uncovered minterm.  Not provably minimum (that is Petrick,
    and it buys nothing at this size), but deterministic and always correct:
    :func:`minimal_cover` checks the result against the table it came from.
    """
    if not minterms:
        return []
    primes = _primes(width, minterms)
    covered_by = {m: [p for p in primes if _covers(p, m, width)] for m in minterms}

    chosen: List[Cube] = []
    for options in covered_by.values():
        if len(options) == 1 and options[0] not in chosen:
            chosen.append(options[0])

    remaining = {m for m in minterms if not any(_covers(p, m, width) for p in chosen)}
    while remaining:
        best = max(
            primes,
            key=lambda p: (
                sum(1 for m in remaining if _covers(p, m, width)),
                -sum(bit is not None for bit in p),
            ),
        )
        if not any(_covers(best, m, width) for m in remaining):
            raise LogicError("internal error: no prime implicant covers the remaining minterms")
        chosen.append(best)
        remaining = {m for m in remaining if not _covers(best, m, width)}
    # Left to itself the cover comes out in whatever order the essential
    # primes were discovered in.  Ordering it by the inputs each cube names
    # makes the expression read in pin order and makes it reproducible.
    chosen.sort(key=lambda cube: tuple((i, bit) for i, bit in enumerate(cube) if bit is not None))
    return chosen


def minimal_cover(
    values: Sequence[int], names: Sequence[str]
) -> Tuple[List[Cube], Tuple[str, ...], bool]:
    """Minimise one output into ``(cubes, names, inverted)``.

    ``names`` comes back reduced to the inputs the output really depends on,
    and ``inverted`` says the cubes cover the complement.  Both forms are
    built, the shorter one wins, and the result is checked against ``values``
    before it is returned.
    """
    width_in = len(names)
    if len(values) != 1 << width_in:
        raise LogicError(
            f"{len(values)} values for {width_in} inputs; expected {1 << width_in}"
        )

    # Project onto the support: an input the output ignores must not appear in
    # its expression, and leaving it in doubles the number of cubes.
    last = width_in - 1
    support = [
        j
        for j in range(width_in)
        if any(values[i] != values[i ^ (1 << (last - j))] for i in range(len(values)))
    ]
    reduced_names = tuple(names[j] for j in support)
    width = len(support)
    reduced: List[int] = []
    for index in range(1 << width):
        full = 0
        for k, j in enumerate(support):
            if (index >> (width - 1 - k)) & 1:
                full |= 1 << (last - j)
        reduced.append(values[full])

    ones = {i for i, v in enumerate(reduced) if v}
    zeros = {i for i, v in enumerate(reduced) if not v}
    if not ones:
        return [], reduced_names, False
    if not zeros:
        return [tuple([None] * width)], reduced_names, False

    positive = _cover(width, ones)
    negative = _cover(width, zeros)

    def cost(cubes: Sequence[Cube], flipped: bool) -> Tuple[int, int]:
        # Literals first, then negation signs: at equal length a NOR reads as
        # ``~(A | B)`` and not as ``~A & ~B``, which is the spelling the PDK's
        # own Liberty uses for the same cell -- while an AND stays ``A & B``
        # rather than becoming the double negative that is just as short.
        literals = sum(sum(bit is not None for bit in cube) for cube in cubes)
        negations = sum(sum(bit == 0 for bit in cube) for cube in cubes) + int(flipped)
        return literals, negations

    inverted = cost(negative, True) < cost(positive, False)
    cubes = negative if inverted else positive

    for index, expected in enumerate(reduced):
        hit = 1 if any(_covers(cube, index, width) for cube in cubes) else 0
        if (1 - hit if inverted else hit) != expected:
            raise LogicError(
                "internal error: the minimised expression disagrees with the truth "
                f"table it was built from at vector {index}"
            )
    return cubes, reduced_names, inverted


_STYLES = {
    # (and, or, not, true, false)
    "verilog": (" & ", " | ", "~", "1'b1", "1'b0"),
    "liberty": ("*", "+", "!", "1", "0"),
}


def render(
    cubes: Sequence[Cube], names: Sequence[str], inverted: bool, *, style: str = "verilog"
) -> str:
    """Spell a cover as an expression."""
    try:
        conj, disj, negate, true, false = _STYLES[style]
    except KeyError:
        raise LogicError(
            f"unknown expression style {style!r}; known: {', '.join(sorted(_STYLES))}"
        ) from None

    if not cubes:
        return true if inverted else false
    terms: List[str] = []
    for cube in cubes:
        literals = [
            (names[i] if bit else f"{negate}{names[i]}")
            for i, bit in enumerate(cube)
            if bit is not None
        ]
        if not literals:
            return false if inverted else true
        terms.append(conj.join(literals))
    body = disj.join(f"({t})" if len(terms) > 1 and conj in t else t for t in terms)
    return f"{negate}({body})" if inverted else body


# ---------------------------------------------------------------------------
# Reading somebody else's expression
# ---------------------------------------------------------------------------

_BOOL_TOKEN_RE = re.compile(
    r"""\s*(?:
        (?P<name>[A-Za-z_][A-Za-z0-9_$\[\]\.]*)
      | (?P<const>[01])
      | (?P<op>[!~'*&+|^()])
    )""",
    re.VERBOSE,
)


def _tokenize_boolean(text: str) -> List[Tuple[str, str]]:
    tokens: List[Tuple[str, str]] = []
    at = 0
    while at < len(text):
        if text[at].isspace():
            at += 1
            continue
        match = _BOOL_TOKEN_RE.match(text, at)
        if match is None:
            raise LogicError(f"cannot read {text[at]!r} in the expression {text!r}")
        for kind in ("name", "const", "op"):
            value = match.group(kind)
            if value is not None:
                tokens.append((kind, value))
                break
        at = match.end()
    if not tokens:
        raise LogicError(f"the expression {text!r} is empty")
    return tokens


def parse_boolean(
    text: str, *, known: Optional[Iterable[str]] = None
) -> Callable[[Mapping[str, int]], int]:
    """Compile a Liberty (or Verilog) boolean expression into a callable.

    Liberty's operator set and precedence: ``!`` and a trailing ``'`` negate,
    juxtaposition and ``*``/``&`` are AND, ``^`` is XOR, ``+``/``|`` are OR.
    ``~`` is accepted too, so the same reader can be pointed at the Verilog
    this module writes.

    ``known`` is the pin list to check names against.  An expression naming a
    pin the cell does not have is an error: it is the loudest evidence there is
    that the two files are not describing the same cell.
    """
    tokens = _tokenize_boolean(text)
    allowed = None if known is None else {str(name) for name in known}
    position = 0

    def peek() -> Optional[Tuple[str, str]]:
        return tokens[position] if position < len(tokens) else None

    def take() -> Tuple[str, str]:
        nonlocal position
        token = tokens[position]
        position += 1
        return token

    def primary() -> Callable[[Mapping[str, int]], int]:
        token = peek()
        if token is None:
            raise LogicError(f"the expression {text!r} ends where a term was expected")
        kind, value = take()
        if kind == "op" and value in ("!", "~"):
            inner = primary()
            node: Callable[[Mapping[str, int]], int] = lambda values: 1 - inner(values)
        elif kind == "op" and value == "(":
            node = disjunction()
            closing = peek()
            if closing is None or closing[1] != ")":
                raise LogicError(f"unbalanced parentheses in the expression {text!r}")
            take()
        elif kind == "const":
            constant = int(value)
            node = lambda values: constant
        elif kind == "name":
            if allowed is not None and value not in allowed:
                raise LogicError(
                    f"the expression {text!r} names {value!r}, which is not a pin of "
                    f"this cell; it has: {', '.join(sorted(allowed)) or '(none)'}"
                )
            name = value

            def node(values: Mapping[str, int], _name: str = name) -> int:
                try:
                    return int(values[_name])
                except KeyError:
                    raise LogicError(f"no value given for {_name!r}") from None

        else:
            raise LogicError(f"{value!r} cannot start a term in the expression {text!r}")

        while True:
            following = peek()
            if following is None or following != ("op", "'"):
                break
            take()
            previous = node
            node = lambda values, _p=previous: 1 - _p(values)
        return node

    def conjunction() -> Callable[[Mapping[str, int]], int]:
        node = primary()
        while True:
            token = peek()
            if token is None:
                break
            if token == ("op", "*") or token == ("op", "&"):
                take()
            elif token[0] in ("name", "const") or token in (("op", "("), ("op", "!"), ("op", "~")):
                pass  # juxtaposition is AND in Liberty
            else:
                break
            right = primary()
            left = node
            node = lambda values, _l=left, _r=right: _l(values) & _r(values)
        return node

    def exclusive() -> Callable[[Mapping[str, int]], int]:
        node = conjunction()
        while peek() == ("op", "^"):
            take()
            right = conjunction()
            left = node
            node = lambda values, _l=left, _r=right: _l(values) ^ _r(values)
        return node

    def disjunction() -> Callable[[Mapping[str, int]], int]:
        node = exclusive()
        while peek() in (("op", "+"), ("op", "|")):
            take()
            right = exclusive()
            left = node
            node = lambda values, _l=left, _r=right: _l(values) | _r(values)
        return node

    root = disjunction()
    if position != len(tokens):
        raise LogicError(
            f"the expression {text!r} has trailing text starting at {tokens[position][1]!r}"
        )
    return root


__all__ = [
    "Cube",
    "LogicError",
    "MAX_INPUTS",
    "TruthTable",
    "minimal_cover",
    "parse_boolean",
    "render",
    "truth_table",
]
