#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
"""Characterize a SPICE cell with ngspice and write a Liberty (.lib) file for it.

Give it a transistor-level ``.subckt``, a device-model library and a Liberty *template*,
and it produces one ``.lib`` per process corner, containing for every cell:

  * ``function`` -- **measured**, not assumed: an ``.op`` per input vector gives the truth
    table, which is minimized (Quine-McCluskey) into a Liberty expression and then
    re-evaluated against that same table before it is written out;
  * ``cell_rise`` / ``cell_fall`` / ``rise_transition`` / ``fall_transition`` -- an NLDM
    table per timing arc over the input-slew x output-load grid;
  * ``internal_power`` (``rise_power`` / ``fall_power``) over the same grid;
  * ``leakage_power`` per input state, and ``cell_leakage_power`` as their average;
  * input pin ``capacitance`` / ``rise_capacitance`` / ``fall_capacitance`` (+ ranges).

This is the *characterization* half of the pair; `gen_cell_tb.py` is the *verification*
half and stays independent of it. The two meet in one place only: unless ``--no-verify``
is given, this script invokes ``gen_cell_tb.py`` once per corner to build the exhaustive
functional deck for the same cell and runs it, so no timing number is ever reported for a
netlist that does not compute the right function *at that corner*.

Nothing about the technology is hard-coded here -- see "The template contract" below.


Quick start (inside the EDA container -- the PDK is not visible from the host)
-----------------------------------------------------------------------------
    ./scripts/docker_run.sh "make aion-char-lib"          # characterize the AION example
    ./scripts/docker_run.sh "make aion-char-lib-selfcheck" # calibrate against a PDK cell

or directly::

    gen_cell_lib.py custom_circuit_example/aion_nand2_11_flat.spice \\
        --cell AION_nand2_11 --verilog aion_cells.v \\
        --lib   $PDK/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib \\
        --cell-spice $PDK/libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice \\
        --model-lib  $PDK/libs.tech/ngspice/models/cornerMOSlv.lib \\
        -o lib/


What it needs, and what each input buys
---------------------------------------
Required: the SPICE netlist holding the ``.subckt`` (positional), ``--model-lib``, and some
way to know **which pins are inputs and which are outputs** -- a SPICE ``.subckt`` does not
say. That last one has three sources, in this order of precedence:

===================  ===========================================================
``--inputs``/        explicit, and the only option for a cell with no other view
``--outputs``
``--verilog FILE``   the directions are read out of the module header and its
                     ``input``/``output`` declarations. **Any** Verilog view will
                     do, behavioural included -- the PDK's own
                     ``sg13g2_stdcell.v``, written with gate primitives, works.
                     If the file happens to be a *structural* netlist, it also
                     becomes the design under test for the functional check.
``--lib FILE``       Liberty declares ``direction`` per pin, so a library that
                     defines the cell answers the question too.
===================  ===========================================================

Nothing numeric is ever read from ``--lib`` or ``--verilog``: they are *oracles*. What is
being characterized is a transistor netlist, so any independent statement of what it should
compute will do, and there are two, checked at every corner before a measurement is
believed:

``--lib``       the strongest. `gen_cell_tb.py` builds a gold model from the Liberty
                ``function`` attributes and runs its exhaustive SPICE testbench, so the
                comparison happens on real analog waveforms at that corner's voltage and
                temperature. With a *structural* ``--verilog`` as well, that deck is a
                3-way check: gold, the gate netlist, and this netlist.
``--verilog``   no Liberty needed. The Verilog view is elaborated with Icarus (leaf models
                come from ``--cell-verilog``; ``specify`` blocks are stripped, since they
                carry no function and Icarus rejects some of the PDK's), swept over every
                input combination, and compared against the truth table this tool measured
                from the transistors. Behavioural or structural both work -- the PDK's own
                ``sg13g2_stdcell.v`` does.
neither         the run still works and the function is still measured; the console and
                ``char_report.md`` say the check was skipped.

The proof that nothing is copied even when ``--lib`` is given: for ``sg13g2_nand2_1`` this
tool emits ``function : "!A+!B"`` where IHP's library says ``"!(A*B)"`` -- same function,
independently derived -- and diffing the emitted cell group of a run *with* ``--lib``
against one with only ``--inputs``/``--outputs`` gives no differences at all.

Both oracles are fatal on disagreement. Rewiring one transistor of the worked example so it
computes the wrong function is caught and named vector by vector::

    error: [FAIL] AION_nand2_11 : the measured truth table disagrees with aion_cells.v in
    3 of 8 cases:
      I0=0 I1=1 I2=0: O0 is 0 in the netlist, 1 in Verilog
      ...

So the minimum for a cell nobody has any other view of is::

    gen_cell_lib.py my_cell.spice --cell my_cell --inputs A,B --outputs Y \\
        --model-lib .../cornerMOSlv.lib --no-verify

``--area`` and ``--footprint`` are optional metadata. ``area`` defaults to 0 and only feeds
area reports; ``cell_footprint`` groups pin-compatible cells so a synthesis tool may swap
one for another (with ``in_place_swap_mode : match_footprint``), which is meaningful for a
*family* of drive strengths and pointless for a single cell.


Where the output goes
---------------------
``-o DIR``, or ``./lib`` relative to the working directory if it is not given -- never
next to the netlist, which is frequently a read-only file inside a PDK install. The
directory gets:

    <libname>_<corner>.lib   one Liberty file per corner
    char_report.md           function, truth table, arcs, unateness, pin capacitance,
                             the slews a driver actually delivered, coverage notes
    char_data.json           every measurement in SI units, for diffing runs
    decks/                   everything that was simulated -- see below

The decks are deleted on success unless ``--keep-decks`` is given, and always kept when a
run fails, since that is when they are worth reading. Under ``decks/`` there is one
directory per corner, named like the library, plus the verification decks::

    decks/<corner>/op_<cell>.spice              .op per input vector: truth table + leakage
    decks/<corner>/arc_<cell>_<pin>_<out>_<sense><state>_s<slew>[_a|_b].spice
                                                one timing/power arc, a replica per load
    decks/<corner>/cap_<cell>_<pin>.spice       input pin capacitance, a replica per state
    decks/<corner>/cal_<pin>_<sense>_<edge>_<n>.spice   --driver-cell calibration attempts
    decks/verify/<corner>/spice/tb_<cell>.spice the exhaustive functional testbench, written
                                                by gen_cell_tb.py and run before measuring
    decks/verify/<corner>/spice/tb_<cell>.plot.spice   ngspice plot script for that deck
    decks/verify/<corner>/gold_functions.md     the Liberty function used per instance, the
                                                gold equations and the truth table
    decks/verify/<cell>_wrap.v                  the one-instance wrapper handed to
                                                gen_cell_tb.py when the cell has no
                                                structural Verilog view

Every deck has its ngspice log beside it as ``<deck>.log``, starting with the command line
that produced it, and every deck directory gets a ``.spiceinit`` (see the note next to
SPICEINIT below). All of them are plain ngspice input: ``ngspice -b <deck>.spice`` in that
directory reproduces exactly what this tool measured.


The template contract  (--template, default scripts/lib_templates/sg13g2.lib.tmpl)
---------------------------------------------------------------------------------
The library-level constants of a technology live in a template file, not in this script,
so retargeting is a matter of swapping that file. A template is a Liberty ``library(){}``
skeleton with ``@TOKEN@`` placeholders. The minimum it must provide:

1. **Placeholders** ``@LIBRARY_NAME@``, ``@CELLS@`` (at library scope, where the generated
   ``cell(){}`` groups are inserted), ``@VOLTAGE@``, ``@TEMPERATURE@``, ``@INDEX_SLEW@``
   and ``@INDEX_LOAD@``. Optional, substituted when present: ``@PROCESS@``,
   ``@OPCOND_NAME@``, ``@DATE@``, ``@GENCMD@``, ``@COMMENT@``, ``@MAX_TRANSITION@``,
   ``@MAX_CAPACITANCE@``, ``@DEFAULT_INPUT_PIN_CAP@``. Any ``@TOKEN@`` left unsubstituted
   after filling is an error, so a typo cannot reach the output.
2. **Units** -- ``time_unit``, ``capacitive_load_unit``, ``voltage_unit``, ``current_unit``
   and ``leakage_power_unit``. They are read back out of the *filled* template and used to
   scale every measurement, which is taken in SI units. Change ``time_unit : "1ps"`` and
   the numbers written follow, with no code change.
3. **Thresholds** -- ``input_threshold_pct_rise/fall``, ``output_threshold_pct_rise/fall``,
   ``slew_lower_threshold_pct_rise/fall``, ``slew_upper_threshold_pct_rise/fall`` and
   ``slew_derate_from_library``. These are read back too, and they are what the ``.meas``
   statements in the generated decks are built from -- so the tables really are measured
   at the thresholds the library declares.
4. **Declarations** -- ``delay_model : table_lookup;``, an ``lu_table_template`` named by
   ``--delay-template`` with ``variable_1 : input_net_transition`` and ``variable_2 :
   total_output_net_capacitance``, and a ``power_lut_template`` named by
   ``--power-template`` with ``variable_1 : input_transition_time`` and the same
   ``variable_2``. Both must carry ``@INDEX_SLEW@`` / ``@INDEX_LOAD@``.

Everything else in the template (copyright header, wire-load models, ``default_*``
attributes) is copied through verbatim. ``--print-template`` dumps the built-in one as a
starting point for a new technology. Rise/fall thresholds are required to be equal to
each other, since one pulse measures both edges.


Method
------
*Function and leakage* -- one deck with an instance per input vector, each on its own
supply source, and a single ``.op``. Output nodes thresholded at VDD/2 give the truth
table; each supply current gives that state's leakage.

*Stimulus* -- an ideal linear ramp by default. With ``--driver-cell`` the pin is instead
driven by a real cell through a 0 V ammeter (so the input-port energy is still measured at
the cell's own pin), and the ramp into that driver is calibrated by bracketed
interpolation until the slew arriving at the pin matches the index. The samples of that
curve are shared across the whole grid, so after the first row a new target usually costs
one or two extra simulations. A driver also has a floor -- the fastest slew it can put on
this pin however hard it is driven -- which is measured once and reported per grid row it
affects (``--driver-underrun``). Because a driver's pull-up and pull-down are not equally
strong, each input edge gets its own calibration and its own deck.

*Timing and internal power* -- for every (input pin, output pin) pair the truth table
shows a dependency for, the side-input states that sensitize it are collected and split by
sense. Per (arc, sense, side state, slew) one deck is written holding a replica per output
load, each replica with its own supply source, its own copies of the input sources and its
load capacitor behind a 0 V ammeter. One input pulse gives both output edges, so a single
transient yields all four timing tables plus both switching energies. The input is a
linear ramp of ``slew / (slew_upper - slew_lower)``, so its *measured* slew is the index
value the table is built on. Results from several sensitizing states are combined
worst-case (``--combine``).

*Internal energy* is port accounting over a settled-to-settled window::

    E_internal = E_supply_in + E_input_in - E_load_out - 0.5*C*VDD^2

with each port's power integrated by a B-source. The last term is the resistive loss that
belongs to the load rather than the cell (half of ``C*VDD^2`` per edge). Subtracting the
input-port energy matters: the charge that the switching pin's gate capacitance exchanges
with the cell's own VDD rail is several fJ, comparable to the whole internal energy, and
it is already accounted for elsewhere as this cell's pin capacitance seen by its driver.
Charge-only variants of this formula are recorded in ``char_data.json`` as well, but are
not used: on a real cell they come out negative for one of the two edges.

*Input capacitance* -- charge drawn through the pin, ``C = |Q| / VDD``, per side-input
state, with the output loaded. The integration window is the input edge itself
(``--cap-window``), which is the convention the IHP libraries were built with; integrating
until the cell settles instead adds the Miller charge that arrives while the output is
still moving, worth about +30% on these cells.


How good are the numbers?  (measured, not claimed)
--------------------------------------------------
``make lib-selfcheck`` characterizes ``sg13g2_nand2_1`` out of the PDK's own SPICE and
diffs the result against the Liberty IHP ships for it, over the whole 7x7 grid. As of the
run this was written from (typ corner, both arcs):

    table              mean deviation   worst grid point
    cell_rise               4.1 - 4.4%       9.2%
    cell_fall               3.6 - 4.8%      11.3%
    rise_transition         5.4 - 5.5%      26.2%
    fall_transition         4.3 - 5.3%      17.3%
    rise_power             47   - 57%      160%
    fall_power             23   - 45%       96%
    input capacitance      -6.5% (2.70 fF vs 2.89 fF on pin A)
    leakage, per state    -1% to -38% depending on the state

Timing is good to a few percent, and the residual is a smooth function of the grid rather
than noise.

It is **not** a simulation-accuracy problem, which is the first thing to suspect. Re-running
one generated arc deck under tighter tolerances (``reltol`` down to 1e-5 with ``vntol=1e-9``,
``abstol=1e-15``, ``chgtol=1e-16``, ``trtol=1``), under Gear integration instead of
trapezoidal, and with ten times the timesteps, moves the measured delays and transitions by
**under 0.2%** in every case -- against a 3.4% gap to IHP. The whole grid re-run with
``--spice-option 'reltol=1e-5 vntol=1e-9' --spice-option 'method=gear'`` gives mean
deviations identical to the defaults. ngspice is a true SPICE here -- direct sparse solve,
full Newton-Raphson per timestep, LTE step control, real PSP103 compact models through OSDI,
none of the partitioning or table-lookup that makes a FastSPICE fast -- so it is the accurate
end of the trade, and it is not what limits this. What limits it is what goes into it.

Where the rest of it comes from is known rather than guessed --
``libs.ref/sg13g2_stdcell/doc/ReleaseNotes.txt`` says of Rev0.1.0 that the cells were
"re-characterized with updated QRC tech file and 'buf_1' active driver setting for all
input pins". So the reference was measured on a *parasitic-extracted* netlist, with every
input driven by a real ``sg13g2_buf_1`` cell. This tool uses the netlist it is handed and
an ideal linear ramp. Both differences were measured on ``sg13g2_nand2_1``:

* **netlist.** Characterizing the PDK's schematic netlist, a Magic device-only extraction
  (layout-derived shared-diffusion junctions, no wiring caps) and a full Magic RC
  extraction gives mean delay deviations of 3.6-4.8%, 3.6-4.6% and 4.1-5.4%, with worst
  grid points of 11%, 7-10% and 17-20%. The shipped schematic netlist is pessimistic --
  it gives every device a full-size drain *and* source -- and full Magic extraction
  overshoots; the reference sits between the two, which is where a QRC extraction would.
* **stimulus.** ``--driver-cell`` implements the second half: the pin under test is driven
  by a real cell, with the ramp into *that* calibrated per edge until the slew arriving at
  the pin matches the grid index. Measured on ``sg13g2_nand2_1`` with ``sg13g2_buf_1``, it
  reproduces IHP's tables **worse**, not better: mean delay deviation goes from 3.6-4.8% to
  21-25%, because the delivered waveform is not a ramp. To put a 2.5 ns 20-80 slew on the
  pin, a buffer has to be driven so slowly that its output becomes an S-curve which is far
  steeper than a linear ramp around the 50% crossing -- and the cell responds to the
  crossing, not to the 20-80 time. Delays come out roughly half of the ideal-ramp ones at
  the slow end of the grid. The 20-80 slew simply does not describe a real driver's
  waveform, which is the whole reason CCS and ECSM exist. IHP's tables sit close to the
  ideal-ramp numbers, so whatever their "active driver setting" does, the waveform it puts
  on the pin behaves much more like a ramp than like a raw buffer output. The ideal ramp
  therefore stays the default here, and ``--driver-cell`` is offered for flows that want a
  real driver in the loop rather than as an accuracy improvement.

Internal power is an estimate, and is reported as such. The total switching energy per
cycle comes out around 1.4-1.5x IHP's, and that ratio survives *both* corrections above:
the device-only extraction moves ``fall_power`` from 45% to 28% mean deviation but leaves
``rise_power`` at 47%, and the active driver merely swaps energy between the two edges
(3.28/2.83 fJ instead of 2.65/3.62 fJ, total unchanged). So what is left is an accounting
convention, not a setup difference, and it lives in how much of the gate-coupling charge
-- the charge the switching pin's gate exchanges with the cell's own VDD rail, worth
several fJ here -- is charged to the cell rather than to its driver. Nobody agrees on
this: lctime adds the full input-port energy and subtracts no load energy at all (see
"Why not lctime?"), and its own source carries both a "TODO: what unit does rise_power
have... is it really power or energy?" and a warning for the negative energies that
convention produces.

The same boundary was found, and closed, on the input capacitance. Integrating the pin
charge until the cell has settled collects the Miller charge that keeps flowing after the
input edge is over, while the output is still switching, and gives 3.75 fF on
``sg13g2_inv_1``; integrating over the input transition only gives 2.99 fF, against IHP's
2.87 fF. So the reference counts the pin charge over the input edge, and this tool now
does too (``--cap-window ramp``, the default, with ``--cap-slew`` defaulting to the fastest
grid point -- with a slow input the output finishes switching while the input is still
ramping and the distinction disappears). That moved pin A of ``sg13g2_nand2_1`` from +30%
to -6.5%. ``--cap-window settled`` gives the physically complete charge a driver has to
supply, which is the more honest number in isolation but does not match how the libraries
it will sit next to were built.

That boundary is worth about 0.76 fF here, or 1.1 fJ at this supply -- which is the size of
the internal-energy excess as well, and is why the two are described as one finding. It
does not fix ``internal_power`` though: the leftover energy has to be attributed to one of
the two edges, and no single window choice reproduces IHP's split.

Anything that depends on a reference library can be re-measured for any cell with
``--compare-lib``; do not take the table above on trust when the cell or the PDK changes.

Other limitations, stated rather than hidden: NLDM only (no CCS/ECSM); combinational cells
only -- a cell with internal state is detected as a non-resolvable truth table and
refused; the stimulus is a linear ramp rather than a real driver waveform;
``max_transition`` / ``max_capacitance`` are taken from the grid rather than derived from
a degradation criterion; one load model per output.


Why not lctime?
---------------
The container ships lctime, which does this job. It cannot be used on this PDK for the
same reason `gen_cell_tb.py` documents for ``sp2bool``: ``lccommon/net_util.py::
get_channel_type()`` calls a device NMOS only when its model name starts with ``n``, and
IHP's models are ``sg13_lv_nmos`` / ``sg13_lv_pmos``, so every transistor is taken to be a
PMOS. Two further differences came out of reading its source, both of which this tool
deliberately does otherwise:

* ``characterization/timing_combinatorial.py`` builds its stimulus as
  ``StepWave(rise_threshold=0, fall_threshold=1, transition_time=input_transition_time)``,
  which spans the *whole* swing in the index value -- so the measured 20-80 slew of the
  stimulus is only 0.6 of the number the table is indexed by. Liberty defines
  ``input_net_transition`` between the library's slew thresholds, which is what
  ``--input-ramp measured`` (the default) does. Running the calibration with
  ``--input-ramp full`` to imitate lctime moves the mean delay deviation from 3.6-4.8% to
  13-16%, so the reference library agrees with the Liberty reading, not with lctime's.
* its switching energy is ``supply_energy + gate_energy`` with no load term at all, so its
  ``rise_power`` grows with the load capacitance -- which the shipped tables plainly do not
  do (they are nearly flat in load, which is only possible if the load energy is removed).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aion_char import tb_generator as tb

SCRIPT = Path(__file__).name
DEFAULT_TEMPLATE = Path(__file__).resolve().parent / "lib_templates" / "sg13g2.lib.tmpl"

# The PDK's own grid, so a library generated here can be read next to IHP's in one STA run.
DEFAULT_SLEWS_NS = "0.0186, 0.0966, 0.174, 0.3294, 0.6408, 1.263, 2.5074"
DEFAULT_LOADS_PF = "0.001, 0.0234, 0.039, 0.0648, 0.108, 0.18, 0.3"
DEFAULT_CORNERS = [
    "typ:mos_tt:1.20:25",
    "slow:mos_ss:1.08:125",
    "fast:mos_ff:1.32:-40",
]


class CharError(Exception):
    """Fatal, user-facing characterization error."""


def _n(x: float) -> str:
    """A float as SPICE sees it: no unit suffixes, enough digits to round-trip."""
    return f"{x:.12g}"


def _v(x: float) -> str:
    """A float as Liberty sees it."""
    return f"{x:.6g}"


# --------------------------------------------------------------------------------------
# The Liberty template
# --------------------------------------------------------------------------------------


@dataclass
class Units:
    """SI value of one library unit, for every unit the emitted numbers use."""

    time: float
    cap: float
    volt: float
    curr: float
    leak: float
    energy: float


@dataclass
class Thresholds:
    """Measurement thresholds, as fractions of VDD."""

    input_pct: float
    output_pct: float
    slew_lower: float
    slew_upper: float
    derate: float


_RE_ATTR = re.compile(r'^\s*([a-z_0-9]+)\s*:\s*"?([^";]+?)"?\s*;', re.M)
_RE_CAP_UNIT = re.compile(r"^\s*capacitive_load_unit\s*\(\s*([\d.eE+-]+)\s*,\s*(\w+)\s*\)", re.M)
_RE_UNIT_VAL = re.compile(r"^\s*([\d.eE+-]+)\s*([a-zA-Z]+)\s*$")

_SI_PREFIX = {
    "": 1.0, "k": 1e3, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15, "a": 1e-18,
}

# A /* ... */ block carrying this marker documents the template itself and is dropped when
# the template is rendered, so it does not end up in every generated library.
TEMPLATE_DOC = "TEMPLATE-DOC"
_RE_TEMPLATE_DOC = re.compile(r"/\*(?:(?!\*/).)*?" + TEMPLATE_DOC + r"(?:(?!\*/).)*?\*/\s*", re.S)


def _si_unit(text: str, base: str, what: str) -> float:
    """Turn a Liberty unit string such as ``1ns``, ``1uA`` or ``1pW`` into its SI value."""
    m = _RE_UNIT_VAL.match(text.strip())
    if not m:
        raise CharError(f"template: cannot read {what} from {text!r} (expected e.g. '1ns')")
    mult, suffix = float(m.group(1)), m.group(2).lower()
    if not suffix.endswith(base):
        raise CharError(f"template: {what} {text!r} is not in units of '{base}'")
    prefix = suffix[: -len(base)]
    if prefix not in _SI_PREFIX:
        raise CharError(f"template: unknown unit prefix {prefix!r} in {text!r} ({what})")
    return mult * _SI_PREFIX[prefix]


REQUIRED_TOKENS = ["LIBRARY_NAME", "CELLS", "VOLTAGE", "TEMPERATURE", "INDEX_SLEW", "INDEX_LOAD"]


@dataclass
class Template:
    """A Liberty skeleton plus the constants read back out of it."""

    path: Path
    text: str
    units: Units
    thresholds: Thresholds
    delay_template: str
    power_template: str

    @staticmethod
    def load(path: Path, delay_template: str, power_template: str, energy_unit: str) -> "Template":
        if not path.is_file():
            raise CharError(f"Liberty template not found: {path}")
        text = path.read_text()

        missing = [t for t in REQUIRED_TOKENS if f"@{t}@" not in text]
        if missing:
            raise CharError(
                f"{path}: template is missing required placeholder(s) "
                + ", ".join(f"@{t}@" for t in missing)
                + "\n  See 'The template contract' in "
                + SCRIPT
                + " (--print-template dumps a working one)."
            )

        attrs = dict(_RE_ATTR.findall(text))
        need = [
            "delay_model", "time_unit", "voltage_unit", "current_unit", "leakage_power_unit",
            "input_threshold_pct_rise", "input_threshold_pct_fall",
            "output_threshold_pct_rise", "output_threshold_pct_fall",
            "slew_lower_threshold_pct_rise", "slew_lower_threshold_pct_fall",
            "slew_upper_threshold_pct_rise", "slew_upper_threshold_pct_fall",
            "slew_derate_from_library",
        ]
        absent = [a for a in need if a not in attrs]
        if absent:
            raise CharError(
                f"{path}: template does not declare {', '.join(absent)}.\n"
                "  These are read back out of the template and used to scale the measurements "
                "and to place the .meas thresholds, so they cannot be defaulted."
            )
        if attrs["delay_model"].strip() != "table_lookup":
            raise CharError(
                f"{path}: delay_model is {attrs['delay_model']!r}; this generator writes NLDM "
                "tables, so it must be 'table_lookup'"
            )

        m = _RE_CAP_UNIT.search(text)
        if not m:
            raise CharError(f"{path}: template does not declare capacitive_load_unit (x, unit)")
        suffix = m.group(2).lower()
        if not suffix.endswith("f") or suffix[:-1] not in _SI_PREFIX:
            raise CharError(f"{path}: capacitive_load_unit {suffix!r} is not a capacitance")
        cap = float(m.group(1)) * _SI_PREFIX[suffix[:-1]]

        volt = _si_unit(attrs["voltage_unit"], "v", "voltage_unit")
        units = Units(
            time=_si_unit(attrs["time_unit"], "s", "time_unit"),
            cap=cap,
            volt=volt,
            curr=_si_unit(attrs["current_unit"], "a", "current_unit"),
            leak=_si_unit(attrs["leakage_power_unit"], "w", "leakage_power_unit"),
            # Liberty's own derived power unit (V*A) times the time unit would give an energy
            # unit that no shipped library actually uses; every one of them expresses internal
            # energy in capacitance*voltage^2. Overridable with --energy-unit.
            energy=(cap * volt * volt if energy_unit == "auto" else float(energy_unit)),
        )

        def pct(base: str) -> float:
            r, f = float(attrs[f"{base}_rise"]), float(attrs[f"{base}_fall"])
            if r != f:
                raise CharError(
                    f"{path}: {base}_rise ({r}) and {base}_fall ({f}) differ; this generator "
                    "measures both edges from one pulse and needs them equal"
                )
            return r / 100.0

        th = Thresholds(
            input_pct=pct("input_threshold_pct"),
            output_pct=pct("output_threshold_pct"),
            slew_lower=pct("slew_lower_threshold_pct"),
            slew_upper=pct("slew_upper_threshold_pct"),
            derate=float(attrs["slew_derate_from_library"]),
        )
        if th.derate != 1.0:
            raise CharError(
                f"{path}: slew_derate_from_library is {th.derate}; only 1 is supported "
                "(the tables are written at the thresholds the library declares)"
            )

        for name, kind, v1 in (
            (delay_template, "lu_table_template", "input_net_transition"),
            (power_template, "power_lut_template", "input_transition_time"),
        ):
            body = _group_body(text, kind, name)
            if body is None:
                raise CharError(f"{path}: no {kind} ({name}) -- see --delay-template/--power-template")
            if f"variable_1 : {v1}" not in body.replace("  ", " "):
                raise CharError(f"{path}: {kind} ({name}) must have 'variable_1 : {v1}'")
            if "variable_2 : total_output_net_capacitance" not in body.replace("  ", " "):
                raise CharError(
                    f"{path}: {kind} ({name}) must have "
                    "'variable_2 : total_output_net_capacitance'"
                )
            if "@INDEX_SLEW@" not in body or "@INDEX_LOAD@" not in body:
                raise CharError(
                    f"{path}: {kind} ({name}) must take its indices from @INDEX_SLEW@ and "
                    "@INDEX_LOAD@, so the grid comes from the command line"
                )

        return Template(path, text, units, th, delay_template, power_template)

    def render(self, **tokens: str) -> str:
        return tb.fill(_RE_TEMPLATE_DOC.sub("", self.text), **tokens)


def _group_body(text: str, kind: str, name: str) -> str | None:
    """The body of ``<kind> (<name>) { ... }``, by brace counting."""
    m = re.search(rf"\b{re.escape(kind)}\s*\(\s*{re.escape(name)}\s*\)\s*\{{", text)
    if not m:
        return None
    depth, i = 1, m.end()
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[m.end() : i - 1]


# --------------------------------------------------------------------------------------
# Corners
# --------------------------------------------------------------------------------------


@dataclass
class Corner:
    name: str
    section: str
    vdd: float
    temp: float

    @staticmethod
    def parse(spec: str) -> "Corner":
        parts = spec.split(":")
        if len(parts) != 4:
            raise CharError(
                f"--corner {spec!r}: expected NAME:SECTION:VDD:TEMP, e.g. typ:mos_tt:1.20:25 "
                "(SECTION may be empty to .include the whole model file)"
            )
        try:
            return Corner(parts[0], parts[1], float(parts[2]), float(parts[3]))
        except ValueError as exc:
            raise CharError(f"--corner {spec!r}: {exc}") from None

    @property
    def tag(self) -> str:
        """The PDK's own file-name convention: typ_1p20V_25C, slow_1p08V_125C, ..."""
        v = f"{self.vdd:.2f}".replace(".", "p")
        t = f"{self.temp:g}".replace("-", "m")
        return f"{self.name}_{v}V_{t}C"


