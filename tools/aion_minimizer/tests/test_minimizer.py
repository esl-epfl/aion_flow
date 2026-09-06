"""Two-level minimization and, above all, the polarity decision."""

from __future__ import annotations

import itertools

import pytest
from sympy import Not, Symbol, symbols

from aion_minimizer.minimizer import (
    complements_for_pulldown,
    complements_for_pullup,
    minimize_truth_table,
    polarity_cost,
    series_depth,
)


def table(names, fn):
    return {
        combo: int(fn(*combo))
        for combo in itertools.product((0, 1), repeat=len(names))
    }


def test_pullup_needs_the_complement_of_plain_literals():
    """A PMOS conducts when its gate is low, so ``A`` is applied as ``A_bar``."""
    a, b = symbols("A B")
    assert complements_for_pullup(a | b) == {"A", "B"}
    assert complements_for_pullup(~a & ~b) == set()


def test_pulldown_needs_the_complement_of_negated_literals():
    a, b = symbols("A B")
    assert complements_for_pulldown(a & b) == set()
    assert complements_for_pulldown(~a | ~b) == {"A", "B"}


def test_and3_prefers_the_inverted_polarity():
    """NAND3 plus an output inverter is 8 devices; the direct form is 12."""
    names = ["A", "B", "C"]
    forms = minimize_truth_table(names, table(names, lambda a, b, c: a and b and c))
    assert forms.output_inverted
    assert forms.complements == set()
    assert polarity_cost(forms.f_expr, forms.not_f_expr, True) == 8


def test_or3_prefers_the_inverted_polarity():
    names = ["A", "B", "C"]
    forms = minimize_truth_table(names, table(names, lambda a, b, c: a or b or c))
    assert forms.output_inverted
    assert forms.complements == set()
    assert polarity_cost(forms.f_expr, forms.not_f_expr, True) == 8


def test_nand2_stays_in_the_direct_polarity():
    names = ["A", "B"]
    forms = minimize_truth_table(names, table(names, lambda a, b: not (a and b)))
    assert not forms.output_inverted
    assert forms.complements == set()
    assert polarity_cost(forms.f_expr, forms.not_f_expr, False) == 4


def test_constant_functions_are_reported_not_raised():
    names = ["A"]
    assert minimize_truth_table(names, {(0,): 1, (1,): 1}).constant == 1
    assert minimize_truth_table(names, {(0,): 0, (1,): 0}).constant == 0


def test_series_depth_counts_the_right_axis():
    """POS groups sit in series; SOP terms sit in parallel."""
    a, b, c = symbols("A B C")
    # Pull-up of three single-literal groups is three deep.
    assert series_depth(~a & ~b & ~c, a | b | c) == 3
    # Pull-down of one three-literal product is three deep.
    assert series_depth(a | b | c, ~a & ~b & ~c) == 3


def test_xor_two_level_form_is_exponential():
    """The reason a single stage cannot be the answer for parity."""
    for width in (2, 3, 4):
        names = [f"I{i}" for i in range(width)]
        parity = table(names, lambda *bits: sum(bits) % 2)
        forms = minimize_truth_table(names, parity)
        cost = polarity_cost(forms.f_expr, forms.not_f_expr, forms.output_inverted)
        assert cost >= width * 2 ** (width - 1)
