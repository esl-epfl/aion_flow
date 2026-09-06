"""Split a gate netlist into the cheapest set of complementary CMOS stages.

Merging a whole cell into one complex gate is only a good idea while its
two-level form stays small.  It does not for non-unate functions: an n-input
XOR has 2^(n-1) prime implicants of n literals each, so a 4-input XOR tree that
costs 30 devices as standard cells costs 72 as a single stage.

So instead of always flattening everything, the decomposer searches over ways
to *partition* the gate DAG.  Each part becomes either one resynthesized
complementary stage or the original PDK cell left untouched, and the partition
minimizing total devices wins.  Flattening everything into one stage is simply
the partition with a single part, so nothing that used to be found is lost.

The search is exact.  Cutting the DAG at every net with more than one consumer
leaves a forest of fanout-free trees; within a tree no part can be shared, so a
memoized recursion over "the cheapest way to produce this net" is optimal.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from aion_minimizer.gate_extractor import GateFunction
from aion_minimizer.minimizer import (
    MinimizedForms,
    minimize_truth_table,
    polarity_complements,
    series_depth,
)
from aion_minimizer.netlist_evaluator import FlattenedNetlist
from aion_minimizer.spice_parser import Subcircuit

#: Above this the local truth table (2**k rows) stops being cheap to build.
DEFAULT_MAX_CLUSTER_INPUTS = 8

#: Safety valve for pathological shapes; clusters are enumerated per root.
MAX_CLUSTERS_PER_NODE = 20000

_UNREACHABLE = 10**9

MEGAGATE = "megagate"
INLINE = "inline"


@dataclass
class Stage:
    """One driver of one net inside the generated cell."""

    output_net: str
    kind: str  # MEGAGATE or INLINE
    instances: List[str]
    transistors: int
    inputs: List[str] = field(default_factory=list)
    forms: Optional[MinimizedForms] = None

    @property
    def complements(self) -> Set[str]:
        return set(self.forms.complements) if self.forms is not None else set()


@dataclass
class Decomposition:
    """The chosen partition, ready to render."""

    stages: List[Stage]
    transistors: int
    max_stack_depth: int

    @property
    def complements(self) -> Set[str]:
        needed: Set[str] = set()
        for stage in self.stages:
            needed |= stage.complements
        return needed


@dataclass
class _Plan:
    cost: int
    stages: Tuple[Stage, ...]


def decompose(
    flat: FlattenedNetlist,
    gate_functions: Dict[str, GateFunction],
    gate_subckts: Dict[str, Subcircuit],
    mode: str = "transistor",
    max_stack_depth: int = 4,
    max_cluster_inputs: int = DEFAULT_MAX_CLUSTER_INPUTS,
    allow_inline: bool = True,
    balance_max_stack: int = 3,
) -> Decomposition:
    """Return the cheapest partition of ``flat`` into stages."""
    driver = {net: name for name, net in flat.instance_outputs.items()}
    consumers: Dict[str, Set[str]] = {}
    for name, nets in flat.instance_inputs.items():
        for net in nets:
            consumers.setdefault(net, set()).add(name)

    outputs = set(flat.primary_outputs)
    order = {name: i for i, name in enumerate(flat.instance_order)}
    plan_memo: Dict[str, _Plan] = {}
    cluster_memo: Dict[str, List[Tuple[str, ...]]] = {}

    def fanin(name: str) -> List[str]:
        seen: List[str] = []
        for net in flat.instance_inputs[name]:
            producer = driver.get(net)
            if producer is not None and producer not in seen:
                seen.append(producer)
        return seen

    def is_single_output(members: Set[str], root: str) -> bool:
        """True when only the root's net escapes the cluster.

        Absorbing an instance is only legal if every consumer of its output is
        absorbed too — otherwise the merged stage would have to drive a second
        net it no longer computes.
        """
        for name in members:
            if name == root:
                continue
            net = flat.instance_outputs[name]
            if net in outputs:
                return False
            if not consumers.get(net, set()) <= members:
                return False
        return True

    def clusters(name: str) -> List[Tuple[str, ...]]:
        """Every legal single-output cluster rooted at ``name``.

        Grown through the fan-in cone, so reconvergent shapes are reachable:
        a net with two consumers can still be merged when both of them end up
        inside the same cluster.
        """
        if name in cluster_memo:
            return cluster_memo[name]
        cluster_memo[name] = [(name,)]  # guards against a cyclic fan-in

        options: List[List[Tuple[str, ...]]] = []
        for child in fanin(name):
            options.append([()] + list(clusters(child)))

        found: List[Tuple[str, ...]] = []
        seen: Set[Tuple[str, ...]] = set()
        for combo in itertools.product(*options):
            members = {name}
            for part in combo:
                members.update(part)
            if not is_single_output(members, name):
                continue
            key = tuple(sorted(members, key=order.__getitem__))
            if key in seen:
                continue
            seen.add(key)
            found.append(key)
            if len(found) >= MAX_CLUSTERS_PER_NODE:
                break
        cluster_memo[name] = found
        return found

    def solve(name: str) -> _Plan:
        if name in plan_memo:
            return plan_memo[name]
        plan_memo[name] = _Plan(cost=_UNREACHABLE, stages=())

        best: Optional[_Plan] = None
        for members in clusters(name):
            inputs = _boundary_inputs(flat, members)
            sub_plans = [solve(driver[net]) for net in inputs if net in driver]
            sub_cost = sum(plan.cost for plan in sub_plans)
            if sub_cost >= _UNREACHABLE:
                continue
            sub_stages: Tuple[Stage, ...] = tuple(
                stage for plan in sub_plans for stage in plan.stages
            )

            for stage in _stage_options(
                flat,
                gate_functions,
                gate_subckts,
                members,
                inputs,
                mode=mode,
                max_stack_depth=max_stack_depth,
                max_cluster_inputs=max_cluster_inputs,
                allow_inline=allow_inline,
                balance_max_stack=balance_max_stack,
            ):
                total = stage.transistors + sub_cost
                if best is None or total < best.cost:
                    best = _Plan(cost=total, stages=(stage,) + sub_stages)

        if best is None:
            raise ValueError(
                f"No feasible implementation for instance {name!r}: every "
                f"candidate exceeded max_cluster_inputs={max_cluster_inputs} or "
                f"max_stack_depth={max_stack_depth}"
            )
        plan_memo[name] = best
        return best

    chosen: Dict[str, Stage] = {}
    for net in flat.primary_outputs:
        for stage in solve(driver[net]).stages:
            chosen.setdefault(stage.output_net, stage)

    # Only the output cone survives: a stage that collapsed to a constant kills
    # everything that fed it.
    live = _live_stages(flat, chosen, flat.primary_outputs)
    ordered = sorted(live, key=lambda s: order[s.instances[0]])

    complements: Set[str] = set()
    for stage in ordered:
        complements |= stage.complements
    total = sum(stage.transistors for stage in ordered)
    # Stage costs charge each stage for the inverters it needs; a signal wanted
    # by two stages is only built once, so refund the duplicates.
    charged = sum(len(stage.complements) for stage in ordered)
    total -= 2 * (charged - len(complements))

    depth = max(
        (
            series_depth(s.forms.f_expr, s.forms.not_f_expr)
            for s in ordered
            if s.forms is not None and s.forms.constant is None
        ),
        default=0,
    )
    return Decomposition(stages=ordered, transistors=total, max_stack_depth=depth)


def _live_stages(
    flat: FlattenedNetlist, chosen: Dict[str, Stage], primary_outputs: Sequence[str]
) -> List[Stage]:
    """Stages the primary outputs still depend on."""
    live: Dict[str, Stage] = {}
    stack = list(primary_outputs)
    while stack:
        net = stack.pop()
        stage = chosen.get(net)
        if stage is None or net in live:
            continue
        live[net] = stage
        if stage.kind == MEGAGATE:
            stack.extend(stage.inputs)
        else:
            stack.extend(_boundary_inputs(flat, stage.instances))
    return list(live.values())


def _boundary_inputs(flat: FlattenedNetlist, members: Sequence[str]) -> List[str]:
    """Nets a cluster consumes but does not produce, in a stable order."""
    produced = {flat.instance_outputs[name] for name in members}
    seen: List[str] = []
    for name in members:
        for net in flat.instance_inputs[name]:
            if net in produced or net in flat.constant_nets or net in seen:
                continue
            seen.append(net)
    return seen


def _cluster_truth_table(
    flat: FlattenedNetlist,
    gate_functions: Dict[str, GateFunction],
    members: Sequence[str],
    inputs: Sequence[str],
) -> Dict[Tuple[int, ...], int]:
    """Evaluate a cluster over every assignment of its boundary inputs."""
    output_net = flat.instance_outputs[members[-1]]
    table: Dict[Tuple[int, ...], int] = {}
    for combo in itertools.product((0, 1), repeat=len(inputs)):
        values: Dict[str, int] = dict(flat.constant_nets)
        values.update(zip(inputs, combo))
        for name in members:
            fn = gate_functions[flat.instance_cells[name]]
            args = dict(zip(fn.inputs, (values[n] for n in flat.instance_inputs[name])))
            result = fn.eval(**args)
            if result is None:
                raise ValueError(f"Instance {name!r} produced X for inputs {combo}")
            values[flat.instance_outputs[name]] = result
        table[combo] = values[output_net]
    return table


def _stage_options(
    flat: FlattenedNetlist,
    gate_functions: Dict[str, GateFunction],
    gate_subckts: Dict[str, Subcircuit],
    members: Tuple[str, ...],
    inputs: List[str],
    mode: str,
    max_stack_depth: int,
    max_cluster_inputs: int,
    allow_inline: bool,
    balance_max_stack: int,
) -> List[Stage]:
    """The legal ways to implement one cluster."""
    output_net = flat.instance_outputs[members[-1]]
    options: List[Stage] = []

    if allow_inline and len(members) == 1:
        cell = gate_subckts[flat.instance_cells[members[0]]]
        options.append(
            Stage(
                output_net=output_net,
                kind=INLINE,
                instances=list(members),
                transistors=len(cell.mosfets),
            )
        )

    if len(inputs) <= max_cluster_inputs:
        table = _cluster_truth_table(flat, gate_functions, members, inputs)
        forms = minimize_truth_table(
            list(inputs), table, mode=mode, balance_max_stack=balance_max_stack
        )
        if forms.constant is not None:
            options.append(
                Stage(
                    output_net=output_net,
                    kind=MEGAGATE,
                    instances=list(members),
                    transistors=2,
                    inputs=list(inputs),
                    forms=forms,
                )
            )
        elif series_depth(forms.f_expr, forms.not_f_expr) <= max_stack_depth:
            from aion_minimizer.minimizer import _literal_count

            devices = _literal_count(forms.f_expr) + _literal_count(forms.not_f_expr)
            devices += 2 * len(forms.complements)
            if forms.output_inverted:
                devices += 2
            options.append(
                Stage(
                    output_net=output_net,
                    kind=MEGAGATE,
                    instances=list(members),
                    transistors=devices,
                    inputs=list(inputs),
                    forms=forms,
                )
            )
    return options