# --------------------------------------------------------------------------------------
# The cell under characterization
# --------------------------------------------------------------------------------------


@dataclass
class CharCell:
    name: str
    inputs: list[str]
    outputs: list[str]
    power: str
    ground: str
    ports: list[str]
    area: float = 0.0
    footprint: str = ""

    def instance(self, tag: str, conns: dict[str, str]) -> str:
        """One X-line, positional, following the .subckt's own port order."""
        pins = []
        for p in self.ports:
            key = next((k for k in conns if k.upper() == p.upper()), None)
            if key is None:
                raise CharError(
                    f"cell '{self.name}': .subckt pin '{p}' is neither an input, an output "
                    "nor a supply; name it with --inputs/--outputs/--power/--ground"
                )
            pins.append(conns[key])
        return f"X{tag} " + " ".join(pins) + f" {self.name}"


@dataclass
class Driver:
    """A real cell used as the stimulus for the pin under test (``--driver-cell``).

    Nothing about it is built in: the cell name, which of its pins is the input and which
    the output, and where its supplies go all come from the command line, because a SPICE
    ``.subckt`` says none of it.
    """

    cell: str
    in_pin: str
    out_pin: str
    power: str
    ground: str
    ports: list[str]

    def instance(self, tag: str, out_node: str, in_node: str, sup: str, gnd: str) -> str:
        conns = {
            self.out_pin: out_node, self.in_pin: in_node, self.power: sup, self.ground: gnd
        }
        pins = []
        for p in self.ports:
            key = next((k for k in conns if k.upper() == p.upper()), None)
            if key is None:
                raise CharError(
                    f"driver cell '{self.cell}': pin '{p}' is not named by --driver-input, "
                    "--driver-output, --driver-power or --driver-ground"
                )
            pins.append(conns[key])
        return f"Xdrv{tag} " + " ".join(pins) + f" {self.cell}"


