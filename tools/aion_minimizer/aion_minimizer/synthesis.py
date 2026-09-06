"""Drive the full gate-netlist to transistor-netlist synthesis.

Keeping the orchestration out of :mod:`aion_minimizer.cli` lets the tests drive
it directly and gives the CLI a single result object to report on.

The pipeline is: flatten the gate netlist, partition it into the cheapest set
of complementary CMOS stages (:mod:`aion_minimizer.decompose`), size every
stage, build one inverter per complemented signal, and emit the lot as a single
``.subckt``.  Because a part of the partition may keep its PDK cell, the result
is never worse than the netlist it was given.

Complemented *primary inputs* can be handled two ways.  By default the cell
builds its own inverter.  With ``external_inputs`` the inverter is left out and
the complement becomes an extra ``<pin>_bar`` port, which the caller has to
drive: the cell drops two devices, and whoever instantiates it either reuses a
complement the parent netlist already has — free — or inserts an inverter
there, which is a wash.  Only primary inputs can be externalized; a complement
of an internal net has no port to hang off.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from aion_minimizer.cost_model import Inverter
from aion_minimizer.decompose import (
    DEFAULT_MAX_CLUSTER_INPUTS,
    INLINE,
    MEGAGATE,
    Decomposition,
    Stage,
    decompose,
)
from aion_minimizer.gate_extractor import GateFunction
from aion_minimizer.inline import inline_instances
from aion_minimizer.minimizer import minimize_function, series_depth
from aion_minimizer.netlist_evaluator import FlattenedNetlist, flatten_top
from aion_minimizer.pn_network import generate_networks
from aion_minimizer.render import DeviceNamer, render_inverter, render_network
from aion_minimizer.sizing import (
    SizingRules,
    restoring_inverter,
    size_inverter,
    size_network,
)
from aion_minimizer.spice_parser import Mosfet, Subcircuit, SubcircuitInstance
from aion_minimizer.spice_writer import write_subckt

#: Series stacks deeper than this degrade drive strength badly enough that the
#: merged cell stops being worth building.
DEFAULT_MAX_STACK_DEPTH = 4

COMPLEMENT_SUFFIX = "_bar"

#: How to supply a complemented primary input.
INTERNAL = "internal"
EXTERNAL = "external"
AUTO = "auto"
INVERTED_INPUT_MODES = (INTERNAL, EXTERNAL, AUTO)


@dataclass
class SynthesisResult:
    """Everything the CLI and the tests need to know about one run."""

    top_name: str
    spice: str
    flat: FlattenedNetlist
    decomposition: Decomposition
    devices: List[Mosfet]
    original_transistors: int
    inverters: List[Inverter] = field(default_factory=list)
    #: Primary inputs whose complement the cell builds itself.
    internal_complements: List[str] = field(default_factory=list)
    #: Primary inputs whose complement arrives on a ``<pin>_bar`` port.
    external_complements: List[str] = field(default_factory=list)
    #: Complemented internal nets; these can never be externalized.
    net_complements: List[str] = field(default_factory=list)

    @property
    def ports(self) -> List[str]:
        """The generated cell's pin list, extra ``_bar`` ports included."""
        return _ports_with_complements(self.flat.ports, self.external_complements)

    @property
    def complement_ports(self) -> Dict[str, str]:
        """``<pin>_bar`` -> the pin it must be the complement of."""
        return {
            net + COMPLEMENT_SUFFIX: net for net in self.external_complements
        }

    def externalization_report(self) -> Dict[str, object]:
        """Machine-readable summary for the caller that has to wire the cell.

        ``aion_opt`` uses this to decide, per input, whether pulling the
        inverter out of the cell actually pays: it costs two devices inside the
        cell and gains an inverter outside unless the parent netlist already
        carries the complement.
        """
        return {
            "cell": self.top_name,
            "ports": self.ports,
            "transistors": self.transistors,
            "original_transistors": self.original_transistors,
            "complemented_inputs": {
                "internal": list(self.internal_complements),
                "external": list(self.external_complements),
                "nets": list(self.net_complements),
            },
            "complement_ports": self.complement_ports,
            "devices_saved_per_externalized_input": 2,
        }

    @property
    def transistors(self) -> int:
        return len(self.devices)

    @property
    def savings(self) -> int:
        return self.original_transistors - self.transistors

    @property
    def stages(self) -> List[Stage]:
        return self.decomposition.stages

    @property
    def merged_stages(self) -> int:
        return sum(1 for s in self.stages if s.kind == MEGAGATE)

    @property
    def kept_cells(self) -> int:
        return sum(len(s.instances) for s in self.stages if s.kind == INLINE)

    @property
    def max_stack_depth(self) -> int:
        return self.decomposition.max_stack_depth


