"""Two-level Boolean minimization for complementary P/N networks.

The minimizer receives the flattened top-level Boolean function and produces
compact two-level forms:

* ``!F`` as a Sum-of-Products (DNF) — used for the NMOS pull-down network.
* ``F`` as a Product-of-Sums (CNF/PoS) — used for the PMOS pull-up network.

SymPy's Quine-McCluskey implementation (``SOPform`` / ``POSform``) is used for
exact two-level minimization.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from sympy import And, Not, Or, POSform, SOPform, symbols

from aion_minimizer.netlist_evaluator import FlattenedNetlist


@dataclass
class MinimizedForms:
    """Result of two-level Boolean minimization."""

    inputs: List[str]
    f_expr: object  # original F in POS (or constant)
    not_f_expr: object  # !F in SOP (or constant)
    mode: str
    output_inverted: bool = False


def _collect_symbols(input_names: List[str]):
    syms = symbols(" ".join(input_names))
    if not isinstance(syms, (list, tuple)):
        syms = (syms,)
    return list(syms)


def _literal_count(expr: object) -> int:
    """Count literal occurrences in a two-level SymPy Boolean expression."""
    if expr is True or expr is False:
        return 0
    if getattr(expr, "is_Symbol", False):
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


def _max_stack_depth(expr: object) -> int:
    """Return the largest number of literals in any sum/product term."""
    if expr is True or expr is False:
        return 0
    if isinstance(expr, (And, Or)):
        return max(_literal_count(arg) for arg in expr.args)
    return _literal_count(expr)


def _inverters_for_expr(expr: object) -> int:
    """Estimate unique inverted primary inputs required by ``expr``."""
    if expr is True or expr is False:
        return 0
    if isinstance(expr, Not):
        return 1
    if isinstance(expr, (And, Or)):
        return sum(_inverters_for_expr(arg) for arg in expr.args)
    return 0


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
    if mode not in ("transistor", "area", "balance"):
        raise ValueError(f"Unknown minimization mode: {mode!r}")

    inputs = flat.primary_inputs
    syms = _collect_symbols(inputs)

    # Collect minterms where F is 1 and 0.
    ones = [combo for combo, val in flat.truth_table.items() if val == 1]
    zeros = [combo for combo, val in flat.truth_table.items() if val == 0]

    # Default minimal forms.
    f_pos = POSform(syms, ones) if ones else False
    not_f_sop = SOPform(syms, zeros) if zeros else True

    if mode == "transistor":
        # Optionally implement the simpler polarity and add an output inverter.
        # Direct implementation cost: 2 * literals(F_POS) + input inverters.
        # Inverted implementation cost: 2 * literals(!F_POS) + 2 (out inverter) + input inverters.
        not_f_pos = POSform(syms, zeros) if zeros else True
        f_sop = SOPform(syms, ones) if ones else False

        direct_literals = _literal_count(f_pos)
        inverted_literals = _literal_count(not_f_pos)

        direct_inverters = _inverters_for_expr(f_pos) + _inverters_for_expr(not_f_sop)
        inverted_inverters = (
            _inverters_for_expr(not_f_pos) + _inverters_for_expr(f_sop)
        )

        direct_cost = 2 * direct_literals + direct_inverters
        inverted_cost = 2 * inverted_literals + inverted_inverters + 2

        output_inverted = inverted_cost < direct_cost
        if output_inverted:
            f_expr = not_f_pos
            not_f_expr = f_sop
        else:
            f_expr = f_pos
            not_f_expr = not_f_sop

    elif mode == "area":
        # Prefer shorter series stacks and fewer terms among minimal forms.
        # SymPy already gives a minimal form; we accept it but could later
        # post-process in the cost model.  Here we keep F as POS and !F as SOP.
        f_expr = f_pos
        not_f_expr = not_f_sop
        output_inverted = False

    else:  # balance
        # If the minimal form would create a deep series stack, try the
        # inverted polarity (which often trades stack depth for width).
        f_expr = f_pos
        not_f_expr = not_f_sop
        output_inverted = False

        if _max_stack_depth(f_pos) > balance_max_stack:
            not_f_pos = POSform(syms, zeros) if zeros else True
            if _max_stack_depth(not_f_pos) <= balance_max_stack:
                f_sop = SOPform(syms, ones) if ones else False
                f_expr = not_f_pos
                not_f_expr = f_sop
                output_inverted = True

    return MinimizedForms(
        inputs=inputs,
        f_expr=f_expr,
        not_f_expr=not_f_expr,
        mode=mode,
        output_inverted=output_inverted,
    )
