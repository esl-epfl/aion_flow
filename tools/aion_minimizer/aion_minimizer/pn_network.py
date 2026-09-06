"""Build dual PMOS/NMOS series/parallel transistor networks.

From the minimized two-level forms:

* NMOS pull-down: each product term of ``!F`` becomes a series stack; stacks
  are placed in parallel between the output and VSS.
* PMOS pull-up: each sum term of ``F`` becomes a parallel group; groups are
  placed in series between VDD and the output.

A switch stores the literal that controls it.  The actual gate signal applied
is computed when the network is emitted/sized, taking into account that NMOS
conduct on ``1`` and PMOS conduct on ``0``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sympy import And, Not, Or, Symbol

from aion_minimizer.minimizer import MinimizedForms


@dataclass(frozen=True)
class Literal:
    """A Boolean literal, e.g. ``A`` or ``~A``."""

    name: str
    inverted: bool = False

    def __str__(self) -> str:
        # Use a SPICE-friendly suffix for complemented signals.
        return f"{self.name}_bar" if self.inverted else self.name

    def complement(self) -> "Literal":
        return Literal(self.name, not self.inverted)


@dataclass
class Switch:
    """One transistor switch in a P or N network."""

    type: str  # 'n' or 'p'
    literal: Literal

    @property
    def is_nmos(self) -> bool:
        return self.type == "n"

    @property
    def is_pmos(self) -> bool:
        return self.type == "p"

    @property
    def gate_signal(self) -> str:
        """Signal that must be applied to the transistor gate."""
        if self.is_nmos:
            # NMOS conducts when the literal is true.
            return str(self.literal)
        else:
            # PMOS conducts when the literal is false.
            return str(self.literal.complement())


@dataclass
class TransistorNetwork:
    """Dual pull-up / pull-down network for a single output."""

    output: str
    p_branches: List[List[Switch]] = field(default_factory=list)
    n_branches: List[List[Switch]] = field(default_factory=list)
    #: ``0``/``1`` for a constant function, ``None`` for a real network.
    constant: Optional[int] = None

    @property
    def pmos_count(self) -> int:
        return sum(len(b) for b in self.p_branches)

    @property
    def nmos_count(self) -> int:
        return sum(len(b) for b in self.n_branches)

    @property
    def transistor_count(self) -> int:
        return self.pmos_count + self.nmos_count


def _to_literal(expr: object) -> Literal:
    if isinstance(expr, Symbol):
        return Literal(expr.name, False)
    if isinstance(expr, Not) and isinstance(expr.args[0], Symbol):
        return Literal(expr.args[0].name, True)
    raise ValueError(f"Unsupported Boolean literal: {expr!r}")


def _sop_terms(expr: object) -> List[List[Literal]]:
    """Return the product terms of a Sum-of-Products expression."""
    if expr is True or expr is False:
        raise ValueError("Constant functions are not supported by the network generator")

    if isinstance(expr, Or):
        return [_product_literals(arg) for arg in expr.args]
    return [_product_literals(expr)]


def _product_literals(expr: object) -> List[Literal]:
    if isinstance(expr, And):
        return [_to_literal(arg) for arg in expr.args]
    return [_to_literal(expr)]


def _pos_groups(expr: object) -> List[List[Literal]]:
    """Return the sum (OR) groups of a Product-of-Sums expression."""
    if expr is True or expr is False:
        raise ValueError("Constant functions are not supported by the network generator")

    if isinstance(expr, And):
        return [_sum_literals(arg) for arg in expr.args]
    return [_sum_literals(expr)]


def _sum_literals(expr: object) -> List[Literal]:
    if isinstance(expr, Or):
        return [_to_literal(arg) for arg in expr.args]
    return [_to_literal(expr)]


def generate_networks(min_forms: MinimizedForms, output: str) -> TransistorNetwork:
    """Build the dual P/N transistor network for the minimized function."""
    if min_forms.constant is not None:
        # A constant output has no switching network; the writer emits a tie
        # pair whose gates are wired to the rails.
        return TransistorNetwork(output=output, constant=min_forms.constant)

    n_branches: List[List[Switch]] = []
    for term in _sop_terms(min_forms.not_f_expr):
        stack = [Switch("n", lit) for lit in term]
        n_branches.append(stack)

    p_branches: List[List[Switch]] = []
    for group in _pos_groups(min_forms.f_expr):
        branch = [Switch("p", lit) for lit in group]
        p_branches.append(branch)

    return TransistorNetwork(
        output=output,
        p_branches=p_branches,
        n_branches=n_branches,
    )
