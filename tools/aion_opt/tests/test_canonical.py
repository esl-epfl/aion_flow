"""Canonical labelling: isomorphic patterns must collide, others must not."""

from __future__ import annotations

from itertools import permutations

from aion_opt.pattern.canonical import canonicalize, canonicalize_named


def _relabel(perm, types, edges, in_pins, out_pins):
    """Apply a node relabelling to a whole pattern description."""
    return (
        tuple(types[perm.index(i)] for i in range(len(types))),
        tuple(sorted((perm[s], sp, perm[d], dp) for s, sp, d, dp in edges)),
        tuple(sorted((perm[i], p) for i, p in in_pins)),
        tuple(sorted((perm[i], p) for i, p in out_pins)),
    )


def test_key_is_invariant_under_relabelling():
    types = ("nand2", "nor2", "inv")
    edges = ((0, "Y", 1, "A1"), (1, "Y", 2, "A"))
    in_pins = ((0, "A1"), (0, "A2"), (1, "A2"))
    out_pins = ((2, "Y"),)

    reference, _ = canonicalize(types, edges, in_pins, out_pins)
    for perm in permutations(range(3)):
        key, _ = canonicalize(*_relabel(perm, types, edges, in_pins, out_pins))
        assert key == reference


def test_different_structures_get_different_keys():
    chain, _ = canonicalize(
        ("nand2", "nand2"), ((0, "Y", 1, "A1"),), ((0, "A1"), (1, "A2")), ((1, "Y"),)
    )
    reconvergent, _ = canonicalize(
        ("nand2", "nand2"),
        ((0, "Y", 1, "A1"), (0, "Y", 1, "A2")),
        ((0, "A1"),),
        ((1, "Y"),),
    )
    assert chain != reconvergent


def test_boundary_pins_are_part_of_the_key():
    """Same internal wiring, different port count -> different cell."""
    both_inputs, _ = canonicalize(
        ("nand2", "inv"), ((0, "Y", 1, "A"),), ((0, "A1"), (0, "A2")), ((1, "Y"),)
    )
    one_input, _ = canonicalize(
        ("nand2", "inv"), ((0, "Y", 1, "A"),), ((0, "A1"),), ((1, "Y"),)
    )
    assert both_inputs != one_input


def test_pin_swap_is_not_an_automorphism():
    """A1 and A2 are distinct pins, so swapping them changes the pattern."""
    a1, _ = canonicalize(("inv", "nand2"), ((0, "Y", 1, "A1"),), ((1, "A2"),), ((1, "Y"),))
    a2, _ = canonicalize(("inv", "nand2"), ((0, "Y", 1, "A2"),), ((1, "A1"),), ((1, "Y"),))
    assert a1 != a2


def test_mapping_is_a_bijection():
    types = ("a", "a", "a", "b")
    edges = ((0, "Y", 1, "A"), (1, "Y", 2, "A"), (2, "Y", 3, "A"))
    key, mapping = canonicalize(types, edges, ((0, "A"),), ((3, "Y"),))
    assert sorted(mapping) == list(range(4))
    assert key


def test_named_wrapper_matches_index_form():
    node_types = {"u3": "nand2", "u1": "nor2"}
    edges = [("u1", "Y", "u3", "A1", "n5")]
    key, mapping = canonicalize_named(
        node_types, edges, [("n0", "u1", "A1"), ("n1", "u3", "A2")], [("n2", "u3", "Y")]
    )
    assert set(mapping) == {"u1", "u3"}
    assert sorted(mapping.values()) == [0, 1]

    # Renaming the instances must not change the key.
    renamed_types = {"zz": "nand2", "aa": "nor2"}
    renamed_edges = [("aa", "Y", "zz", "A1", "whatever")]
    key2, _ = canonicalize_named(
        renamed_types,
        renamed_edges,
        [("x", "aa", "A1"), ("y", "zz", "A2")],
        [("z", "zz", "Y")],
    )
    assert key == key2


def test_symmetric_pattern_is_stable():
    """Two identical gates feeding one gate: the two are interchangeable."""
    types = ("inv", "inv", "nand2")
    edges_a = ((0, "Y", 2, "A1"), (1, "Y", 2, "A2"))
    edges_b = ((1, "Y", 2, "A1"), (0, "Y", 2, "A2"))
    key_a, _ = canonicalize(types, edges_a, ((0, "A"), (1, "A")), ((2, "Y"),))
    key_b, _ = canonicalize(types, edges_b, ((0, "A"), (1, "A")), ((2, "Y"),))
    assert key_a == key_b