def synthesize(
    top: Subcircuit,
    gate_functions: Dict[str, GateFunction],
    gate_subckts: Dict[str, Subcircuit],
    mode: str = "transistor",
    rules: Optional[SizingRules] = None,
    max_stack_depth: int = DEFAULT_MAX_STACK_DEPTH,
    max_cluster_inputs: int = DEFAULT_MAX_CLUSTER_INPUTS,
    allow_inline: bool = True,
    single_stage: bool = False,
    balance_max_stack: int = 3,
    skipped: Optional[Dict[str, str]] = None,
    inverted_inputs: str = INTERNAL,
    external_inputs: Optional[Sequence[str]] = None,
) -> SynthesisResult:
    """Synthesize ``top`` into a single transistor-level subcircuit."""
    rules = rules or SizingRules()
    # A cell whose ports already carry `<pin>_bar` was produced by an earlier
    # run (or by a generator that made the decision upstream).  Re-reading it
    # must be idempotent: keep the port, do not enumerate it as a free input,
    # and treat that pin as externalized whatever the mode says.
    provided = _provided_complements(top.pins)
    flat = flatten_top(
        top,
        gate_functions,
        gate_subckts,
        skipped,
        ignore_pins={net + COMPLEMENT_SUFFIX for net in provided},
    )

    if single_stage:
        plan = _single_stage_plan(flat, mode, balance_max_stack)
    else:
        plan = decompose(
            flat,
            gate_functions,
            gate_subckts,
            mode=mode,
            max_stack_depth=max_stack_depth,
            max_cluster_inputs=max_cluster_inputs,
            allow_inline=allow_inline,
            balance_max_stack=balance_max_stack,
        )

    external = _resolve_external(
        flat, plan, inverted_inputs, external_inputs, provided
    )
    devices, inverters = _render(flat, plan, top, gate_subckts, rules, external)

    inputs = set(flat.primary_inputs)
    complements = plan.complements
    ports = _ports_with_complements(flat.ports, external)
    spice = write_subckt(top.name, ports, devices)
    original = sum(
        len(gate_subckts[inst.subckt_name].mosfets) for inst in top.instances
    )
    return SynthesisResult(
        top_name=top.name,
        spice=spice,
        flat=flat,
        decomposition=plan,
        devices=devices,
        original_transistors=original,
        inverters=inverters,
        internal_complements=sorted(complements & inputs - set(external)),
        external_complements=list(external),
        net_complements=sorted(complements - inputs),
    )


def _provided_complements(ports: Sequence[str]) -> List[str]:
    """Pins whose ``<pin>_bar`` companion is already in the port list."""
    names = set(ports)
    return [
        pin
        for pin in ports
        if not pin.endswith(COMPLEMENT_SUFFIX)
        and pin + COMPLEMENT_SUFFIX in names
    ]


def _resolve_external(
    flat: FlattenedNetlist,
    plan: Decomposition,
    inverted_inputs: str,
    external_inputs: Optional[Sequence[str]],
    provided: Sequence[str] = (),
) -> List[str]:
    """Decide which complemented primary inputs become ports.

    Only primary inputs are eligible: a complemented internal net has nothing
    to hang a port off, so it always stays inside the cell.
    """
    if inverted_inputs not in INVERTED_INPUT_MODES:
        raise ValueError(
            f"Unknown inverted-input mode {inverted_inputs!r}; "
            f"expected one of {INVERTED_INPUT_MODES}"
        )
    eligible = plan.complements & set(flat.primary_inputs)

    if inverted_inputs == INTERNAL:
        requested: set = set()
    elif inverted_inputs == EXTERNAL:
        requested = set(eligible)
    else:  # AUTO: the caller supplies the per-input decision.
        requested = set(external_inputs or ())
        unknown = requested - set(flat.primary_inputs)
        if unknown:
            raise ValueError(
                f"--external-inputs names pins that are not primary inputs of "
                f"{flat.top_name!r}: {sorted(unknown)}"
            )
    # A port the caller already put on the cell is externalized whatever the
    # mode says; there is no inverter to build for it either way.
    requested |= set(provided)
    # Asking for a complement the cell does not need is a no-op, not an error:
    # the decision upstream is made per pattern, not per synthesized variant.
    return [net for net in flat.primary_inputs if net in requested & eligible]