@dataclass
class Ctx:
    """Everything a deck needs that is not the cell itself."""

    vdd: float
    temp: float
    models: str
    includes: list[str]
    th: Thresholds
    settle: float
    corner: Corner
    input_ramp: str = "measured"
    driver: Driver | None = None
    options: list[str] = field(default_factory=list)

    @property
    def vth_in(self) -> float:
        return self.vdd * self.th.input_pct

    @property
    def vth_out(self) -> float:
        return self.vdd * self.th.output_pct

    def ramp_of(self, slew: float) -> float:
        """Full 0->VDD ramp time for a grid point whose index value is `slew`.

        Which is a convention, not a fact, and characterizers disagree:

        ``measured`` (default) makes the *measured* lower..upper transition of the stimulus
        equal the index value, so a 20/80 library with an index of 18.6 ps is driven by a
        31 ps full-swing ramp. This is what Liberty's definition of ``input_net_transition``
        asks for, with ``slew_derate_from_library`` at 1.

        ``full`` drives a full-swing ramp of exactly the index value, so the measured 20-80
        slew is only 0.6 of it. lctime does this (``StepWave`` with rise_threshold=0 and
        fall_threshold=1 spans the whole swing in ``input_transition_time``), and a vendor
        library characterized that way is driven ~1.7x more steeply than its index claims.
        Use it to reproduce such a library rather than to build a correct one.
        """
        if self.input_ramp == "full":
            return slew
        span = self.th.slew_upper - self.th.slew_lower
        if span <= 0:
            raise CharError("slew upper threshold must be above the lower threshold")
        return slew / span

    def hold_of(self, ramp: float, cload: float) -> float:
        """Settling allowance before the next edge.

        An estimate, not a guarantee: it assumes a roughly minimum-strength cell, so a
        deliberately weak one will not have settled. That is why every deck measures its
        own output at the end of each window and the runner simply doubles the allowance
        and re-runs when the check fails, rather than trusting this formula.
        """
        return self.settle * (5.0 * ramp + 1e-9 + 3e-8 * (cload / 1e-12))

    def tmax_of(self, ramp: float, tstop: float) -> float:
        """Ceiling on the internal timestep.

        Measured against a reference run with a 100x finer step on sg13g2_nand2_1,
        ramp/30 reproduces delays and transitions to within 0.1% and the switching charge
        to 0.05%, while ramp/3 is already 2.5% out on the transitions. The second term
        keeps a long settling window from turning into millions of timesteps.
        """
        return max(ramp / 30.0, tstop / 2e5)


# --------------------------------------------------------------------------------------
# Deck emitters
# --------------------------------------------------------------------------------------


def deck_header(what: str, ctx: Ctx) -> list[str]:
    return [
        "* SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1",
        f"* AUTO-GENERATED by scripts/{SCRIPT} -- do not edit.",
        f"* {what}",
        f"* corner {ctx.corner.name}: section={ctx.corner.section or '(none)'}, "
        f"VDD={_n(ctx.vdd)} V, T={_n(ctx.temp)} C",
        "",
        ctx.models,
        *ctx.includes,
        "",
        *[f".options {o}" for o in ctx.options],
        f".temp {_n(ctx.temp)}",
        "",
    ]


def emit_op_deck(cell: CharCell, ctx: Ctx) -> tuple[str, dict]:
    """Truth table and per-state leakage: one instance per input vector, one .op."""
    ni = len(cell.inputs)
    nvec = 1 << ni
    L = deck_header(f"{cell.name}: truth table and per-state leakage ({nvec} vectors)", ctx)
    vectors = []
    for v in range(nvec):
        bits = [(v >> b) & 1 for b in range(ni)]
        conns = {cell.power: f"sup_{v}", cell.ground: "0"}
        for b, sig in enumerate(cell.inputs):
            node = f"i_{v}_{b}"
            conns[sig] = node
            L.append(f"V{node} {node} 0 {_n(ctx.vdd) if bits[b] else '0'}")
        for o in cell.outputs:
            conns[o] = f"o_{v}_{o}"
        L.append(f"Vsup_{v} sup_{v} 0 {_n(ctx.vdd)}")
        L.append(cell.instance(str(v), conns))
        L.append("")
        vectors.append(
            {
                "vec": v,
                "bits": bits,
                "outputs": {o: f"v(o_{v}_{o})".lower() for o in cell.outputs},
                "supply": f"i(vsup_{v})",
            }
        )
    L.append(".control")
    L.append("op")
    for e in vectors:
        for expr in e["outputs"].values():
            L.append(f"print {expr}")
        L.append(f"print {e['supply']}")
    L.append(".endc")
    L.append(".end")
    return "\n".join(L) + "\n", {"kind": "op", "vectors": vectors}


def emit_arc_deck(
    cell: CharCell,
    ctx: Ctx,
    pin: str,
    out: str,
    side: dict[str, int],
    edge_a_output: str,
    slew: float,
    loads: list[float],
    other_load: float,
    drive_ramp: float | None = None,
) -> tuple[str, dict]:
    """One timing/power arc at one input slew, with a replica per output load.

    One pulse on `pin` gives both output edges. Every replica has its own supply source,
    its own copies of *all* input sources, and its load behind a 0 V ammeter, so each
    port's power can be integrated per replica.

    With ``--driver-cell``, `drive_ramp` is the ramp into the *driver*, calibrated so that
    the waveform arriving at `pin` has the wanted slew; the pin is then fed through the
    driver and a 0 V ammeter, so the input-port energy is still measured at the cell's own
    pin. Without it the pin is driven by an ideal ramp of ``ctx.ramp_of(slew)``.
    """
    ramp = ctx.ramp_of(slew)
    src_ramp = ramp if drive_ramp is None else drive_ramp
    hold = ctx.hold_of(max(ramp, src_ramp), max(loads))
    t0 = max(ramp, src_ramp, 1e-10)
    t1 = t0 + src_ramp + hold
    t2 = t1 + src_ramp + hold
    tstop = t2 + hold
    tmax = ctx.tmax_of(min(ramp, src_ramp), tstop)
    sidetxt = ", ".join(f"{k}={v}" for k, v in sorted(side.items())) or "none"

    L = deck_header(
        f"{cell.name}: arc {pin} -> {out} at slew {_n(slew)} s, side inputs {{{sidetxt}}}"
        + (f", driven by {ctx.driver.cell}" if ctx.driver else ""),
        ctx,
    )
    points = []
    for k, cl in enumerate(loads):
        conns = {cell.power: f"sup_{k}", cell.ground: "0", pin: f"sw_{k}"}
        L.append(f"* ---- replica {k}: load {_n(cl)} F ----")
        pulse = (
            f"PWL(0 0 {_n(t0)} 0 {_n(t0 + src_ramp)} {_n(ctx.vdd)} "
            f"{_n(t1)} {_n(ctx.vdd)} {_n(t1 + src_ramp)} 0)"
        )
        if ctx.driver is None:
            L.append(f"Vsw_{k} sw_{k} 0 {pulse}")
            # An ideal source reads negative current when it supplies, hence the sign.
            in_term = f"-v(sw_{k})*i(vsw_{k})"
        else:
            # The driver gets its own supply so the DUT's supply current stays clean, and
            # its output reaches the pin through a 0 V ammeter so the energy crossing the
            # cell's own pin is still what gets measured.
            L.append(f"Vsrc_{k} src_{k} 0 {pulse}")
            L.append(f"Vdsup_{k} dsup_{k} 0 {_n(ctx.vdd)}")
            L.append(ctx.driver.instance(str(k), f"dsw_{k}", f"src_{k}", f"dsup_{k}", "0"))
            L.append(f"Vg_{k} dsw_{k} sw_{k} 0")
            # This ammeter's + terminal faces the driver, so current into the cell is
            # positive -- the opposite sign convention to the source above.
            in_term = f"v(sw_{k})*i(vg_{k})"
        for j, (sig, val) in enumerate(sorted(side.items())):
            node = f"s_{k}_{j}"
            conns[sig] = node
            L.append(f"V{node} {node} 0 {_n(ctx.vdd) if val else '0'}")
        for o in cell.outputs:
            conns[o] = f"o_{k}" if o == out else f"oo_{k}_{o}"
        L.append(f"Vsup_{k} sup_{k} 0 {_n(ctx.vdd)}")
        L.append(cell.instance(str(k), conns))
        L.append(f"Vl_{k} o_{k} c_{k} 0")
        L.append(f"Cl_{k} c_{k} 0 {_n(cl)}")
        for o in cell.outputs:
            if o != out:
                L.append(f"Coo_{k}_{o} oo_{k}_{o} 0 {_n(other_load)}")
        # Port powers, signed so that positive means "into the cell".
        side_terms = [f"v(s_{k}_{j})*i(vs_{k}_{j})" for j in range(len(side))]
        in_expr = in_term + ("".join(f" - {t}" for t in side_terms))
        L.append(f"Bps_{k} ps_{k} 0 V = -{_n(ctx.vdd)}*i(vsup_{k})")
        L.append(f"Bpi_{k} pi_{k} 0 V = {in_expr}")
        L.append(f"Bpo_{k} po_{k} 0 V = v(o_{k})*i(vl_{k})")
        L.append("")
        points.append(
            {
                "load": cl,
                "load_index": k,
                "meas": {q: f"{q}_{k}" for q in (
                    "da", "db", "sa", "sb", "esa", "esb", "eia", "eib", "eoa", "eob",
                    "qsa", "qsb", "qla", "qlb", "va", "vb", "iq0", "iq1", "iq2",
                )},
            }
        )

    nk = len(loads)
    save = [f"v(o_{k})" for k in range(nk)] + [f"v(sw_{k})" for k in range(nk)]
    save += [f"v(ps_{k}) v(pi_{k}) v(po_{k})" for k in range(nk)]
    save += [f"i(vsup_{k}) i(vl_{k})" for k in range(nk)]
    L.append(".save " + " ".join(save))
    L.append(f".tran {_n(tmax)} {_n(tstop)} 0 {_n(tmax)}")
    L.append("")

    up, dn = ("RISE", "FALL") if edge_a_output == "rise" else ("FALL", "RISE")
    lo_v, hi_v = ctx.vdd * ctx.th.slew_lower, ctx.vdd * ctx.th.slew_upper
    for k in range(nk):
        o, w = f"o_{k}", (_n(t0), _n(t1), _n(t2))
        L.append(f"* ---- replica {k} ----")
        L.append(
            f".meas tran da_{k} TRIG v(sw_{k}) VAL={_n(ctx.vth_in)} RISE=1 "
            f"TARG v({o}) VAL={_n(ctx.vth_out)} {up}=1"
        )
        L.append(
            f".meas tran db_{k} TRIG v(sw_{k}) VAL={_n(ctx.vth_in)} FALL=1 "
            f"TARG v({o}) VAL={_n(ctx.vth_out)} {dn}=1"
        )
        if edge_a_output == "rise":
            L.append(f".meas tran sa_{k} TRIG v({o}) VAL={_n(lo_v)} RISE=1 "
                     f"TARG v({o}) VAL={_n(hi_v)} RISE=1")
            L.append(f".meas tran sb_{k} TRIG v({o}) VAL={_n(hi_v)} FALL=1 "
                     f"TARG v({o}) VAL={_n(lo_v)} FALL=1")
        else:
            L.append(f".meas tran sa_{k} TRIG v({o}) VAL={_n(hi_v)} FALL=1 "
                     f"TARG v({o}) VAL={_n(lo_v)} FALL=1")
            L.append(f".meas tran sb_{k} TRIG v({o}) VAL={_n(lo_v)} RISE=1 "
                     f"TARG v({o}) VAL={_n(hi_v)} RISE=1")
        for q, node in (("es", f"ps_{k}"), ("ei", f"pi_{k}"), ("eo", f"po_{k}")):
            L.append(f".meas tran {q}a_{k} INTEG v({node}) FROM={w[0]} TO={w[1]}")
            L.append(f".meas tran {q}b_{k} INTEG v({node}) FROM={w[1]} TO={w[2]}")
        L.append(f".meas tran qsa_{k} INTEG i(vsup_{k}) FROM={w[0]} TO={w[1]}")
        L.append(f".meas tran qsb_{k} INTEG i(vsup_{k}) FROM={w[1]} TO={w[2]}")
        L.append(f".meas tran qla_{k} INTEG i(vl_{k}) FROM={w[0]} TO={w[1]}")
        L.append(f".meas tran qlb_{k} INTEG i(vl_{k}) FROM={w[1]} TO={w[2]}")
        L.append(f".meas tran va_{k} FIND v({o}) AT={_n(t1 - tmax)}")
        L.append(f".meas tran vb_{k} FIND v({o}) AT={_n(t2 - tmax)}")
        L.append(f".meas tran iq0_{k} FIND i(vsup_{k}) AT={_n(t0 - tmax)}")
        L.append(f".meas tran iq1_{k} FIND i(vsup_{k}) AT={_n(t1 - tmax)}")
        L.append(f".meas tran iq2_{k} FIND i(vsup_{k}) AT={_n(t2 - tmax)}")
        L.append("")
    L.append(".end")

    return "\n".join(L) + "\n", {
        "kind": "arc",
        "pin": pin,
        "output": out,
        "side": side,
        "edge_a_output": edge_a_output,
        "slew": slew,
        "ramp": ramp,
        "window_a": t1 - t0,
        "window_b": t2 - t1,
        "points": points,
    }


def emit_cal_deck(
    cell: CharCell, ctx: Ctx, pin: str, side: dict[str, int], src_ramp: float, cload: float
) -> tuple[str, dict]:
    """One driver + one cell instance, to find out what slew reaches the cell's pin.

    Used only to calibrate ``--driver-cell``: the answer depends on the cell's input
    capacitance in this side-input state and on the Miller feedback from its output, so it
    has to be measured on the real thing rather than computed.
    """
    assert ctx.driver is not None
    hold = ctx.hold_of(src_ramp, cload)
    t0 = max(src_ramp, 1e-10)
    t1 = t0 + src_ramp + hold
    t2 = t1 + src_ramp + hold
    tstop = t2 + hold
    tmax = ctx.tmax_of(src_ramp, tstop)
    lo_v, hi_v = ctx.vdd * ctx.th.slew_lower, ctx.vdd * ctx.th.slew_upper

    L = deck_header(f"{cell.name}: driver calibration for pin {pin}", ctx)
    conns = {cell.power: "sup", cell.ground: "0", pin: "sw"}
    L.append(
        f"Vsrc src 0 PWL(0 0 {_n(t0)} 0 {_n(t0 + src_ramp)} {_n(ctx.vdd)} "
        f"{_n(t1)} {_n(ctx.vdd)} {_n(t1 + src_ramp)} 0)"
    )
    L.append(f"Vdsup dsup 0 {_n(ctx.vdd)}")
    L.append(ctx.driver.instance("0", "sw", "src", "dsup", "0"))
    for j, (sig, val) in enumerate(sorted(side.items())):
        conns[sig] = f"s_{j}"
        L.append(f"Vs_{j} s_{j} 0 {_n(ctx.vdd) if val else '0'}")
    for o in cell.outputs:
        conns[o] = f"o_{o}"
    L.append(f"Vsup sup 0 {_n(ctx.vdd)}")
    L.append(cell.instance("0", conns))
    for o in cell.outputs:
        L.append(f"Co_{o} o_{o} 0 {_n(cload)}")
    L.append("")
    L.append(".save v(sw)")
    L.append(f".tran {_n(tmax)} {_n(tstop)} 0 {_n(tmax)}")
    L.append(f".meas tran sr TRIG v(sw) VAL={_n(lo_v)} RISE=1 TARG v(sw) VAL={_n(hi_v)} RISE=1")
    L.append(f".meas tran sf TRIG v(sw) VAL={_n(hi_v)} FALL=1 TARG v(sw) VAL={_n(lo_v)} FALL=1")
    L.append(".end")
    return "\n".join(L) + "\n", {"kind": "cal", "pin": pin, "src_ramp": src_ramp}


