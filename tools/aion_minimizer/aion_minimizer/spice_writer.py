"""Emit transistor-level SPICE netlists.

The writer produces a single ``.subckt`` containing:

1. Any required input inverters.
2. The PMOS pull-up network from VDD to the output.
3. The NMOS pull-down network from the output to VSS.

Devices are named sequentially with ``XN*`` for NMOS and ``XP*`` for PMOS.
"""

from __future__ import annotations

from typing import List

from aion_minimizer.sizing import SizedNetwork, SizedTransistor


def _indent(line: str) -> str:
    return f"    {line}"


def _emit_device(
    prefix: str,
    index: int,
    transistor: SizedTransistor,
    drain: str,
    source: str,
    bulk: str,
) -> str:
    model = "sg13_lv_pmos" if transistor.type == "p" else "sg13_lv_nmos"
    return (
        f"{prefix}{index} {drain} {transistor.gate} {source} {bulk} {model} "
        f"w={transistor.w} l={transistor.l} ng={transistor.ng} m={transistor.m}"
    )


def write_spice(
    subckt_name: str,
    primary_inputs: List[str],
    primary_output: str,
    sized: SizedNetwork,
    vdd: str = "VDD",
    vss: str = "VSS",
    output_inverted: bool = False,
) -> str:
    """Return a SPICE ``.subckt`` string for the sized megagate."""
    lines: List[str] = []
    lines.append(f".subckt {subckt_name} {' '.join(primary_inputs)} {primary_output} {vdd} {vss}")

    n_index = 0
    p_index = 0

    # Internal node that carries the raw complex-gate output.
    gate_output = primary_output if not output_inverted else "mega_out"

    # Inverters first.
    for inv in sized.inverters:
        lines.append(
            _indent(
                _emit_device(
                    "XP", p_index, inv.pmos, inv.output, vdd, vdd
                )
            )
        )
        p_index += 1
        lines.append(
            _indent(
                _emit_device(
                    "XN", n_index, inv.nmos, inv.output, vss, vss
                )
            )
        )
        n_index += 1

    # PMOS pull-up: groups in series from VDD to the gate output.
    # The output side is the drain so that it is recognized as the output node.
    left = vdd
    num_p_groups = len(sized.p_branches)
    for group_idx, group in enumerate(sized.p_branches):
        right = gate_output if group_idx == num_p_groups - 1 else f"net_p_{group_idx}"
        for transistor in group:
            lines.append(
                _indent(
                    _emit_device(
                        "XP", p_index, transistor, right, left, vdd
                    )
                )
            )
            p_index += 1
        left = right

    # NMOS pull-down: stacks in parallel from the gate output to VSS.
    for stack_idx, stack in enumerate(sized.n_branches):
        top = gate_output
        for level, transistor in enumerate(stack):
            bottom = vss if level == len(stack) - 1 else f"net_n_{stack_idx}_{level}"
            lines.append(
                _indent(
                    _emit_device(
                        "XN", n_index, transistor, top, bottom, vss
                    )
                )
            )
            n_index += 1
            top = bottom

    # Optional output inverter.
    if output_inverted:
        lines.append(
            _indent(
                f"XP{p_index} {primary_output} {gate_output} {vdd} {vdd} sg13_lv_pmos w=1.480u l=0.130u ng=1 m=1"
            )
        )
        p_index += 1
        lines.append(
            _indent(
                f"XN{n_index} {primary_output} {gate_output} {vss} {vss} sg13_lv_nmos w=0.740u l=0.130u ng=1 m=1"
            )
        )
        n_index += 1

    lines.append(".ends")
    return "\n".join(lines) + "\n"


def write_spice_to_file(
    path: str,
    subckt_name: str,
    primary_inputs: List[str],
    primary_output: str,
    sized: SizedNetwork,
    vdd: str = "VDD",
    vss: str = "VSS",
    output_inverted: bool = False,
) -> None:
    """Write the sized megagate SPICE netlist to ``path``."""
    from pathlib import Path

    Path(path).write_text(
        write_spice(
            subckt_name,
            primary_inputs,
            primary_output,
            sized,
            vdd,
            vss,
            output_inverted=output_inverted,
        )
    )
