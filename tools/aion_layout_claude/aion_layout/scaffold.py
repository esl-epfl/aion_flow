# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-05
#  Description:               Starting cell generator emitted from a netlist
# ================================================================

"""The first ``cells/<name>.py`` of an iteration, written from the netlist.

This is a thin wrapper over the vendored :mod:`aion_layout.auto_scaffold`, and
the thinness is the point: ``auto_scaffold`` already knows how to place a row
of poly gates under the netlist's inputs, and it is *deliberately incomplete*
-- it draws no taps, no source/drain contacts and no routing.  Re-deriving that
placement here would give the flow two floorplanners that could disagree.

What this module adds is the three things a scaffold has to have before a model
can iterate on it, and that ``auto_scaffold`` does not emit:

**A module docstring that says what is missing.**  A file that looks like a
finished cell generator and is not one is the single easiest way to waste an
iteration.  The emitted docstring lists every gap by name, so the module is
self-describing wherever it is read -- in an editor, in the evidence packet, or
by the model that has to finish it.

**A ``__main__`` block.**  The reference generators in ``context/py/`` can be
run directly to write their GDS, and a scaffold that cannot be run is a
scaffold nobody checks.

**Refusal to emit something that will not run.**  The source is parsed and
compiled before it is written, and every ``tech['...']`` name it mentions is
looked up in the technology object.  A scaffold that raises ``KeyError`` on
import costs an iteration to diagnose; a :class:`ScaffoldError` at the moment
of writing costs none.  ``cell_width`` is checked against the technology for
the same reason and is the likelier mistake: it is in **nanometres**, so a
width given in micrometres compiles, imports, and then raises a bare
``ValueError`` from ``Rect.from_lbrt`` the first time ``generate`` is called --
a failure that reaches the flow as a broken generator rather than as a bad
argument.

The emitted file is a *starting point*, never a cell.  It will not pass DRC and
cannot pass LVS, and it says so about itself.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from .auto_scaffold import generate_scaffold_source
from .netlist_view import suggest_gate_order
from .spice_parser import Subckt, SpiceParseError, parse_first_subckt
from .tech import Tech, sg13g2_tech


class ScaffoldError(RuntimeError):
    """Raised when a scaffold cannot be produced, or would not import."""


#: ``tech['X']`` / ``tech["X"]`` inside the generated source.
_TECH_LAYER_RE = re.compile(r"""tech\[\s*(['"])([A-Za-z0-9_]+)\1\s*\]""")

#: Layers the ``building_blocks`` helpers the scaffold calls reach for without
#: naming them in the emitted source.  Checked alongside the literal ones so a
#: technology missing an implant layer fails here and not at import time.
_IMPLICIT_LAYERS: Tuple[str, ...] = ("Activ", "PSD", "Metal1")

#: Fallback site width in nm for a technology that declares no standard cell
#: grid.  ``auto_scaffold`` hard-codes the same number.
_SITE_WIDTH_NM = 480.0


def scaffold_source(
    subckt: Subckt,
    *,
    tech: Optional[Tech] = None,
    cell_name: Optional[str] = None,
    cell_width: Optional[float] = None,
) -> str:
    """Return Python source for a starter generator for ``subckt``.

    ``cell_name`` only names the cell in the docstring and the ``__main__``
    block; ``generate`` still takes the name from its caller, because the cell
    is built under whatever name the flow asks for.

    ``cell_width`` is in **nanometres**, like every other coordinate in this
    framework; ``None`` lets ``auto_scaffold`` pick two sites per input.

    Raises :class:`ScaffoldError` when the source would not compile, when it
    does not define ``generate(name, tech)``, when it mentions a layer the
    technology does not have, or when ``cell_width`` leaves no room for the
    gates.
    """
    tech = tech or sg13g2_tech
    if not isinstance(subckt, Subckt):
        raise ScaffoldError(f"expected a Subckt, got {type(subckt).__name__}")
    if not subckt.devices:
        raise ScaffoldError(
            f"subcircuit {subckt.name!r} declares no MOSFETs; there is nothing "
            "to place and a scaffold would be an empty cell"
        )
    name = cell_name or subckt.name
    _check_cell_width(cell_width, subckt, tech)

    try:
        source = generate_scaffold_source(subckt, cell_width=cell_width)
    except Exception as exc:  # auto_scaffold is vendored; report, never mask
        raise ScaffoldError(
            f"auto_scaffold could not place {subckt.name!r}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    source = _replace_module_docstring(source, _docstring(subckt, name))
    source += _main_block(name)

    _check_layers(source, tech)
    tree = _parse(source)
    _check_generate(tree, source)
    try:
        compile(source, f"<scaffold:{name}>", "exec")
    except SyntaxError as exc:  # pragma: no cover - _parse would have caught it
        raise ScaffoldError(f"scaffold for {name!r} does not compile: {exc}") from exc
    return source


def scaffold_module(
    netlist: Path | str,
    out_py: Path | str,
    *,
    cell_name: Optional[str] = None,
    tech: Optional[Tech] = None,
    cell_width: Optional[float] = None,
    force: bool = False,
) -> Path:
    """Write a starter generator for the first subcircuit of ``netlist``.

    Returns the path written.  ``cell_width`` is in **nanometres**.  An
    existing ``out_py`` is refused rather than overwritten unless ``force`` is
    set: by the second iteration that file is the model's cell, and silently
    replacing it with a scaffold would throw the work away with no error to
    notice.
    """
    netlist_path = Path(netlist)
    if not netlist_path.is_file():
        raise ScaffoldError(f"no netlist at {netlist_path}")
    try:
        subckt = parse_first_subckt(netlist_path)
    except SpiceParseError as exc:
        raise ScaffoldError(f"cannot parse {netlist_path}: {exc}") from exc

    out_path = Path(out_py)
    if out_path.exists() and not force:
        raise ScaffoldError(
            f"{out_path} already exists; pass force=True to replace it with a "
            "scaffold (this discards whatever is in it)"
        )

    source = scaffold_source(
        subckt, tech=tech, cell_name=cell_name, cell_width=cell_width
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(source)
    return out_path


# ---------------------------------------------------------------------------
# Source surgery
#
# The docstring is located through the AST rather than by matching the string
# ``auto_scaffold`` happens to emit today.  A regex over vendored source is a
# silent failure waiting for the day that source changes; a missing docstring
# node is something this module can see and handle.
# ---------------------------------------------------------------------------


def _parse(source: str) -> ast.Module:
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        raise ScaffoldError(f"generated scaffold does not parse: {exc}") from exc


def _replace_module_docstring(source: str, docstring: str) -> str:
    """Return ``source`` with its module docstring replaced by ``docstring``."""
    tree = _parse(source)
    lines = source.splitlines()
    body = tree.body
    if not body:
        raise ScaffoldError("generated scaffold is empty")

    first = body[0]
    is_docstring = (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    )
    block = _docstring_lines(docstring)
    if is_docstring:
        end = first.end_lineno or first.lineno
        lines[first.lineno - 1 : end] = block
    else:
        # No docstring to replace.  A module docstring may legally precede a
        # ``from __future__`` import, so inserting before the first statement
        # is always valid.
        lines[first.lineno - 1 : first.lineno - 1] = block + [""]
    return "\n".join(lines) + "\n"


def _docstring_lines(text: str) -> List[str]:
    if '"""' in text:
        raise ScaffoldError("scaffold docstring may not contain a triple quote")
    return ['"""' + text.rstrip() + '\n"""']


def _check_generate(tree: ast.Module, source: str) -> None:
    """Refuse a scaffold that does not define ``generate(name, tech)``."""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "generate":
            args = [a.arg for a in node.args.args]
            if args[:2] != ["name", "tech"]:
                raise ScaffoldError(
                    "generated scaffold defines generate"
                    f"({', '.join(args)}); the flow calls generate(name, tech)"
                )
            return
    raise ScaffoldError(
        "generated scaffold defines no module-level generate(); the flow has "
        "no other entry point into a cell module"
    )


def _check_cell_width(
    cell_width: Optional[float], subckt: Subckt, tech: Tech
) -> None:
    """Refuse a ``cell_width`` the gates cannot be placed in.

    ``auto_scaffold`` insets the active area by half a site on each end and
    spreads the gates across what is left.  A width at or below one site makes
    that span zero or negative, and the generator it emits compiles and imports
    before dying inside ``Rect.from_lbrt`` -- so the check belongs here, where
    the number came in, and the message names the unit, because passing
    micrometres is the way this goes wrong.
    """
    if cell_width is None:
        return
    if isinstance(cell_width, bool) or not isinstance(cell_width, (int, float)):
        raise ScaffoldError(
            f"cell_width must be a number of nanometres, not "
            f"{type(cell_width).__name__}"
        )
    width = float(cell_width)
    if width != width or width in (float("inf"), float("-inf")):
        raise ScaffoldError(f"cell_width {cell_width!r} is not a finite number")

    site = float(tech.standard_cell.get("site_width_nm", _SITE_WIDTH_NM))
    span = width - site
    if span <= 0.0:
        raise ScaffoldError(
            f"cell_width {width:g} nm leaves no active area: auto_scaffold "
            f"insets half of the {site:g} nm site at each end, so the width "
            f"must exceed {site:g} nm. cell_width is in NANOMETRES -- "
            f"{width:g} um would be {width * 1000:g}"
        )

    gates = len(suggest_gate_order(subckt))
    if gates < 1:
        return
    poly = tech.get("GatPoly")
    needed = (poly.min_width or 0.0) + (poly.min_spacing or 0.0) if poly else 0.0
    pitch = span / (gates + 1)
    if needed and pitch < needed:
        raise ScaffoldError(
            f"cell_width {width:g} nm gives a gate pitch of {pitch:.1f} nm for "
            f"{gates} input gate(s); GatPoly needs {needed:g} nm "
            f"(width {poly.min_width:g} + space {poly.min_spacing:g}). "
            f"cell_width is in NANOMETRES"
        )


def _check_layers(source: str, tech: Tech) -> None:
    """Refuse a scaffold naming a layer ``tech`` does not have."""
    named = {m.group(2) for m in _TECH_LAYER_RE.finditer(source)}
    missing = sorted(
        n for n in named.union(_IMPLICIT_LAYERS) if tech.get(n) is None
    )
    if missing:
        raise ScaffoldError(
            f"technology {tech.name!r} has no layer(s) "
            + ", ".join(missing)
            + "; the scaffold would raise KeyError on import"
        )


# ---------------------------------------------------------------------------
# The self-description
# ---------------------------------------------------------------------------

#: What the scaffold does not draw.  Each entry is one line of the emitted
#: docstring and names a gap the model has to close.  ``auto_scaffold``'s own
#: comments are the source for the first two DRC claims; the prBoundary entry
#: is a property of ``Cell.write_gds``, which emits ``_shapes`` only and never
#: the rectangle passed to ``set_boundary``.
_MISSING: Tuple[str, ...] = (
    "Source/drain contacts.  No Cont is drawn anywhere, so no transistor "
    "terminal reaches Metal1 and no device is wired to anything.",
    "Routing.  The Metal1 shapes are isolated stubs: one bar per input gate "
    "and one stub for the output.  Internal nets have no geometry at all.",
    "Substrate and well taps.  Neither rail is tapped, which auto_scaffold "
    "records as eight LU.a/LU.b latch-up violations in a live DRC run.",
    "Minimum area.  At the default cell width the input/output stubs are "
    "below M1.d (0.09 um^2); auto_scaffold records four such violations.",
    "Net labels.  draw_power_rail() adds a Port and no TextShape, so VDD/VSS "
    "reach the GDS as a pin text (8/2) with no Metal1 label text (8/25), and "
    "no internal net is labelled at all.",
    "Well/implant detail.  One NWell rectangle covers the p-row; there is no "
    "PSD/NSD tap implant and no per-row implant sizing.",
    "Device sizing.  Both diffusion strips are one nominal height; the "
    "netlist's w= values are not honoured, so extracted widths will not match.",
)


def _docstring(subckt: Subckt, name: str) -> str:
    """Return the module docstring for the emitted scaffold."""
    lines: List[str] = [
        f"SCAFFOLD ONLY -- an unfinished starting point for {name}.",
        "",
        "Written by aion_layout.scaffold from the target netlist.  It places a",
        "poly gate under every input and nothing else that a cell needs.  It",
        "will not pass DRC and it cannot pass LVS; do not mistake it for a cell.",
        "",
        f"Netlist: .subckt {subckt.name} {' '.join(subckt.pins)}",
        f"Devices: {len(subckt.nmos_devices)} nmos, {len(subckt.pmos_devices)} pmos",
    ]
    output = subckt.output_net
    lines.append(
        f"Inputs:  {' '.join(subckt.input_nets) or '(none identified)'}"
        f"   Output: {output or '(not identified)'}"
    )
    internal = sorted(subckt.nets - set(subckt.pins))
    lines.append(f"Internal nets (undrawn): {' '.join(internal) or '(none)'}")
    lines += ["", "DELIBERATELY MISSING -- the model draws these:", ""]
    for i, item in enumerate(_MISSING, 1):
        lines += _wrap(f"{i}. {item}", indent="   ")
    return "\n".join(lines)


def _wrap(text: str, *, indent: str = "", width: int = 76) -> List[str]:
    """Wrap ``text`` to ``width`` columns, continuation lines at ``indent``."""
    words: Sequence[str] = text.split()
    out: List[str] = []
    line = ""
    for word in words:
        prefix = indent if out else ""
        candidate = f"{line} {word}" if line else prefix + word
        if line and len(candidate) > width:
            out.append(line)
            line = indent + word
        else:
            line = candidate
    if line:
        out.append(line)
    return out


def _main_block(name: str) -> str:
    """Return the ``__main__`` block, in the shape of ``context/py/*.py``."""
    return (
        "\n"
        'if __name__ == "__main__":\n'
        "    import sys\n"
        "\n"
        "    from aion_layout.tech import sg13g2_tech\n"
        "\n"
        f"    out = sys.argv[1] if len(sys.argv) > 1 else {name + '.gds'!r}\n"
        f"    generate({name!r}, sg13g2_tech).write_gds(out)\n"
        f'    print(f"wrote {{out}}")\n'
    )


__all__ = ["ScaffoldError", "scaffold_module", "scaffold_source"]
