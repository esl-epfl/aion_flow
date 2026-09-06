"""The partitioning search itself."""

from __future__ import annotations

import pytest

from aion_minimizer.decompose import INLINE, MEGAGATE, decompose
from aion_minimizer.netlist_evaluator import flatten_top
from aion_minimizer.spice_parser import parse_spice
from netlists import CORPUS


@pytest.fixture
def plan(gate_functions, gate_subckts):
    def run(name: str, **kwargs):
        subckts = parse_spice(CORPUS[name][0])
        top = next(s for s in subckts.values() if not s.is_gate_definition)
        flat = flatten_top(top, gate_functions, gate_subckts)
        return flat, decompose(flat, gate_functions, gate_subckts, **kwargs)

    return run


ALL = sorted(CORPUS)


@pytest.mark.parametrize("name", ALL)
def test_every_stage_drives_a_distinct_net(name, plan):
    _, result = plan(name)
    nets = [stage.output_net for stage in result.stages]
    assert len(nets) == len(set(nets))


@pytest.mark.parametrize("name", ALL)
def test_every_output_is_driven(name, plan):
    flat, result = plan(name)
    driven = {stage.output_net for stage in result.stages}
    assert set(flat.primary_outputs) <= driven


@pytest.mark.parametrize("name", ALL)
def test_every_stage_input_is_driven_or_primary(name, plan):
    """No stage may read a net nothing produces."""
    flat, result = plan(name)
    available = set(flat.primary_inputs) | set(flat.constant_nets)
    available |= {stage.output_net for stage in result.stages}
    for stage in result.stages:
        if stage.kind == MEGAGATE:
            assert set(stage.inputs) <= available, stage


@pytest.mark.parametrize("name", ALL)
def test_no_instance_is_placed_twice(name, plan):
    _, result = plan(name)
    placed = [inst for stage in result.stages for inst in stage.instances]
    assert len(placed) == len(set(placed))


@pytest.mark.parametrize("name", ALL)
def test_absorbing_an_instance_absorbs_all_of_its_consumers(name, plan):
    """The legality rule: only the root's net may be read from outside.

    `reconvergent_constant` is the case that matters — `net1` feeds two gates,
    so it can only be swallowed when both of them are swallowed too.  Allowing
    that is what lets the tool see the whole function folds to a constant.
    """
    flat, result = plan(name)
    for stage in result.stages:
        members = set(stage.instances)
        for inst in members:
            net = flat.instance_outputs[inst]
            if net == stage.output_net:
                continue
            assert net not in flat.primary_outputs, stage
            consumers = {
                other
                for other, nets in flat.instance_inputs.items()
                if net in nets
            }
            assert consumers <= members, (stage, net, consumers)


def test_stack_budget_is_enforced(plan):
    """A tight budget forces parts to split rather than stack deeper."""
    _, loose = plan("and3", max_stack_depth=4)
    _, tight = plan("and3", max_stack_depth=2)
    assert loose.max_stack_depth == 3
    assert tight.max_stack_depth <= 2
    assert tight.transistors >= loose.transistors


def test_cluster_input_cap_forces_splitting(plan):
    _, capped = plan("reconvergent_blob", max_cluster_inputs=2)
    assert len(capped.stages) > 1


def test_no_inline_leaves_no_pdk_cells(plan):
    _, result = plan("xor3", allow_inline=False)
    assert all(stage.kind == MEGAGATE for stage in result.stages)


def test_xor_parts_are_all_kept(plan):
    _, result = plan("xor4")
    assert all(stage.kind == INLINE for stage in result.stages)


def test_dead_logic_is_dropped(plan):
    """When the output folds to a constant nothing upstream is emitted."""
    _, result = plan("reconvergent_constant")
    assert len(result.stages) == 1
    assert result.stages[0].forms.constant == 1


def test_partitioning_is_deterministic(plan):
    first = plan("reconvergent_blob")[1]
    second = plan("reconvergent_blob")[1]
    assert [(s.output_net, s.kind, s.instances) for s in first.stages] == [
        (s.output_net, s.kind, s.instances) for s in second.stages
    ]
