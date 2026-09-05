"""Two-level Boolean minimization for complementary P/N networks.

The minimizer receives the flattened top-level Boolean function and produces
compact two-level forms:

* ``!F`` as a Sum-of-Products (DNF) — used for the NMOS pull-down network.
* ``F`` as a Product-of-Sums (CNF/PoS) — used for the PMOS pull-up network.

SymPy's Quine-McCluskey implementation (``SOPform`` / ``POSform``) is used for
exact two-level minimization.

Both polarities are always costed and the cheaper one wins.  Costing has to
account for the input inverters each polarity implies, and the rule differs
between the two networks:

* Pull-down (SOP of ``!F``): an NMOS conducts when its literal is true, so a
  **complemented** literal ``~X`` needs the signal ``X_bar``.
* Pull-up (POS of ``F``): a PMOS conducts when its literal is true, i.e. when
  its *gate* is low, so a **plain** literal ``X`` needs the signal ``X_bar``.

Getting that backwards costs real transistors: it is the difference between
building AND3 as a NAND3 plus an output inverter (8 devices) and building it as
three input inverters driving an inverted-input NAND3 (12 devices).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from sympy import And, Not, Or, POSform, SOPform, Symbol, symbols

from aion_minimizer.netlist_evaluator import FlattenedNetlist

MODES = ("transistor", "area", "balance")


@dataclass
class MinimizedForms:
    """Result of two-level Boolean minimization."""

    inputs: List[str]
    f_expr: object  # F as POS, driving the PMOS pull-up (or constant)
    not_f_expr: object  # !F as SOP, driving the NMOS pull-down (or constant)
    mode: str
    output_inverted: bool = False
    #: ``0``/``1`` when the flattened function is constant, ``None`` otherwise.
    constant: Optional[int] = None
    #: Primary inputs that must be available complemented.
    complements: Set[str] = field(default_factory=set)


def _collect_symbols(input_names: List[str]):
    if not input_names:
        return []
    syms = symbols(" ".join(input_names))
    if not isinstance(syms, (list, tuple)):
        syms = (syms,)
    return list(syms)


def _literal_count(expr: object) -> int:
    """Count literal occurrences in a two-level SymPy Boolean expression."""
    if expr is True or expr is False:
        return 0
    if isinstance(expr, Symbol):
        return 1
    if isinstance(expr, Not):
        return 1
    if isinstance(expr, (And, Or)):
        return sum(_literal_count(arg) for arg in expr.args)
    return 0


def _term_count(expr: object) -> int:
    """Count top-level AND/OR terms."""
    if expr is True or expr is False:
        return 0
    if isinstance(expr, (And, Or)):
        return len(expr.args)
    return 1


def _series_depth_pos(expr: object) -> int:
    """Series depth of the pull-up built from a Product-of-Sums ``expr``.

    Each OR group is a parallel bank of PMOS and the groups sit in series, so
    the series depth is the number of AND terms.
    """
    if expr is True or expr is False:
        return 0
    if isinstance(expr, And):
        return len(expr.args)
    return 1


def _series_depth_sop(expr: object) -> int:
    """Series depth of the pull-down built from a Sum-of-Products ``expr``.

    Each AND term is a series NMOS stack and the terms sit in parallel, so the
    series depth is the widest product term.
    """
    if expr is True or expr is False:
        return 0
    if isinstance(expr, Or):
        return max(_literal_count(arg) for arg in expr.args)
    return _literal_count(expr)


def _walk_literals(expr: object):
    """Yield every ``(name, inverted)`` literal of a two-level expression."""
    if expr is True or expr is False:
        return
    if isinstance(expr, Symbol):
        yield expr.name, False
    elif isinstance(expr, Not):
        inner = expr.args[0]
        if isinstance(inner, Symbol):
            yield inner.name, True
        else:  # pragma: no cover - two-level forms never nest this way
            raise ValueError(f"Unsupported Boolean literal: {expr!r}")
    elif isinstance(expr, (And, Or)):
        for arg in expr.args:
            yield from _walk_literals(arg)
    else:  # pragma: no cover
        raise ValueError(f"Unsupported Boolean expression: {expr!r}")


def complements_for_pullup(expr: object) -> Set[str]:
    """Inputs needing a ``_bar`` signal to drive the PMOS pull-up of ``expr``.

    A PMOS conducts when its gate is low, so a plain literal ``X`` in the POS
    form has to be applied as ``X_bar``.
    """
    return {name for name, inverted in _walk_literals(expr) if not inverted}


def complements_for_pulldown(expr: object) -> Set[str]:
    """Inputs needing a ``_bar`` signal to drive the NMOS pull-down of ``expr``.

    An NMOS conducts when its gate is high, so a complemented literal ``~X`` in
    the SOP form has to be applied as ``X_bar``.
    """
    return {name for name, inverted in _walk_literals(expr) if inverted}


def polarity_complements(pullup: object, pulldown: object) -> Set[str]:
    """Union of the inputs both networks need complemented."""
    return complements_for_pullup(pullup) | complements_for_pulldown(pulldown)


def polarity_cost(
    pullup: object, pulldown: object, output_inverted: bool = False
) -> int:
    """Transistor cost of one polarity choice, inverters included."""
    devices = _literal_count(pullup) + _literal_count(pulldown)
    devices += 2 * len(polarity_complements(pullup, pulldown))
    if output_inverted:
        devices += 2
    return devices


def series_depth(pullup: object, pulldown: object) -> int:
    """Worst series stack depth over both networks."""
    return max(_series_depth_pos(pullup), _series_depth_sop(pulldown))


def minimize_function(
    flat: FlattenedNetlist,
    mode: str = "transistor",
    balance_max_stack: int = 3,
) -> MinimizedForms:
    """Minimize ``flat.expr`` into two-level forms suitable for CMOS synthesis.

    Parameters
    ----------
    flat
        The flattened top-level netlist from Step 3.
    mode
        One of ``transistor``, ``area``, or ``balance``.
    balance_max_stack
        Maximum allowed series stack depth for ``balance`` mode.
    """
    return minimize_truth_table(
        flat.primary_inputs,
        flat.truth_table,
        mode=mode,
        balance_max_stack=balance_max_stack,
    )


def minimize_truth_table(
    inputs: List[str],
    truth_table: Dict[Tuple[int, ...], int],
    mode: str = "transistor",
    balance_max_stack: int = 3,
) -> MinimizedForms:
    """Minimize a raw truth table; see :func:`minimize_function`.

    Taking the table directly lets the decomposer cost a single cluster of
    gates without building a whole :class:`FlattenedNetlist` for it.
    """
    if mode not in MODES:
        raise ValueError(f"Unknown minimization mode: {mode!r}")

    syms = _collect_symbols(inputs)

    # Collect minterms where F is 1 and 0.
    ones = [combo for combo, val in truth_table.items() if val == 1]
    zeros = [combo for combo, val in truth_table.items() if val == 0]

    # A function that is constant over every input vector has no two-level
    # network; the caller emits a tie cell instead of a pull-up/pull-down pair.
    if not zeros:
        return MinimizedForms(
            inputs=inputs, f_expr=True, not_f_expr=False, mode=mode, constant=1
        )
    if not ones:
        return MinimizedForms(
            inputs=inputs, f_expr=False, not_f_expr=True, mode=mode, constant=0
        )

    # Direct polarity: pull-up from F (POS), pull-down from !F (SOP).
    f_pos = POSform(syms, ones)
    not_f_sop = SOPform(syms, zeros)

    # Inverted polarity: build !F and restore with an output inverter.
    not_f_pos = POSform(syms, zeros)
    f_sop = SOPform(syms, ones)

    direct = (f_pos, not_f_sop, False)
    inverted = (not_f_pos, f_sop, True)

    if mode == "balance":
        # Prefer whichever polarity fits the stack budget; fall back to cost.
        direct_fits = series_depth(*direct[:2]) <= balance_max_stack
        inverted_fits = series_depth(*inverted[:2]) <= balance_max_stack
        if direct_fits and not inverted_fits:
            choice = direct
        elif inverted_fits and not direct_fits:
            choice = inverted
        else:
            choice = min(
                (direct, inverted),
                key=lambda c: (polarity_cost(c[0], c[1], c[2]), series_depth(c[0], c[1])),
            )
    else:
        # `transistor` and `area` both minimize devices; ties go to the shallower
        # network, and then to the direct polarity for determinism.
        choice = min(
            (direct, inverted),
            key=lambda c: (
                polarity_cost(c[0], c[1], c[2]),
                series_depth(c[0], c[1]),
                c[2],
            ),
        )

    pullup, pulldown, output_inverted = choice
    return MinimizedForms(
        inputs=inputs,
        f_expr=pullup,
        not_f_expr=pulldown,
        mode=mode,
        output_inverted=output_inverted,
        complements=polarity_complements(pullup, pulldown) & set(inputs),
    )