class DriverCal:
    """Solves "which ramp into the driver puts `target` slew on the pin", with memory.

    The map from the driver's input ramp to the slew arriving at the pin is one smooth
    monotone curve per (cell, pin, side state, edge). Every sample of it is a simulation, so
    they are kept and shared: the seven grid rows of one arc walk the same curve, and after
    the first row a new target usually needs one or two more points. Samples are also what
    makes the driver's *floor* -- the fastest slew it can deliver into this pin, however
    hard it is driven -- a one-off measurement instead of a per-row one.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._samples: dict[tuple, list[tuple[float, float]]] = {}

    def _add(self, key, ramp: float, slew: float) -> None:
        with self._lock:
            pts = self._samples.setdefault(key, [])
            pts.append((ramp, slew))
            pts.sort()

    def _get(self, key) -> list[tuple[float, float]]:
        with self._lock:
            return list(self._samples.get(key, []))

    def solve(self, args, ctx, cell, pin, side, target, edge, workdir, tag):
        key = (cell.name, pin, tuple(sorted(side.items())), edge, ctx.corner.tag)
        meas = "sr" if edge == "rise" else "sf"
        cal_load = args.driver_cal_load * args.units_cap
        evals = [0]

        def slew_at(src_ramp: float) -> float:
            for r, s in self._get(key):
                if abs(r - src_ramp) <= 1e-18:
                    return s
            evals[0] += 1
            text, _ = emit_cal_deck(cell, ctx, pin, side, src_ramp, cal_load)
            deck = workdir / f"cal_{tag}_{evals[0]}.spice"
            deck.write_text(text)
            slew = need(run_deck(args.ngspice, deck, args.timeout), meas)
            self._add(key, src_ramp, slew)
            return slew

        floor = slew_at(args.driver_min_ramp)
        if floor >= target * (1 - args.driver_tol):
            note = (
                f"{cell.name} pin {pin} {edge} edge, target slew {target:.4g} s: the driver "
                f"'{ctx.driver.cell}' cannot deliver less than {floor:.4g} s into this pin, so "
                "that grid row was characterized at the floor"
            )
            if args.driver_underrun == "error":
                raise CharError(
                    note + ".\n  Use a stronger --driver-cell, drop the fastest --slews "
                    "entries, or pass --driver-underrun note to characterize at the floor."
                )
            return args.driver_min_ramp, floor, note

        # Bracket the target, extending the sampled range only if it does not already cover it.
        pts = self._get(key)
        hi = next((r for r, s in pts if s >= target), None)
        if hi is None:
            hi = max(ctx.ramp_of(target), max(r for r, _ in pts))
            for _ in range(8):
                if slew_at(hi) >= target:
                    break
                hi *= 2.0
            else:
                raise CharError(
                    f"{cell.name} pin {pin}: a slew of {target:.4g} s never arrives at the pin, "
                    f"even with a {hi:.4g} s ramp into '{ctx.driver.cell}'"
                )

        # Regula falsi on the samples: the curve is close to affine away from the floor, so
        # interpolating between the two bracketing points converges in a couple of steps.
        for it in range(args.driver_max_iter):
            pts = self._get(key)
            below = [(r, s) for r, s in pts if s <= target]
            above = [(r, s) for r, s in pts if s > target]
            best = min(pts, key=lambda p: abs(p[1] - target))
            if abs(best[1] - target) <= args.driver_tol * target or not (below and above):
                break
            r0, s0 = max(below)
            r1, s1 = min(above)
            # Alternate interpolation with bisection: pure regula falsi keeps one end of the
            # bracket fixed on a curved function and can crawl.
            if it % 2 or s1 == s0:
                nxt = 0.5 * (r0 + r1)
            else:
                nxt = r0 + (r1 - r0) * (target - s0) / (s1 - s0)
                nxt = min(max(nxt, r0 + 0.05 * (r1 - r0)), r1 - 0.05 * (r1 - r0))
            slew_at(nxt)

        best = min(self._get(key), key=lambda p: abs(p[1] - target))
        note = None
        if abs(best[1] - target) > args.driver_tol * target:
            note = (
                f"{cell.name} pin {pin} {edge} edge: the slew at the pin settled at "
                f"{best[1]:.4g} s against a target of {target:.4g} s"
            )
        return best[0], best[1], note


def emit_cap_deck(
    cell: CharCell, ctx: Ctx, pin: str, states: list[dict[str, int]], slew: float, cload: float
) -> tuple[str, dict]:
    """Input pin capacitance: charge through the pin over a settled 0 -> VDD -> 0 swing."""
    ramp = ctx.ramp_of(slew)
    hold = ctx.hold_of(ramp, cload)
    t0 = max(ramp, 1e-10)
    t1 = t0 + ramp + hold
    t2 = t1 + ramp + hold
    tstop = t2 + hold
    tmax = ctx.tmax_of(ramp, tstop)

    L = deck_header(f"{cell.name}: input capacitance of pin {pin}", ctx)
    entries = []
    for k, st in enumerate(states):
        conns = {cell.power: f"sup_{k}", cell.ground: "0", pin: f"p_{k}"}
        L.append(f"* ---- state {{{', '.join(f'{s}={v}' for s, v in sorted(st.items())) or 'none'}}}")
        L.append(f"Vsup_{k} sup_{k} 0 {_n(ctx.vdd)}")
        L.append(
            f"Vp_{k} p_{k} 0 PWL(0 0 {_n(t0)} 0 {_n(t0 + ramp)} {_n(ctx.vdd)} "
            f"{_n(t1)} {_n(ctx.vdd)} {_n(t1 + ramp)} 0)"
        )
        for j, (sig, val) in enumerate(sorted(st.items())):
            node = f"s_{k}_{j}"
            conns[sig] = node
            L.append(f"V{node} {node} 0 {_n(ctx.vdd) if val else '0'}")
        for o in cell.outputs:
            conns[o] = f"o_{k}_{o}"
        L.append(cell.instance(str(k), conns))
        for o in cell.outputs:
            L.append(f"Co_{k}_{o} o_{k}_{o} 0 {_n(cload)}")
        L.append("")
        entries.append(
            {
                "state": st,
                "meas": {
                    "qr": f"qr_{k}", "qf": f"qf_{k}",          # settled to settled
                    "qrr": f"qrr_{k}", "qff": f"qff_{k}",      # over the input ramp only
                },
            }
        )
    L.append(".save " + " ".join(f"i(vp_{k})" for k in range(len(states))))
    L.append(f".tran {_n(tmax)} {_n(tstop)} 0 {_n(tmax)}")
    L.append("")
    for k in range(len(states)):
        L.append(f".meas tran qr_{k} INTEG i(vp_{k}) FROM={_n(t0)} TO={_n(t1)}")
        L.append(f".meas tran qf_{k} INTEG i(vp_{k}) FROM={_n(t1)} TO={_n(t2)}")
        L.append(f".meas tran qrr_{k} INTEG i(vp_{k}) FROM={_n(t0)} TO={_n(t0 + ramp)}")
        L.append(f".meas tran qff_{k} INTEG i(vp_{k}) FROM={_n(t1)} TO={_n(t1 + ramp)}")
    L.append(".end")
    return "\n".join(L) + "\n", {
        "kind": "cap", "pin": pin, "slew": slew, "load": cload, "states": entries,
    }


# --------------------------------------------------------------------------------------
# Arc discovery and boolean minimization
# --------------------------------------------------------------------------------------


def arcs_from_table(inputs: list[str], outputs: list[str], table: dict[str, list[int]]) -> list[dict]:
    """Every (input, output) pair the truth table shows a real dependency for.

    The side-input states that sensitize a pair are split by sense: raising the input
    raises the output (positive_unate) or lowers it (negative_unate). A pin with states of
    both kinds is non_unate, which Liberty wants as separate `when`-qualified groups.
    """
    ni = len(inputs)
    idx = {s: i for i, s in enumerate(inputs)}
    arcs = []
    for pin in inputs:
        pi = idx[pin]
        others = [s for s in inputs if s != pin]
        for out in outputs:
            pos, neg = [], []
            for v in range(1 << ni):
                if (v >> pi) & 1:
                    continue  # visit each pair once, from its input=0 half
                lo, hi = table[out][v], table[out][v | (1 << pi)]
                if lo == hi:
                    continue
                state = {s: (v >> idx[s]) & 1 for s in others}
                (pos if hi > lo else neg).append(state)
            if not pos and not neg:
                continue
            sense = "non_unate" if (pos and neg) else ("positive_unate" if pos else "negative_unate")
            arcs.append({"pin": pin, "output": out, "sense": sense, "pos": pos, "neg": neg})
    return arcs


def qm_cover(n: int, minterms: list[int]) -> list[tuple[int, int]]:
    """Quine-McCluskey prime implicants, then a greedy cover.

    Returns (bits, mask) pairs. The cover is greedy, so not guaranteed minimal -- but it is
    always correct, and every emitted expression is re-checked against the truth table.
    """
    if not minterms:
        return []
    full = (1 << n) - 1
    cur = {(m, full) for m in minterms}
    primes: set[tuple[int, int]] = set()
    while cur:
        used: set[tuple[int, int]] = set()
        nxt: set[tuple[int, int]] = set()
        items = sorted(cur)
        for i, (b1, m1) in enumerate(items):
            for b2, m2 in items[i + 1 :]:
                if m1 != m2:
                    continue
                diff = (b1 ^ b2) & m1
                if diff and diff & (diff - 1) == 0:
                    used.add((b1, m1))
                    used.add((b2, m2))
                    nxt.add((b1 & ~diff & m1, m1 & ~diff))
        primes |= cur - used
        cur = nxt

    remaining, chosen = set(minterms), []
    while remaining:
        best, covered = None, set()
        for p in sorted(primes):
            bits, mask = p
            cov = {m for m in remaining if (m & mask) == bits}
            if len(cov) > len(covered):
                best, covered = p, cov
        if best is None:
            raise CharError("internal error: could not cover all minterms")
        chosen.append(best)
        remaining -= covered
        primes.discard(best)
    return chosen


def sop_expr(inputs: list[str], cover: list[tuple[int, int]]) -> str:
    """A cover in Liberty syntax: `*` for AND, `+` for OR, `!` for NOT."""
    terms = []
    for bits, mask in cover:
        lits = [
            (s if (bits >> i) & 1 else f"!{s}") for i, s in enumerate(inputs) if (mask >> i) & 1
        ]
        terms.append("*".join(lits) if lits else "1")
    return "+".join(terms)


def liberty_function(inputs: list[str], table: list[int]) -> str:
    """The shorter of SOP(f) and !SOP(!f) -- which is what turns a NAND back into !(A*B)."""
    n = len(inputs)
    ones = [v for v in range(1 << n) if table[v]]
    if not ones:
        return "0"
    if len(ones) == 1 << n:
        return "1"
    pos = sop_expr(inputs, qm_cover(n, ones))
    neg = sop_expr(inputs, qm_cover(n, [v for v in range(1 << n) if not table[v]]))
    inv = f"!({neg})" if ("+" in neg or "*" in neg) else f"!{neg}"
    return pos if len(pos) <= len(inv) else inv


def states_expr(others: list[str], states: list[dict[str, int]]) -> str:
    """A `when` condition covering a set of side-input states."""
    if not states or not others:
        return ""
    idx = {s: i for i, s in enumerate(others)}
    minterms = sorted({sum(v << idx[s] for s, v in st.items()) for st in states})
    return sop_expr(others, qm_cover(len(others), minterms))


def check_expr(inputs: list[str], expr: str, table: list[int]) -> None:
    """Re-evaluate an emitted expression over the whole table: a slip in the minimizer
    becomes a hard error instead of a wrong library."""
    ast = tb.parse_lib_expr(expr)
    for v in range(1 << len(inputs)):
        env = {s: (v >> i) & 1 for i, s in enumerate(inputs)}
        if tb.eval_node(ast, env) != table[v]:
            raise CharError(
                f"internal error: emitted function '{expr}' disagrees with the measured truth "
                f"table at vector {v}"
            )


# --------------------------------------------------------------------------------------
# Running ngspice
# --------------------------------------------------------------------------------------

_RE_RESULT = re.compile(r"^\s*([a-z_0-9]+(?:\([^)]*\))?)\s*=\s*(-?[\d.]+(?:e[-+]?\d+)?|failed)", re.I)


@dataclass
class Run:
    deck: Path
    log: Path
    values: dict[str, float]
    failed: list[str]


# ngspice is built with OpenMP and its `num_threads` defaults to several threads per
# process (4 in this container's ~/.spiceinit). Running decks in parallel then oversubscribes
# the machine badly, and OpenMP's busy-waiting turns that into a collapse rather than a
# slowdown: measured here, one arc deck takes 0.2 s on its own but eight at once take about
# a minute each. One thread per process, many processes, is the right split -- this tool
# already has all the parallelism it needs at the deck level.
#
# OMP_NUM_THREADS does not do it: ngspice has its own `num_threads` variable, and it is set
# in .spiceinit. ngspice reads exactly ONE such file -- the first of the current directory,
# $SPICE_USERINIT_DIR and $HOME -- so a local one *shadows* the others rather than adding to
# them. On this image $SPICE_USERINIT_DIR points at the PDK's .spiceinit, which is what loads
# the PSP103 Verilog-A models; a local file that did not carry those `osdi` lines forward made
# every deck die with "Unknown model type psp103va". Hence: copy the file ngspice would have
# used, and only override num_threads in the copy.
_SPICEINIT_NOTE = (
    "* Written by scripts/gen_cell_lib.py: a copy of {src}\n"
    "* with num_threads forced to 1, because decks are run many-at-once and ngspice's OpenMP\n"
    "* threads would otherwise fight each other. Delete it and it will be rewritten.\n"
)


def spiceinit_source() -> Path | None:
    """The .spiceinit ngspice would have picked up, ignoring any current directory."""
    for d in (os.environ.get("SPICE_USERINIT_DIR"), os.environ.get("HOME")):
        if d and (Path(d) / ".spiceinit").is_file():
            return Path(d) / ".spiceinit"
    return None


def spiceinit_text() -> str:
    src = spiceinit_source()
    base = src.read_text() if src else ""
    base = re.sub(r"(?m)^\s*set\s+num_threads\s*=.*$", "", base)
    return (
        _SPICEINIT_NOTE.format(src=src or "(no .spiceinit found)")
        + base.rstrip("\n")
        + "\nset num_threads=1\n"
    )


def ensure_spiceinit(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    init = directory / ".spiceinit"
    want = spiceinit_text()
    if not init.is_file() or init.read_text() != want:
        init.write_text(want)


def run_deck(ngspice: str, deck: Path, timeout: float) -> Run:
    """Run one deck and collect every ``name = value`` ngspice printed."""
    ensure_spiceinit(deck.parent)
    t0 = time.time()
    try:
        proc = subprocess.run(
            [ngspice, "-b", deck.name],
            cwd=deck.parent,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise CharError(f"{deck}: ngspice timed out after {timeout:g} s (raise --timeout)") from None
    out = proc.stdout + proc.stderr
    log = deck.with_suffix(".log")
    log.write_text(f"$ {ngspice} -b {deck.name}   ({time.time() - t0:.1f} s)\n\n{out}")
    if proc.returncode != 0:
        raise CharError(
            f"{deck}: ngspice exited {proc.returncode}; see {log}\n"
            + "\n".join(out.splitlines()[-15:])
        )
    values, failed = {}, []
    for line in out.splitlines():
        m = _RE_RESULT.match(line)
        if not m:
            continue
        name, val = m.group(1).lower(), m.group(2)
        if val == "failed":
            failed.append(name)
        else:
            values[name] = float(val)
    return Run(deck, log, values, failed)


def need(run: Run, name: str) -> float:
    if name in run.values:
        return run.values[name]
    raise CharError(
        f"{run.deck}: ngspice did not produce a value for '{name}'"
        + (f" (it reported 'failed' for {', '.join(run.failed)})" if run.failed else "")
        + f"\n  full log: {run.log}"
    )


# --------------------------------------------------------------------------------------
# Characterization of one cell at one corner
# --------------------------------------------------------------------------------------


@dataclass
class ArcSpec:
    """One arc deck to build and run: an arc, one sensitizing side state, one slew row."""

    pin: str
    output: str
    sense: str
    when: str
    side: dict[str, int]
    edge_a: str
    slew: float
    slew_index: int
    deck: Path
    # With an active driver the two input edges cannot both hit the index with one ramp
    # (a driver's pull-up and pull-down are not equally strong), so each edge gets its own
    # calibrated deck and contributes only its own half: "a" = input rising, "b" = falling.
    use_edge: str = "both"


MAX_SETTLE_RETRIES = 4
DRIVER_CAL = DriverCal()


def _unsettled(run: Run, info: dict, ctx: Ctx) -> list[str]:
    """Replicas whose output had not reached its rail by the end of a window."""
    bad = []
    other = "fall" if info["edge_a_output"] == "rise" else "rise"
    for p in info["points"]:
        for tag, direction in (("va", info["edge_a_output"]), ("vb", other)):
            v = need(run, p["meas"][tag])
            want = ctx.vdd if direction == "rise" else 0.0
            if abs(v - want) > 0.05 * ctx.vdd:
                bad.append(
                    f"load {p['load']:.3g} F, window {tag[-1]}: {v:.4g} V, wanted ~{want:g} V"
                )
    return bad


def run_arc(args, ctx: Ctx, cell: CharCell, spec: ArcSpec, loads: list[float], other_load: float):
    """Emit and run one arc deck, widening the settling window until the output settles.

    The settling allowance is an estimate for a roughly minimum-strength cell; rather than
    ask the user to guess a multiplier for a weak one, the deck reports where its output
    actually was and the allowance is doubled until it is right.
    """
    drive_ramp, achieved, cal_note = None, None, None
    if ctx.driver is not None:
        edge = "rise" if spec.use_edge == "a" else "fall"
        drive_ramp, achieved, cal_note = DRIVER_CAL.solve(
            args, ctx, cell, spec.pin, spec.side, spec.slew, edge,
            spec.deck.parent, f"{spec.pin}_{spec.sense[0]}_{edge}",
        )

    settle = ctx.settle
    for attempt in range(MAX_SETTLE_RETRIES):
        local = dataclasses.replace(ctx, settle=settle)
        text, info = emit_arc_deck(
            cell, local, spec.pin, spec.output, spec.side, spec.edge_a, spec.slew, loads,
            other_load, drive_ramp,
        )
        spec.deck.write_text(text)
        run = run_deck(args.ngspice, spec.deck, args.timeout)
        bad = _unsettled(run, info, local)
        if not bad:
            info["achieved_slew"] = achieved
            info["cal_note"] = cal_note
            return spec, info, run, settle
        settle *= 2
    raise CharError(
        f"{spec.deck}: the output still had not settled with {settle / ctx.settle:g}x the default "
        f"settling allowance:\n  " + "\n  ".join(bad[:6]) + "\n"
        "  Either the cell cannot drive this load at all, or it is far slower than the grid "
        "assumes. Check the largest --loads entry, or raise --settle."
    )


def run_cap(args, ctx: Ctx, cell: CharCell, pin: str, states, slew: float, cload: float, deck: Path):
    text, info = emit_cap_deck(cell, ctx, pin, states, slew, cload)
    deck.write_text(text)
    return pin, info, run_deck(args.ngspice, deck, args.timeout)


@dataclass
class ArcResult:
    pin: str
    output: str
    sense: str
    when: str
    tables: dict[str, list[list[float]]]  # in SI units
    states: list[dict[str, int]] = field(default_factory=list)
    achieved: dict[str, float] = field(default_factory=dict)  # driver mode: slew at the pin


@dataclass
class CellResult:
    cell: CharCell
    table: dict[str, list[int]]
    functions: dict[str, str]
    leakage: list[dict]  # per input vector: bits + watts
    arcs: list[ArcResult]
    caps: dict[str, dict[str, float]]
    notes: list[str] = field(default_factory=list)


def sample(items: list, limit: int, what: str, notes: list[str]) -> list:
    """Cap a work list, and say so out loud rather than silently truncating."""
    if limit <= 0 or len(items) <= limit:
        return items
    notes.append(f"{what}: used {limit} of {len(items)} (raised with the matching --max-* option)")
    return items[:limit]


def characterize(
    cell: CharCell, ctx: Ctx, args, tmpl: Template, workdir: Path
) -> CellResult:
    workdir.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []
    slews = [s * tmpl.units.time for s in args.slew_list]
    loads = [c * tmpl.units.cap for c in args.load_list]

    # ---- phase 1: truth table + leakage -------------------------------------------
    text, info = emit_op_deck(cell, ctx)
    deck = workdir / f"op_{cell.name}.spice"
    deck.write_text(text)
    run = run_deck(args.ngspice, deck, args.timeout)

    table = {o: [0] * (1 << len(cell.inputs)) for o in cell.outputs}
    leakage = []
    vth = ctx.vdd / 2.0
    for e in info["vectors"]:
        for o, expr in e["outputs"].items():
            v = need(run, expr)
            if 0.1 * ctx.vdd < v < 0.9 * ctx.vdd:
                raise CharError(
                    f"{cell.name}: output {o} settles at {v:.4g} V (VDD={ctx.vdd}) for input "
                    f"vector {e['bits']} -- neither a 0 nor a 1.\n"
                    "  A cell with internal state, a floating output or a ratioed circuit "
                    "cannot be given a Liberty function by this generator."
                )
            table[o][e["vec"]] = int(v > vth)
        leakage.append({"bits": e["bits"], "watts": abs(need(run, e["supply"])) * ctx.vdd})

    functions = {}
    for o in cell.outputs:
        expr = liberty_function(cell.inputs, table[o])
        check_expr(cell.inputs, expr, table[o])
        functions[o] = expr

    # ---- phase 2: timing + internal power ------------------------------------------
    arcs = arcs_from_table(cell.inputs, cell.outputs, table)
    specs: list[ArcSpec] = []
    for arc in arcs:
        others = [s for s in cell.inputs if s != arc["pin"]]
        for sense in ("positive_unate", "negative_unate"):
            states = arc["pos"] if sense == "positive_unate" else arc["neg"]
            if not states:
                continue
            when = states_expr(others, states) if arc["sense"] == "non_unate" else ""
            used = sample(
                states, args.max_side_states,
                f"{cell.name} arc {arc['pin']}->{arc['output']} ({sense}) side states", notes,
            )
            # One deck per input edge when a driver has to be calibrated per edge, one deck
            # for both when an ideal (symmetric) ramp is used.
            edges = ["a", "b"] if ctx.driver is not None else ["both"]
            for si, st in enumerate(used):
                for sl, slew in enumerate(slews):
                    for e in edges:
                        suffix = "" if e == "both" else f"_{e}"
                        specs.append(
                            ArcSpec(
                                pin=arc["pin"], output=arc["output"], sense=sense, when=when,
                                side=st, edge_a="rise" if sense == "positive_unate" else "fall",
                                slew=slew, slew_index=sl, use_edge=e,
                                deck=workdir / f"arc_{cell.name}_{arc['pin']}_{arc['output']}"
                                f"_{sense[0]}{si}_s{sl}{suffix}.spice",
                            )
                        )

    # ---- input capacitance ----------------------------------------------------------
    cap_specs: list[tuple[str, list[dict[str, int]], float, float, Path]] = []
    if not args.no_cap:
        # Fastest grid slew by default: with a slow input the output finishes switching while
        # the input is still ramping, so the Miller charge lands inside the ramp window and
        # --cap-window stops meaning anything. See the --cap-window help.
        cap_slew = slews[0] if args.cap_slew is None else args.cap_slew * tmpl.units.time
        cap_load = args.cap_load * tmpl.units.cap
        for pin in cell.inputs:
            others = [s for s in cell.inputs if s != pin]
            all_states = [
                {s: (v >> i) & 1 for i, s in enumerate(others)} for v in range(1 << len(others))
            ]
            states = sample(all_states, args.max_cap_states, f"{cell.name} pin {pin} cap states", notes)
            cap_specs.append((pin, states, cap_slew, cap_load, workdir / f"cap_{cell.name}_{pin}.spice"))

    other_load = args.other_load * tmpl.units.cap
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        arc_futs = [pool.submit(run_arc, args, ctx, cell, s, loads, other_load) for s in specs]
        cap_futs = [pool.submit(run_cap, args, ctx, cell, *c) for c in cap_specs]
        arc_done = [f.result() for f in arc_futs]
        cap_done = [f.result() for f in cap_futs]

    # ---- reduce the arc decks into tables --------------------------------------------
    grouped: dict[tuple[str, str, str], dict] = {}
    for spec, info, run, used_settle in arc_done:
        if used_settle != ctx.settle:
            notes.append(
                f"{spec.deck.name}: needed {used_settle / ctx.settle:g}x the default settling "
                "allowance (the deck was re-run until its output had settled)"
            )
        if info.get("cal_note") and info["cal_note"] not in notes:
            notes.append(info["cal_note"])
        g = grouped.setdefault(
            (spec.pin, spec.output, spec.sense),
            {"when": spec.when, "tables": {}, "states": [], "raw": [], "achieved": {}},
        )
        if spec.side not in g["states"]:
            g["states"].append(spec.side)
        if info.get("achieved_slew") is not None:
            g["achieved"][f"slew{spec.slew_index}_{spec.use_edge}"] = info["achieved_slew"]
        for p in info["points"]:
            k, cl = p["load_index"], p["load"]
            m = {q: need(run, n) for q, n in p["meas"].items()}
            # Port accounting: energy in from the supply and the input pins, minus what went
            # to the load, minus the load's own resistive share (half of C*VDD^2 per edge).
            e_a = m["esa"] + m["eia"] - m["eoa"] - 0.5 * cl * ctx.vdd**2
            e_b = m["esb"] + m["eib"] - m["eob"] - 0.5 * cl * ctx.vdd**2
            if info["edge_a_output"] == "rise":
                half_a = {"cell_rise": m["da"], "rise_transition": m["sa"], "rise_power": e_a}
                half_b = {"cell_fall": m["db"], "fall_transition": m["sb"], "fall_power": e_b}
            else:
                half_a = {"cell_fall": m["da"], "fall_transition": m["sa"], "fall_power": e_a}
                half_b = {"cell_rise": m["db"], "rise_transition": m["sb"], "rise_power": e_b}
            # A deck calibrated for one input edge only says anything about that edge.
            vals = {"a": half_a, "b": half_b, "both": {**half_a, **half_b}}[spec.use_edge]
            for q, v in vals.items():
                t = g["tables"].setdefault(q, [[None] * len(loads) for _ in slews])
                cur = t[spec.slew_index][k]
                t[spec.slew_index][k] = v if cur is None else COMBINE[args.combine](cur, v)
            g["raw"].append(
                {"slew": spec.slew, "load": cl, "side": spec.side,
                 "edge_a_output": info["edge_a_output"], **m}
            )

    results = []
    for (pin, out, sense), g in grouped.items():
        for q, t in g["tables"].items():
            if any(None in row for row in t):
                raise CharError(f"{cell.name}: incomplete {q} table for {pin}->{out} ({sense})")
        results.append(
            ArcResult(pin, out, sense, g["when"], g["tables"], g["states"], g["achieved"])
        )

    # ---- reduce the capacitance decks -------------------------------------------------
    caps: dict[str, dict[str, float]] = {}
    kr, kf = ("qrr", "qff") if args.cap_window == "ramp" else ("qr", "qf")
    for pin, info, run in cap_done:
        rise = [abs(need(run, s["meas"][kr])) / ctx.vdd for s in info["states"]]
        fall = [abs(need(run, s["meas"][kf])) / ctx.vdd for s in info["states"]]
        for i, (r, f) in enumerate(zip(rise, fall)):
            if abs(r - f) > 0.25 * max(r, f):
                notes.append(
                    f"{cell.name} pin {pin}, side state {info['states'][i]['state']}: the charge "
                    f"in ({r / 1e-15:.3g} fF) and out ({f / 1e-15:.3g} fF) differ by more than "
                    "25%, which usually means the excursion had not settled"
                )
        pick = COMBINE[args.cap_combine]
        caps[pin] = {
            "rise": _reduce(rise, pick), "fall": _reduce(fall, pick),
            "rise_min": min(rise), "rise_max": max(rise),
            "fall_min": min(fall), "fall_max": max(fall),
        }

    return CellResult(cell, table, functions, leakage, results, caps, notes)


COMBINE = {
    "max": max,
    "min": min,
    "first": lambda a, b: a,
    "mean": lambda a, b: (a + b) / 2.0,  # running mean of two is only exact for two states
}


def _reduce(vals: list[float], pick) -> float:
    out = vals[0]
    for v in vals[1:]:
        out = pick(out, v)
    return out


# --------------------------------------------------------------------------------------
# Functional verification, delegated to gen_cell_tb.py
# --------------------------------------------------------------------------------------


VERILOG_TB = """\
// AUTO-GENERATED by scripts/{script} -- do not edit.
// Sweeps every input combination of {cell} and prints the truth table, so the table
// measured from the transistors can be checked against the Verilog view of the same cell.
`timescale 1ns/1ps
module tb_truth;
  localparam int NI = {ni};
  logic [NI-1:0] vec;
{wires}
  wire {outs};
  {cell} dut ({conns});
  initial begin
    for (int unsigned v = 0; v < (1 << NI); v++) begin
      vec = v[NI-1:0];
      #1;
{prints}
    end
    $finish;
  end
endmodule
"""

_RE_SPECIFY = re.compile(r"^[ \t]*specify\b.*?^[ \t]*endspecify\b", re.S | re.M)


def verify_verilog(args, cell: CharCell, table: dict[str, list[int]], workdir: Path) -> str:
    """Check the measured truth table against the Verilog view, by simulating it.

    The Liberty oracle is one way to say what a cell ought to compute; a Verilog view is
    another, and when the thing being measured is a transistor netlist the Verilog is just
    as independent of it. This route needs no Liberty at all: elaborate whatever
    ``--verilog`` describes (behavioural or structural, with ``--cell-verilog`` supplying
    the leaf models a structural netlist instantiates), sweep every input combination, and
    compare against the table the `.op` deck measured at this corner.

    `specify` blocks are stripped first: they carry no function, and Icarus refuses some of
    the PDK's ("sorry: ifnone with an edge-sensitive path is not supported").
    """
    iverilog = shutil.which(args.iverilog)
    if iverilog is None:
        return f"skipped (no --lib, and '{args.iverilog}' not found for the Verilog check)"
    vdir = workdir / "verify-verilog"
    vdir.mkdir(parents=True, exist_ok=True)

    sources = []
    for src in [args.verilog] + list(args.cell_verilog):
        dst = vdir / f"nospec_{src.name}"
        dst.write_text(_RE_SPECIFY.sub("", src.read_text()))
        sources.append(dst)

    ni = len(cell.inputs)
    tb = vdir / f"tb_truth_{cell.name}.v"
    tb.write_text(
        VERILOG_TB.format(
            script=SCRIPT,
            cell=cell.name,
            ni=ni,
            wires="\n".join(f"  wire {s} = vec[{i}];" for i, s in enumerate(cell.inputs)),
            outs=", ".join(cell.outputs),
            conns=", ".join(f".{p}({p})" for p in cell.inputs + cell.outputs),
            prints="\n".join(
                f'      $display("VEC %0d {o} %b", v, {o});' for o in cell.outputs
            ),
        )
    )
    vvp = vdir / f"tb_truth_{cell.name}.vvp"
    build = subprocess.run(
        [iverilog, "-g2012", "-o", str(vvp), str(tb)] + [str(s) for s in sources],
        capture_output=True, text=True,
    )
    if build.returncode != 0:
        raise CharError(
            f"could not elaborate {args.verilog} to check the function:\n"
            + (build.stdout + build.stderr).strip()
            + "\n  A structural netlist needs its leaf cell models too: pass them with "
            "--cell-verilog. Or use --lib for the SPICE-level check, or --no-verify."
        )
    run = subprocess.run([shutil.which("vvp") or "vvp", str(vvp)], capture_output=True,
                         text=True, timeout=args.timeout)
    (vdir / f"tb_truth_{cell.name}.log").write_text(run.stdout + run.stderr)

    seen: dict[tuple[int, str], int] = {}
    for line in run.stdout.splitlines():
        m = re.match(r"VEC (\d+) (\w+) ([01xzXZ])", line.strip())
        if not m:
            continue
        v, pin, val = int(m.group(1)), m.group(2), m.group(3)
        if val not in "01":
            raise CharError(
                f"{args.verilog}: '{cell.name}' output {pin} is '{val}' for input vector "
                f"{v:0{ni}b}; a cell whose Verilog view goes X cannot be checked against"
            )
        seen[(v, pin)] = int(val)

    mismatches = []
    for o in cell.outputs:
        for v in range(1 << ni):
            if (v, o) not in seen:
                raise CharError(
                    f"the Verilog check produced no value for {o} at vector {v}; see "
                    f"{vdir / f'tb_truth_{cell.name}.log'}"
                )
            if seen[(v, o)] != table[o][v]:
                bits = " ".join(f"{s}={((v >> i) & 1)}" for i, s in enumerate(cell.inputs))
                mismatches.append(
                    f"{bits}: {o} is {table[o][v]} in the netlist, {seen[(v, o)]} in Verilog"
                )
    if mismatches:
        raise CharError(
            f"[FAIL] {cell.name} : the measured truth table disagrees with {args.verilog.name} "
            f"in {len(mismatches)} of {(1 << ni) * len(cell.outputs)} cases:\n  "
            + "\n  ".join(mismatches[:8])
            + "\n  Characterizing a netlist that computes the wrong function would be "
            "pointless, so this is fatal. Use --no-verify to override."
        )
    return (
        f"[PASS] {cell.name} : {1 << ni}/{1 << ni} vectors match "
        f"(2-way: measured transistors, {args.verilog.name})"
    )


def structural_view(args, cell_name: str) -> bool:
    """Is --verilog a structural netlist that defines this cell out of library cells?

    Answered by trying to parse it as one. A behavioural model, or a file where some *other*
    module is not structural (the PDK's sg13g2_stdcell.v has both), simply is not one.
    """
    if not args.verilog:
        return False
    try:
        return cell_name in {m.name for m in tb.parse_netlist(args.verilog)}
    except tb.GenError:
        return False


WRAP_V = """\
// AUTO-GENERATED by scripts/{script} -- do not edit.
// A one-instance wrapper so gen_cell_tb.py can build its exhaustive functional deck for a
// library cell that has no structural Verilog view of its own.
module {cell} ({ports});
{decls}
  {cell} g0 ({conns});
endmodule
"""


def verify_corner(cell: CharCell, ctx: Ctx, args, workdir: Path) -> str:
    """Build and run the exhaustive functional deck for this cell at this corner.

    This is the one place the two scripts meet: `gen_cell_tb.py` owns verification, and it
    is invoked here exactly as a user would from the command line.
    """
    if not args.lib:
        return "skipped (no --lib: gen_cell_tb.py needs a Liberty oracle)"
    vdir = workdir / "verify"
    vdir.mkdir(parents=True, exist_ok=True)

    # gen_cell_tb.py builds its gold model out of a *structural* netlist of library cells.
    # A behavioural view -- which is what --verilog usually is, and what the PDK ships --
    # is fine for pin directions but cannot serve as one, so fall back to the wrapper.
    verilog = args.verilog if structural_view(args, cell.name) else None
    if verilog is None:
        # No structural view: wrap the cell in a module of the same name, so the deck is a
        # 2-way check of the transistors against the cell's own Liberty function.
        ports = cell.inputs + cell.outputs
        wrap = vdir / f"{cell.name}_wrap.v"
        wrap.write_text(
            WRAP_V.format(
                script=SCRIPT,
                cell=cell.name,
                ports=", ".join(ports),
                decls="\n".join(
                    [f"  input {p};" for p in cell.inputs] + [f"  output {p};" for p in cell.outputs]
                ),
                conns=", ".join(f".{p}({p})" for p in ports),
            )
        )
        verilog = wrap

    gen = Path(__file__).resolve().parent / "tb_generator.py"
    cmd = [
        sys.executable, str(gen), str(verilog),
        "--lib", str(args.lib),
        "--emit", "spice",
        "--module", cell.name,
        "--model-lib", str(args.model_lib),
        "--model-section", ctx.corner.section,
        "--vdd", _n(ctx.vdd),
        "--temp", _n(ctx.temp),
        "--no-makefile",
        "-o", str(vdir / ctx.corner.tag),
    ]
    # With a structural view the netlist under test is the *custom* implementation, checked
    # against the cells it claims to be equivalent to. Without one, the wrapper instantiates
    # the cell itself, so the netlist is where its subckt has to come from.
    cell_spice = list(args.cell_spice)
    if verilog is not args.verilog:
        cell_spice += [f for f in args.netlist if f not in cell_spice]
    for f in cell_spice:
        cmd += ["--cell-spice", str(f)]
    if verilog is args.verilog:
        for f in args.netlist:
            cmd += ["--custom-netlist", str(f)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise CharError(
            "tb_generator refused to build the verification deck:\n"
            + proc.stdout + proc.stderr
            + "\n  (pass --no-verify to characterize without the functional check)"
        )
    deck = vdir / ctx.corner.tag / "spice" / f"tb_{cell.name}.spice"
    if not deck.is_file():
        raise CharError(f"expected {deck} from tb_generator, but it was not written")
    ensure_spiceinit(deck.parent)
    proc = subprocess.run(
        [args.ngspice, "-b", deck.name], cwd=deck.parent, capture_output=True, text=True,
        timeout=args.timeout,
    )
    out = proc.stdout + proc.stderr
    (deck.parent / "verify.log").write_text(out)
    verdict = next((l.strip() for l in out.splitlines() if l.startswith(("[PASS]", "[FAIL]"))), "")
    if proc.returncode != 0 or verdict.startswith("[FAIL]") or not verdict:
        raise CharError(
            f"{cell.name}: functional verification failed at corner {ctx.corner.name}.\n"
            f"  {verdict or 'no [PASS]/[FAIL] line; see ' + str(deck.parent / 'verify.log')}\n"
            "  Characterizing a netlist that computes the wrong function would be pointless, "
            "so this is fatal. Use --no-verify to override."
        )
    return verdict


# --------------------------------------------------------------------------------------
# Liberty emission
# --------------------------------------------------------------------------------------


def fmt_table(name: str, tmpl_name: str, slews: list[float], loads: list[float],
              values: list[list[float]], scale: float, indent: str) -> list[str]:
    L = [f"{indent}{name} ({tmpl_name}) {{"]
    L.append(f'{indent}  index_1 ("{", ".join(_v(s) for s in slews)}");')
    L.append(f'{indent}  index_2 ("{", ".join(_v(c) for c in loads)}");')
    L.append(f"{indent}  values ( \\")
    rows = [f'{indent}    "{", ".join(_v(v / scale) for v in row)}"' for row in values]
    L.append(", \\\n".join(rows) + " \\")
    L.append(f"{indent}  );")
    L.append(f"{indent}}}")
    return L


def emit_cell(res: CellResult, args, tmpl: Template) -> str:
    u = tmpl.units
    cell = res.cell
    slews, loads = args.slew_list, args.load_list
    L = [f"  cell ({cell.name}) {{"]
    L.append(f"    area : {_v(cell.area)};")
    if cell.footprint:
        L.append(f'    cell_footprint : "{cell.footprint}";')
    avg = sum(e["watts"] for e in res.leakage) / len(res.leakage)
    L.append(f"    cell_leakage_power : {_v(avg / u.leak)};")
    for e in res.leakage:
        when = "*".join(
            (s if b else f"!{s}") for s, b in zip(cell.inputs, e["bits"])
        )
        L.append("    leakage_power () {")
        L.append(f"      value : {_v(e['watts'] / u.leak)};")
        L.append(f'      when : "{when}";')
        L.append("    }")

    for out in cell.outputs:
        L.append(f"    pin ({out}) {{")
        L.append('      direction : "output";')
        L.append(f'      function : "{res.functions[out]}";')
        L.append(f"      min_capacitance : {_v(min(loads))};")
        L.append(f"      max_capacitance : {_v(max(loads))};")
        L.append(f"      max_transition : {_v(max(slews))};")
        for arc in [a for a in res.arcs if a.output == out]:
            L.append("      timing () {")
            L.append(f'        related_pin : "{arc.pin}";')
            L.append(f"        timing_sense : {arc.sense};")
            L.append("        timing_type : combinational;")
            if arc.when:
                L.append(f'        when : "{arc.when}";')
            for q, scale in (("cell_rise", u.time), ("rise_transition", u.time),
                             ("cell_fall", u.time), ("fall_transition", u.time)):
                L += fmt_table(q, tmpl.delay_template, slews, loads, arc.tables[q], scale, "        ")
            L.append("      }")
        if not args.no_power:
            for arc in [a for a in res.arcs if a.output == out]:
                L.append("      internal_power () {")
                L.append(f'        related_pin : "{arc.pin}";')
                if arc.when:
                    L.append(f'        when : "{arc.when}";')
                for q in ("rise_power", "fall_power"):
                    L += fmt_table(
                        q, tmpl.power_template, slews, loads, arc.tables[q], u.energy, "        "
                    )
                L.append("      }")
        L.append("    }")

    for pin in cell.inputs:
        L.append(f"    pin ({pin}) {{")
        L.append('      direction : "input";')
        L.append(f"      max_transition : {_v(max(slews))};")
        c = res.caps.get(pin)
        if c:
            L.append(f"      capacitance : {_v((c['rise'] + c['fall']) / 2 / u.cap)};")
            L.append(f"      rise_capacitance : {_v(c['rise'] / u.cap)};")
            L.append(
                f"      rise_capacitance_range ({_v(c['rise_min'] / u.cap)}, "
                f"{_v(c['rise_max'] / u.cap)});"
            )
            L.append(f"      fall_capacitance : {_v(c['fall'] / u.cap)};")
            L.append(
                f"      fall_capacitance_range ({_v(c['fall_min'] / u.cap)}, "
                f"{_v(c['fall_max'] / u.cap)});"
            )
        L.append("    }")
    L.append("  }")
    return "\n".join(L)


def emit_library(results: list[CellResult], corner: Corner, args, tmpl: Template, gencmd: str) -> str:
    name = f"{args.lib_name}_{corner.tag}"
    cells = "\n".join(emit_cell(r, args, tmpl) for r in results)
    return tmpl.render(
        library_name=name,
        cells=cells,
        index_slew=", ".join(_v(s) for s in args.slew_list),
        index_load=", ".join(_v(c) for c in args.load_list),
        voltage=_v(corner.vdd),
        temperature=_v(corner.temp),
        process="1",
        opcond_name=name,
        date=time.strftime("%a %b %d %H:%M:%S %Y"),
        gencmd=gencmd,
        comment=f"characterized by {SCRIPT} at corner {corner.name} "
        f"({corner.section or 'no section'})",
        max_transition=_v(max(args.slew_list)),
        max_capacitance=_v(max(args.load_list)),
        default_input_pin_cap=_v(
            sum(
                (c["rise"] + c["fall"]) / 2 / tmpl.units.cap
                for r in results for c in r.caps.values()
            )
            / max(1, sum(len(r.caps) for r in results))
        ),
    )


# --------------------------------------------------------------------------------------
# Reference-library comparison  (--compare-lib)
# --------------------------------------------------------------------------------------

_RE_TABLE = re.compile(
    r"(cell_rise|cell_fall|rise_transition|fall_transition|rise_power|fall_power)\s*\([^)]*\)\s*\{"
    r"(.*?)\}", re.S
)
_RE_VALUES = re.compile(r"values\s*\((.*?)\)\s*;", re.S)


def lib_tables(text: str, cell: str) -> dict[tuple[str, str, str], list[list[float]]]:
    """Every NLDM table of one cell, keyed by (output pin, related pin, table name)."""
    body = _group_body(text, "cell", cell)
    if body is None:
        raise CharError(f"reference library has no cell ({cell})")
    out: dict[tuple[str, str, str], list[list[float]]] = {}
    for pm in re.finditer(r"\bpin\s*\(\s*([\w\[\]]+)\s*\)\s*\{", body):
        pin = pm.group(1)
        pbody = _group_body(body[pm.start() :], "pin", pin)
        if pbody is None:
            continue
        for gm in re.finditer(r"\b(timing|internal_power)\s*\(\s*\)\s*\{", pbody):
            gbody = _brace_body(pbody, gm.end() - 1)
            rel = re.search(r'related_pin\s*:\s*"?(\w+)"?\s*;', gbody)
            if not rel:
                continue
            for tm in _RE_TABLE.finditer(gbody):
                vm = _RE_VALUES.search(tm.group(2))
                if not vm:
                    continue
                rows = [
                    [float(x) for x in row.split(",") if x.strip()]
                    for row in re.findall(r'"([^"]*)"', vm.group(1))
                ]
                out[(pin, rel.group(1), tm.group(1))] = rows
    return out


def _brace_body(text: str, open_idx: int) -> str:
    depth, i = 1, open_idx + 1
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[open_idx + 1 : i - 1]


def compare_libs(ours: str, ref_path: Path, cells: list[str]) -> list[str]:
    ref = ref_path.read_text()
    L = [f"## Comparison against `{ref_path.name}`", ""]
    L.append("Per table, the deviation of this run from the reference, over the whole grid.")
    L.append("")
    L.append("| cell | pin | related | table | mean dev | max dev | ours@[0][0] | ref@[0][0] |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for cell in cells:
        try:
            a, b = lib_tables(ours, cell), lib_tables(ref, cell)
        except CharError as exc:
            L.append(f"| `{cell}` | | | | *{exc}* | | | |")
            continue
        for key in sorted(a.keys() & b.keys()):
            ta, tb_ = a[key], b[key]
            devs = [
                abs(x - y) / abs(y) for ra, rb in zip(ta, tb_) for x, y in zip(ra, rb) if y
            ]
            if not devs:
                continue
            L.append(
                f"| `{cell}` | {key[0]} | {key[1]} | `{key[2]}` | "
                f"{100 * sum(devs) / len(devs):.1f}% | {100 * max(devs):.1f}% | "
                f"{ta[0][0]:.6g} | {tb_[0][0]:.6g} |"
            )
        only = sorted(a.keys() - b.keys())
        if only:
            L.append(f"| `{cell}` | | | *{len(only)} table(s) not in the reference* | | | | |")
    L.append("")
    return L


# --------------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------------


def emit_report(all_results: dict[str, list[CellResult]], corners: list[Corner], args,
                tmpl: Template, gencmd: str, verdicts: dict[str, list[str]]) -> str:
    L = [
        f"<!-- AUTO-GENERATED by scripts/{SCRIPT} -- do not edit. -->",
        "",
        f"# Characterization report: `{args.lib_name}`",
        "",
        "```",
        gencmd,
        "```",
        "",
        f"Template: `{tmpl.path.name}`  |  grid: {len(args.slew_list)} slews x "
        f"{len(args.load_list)} loads  |  corners: "
        + ", ".join(f"`{c.tag}`" for c in corners),
        "",
        "Stimulus: "
        + (
            f"the pin under test is driven by a real `{args.driver_cell}`, with the ramp into "
            f"it calibrated per edge so the slew arriving at the pin matches the grid index "
            f"(tolerance {args.driver_tol:g})."
            if args.driver_cell
            else f"an ideal linear ramp (`--input-ramp {args.input_ramp}`)."
        ),
        "",
        "## Corners",
        "",
        "| corner | model section | VDD | T | functional check |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in corners:
        L.append(
            f"| `{c.tag}` | `{c.section or '(none)'}` | {c.vdd} V | {c.temp} C | "
            + ("<br>".join(verdicts.get(c.name, [])) or "*skipped (--no-verify)*")
            + " |"
        )
    L.append("")

    first = corners[0]
    for res in all_results[first.name]:
        cell = res.cell
        L.append(f"## `{cell.name}`")
        L.append("")
        L.append(
            f"{len(cell.inputs)} inputs (`{', '.join(cell.inputs)}`), "
            f"{len(cell.outputs)} outputs (`{', '.join(cell.outputs)}`), "
            f"{1 << len(cell.inputs)} input vectors."
        )
        L.append("")
        L.append("Measured function (from the `.op` sweep, then minimized and re-checked):")
        L.append("")
        L.append("```")
        for o in cell.outputs:
            L.append(f"{o} = {res.functions[o]}")
        L.append("```")
        L.append("")
        L.append("Truth table (LSB of the index is the first input):")
        L.append("")
        L.append("```")
        for o in cell.outputs:
            L.append(f"{o}: " + "".join(str(b) for b in res.table[o]))
        L.append("```")
        L.append("")
        L.append("| arc | sense | when | side states used | " +
                 " | ".join(f"{c.name} cell_rise[0][0]" for c in corners) + " |")
        L.append("| --- | --- | --- | --- | " + " | ".join("---" for _ in corners) + " |")
        for arc in res.arcs:
            row = [
                f"`{arc.pin}` -> `{arc.output}`", arc.sense, f"`{arc.when}`" if arc.when else "",
                str(len(arc.states)),
            ]
            for c in corners:
                other = next(
                    (a for r in all_results[c.name] if r.cell.name == cell.name
                     for a in r.arcs if (a.pin, a.output, a.sense) == (arc.pin, arc.output, arc.sense)),
                    None,
                )
                row.append(
                    f"{other.tables['cell_rise'][0][0] / tmpl.units.time:.4g}" if other else "-"
                )
            L.append("| " + " | ".join(row) + " |")
        L.append("")
        if res.caps:
            L.append("| input pin | capacitance | rise | fall | spread over states |")
            L.append("| --- | --- | --- | --- | --- |")
            for pin, c in res.caps.items():
                lo = min(c["rise_min"], c["fall_min"]) / tmpl.units.cap
                hi = max(c["rise_max"], c["fall_max"]) / tmpl.units.cap
                L.append(
                    f"| `{pin}` | {(c['rise'] + c['fall']) / 2 / tmpl.units.cap:.5g} | "
                    f"{c['rise'] / tmpl.units.cap:.5g} | {c['fall'] / tmpl.units.cap:.5g} | "
                    f"{lo:.5g} .. {hi:.5g} |"
                )
            L.append("")
        achieved = [(k, v) for arc in res.arcs for k, v in arc.achieved.items()]
        if achieved:
            L.append("Slew actually delivered to the pin by the driver, per grid row:")
            L.append("")
            L.append("| slew index | target | delivered (min .. max over arcs and edges) |")
            L.append("| --- | --- | --- |")
            for i, s in enumerate(args.slew_list):
                got = [v for k, v in achieved if k.startswith(f"slew{i}_")]
                if got:
                    L.append(
                        f"| {i} | {s:g} | {min(got) / tmpl.units.time:.4g} .. "
                        f"{max(got) / tmpl.units.time:.4g} |"
                    )
            L.append("")
        notes = [n for r in all_results[first.name] if r.cell.name == cell.name for n in r.notes]
        if notes:
            L.append("Coverage notes:")
            L.append("")
            L += [f"* {n}" for n in notes]
            L.append("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------


_RE_V_MODULE = re.compile(r"\bmodule\s+(\w+)\s*(?:#\s*\([^)]*\)\s*)?\(([^;]*?)\)\s*;", re.S)
_RE_V_DECL = re.compile(r"\b(input|output|inout)\b\s*(?:wire|reg|logic|signed|\s)*?(\[[^\]]*\])?\s*([\w\s,]+?)\s*;")
_RE_V_DIR = re.compile(r"^\s*(input|output|inout)\b")


def parse_verilog_ports(path: Path, module: str) -> tuple[list[str], list[str]]:
    """Pin directions for one module, from *any* Verilog view of it.

    Deliberately weaker than `gen_cell_tb.parse_netlist`, which needs a structural netlist
    of named-port cell instances because it builds a gold model out of it. All that is
    wanted here is which pins are inputs and which are outputs, and a behavioural model --
    such as the PDK's own `sg13g2_stdcell.v`, written with gate primitives -- says that
    perfectly well. Both port styles are accepted:

        module m (Y, A, B);  output Y;  input A, B;     // non-ANSI
        module m (input A, input B, output Y);          // ANSI

    Ports are returned in the order the module header lists them, so the truth-table bit
    order does not depend on how the declarations happen to be written.
    """
    src = tb.strip_comments(path.read_text())
    for m in _RE_V_MODULE.finditer(src):
        if m.group(1) != module:
            continue
        header = m.group(2)
        rest = src[m.end():]
        end = re.search(r"\bendmodule\b", rest)
        body = rest[: end.start()] if end else rest
        dirs: dict[str, str] = {}
        order: list[str] = []

        def take(name: str, direction: str) -> None:
            name = name.strip()
            if not name:
                return
            dirs[name] = direction
            if name not in order:
                order.append(name)

        if _RE_V_DIR.search(header):  # ANSI: directions live in the header
            cur = None
            for item in header.split(","):
                dm = _RE_V_DIR.search(item)
                if dm:
                    cur = dm.group(1)
                    item = item[dm.end():]
                item = re.sub(r"\b(wire|reg|logic|signed)\b", " ", item)
                if "[" in item:
                    raise CharError(
                        f"{path}: module '{module}' port '{item.strip()}' is a vector; this "
                        "generator characterizes scalar pins only"
                    )
                if cur is None:
                    raise CharError(f"{path}: module '{module}' has an undeclared port")
                take(item, cur)
        else:  # non-ANSI: the header is a bare list, directions are declared in the body
            order = [p.strip() for p in header.split(",") if p.strip()]
            for direction, rng, names in _RE_V_DECL.findall(body):
                if rng:
                    raise CharError(
                        f"{path}: module '{module}' declares a vector port {rng}; this "
                        "generator characterizes scalar pins only"
                    )
                for name in names.split(","):
                    take(name, direction)

        missing = [p for p in order if p not in dirs]
        if missing:
            raise CharError(
                f"{path}: module '{module}' port(s) {missing} have no input/output declaration"
            )
        inout = sorted(p for p, d in dirs.items() if d == "inout")
        if inout:
            raise CharError(
                f"{path}: module '{module}' has inout port(s) {inout}, which cannot be "
                "characterized as a timing arc"
            )
        return (
            [p for p in order if dirs[p] == "input"],
            [p for p in order if dirs[p] == "output"],
        )
    raise CharError(f"{path}: no module '{module}'")


def resolve_cells(args) -> list[CharCell]:
    subckts = tb.parse_spice_subckts(list(args.netlist) + list(args.cell_spice))
    if not subckts:
        raise CharError(f"no '.subckt' found in {', '.join(str(f) for f in args.netlist)}")

    wanted = list(args.cell)
    if not wanted:
        own = tb.parse_spice_subckts(list(args.netlist))
        if len(own) != 1:
            raise CharError(
                f"{len(own)} subckts in the netlist ({', '.join(sorted(own))}); "
                "name the one to characterize with --cell"
            )
        wanted = list(own)

    lib_cells = {}
    if args.lib:
        try:
            lib_cells = tb.parse_liberty(args.lib, set(wanted))
        except tb.GenError:
            lib_cells = {}

    cells = []
    for name in wanted:
        if name not in subckts:
            raise CharError(
                f"no '.subckt {name}' in the given SPICE files\n  available: "
                + ", ".join(sorted(subckts))
            )
        ports, _ = subckts[name]
        power = next((p for p in ports if p.upper() == args.power.upper()), None)
        ground = next((p for p in ports if p.upper() == args.ground.upper()), None)
        if power is None or ground is None:
            raise CharError(
                f"'.subckt {name} {' '.join(ports)}' has no "
                f"{'--power ' + args.power if power is None else '--ground ' + args.ground} pin"
            )
        signals = [p for p in ports if p not in (power, ground)]

        if args.inputs or args.outputs:
            if not (args.inputs and args.outputs):
                raise CharError("--inputs and --outputs must be given together")
            ins, outs = args.inputs.split(","), args.outputs.split(",")
        elif args.verilog:
            ins, outs = parse_verilog_ports(args.verilog, name)
        elif name in lib_cells:
            ins, outs = lib_cells[name].inputs, lib_cells[name].outputs
        else:
            raise CharError(
                f"cannot tell which pins of '{name}' are inputs and which are outputs.\n"
                "  A SPICE .subckt does not say. Give --inputs/--outputs, or a --verilog "
                "file declaring the module (behavioural is fine), or a --lib defining the cell."
            )
        ins = [i.strip() for i in ins if i.strip()]
        outs = [o.strip() for o in outs if o.strip()]
        unknown = [p for p in ins + outs if p.upper() not in {s.upper() for s in signals}]
        if unknown:
            raise CharError(
                f"cell '{name}': pin(s) {unknown} are not ports of "
                f"'.subckt {name} {' '.join(ports)}'"
            )
        # Keep the .subckt's own order so the truth-table bit order is deterministic.
        order = {p.upper(): i for i, p in enumerate(signals)}
        if not (args.inputs or args.outputs):
            ins.sort(key=lambda p: order[p.upper()])
            outs.sort(key=lambda p: order[p.upper()])
        missing = [s for s in signals if s.upper() not in {p.upper() for p in ins + outs}]
        if missing:
            raise CharError(
                f"cell '{name}': port(s) {missing} are neither inputs nor outputs; every "
                "signal port must be classified"
            )
        cells.append(
            CharCell(
                name=name, inputs=ins, outputs=outs, power=power, ground=ground, ports=ports,
                area=args.area_of(name), footprint=args.footprint_of(name),
            )
        )
    return cells


def resolve_driver(args) -> Driver | None:
    """Turn the --driver-* arguments into a Driver, checking them against the SPICE file."""
    if not args.driver_cell:
        for opt in ("driver_input", "driver_output"):
            if getattr(args, opt):
                raise CharError(f"--{opt.replace('_', '-')} was given without --driver-cell")
        return None
    if not (args.driver_input and args.driver_output):
        raise CharError(
            "--driver-cell needs --driver-input and --driver-output: a SPICE .subckt does not "
            "say which of its pins is the input and which the output"
        )
    for f in args.driver_spice:
        if not f.is_file():
            raise CharError(f"--driver-spice file not found: {f}")
    known = tb.parse_spice_subckts(
        list(args.netlist) + list(args.cell_spice) + list(args.driver_spice)
    )
    if args.driver_cell not in known:
        raise CharError(
            f"no '.subckt {args.driver_cell}' in the SPICE files given; add the file that "
            "defines it with --driver-spice (or --cell-spice)"
        )
    ports, _ = known[args.driver_cell]
    power = args.driver_power or args.power
    ground = args.driver_ground or args.ground
    named = {args.driver_input, args.driver_output, power, ground}
    unknown = [p for p in ports if p.upper() not in {n.upper() for n in named}]
    if unknown:
        raise CharError(
            f"driver cell '{args.driver_cell}' has pin(s) {unknown} that none of "
            "--driver-input/--driver-output/--driver-power/--driver-ground names; every port "
            "of the driver must be connected"
        )
    for role, p in (("--driver-input", args.driver_input), ("--driver-output", args.driver_output)):
        if p.upper() not in {q.upper() for q in ports}:
            raise CharError(
                f"{role} '{p}' is not a port of '.subckt {args.driver_cell} {' '.join(ports)}'"
            )
    return Driver(args.driver_cell, args.driver_input, args.driver_output, power, ground, ports)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Characterize a SPICE cell with ngspice and write a Liberty file.",
        epilog="Every technology-specific constant lives in the --template file; see the "
        "module docstring for the template contract.",
    )
    ap.add_argument("netlist", type=Path, nargs="*", help="SPICE file(s) holding the .subckt(s)")
    ap.add_argument("--cell", action="append", default=[], metavar="NAME",
                    help="subckt to characterize; repeat for several (default: the only one)")
    ap.add_argument("--inputs", metavar="A,B", help="comma-separated input pins")
    ap.add_argument("--outputs", metavar="Y", help="comma-separated output pins")
    ap.add_argument("--power", default="VDD", metavar="PIN", help="supply pin (default: VDD)")
    ap.add_argument("--ground", default="VSS", metavar="PIN", help="ground pin (default: VSS)")
    ap.add_argument("--verilog", type=Path, metavar="FILE",
                    help="Verilog file declaring the module: the source of the pin directions. "
                    "Behavioural models work (the PDK's own sg13g2_stdcell.v does). A "
                    "*structural* netlist additionally lets gen_cell_tb.py check this netlist "
                    "against the cells it claims to be equivalent to, when --lib is also given")
    ap.add_argument("--lib", type=Path, metavar="FILE",
                    help="Liberty file used as the functional oracle (and, for a library cell, "
                    "as the source of pin directions)")
    ap.add_argument("--cell-spice", type=Path, action="append", default=[], metavar="FILE",
                    help="further SPICE subckts the netlist instantiates; repeat")
    ap.add_argument("--cell-verilog", type=Path, action="append", default=[], metavar="FILE",
                    help="Verilog models for the leaf cells a structural --verilog netlist "
                    "instantiates, for the Verilog-based function check; repeat")
    ap.add_argument("--iverilog", default="iverilog", metavar="BIN",
                    help="Icarus Verilog binary used for that check (default: iverilog)")
    ap.add_argument("--model-lib", type=Path, metavar="FILE", help="device model library")
    ap.add_argument("--corner", action="append", default=[], metavar="NAME:SECTION:VDD:TEMP",
                    help="process corner; repeat. Default: " + "  ".join(DEFAULT_CORNERS))
    ap.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, metavar="FILE",
                    help="Liberty template (default: lib_templates/sg13g2.lib.tmpl)")
    ap.add_argument("--print-template", action="store_true",
                    help="dump the template and exit, as a starting point for another technology")
    ap.add_argument("--delay-template", default="TIMING_DELAY_7x7ds1", metavar="NAME")
    ap.add_argument("--power-template", default="POWER_7x7ds1", metavar="NAME")
    ap.add_argument("--slews", default=DEFAULT_SLEWS_NS, metavar="LIST",
                    help="input slew index, in the template's time unit")
    ap.add_argument("--loads", default=DEFAULT_LOADS_PF, metavar="LIST",
                    help="output load index, in the template's capacitance unit")
    ap.add_argument("--lib-name", default=None, metavar="NAME",
                    help="library name stem (default: the netlist's stem)")
    ap.add_argument("-o", "--outdir", type=Path, default=None, metavar="DIR",
                    help="output directory (default: ./lib, relative to where you run it -- "
                    "never inside the PDK the netlist may come from)")
    ap.add_argument("--area", action="append", default=[], metavar="[CELL=]VALUE",
                    help="cell area for the Liberty 'area' attribute")
    ap.add_argument("--footprint", action="append", default=[], metavar="[CELL=]NAME")
    ap.add_argument("--combine", choices=tuple(COMBINE), default="max",
                    help="how to combine several sensitizing side states (default: max)")
    ap.add_argument("--cap-combine", choices=tuple(COMBINE), default="max",
                    help="how to combine input capacitance over side states (default: max)")
    ap.add_argument("--max-side-states", type=int, default=4, metavar="N",
                    help="cap on sensitizing side states per arc and sense (default: 4)")
    ap.add_argument("--max-cap-states", type=int, default=4, metavar="N",
                    help="cap on side states per capacitance measurement (default: 4)")
    ap.add_argument("--cap-slew", type=float, default=None, metavar="T",
                    help="slew for the capacitance decks (default: the fastest grid point, "
                    "where --cap-window actually discriminates)")
    ap.add_argument("--cap-load", type=float, default=0.001, metavar="C",
                    help="output load during the capacitance decks (default: 0.001)")
    ap.add_argument("--cap-window", choices=("ramp", "settled"), default="ramp",
                    help="how much of the pin charge counts as pin capacitance: 'ramp' "
                    "(default) integrates over the input transition only, which is what the "
                    "IHP libraries do; 'settled' integrates to the next settled state and so "
                    "also collects the Miller charge that flows while the output is still "
                    "switching -- about 30%% more on sg13g2_inv_1")
    ap.add_argument("--other-load", type=float, default=0.001, metavar="C",
                    help="load on the outputs that are not being measured (default: 0.001)")
    ap.add_argument("--settle", type=float, default=1.0, metavar="X",
                    help="multiplier on the settling allowance between edges (default: 1)")
    ap.add_argument("--driver-cell", metavar="NAME",
                    help="drive the pin under test with this cell instead of an ideal ramp, "
                    "the way vendor libraries are usually characterized. Needs "
                    "--driver-input/--driver-output; its .subckt must be in one of the SPICE "
                    "files given (or --driver-spice)")
    ap.add_argument("--driver-spice", type=Path, action="append", default=[], metavar="FILE",
                    help="extra SPICE file holding the driver cell; repeat")
    ap.add_argument("--driver-input", metavar="PIN", help="input pin of --driver-cell")
    ap.add_argument("--driver-output", metavar="PIN", help="output pin of --driver-cell")
    ap.add_argument("--driver-power", metavar="PIN",
                    help="supply pin of --driver-cell (default: the same as --power)")
    ap.add_argument("--driver-ground", metavar="PIN",
                    help="ground pin of --driver-cell (default: the same as --ground)")
    ap.add_argument("--driver-cal-load", type=float, default=0.001, metavar="C",
                    help="output load used while calibrating the driver, in the template's "
                    "capacitance unit (default: 0.001)")
    ap.add_argument("--driver-tol", type=float, default=0.02, metavar="X",
                    help="relative tolerance on the slew delivered to the pin (default: 0.02)")
    ap.add_argument("--driver-max-iter", type=int, default=12, metavar="N",
                    help="bisection steps per calibration (default: 12)")
    ap.add_argument("--driver-min-ramp", type=float, default=1e-13, metavar="S",
                    help="fastest ramp, in seconds, that may be fed to the driver; also what "
                    "the driver's own slew floor is measured at (default: 1e-13)")
    ap.add_argument("--driver-underrun", choices=("note", "error"), default="note",
                    help="what to do at a grid point faster than the driver can deliver: "
                    "characterize at the floor and say so in the report (default), or stop")
    ap.add_argument("--input-ramp", choices=("measured", "full"), default="measured",
                    help="what a slew index value means for the stimulus: 'measured' (default) "
                    "drives a ramp whose measured lower..upper transition equals the index, as "
                    "Liberty defines it; 'full' drives a full-swing ramp of exactly the index, "
                    "as lctime does. Use 'full' only to reproduce a library built that way")
    ap.add_argument("--energy-unit", default="auto", metavar="J",
                    help="SI value of the internal-power table unit (default: auto = "
                    "capacitive_load_unit * voltage_unit^2)")
    ap.add_argument("--no-power", action="store_true", help="omit the internal_power groups")
    ap.add_argument("--no-cap", action="store_true", help="omit the input capacitance measurement")
    ap.add_argument("--no-verify", action="store_true",
                    help="skip the per-corner functional check (gen_cell_tb.py), saving runtime")
    ap.add_argument("--compare-lib", type=Path, default=None, metavar="FILE",
                    help="reference Liberty to diff the result against (calibration)")
    ap.add_argument("--check-sta", dest="check_sta", action="store_true", default=True,
                    help="read every emitted library back with OpenSTA (default)")
    ap.add_argument("--no-check-sta", dest="check_sta", action="store_false")
    ap.add_argument("--spice-option", action="append", default=[], metavar="TEXT",
                    help="extra '.options TEXT' line for every generated deck; repeat. The "
                    "defaults are converged for this PDK (tightening reltol/abstol/vntol, or "
                    "switching to method=gear, moves the measured delays by under 0.2%%), so "
                    "this is for awkward cells and for trying things like 'klu'")
    ap.add_argument("--ngspice", default="ngspice", metavar="BIN")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2), metavar="N")
    ap.add_argument("--timeout", type=float, default=1800.0, metavar="S")
    ap.add_argument("--max-inputs", type=int, default=8, metavar="N",
                    help="refuse cells with more inputs than this (default: 8)")
    ap.add_argument("--keep-decks", action="store_true",
                    help="keep the generated decks and ngspice logs (they are kept on failure "
                    "in any case)")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.print_template:
        sys.stdout.write(args.template.read_text())
        return 0

    if not args.netlist:
        raise CharError("no SPICE netlist given (see --help)")
    for f in list(args.netlist) + list(args.cell_spice):
        if not f.is_file():
            raise CharError(f"SPICE file not found: {f}")
    if args.model_lib is None or not args.model_lib.is_file():
        raise CharError(f"device model library not found: {args.model_lib} (--model-lib)")
    if args.verilog and not args.verilog.is_file():
        raise CharError(f"Verilog netlist not found: {args.verilog}")
    for f in args.cell_verilog:
        if not f.is_file():
            raise CharError(f"--cell-verilog file not found: {f}")
    if args.lib and not args.lib.is_file():
        raise CharError(f"Liberty file not found: {args.lib}")

    def parse_map(items: list[str], conv):
        default, per = None, {}
        for it in items:
            if "=" in it:
                k, v = it.split("=", 1)
                per[k] = conv(v)
            else:
                default = conv(it)
        return default, per

    area_def, area_map = parse_map(args.area, float)
    fp_def, fp_map = parse_map(args.footprint, str)
    args.area_of = lambda n: area_map.get(n, area_def if area_def is not None else 0.0)
    args.footprint_of = lambda n: fp_map.get(n, fp_def or "")

    tmpl = Template.load(args.template, args.delay_template, args.power_template, args.energy_unit)
    args.slew_list = [float(x) for x in args.slews.replace(",", " ").split()]
    args.load_list = [float(x) for x in args.loads.replace(",", " ").split()]
    if len(args.slew_list) < 2 or len(args.load_list) < 2:
        raise CharError("--slews and --loads each need at least two points")
    if args.slew_list != sorted(args.slew_list) or args.load_list != sorted(args.load_list):
        raise CharError("--slews and --loads must be given in increasing order")

    args.units_cap = tmpl.units.cap
    driver = resolve_driver(args)
    corners = [Corner.parse(c) for c in (args.corner or DEFAULT_CORNERS)]
    args.lib_name = args.lib_name or args.netlist[0].stem
    # ./lib, not <netlist dir>/lib: the netlist is very often a read-only PDK file, and
    # writing results into a PDK install is both surprising and usually not permitted.
    outdir = args.outdir or Path("lib")
    try:
        outdir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CharError(f"cannot create the output directory {outdir}: {exc}\n  Use -o DIR.") from None

    cells = resolve_cells(args)
    for c in cells:
        if len(c.inputs) > args.max_inputs:
            raise CharError(
                f"cell '{c.name}' has {len(c.inputs)} inputs, above --max-inputs "
                f"{args.max_inputs}: the function sweep alone would need "
                f"{1 << len(c.inputs)} operating points"
            )

    gencmd = " \\\n    ".join(
        [f"{SCRIPT} {' '.join(str(f) for f in args.netlist)}"]
        + [f"--cell {c}" for c in args.cell]
        + ([f"--verilog {args.verilog}"] if args.verilog else [])
        + ([f"--lib {args.lib}"] if args.lib else [])
        + [f"--cell-spice {f}" for f in args.cell_spice]
        + [f"--cell-verilog {f}" for f in args.cell_verilog]
        + [f"--model-lib {args.model_lib}"]
        + [f"--corner {c}" for c in (args.corner or DEFAULT_CORNERS)]
        + [f"--template {args.template}"]
        + ([f"--driver-cell {args.driver_cell} --driver-input {args.driver_input} "
            f"--driver-output {args.driver_output}"] if args.driver_cell else [])
    )

    includes = [
        f".include {f.resolve()}"
        for f in dict.fromkeys(list(args.cell_spice) + list(args.netlist) + list(args.driver_spice))
    ]
    all_results: dict[str, list[CellResult]] = {}
    verdicts: dict[str, str] = {}
    written: list[Path] = []

    for corner in corners:
        sec = f" {corner.section}" if corner.section else ""
        ctx = Ctx(
            vdd=corner.vdd,
            temp=corner.temp,
            models=(f".lib {args.model_lib.resolve()}{sec}" if corner.section
                    else f".include {args.model_lib.resolve()}"),
            includes=includes,
            th=tmpl.thresholds,
            settle=args.settle,
            corner=corner,
            input_ramp=args.input_ramp,
            driver=driver,
            options=args.spice_option,
        )
        workdir = outdir / "decks" / corner.tag
        print(f"[{corner.tag}] characterizing {len(cells)} cell(s) ...", flush=True)
        results = []
        for cell in cells:
            # With a Liberty oracle the check is the full SPICE testbench, run before
            # anything is measured. Without one, the Verilog view is an equally independent
            # statement of what the transistors should compute -- but that check compares
            # against the truth table, so it has to wait until the table exists.
            if not args.no_verify and args.lib:
                verdict = verify_corner(cell, ctx, args, outdir / "decks")
                verdicts.setdefault(corner.name, []).append(verdict)
                print(f"  {cell.name}: {verdict}", flush=True)
            t0 = time.time()
            res = characterize(cell, ctx, args, tmpl, workdir)
            results.append(res)
            if not args.no_verify and not args.lib:
                verdict = (
                    verify_verilog(args, cell, res.table, outdir / "decks")
                    if args.verilog
                    else "skipped (no --lib and no --verilog: nothing to check the function against)"
                )
                verdicts.setdefault(corner.name, []).append(verdict)
                print(f"  {cell.name}: {verdict}", flush=True)
            print(
                f"  {cell.name}: {len(res.arcs)} arc(s), "
                f"{sum(len(a.states) for a in res.arcs)} side state(s), "
                f"{time.time() - t0:.1f} s",
                flush=True,
            )
        all_results[corner.name] = results

        text = emit_library(results, corner, args, tmpl, gencmd)
        path = outdir / f"{args.lib_name}_{corner.tag}.lib"
        path.write_text(text)
        written.append(path)
        print(f"  -> {path}", flush=True)

    # Machine-readable dump, in SI units, for regression diffing between runs.
    data = {
        "generator": SCRIPT,
        "library": args.lib_name,
        "template": str(args.template),
        "grid": {"slews": args.slew_list, "loads": args.load_list},
        "stimulus": (
            {"driver_cell": driver.cell, "input": driver.in_pin, "output": driver.out_pin}
            if driver else {"ideal_ramp": args.input_ramp}
        ),
        "units": {k: getattr(tmpl.units, k) for k in ("time", "cap", "volt", "curr", "leak", "energy")},
        "corners": {
            c.name: {
                "section": c.section, "vdd": c.vdd, "temp": c.temp,
                "cells": [
                    {
                        "name": r.cell.name,
                        "inputs": r.cell.inputs,
                        "outputs": r.cell.outputs,
                        "functions": r.functions,
                        "truth_table": r.table,
                        "leakage_w": r.leakage,
                        "capacitance_f": r.caps,
                        "arcs": [
                            {"pin": a.pin, "output": a.output, "sense": a.sense, "when": a.when,
                             "states": a.states, "tables_si": a.tables,
                             "achieved_slew_s": a.achieved}
                            for a in r.arcs
                        ],
                        "notes": r.notes,
                    }
                    for r in all_results[c.name]
                ],
            }
            for c in corners
        },
    }
    (outdir / "char_data.json").write_text(json.dumps(data, indent=1))
    written.append(outdir / "char_data.json")

    report = emit_report(all_results, corners, args, tmpl, gencmd, verdicts)
    if args.compare_lib:
        if not args.compare_lib.is_file():
            raise CharError(f"--compare-lib file not found: {args.compare_lib}")
        ref_corner = corners[0]
        ours = (outdir / f"{args.lib_name}_{ref_corner.tag}.lib").read_text()
        report += "\n" + "\n".join(compare_libs(ours, args.compare_lib, [c.name for c in cells]))
    (outdir / "char_report.md").write_text(report)
    written.append(outdir / "char_report.md")

    if args.check_sta:
        sta = shutil.which("sta")
        if sta is None:
            print("warning: OpenSTA ('sta') not found; skipping the read-back check")
        else:
            for path in [p for p in written if p.suffix == ".lib"]:
                script = outdir / "sta_check.tcl"
                script.write_text(f"read_liberty {path}\nexit\n")
                proc = subprocess.run(
                    [sta, "-no_init", "-no_splash", "-exit", str(script)],
                    capture_output=True, text=True,
                )
                bad = [l for l in (proc.stdout + proc.stderr).splitlines()
                       if re.search(r"\b(Error|Warning)\b", l)]
                if proc.returncode != 0 or bad:
                    raise CharError(
                        f"OpenSTA refused {path.name}:\n  " + "\n  ".join(bad[:20] or ["(no output)"])
                    )
                script.unlink()
            print(f"OpenSTA read back {len([p for p in written if p.suffix == '.lib'])} librar(y/ies) cleanly")

    if not args.keep_decks:
        shutil.rmtree(outdir / "decks", ignore_errors=True)

    print(f"Wrote {len(written)} files to {outdir}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CharError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except tb.GenError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