def _ports_with_complements(
    ports: Sequence[str], external: Sequence[str]
) -> List[str]:
    """Insert ``<pin>_bar`` ports ahead of the supplies.

    Supplies stay last, which is the convention every cell in this PDK follows,
    and the existing pins keep their relative order so an unchanged cell keeps
    an unchanged pin list.
    """
    present = set(ports)
    extra = [
        net + COMPLEMENT_SUFFIX
        for net in external
        if net + COMPLEMENT_SUFFIX not in present
    ]
    if not extra:
        return list(ports)
    supply_at = next(
        (i for i, pin in enumerate(ports) if pin.upper() in ("VDD", "VSS")),
        len(ports),
    )
    return list(ports[:supply_at]) + extra + list(ports[supply_at:])


def _single_stage_plan(
    flat: FlattenedNetlist, mode: str, balance_max_stack: int
) -> Decomposition:
    """Flatten everything into one stage, whatever it costs.

    Kept behind ``--single-stage`` so the decomposer's choices can be compared
    against the unconditional merge the tool used to do.
    """
    forms = minimize_function(flat, mode=mode, balance_max_stack=balance_max_stack)
    stage = Stage(
        output_net=flat.primary_output,
        kind=MEGAGATE,
        instances=list(flat.instance_order),
        transistors=0,
        inputs=list(flat.primary_inputs),
        forms=forms,
    )
    depth = (
        0
        if forms.constant is not None
        else series_depth(forms.f_expr, forms.not_f_expr)
    )
    return Decomposition(stages=[stage], transistors=0, max_stack_depth=depth)


def _render(
    flat: FlattenedNetlist,
    plan: Decomposition,
    top: Subcircuit,
    gate_subckts: Dict[str, Subcircuit],
    rules: SizingRules,
    external: Sequence[str] = (),
):
    """Size and render every stage, plus one inverter per complemented net."""
    complements = sorted(plan.complements)
    _check_complement_names(flat, complements, external)
    # An externalized complement arrives on a port, so the cell builds no
    # inverter for it; the gate signal name is the same either way.
    inverters = [
        Inverter(input=net, output=net + COMPLEMENT_SUFFIX)
        for net in complements
        if net not in set(external)
    ]

    namer = DeviceNamer(reserved=_reserved_nets(flat, complements))
    by_name = {inst.name: inst for inst in top.instances}
    devices: List[Mosfet] = []

    # Inverters first so the complemented signals exist before their consumers.
    for inv in inverters:
        devices.extend(render_inverter(size_inverter(inv, rules), namer))

    for stage in plan.stages:
        if stage.kind == INLINE:
            devices.extend(
                inline_instances(
                    [by_name[name] for name in stage.instances], gate_subckts, namer
                )
            )
            continue
        sized = size_network(generate_networks(stage.forms, stage.output_net), rules)
        if stage.forms.output_inverted:
            sized.output_inverter = restoring_inverter(rules)
        devices.extend(
            render_network(
                sized,
                stage.output_net,
                namer,
                output_inverted=stage.forms.output_inverted,
            )
        )
    return devices, inverters


def _reserved_nets(flat: FlattenedNetlist, complements: Sequence[str]) -> set:
    nets = set(flat.ports) | set(flat.constant_nets)
    nets |= set(flat.instance_outputs.values())
    for ins in flat.instance_inputs.values():
        nets |= set(ins)
    nets |= {net + COMPLEMENT_SUFFIX for net in complements}
    return nets


def _check_complement_names(
    flat: FlattenedNetlist,
    complements: Sequence[str],
    external: Sequence[str] = (),
) -> None:
    """Refuse to build ``X_bar`` if the design already uses that name."""
    existing = set(flat.ports)
    existing |= set(flat.instance_outputs.values())
    clashes = [
        n
        for n in complements
        if n + COMPLEMENT_SUFFIX in existing and n not in set(external)
    ]
    if clashes:
        raise ValueError(
            "Cannot name the complemented signals: "
            + ", ".join(f"{n}{COMPLEMENT_SUFFIX}" for n in clashes)
            + " already exist in the netlist"
        )
