"""Decide, per pattern input, whether its inverter belongs outside the cell.

`aion_minimizer` sometimes needs a complemented copy of one of a cell's inputs.
It can build that inverter inside the cell — two devices in *every*
instantiation — or take the complement on a ``<port>_bar`` port and leave the
job to whoever instantiates it.  The second option only pays when the parent
netlist can supply the complement cheaply, which is something only this side of
the flow can see.

So the arithmetic is done here, over the occurrences the cover actually
selected:

* keeping the inverter inside costs ``2 x occurrences`` devices;
* pulling it out costs two devices per *distinct* driving net that has no
  complement anywhere in the netlist, and nothing at all for the rest.

A complement is "already there" in the two usual shapes: some inverter already
reads the net (its output is the complement), or the net is itself an
inverter's output (that inverter's input is the complement).  Both are common
in post-synthesis netlists, which is why the decision is worth making at all.

An inverter that is itself about to be absorbed into an AION cell does not
count: its output net will not survive the rewrite.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from aion_opt.graph.circuit import Circuit
from aion_opt.io.cell_lib import CellLib

#: Suffix `aion_minimizer` gives a complemented signal.  The two tools have to
#: agree on it, since the port name is the whole interface between them.
COMPLEMENT_SUFFIX = "_bar"

PLAN_VERSION = 1

#: A cell is an inverter when its function is the negation of its only input.
_NEGATION = re.compile(r"^\s*!\s*\(\s*(\w+)\s*\)\s*$")


def is_inverter(cell_lib: CellLib, cell_type: str) -> bool:
    """True for a plain single-input inverter.

    Derived from the technology dictionary rather than from the cell name, so
    no library is hard-coded.  The single-input test is what rejects the
    tri-state ``einvn`` cells, whose function is also a bare negation but which
    have an extra enable pin.
    """
    function = cell_lib.function(cell_type)
    if not function or not _NEGATION.match(function):
        return False
    pins = cell_lib.pins(cell_type)
    inputs = [p for p, d in pins.items() if d == "input"]
    outputs = [p for p, d in pins.items() if d == "output"]
    return len(inputs) == 1 and len(outputs) == 1


def inverter_pins(cell_lib: CellLib, cell_type: str) -> tuple[str, str]:
    """Return ``(input pin, output pin)`` of an inverter cell."""
    pins = cell_lib.pins(cell_type)
    (input_pin,) = [p for p, d in pins.items() if d == "input"]
    (output_pin,) = [p for p, d in pins.items() if d == "output"]
    return input_pin, output_pin


def default_inverter(cell_lib: CellLib) -> str:
    """The cheapest inverter in the technology, by concrete cell name."""
    candidates = [name for name in cell_lib.cells if is_inverter(cell_lib, name)]
    if not candidates:
        raise ValueError(
            "The technology dictionary contains no single-input inverter, so a "
            "complement cannot be generated outside the cell"
        )
    best = min(candidates, key=lambda name: (cell_lib.area(name), name))
    return cell_lib.concrete_name(best)


def find_complement_bit(
    circuit: Circuit,
    cell_lib: CellLib,
    bit: int | str,
    excluded: Iterable[str] = (),
) -> int | None:
    """Return a bit already carrying the complement of ``bit``, if any.

    ``excluded`` names instances that are about to disappear into an AION cell;
    a complement they produce cannot be relied on.
    """
    if not isinstance(bit, int):
        return None  # constants have no net to hang a complement off
    net = circuit.net_for_bit(bit)
    if net is None:
        return None
    skip = set(excluded)

    def paired(inst_name: str, carries: str, wanted: str) -> int | str | None:
        """The bit on ``wanted`` sitting opposite ``bit`` on ``carries``.

        A ``Net`` aggregates every bit of a multi-bit signal, so its
        ``drivers``/``loads`` mix the consumers of ``s[0]`` with those of
        ``s[1]``.  Matching on the bit rather than on the net is what keeps an
        inverter of ``s[1]`` from being taken for the complement of ``s[0]``.
        """
        inst = circuit.instances.get(inst_name)
        if inst is None or inst_name in skip:
            return None
        if not is_inverter(cell_lib, inst.cell_type):
            return None
        source = inst.connections.get(carries) or []
        target = inst.connections.get(wanted) or []
        for index, candidate in enumerate(source):
            if candidate == bit and index < len(target):
                return target[index]
        return None

    # The net is an inverter's output, so that inverter's input is ~net.
    for inst_name, _pin in sorted(net.drivers):
        inst = circuit.instances.get(inst_name)
        if inst is None:
            continue
        if not is_inverter(cell_lib, inst.cell_type):
            continue
        in_pin, out_pin = inverter_pins(cell_lib, inst.cell_type)
        found = paired(inst_name, out_pin, in_pin)
        if found is not None:
            return found

    # An inverter already reads the net, so its output is ~net.
    for inst_name, _pin in sorted(net.loads):
        inst = circuit.instances.get(inst_name)
        if inst is None:
            continue
        if not is_inverter(cell_lib, inst.cell_type):
            continue
        in_pin, out_pin = inverter_pins(cell_lib, inst.cell_type)
        found = paired(inst_name, in_pin, out_pin)
        if found is not None:
            return found
    return None


@dataclass
class PortStat:
    """What externalizing one port of one cell would cost."""

    occurrences: int = 0
    complement_available: int = 0
    new_inverters: int = 0
    internal_devices: int = 0
    external_devices: int = 0

    @property
    def saving(self) -> int:
        return self.internal_devices - self.external_devices

    @property
    def recommended(self) -> bool:
        return self.saving > 0

    def as_dict(self) -> dict:
        data = asdict(self)
        data["saving"] = self.saving
        data["recommended"] = self.recommended
        return data


@dataclass
class ComplementPlan:
    """Per-module decision, shared by ``generate-cells``, the minimizer and ``rewrite``."""

    modules: dict[str, dict] = field(default_factory=dict)

    def external_ports(self, module: str) -> list[str]:
        """Input ports of ``module`` whose complement arrives from outside."""
        return list(self.modules.get(module, {}).get("external", []))

    def complement_ports(self, module: str) -> dict[str, str]:
        """``<port>_bar -> port`` for one module."""
        return {
            port + COMPLEMENT_SUFFIX: port for port in self.external_ports(module)
        }

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": PLAN_VERSION, "modules": self.modules}
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> "ComplementPlan":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        version = payload.get("version")
        if version != PLAN_VERSION:
            raise ValueError(
                f"{path}: complement plan version {version!r}, expected {PLAN_VERSION}"
            )
        return cls(modules=payload.get("modules", {}))

    @classmethod
    def empty(cls) -> "ComplementPlan":
        return cls()


def read_cell_interfaces(paths: Sequence[Path]) -> dict[str, list[str]]:
    """Read `aion_minimizer --report` files into ``module -> inputs needing ~x``.

    Only the inputs the minimizer says it needs complemented are eligible; the
    tool on this side decides *where* the inverter goes, never whether one is
    needed at all.
    """
    needed: dict[str, list[str]] = {}
    for path in paths:
        report = json.loads(Path(path).read_text(encoding="utf-8"))
        cell = report.get("cell")
        if not cell:
            raise ValueError(f"{path}: report has no 'cell' field")
        entry = report.get("complemented_inputs", {})
        wanted = sorted({*entry.get("internal", []), *entry.get("external", [])})
        needed[cell] = wanted
    return needed


def collect_interface_files(sources: Sequence[Path]) -> list[Path]:
    """Expand directories into the ``*.json`` reports they contain."""
    files: list[Path] = []
    for source in sources:
        if source.is_dir():
            files.extend(sorted(source.glob("*.json")))
        else:
            files.append(source)
    return files


def analyse(
    circuit: Circuit,
    cell_lib: CellLib,
    occurrences: Sequence[tuple[str, Mapping[tuple[str, str, str], str]]],
    module_names: Mapping[str, str],
    absorbed: Iterable[str] = (),
    eligible_ports: Mapping[str, Sequence[str]] | None = None,
) -> ComplementPlan:
    """Cost externalizing every eligible port of every selected pattern.

    ``occurrences`` pairs each selected site's canonical key with *that site's*
    ``boundary entry -> port name`` map.  The map has to be per occurrence: the
    port names are shared across a pattern, but the entries name concrete
    instances and nets, which are not.
    """
    absorbed = set(absorbed)
    stats: dict[str, dict[str, PortStat]] = {}
    #: module -> port -> nets seen, so a net shared by two sites is charged once
    seen_nets: dict[str, dict[str, set]] = {}

    for key, port_map in occurrences:
        module = module_names.get(key)
        if module is None:
            continue
        allowed = eligible_ports.get(module) if eligible_ports is not None else None
        if allowed is not None and not allowed:
            continue

        for (_net, inst, pin), port in port_map.items():
            if allowed is not None and port not in allowed:
                continue
            bits = circuit.instances[inst].connections.get(pin)
            if not bits:
                continue
            bit = bits[0]
            stat = stats.setdefault(module, {}).setdefault(port, PortStat())
            nets = seen_nets.setdefault(module, {}).setdefault(port, set())
            stat.occurrences += 1
            stat.internal_devices += 2
            if find_complement_bit(circuit, cell_lib, bit, absorbed) is not None:
                stat.complement_available += 1
            elif bit not in nets:
                nets.add(bit)
                stat.new_inverters += 1
                stat.external_devices += 2

    plan = ComplementPlan()
    for module, ports in sorted(stats.items()):
        entry = {
            "external": sorted(p for p, s in ports.items() if s.recommended),
            "ports": {},
            "stats": {port: stat.as_dict() for port, stat in sorted(ports.items())},
        }
        entry["ports"] = {
            port + COMPLEMENT_SUFFIX: port for port in entry["external"]
        }
        plan.modules[module] = entry
    return plan
