# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Scope guards for the model-facing documentation
# ================================================================

"""Cheap guards on what the harness is allowed to tell the model.

Three of them, all reproduced:

* **F5** ``GDS_PYTHON_API.md`` must document ``draw_tap`` as an API, not hand the
  model the answer.  An example whose coordinates are the scaffold's own frame
  is the cell layout written into the reference manual, and a violation count
  taken from one cell teaches the model to expect that number for every cell.
* **F7** ``ORCHESTRATION.md`` must not carry an ``@context`` reference the model
  cannot resolve, nor tell it to inspect a rendered PNG -- the model is
  text-only, so the picture carries nothing and chasing it costs a turn.
* **F8** ``copilot-rcp.sh`` is the operator's own wrapper, outside this
  repository.  A copy inside it is a second, divergent entry point to the model.
* **Stage 5** the curriculum states the *objective* for a turn, and the same
  rule applies to it: it may name what the netlist says and what the tools
  measured, and it may not name geometry.  An objective carrying a coordinate is
  the scaffold's answer smuggled into the instruction, and it is only correct
  for the one cell it was copied from.

The rule these enforce: the harness gives the model the *facts of its own run*
and the API it may call.  It does not give it the geometry, and it does not send
it looking for things that are not there.
"""

from __future__ import annotations

import re

import pytest

from aion_layout.auto_scaffold import generate_scaffold_source
from aion_layout.spice_parser import parse_spice_file

#: Frame coordinates below this are process rules (enclosures, widths) that a
#: reference manual legitimately states.  At and above it they are *placement*
#: coordinates: the cell height, the active bands, the rails -- the scaffold's
#: answer, which the model has to derive from its own netlist instead.
FRAME_COORD_MIN_NM = 300.0


@pytest.fixture(scope="module")
def scaffold_frame(netlist_path) -> set[float]:
    """Every placement coordinate the auto-scaffold emits for the fixture cell.

    Read from the generator rather than hardcoded, so the guard tracks the
    scaffold instead of drifting away from it the first time it is retuned.
    """
    source = generate_scaffold_source(parse_spice_file(netlist_path)[0])
    numbers = {float(token) for token in re.findall(r"\d+\.\d+", source)}
    frame = {value for value in numbers if value >= FRAME_COORD_MIN_NM}
    assert frame, "the scaffold emitted no frame coordinates; the guard is vacuous"
    return frame


@pytest.fixture(scope="module")
def gds_api_doc(repo_root) -> str:
    path = repo_root / "GDS_PYTHON_API.md"
    assert path.is_file(), f"{path} is missing"
    return path.read_text()


@pytest.fixture(scope="module")
def draw_tap_section(gds_api_doc) -> str:
    match = re.search(r"^### `draw_tap.*?(?=^### |\Z)", gds_api_doc, re.S | re.M)
    assert match, (
        "GDS_PYTHON_API.md documents no draw_tap helper.  The model cannot clear "
        "LU.a/LU.b without it and has no way to discover an undocumented "
        "function."
    )
    return match.group(0)


# ---------------------------------------------------------------------------
# F5 -- the API reference documents an API, not this cell's layout
# ---------------------------------------------------------------------------

def test_draw_tap_example_uses_no_literal_coordinates(draw_tap_section):
    """Every ``Rect`` in the example must be built from the caller's variables."""
    fences = re.findall(r"```python\n(.*?)```", draw_tap_section, re.S)
    assert fences, f"the draw_tap section carries no example:\n{draw_tap_section}"

    for fence in fences:
        # Strip comments: prose inside a code block is prose.
        code = "\n".join(line.split("#", 1)[0] for line in fence.split("\n"))
        for call in re.findall(r"Rect\.from_lbrt\((.*?)\)", code, re.S):
            literals = re.findall(r"(?<![\w.])\d+(?:\.\d+)?", call)
            assert not literals, (
                f"the draw_tap example builds a rectangle from the literal "
                f"coordinates {literals} in:\n    Rect.from_lbrt({call.strip()})\n"
                "That is a placement decision, and placement is the caller's "
                "job.  Copied constants are the scaffold's geometry pasted into "
                "the reference manual: the model reproduces them instead of "
                "deriving a tap from the rails and active bands it actually drew."
            )


def test_draw_tap_section_does_not_restate_the_scaffold_frame(
    draw_tap_section, scaffold_frame
):
    doc_numbers = {
        float(token) for token in re.findall(r"\b\d+(?:\.\d+)?\b", draw_tap_section)
    }
    leaked = sorted(scaffold_frame & doc_numbers)
    assert not leaked, (
        f"the draw_tap documentation states the scaffold's own frame "
        f"coordinates {leaked}.  Those are the numbers the generator already "
        "holds as variables; repeating them here invites the model to hardcode a "
        "tap position that is only correct for one cell."
    )


#: Counts that belong to one measured run, never to a reference manual.
CELL_SPECIFIC_COUNTS = [
    (r"COUNT:\s*\d", "Magic's own trailer from one run"),
    (r"\b\d+\s+violations?\b", "a violation count"),
    (r"\bLU\.[ab]\b[^\n]{0,12}[x×]\s*\d", "a per-rule histogram"),
    (r"\b\d+\s*[x×]\s*LU\.[ab]\b", "a per-rule histogram"),
    (r"\b\d+\s+items?\s+across\b", "a KLayout item count"),
    (r"AION_inv_nand2_nor2_1", "the name of the one cell this run happens to build"),
]


@pytest.mark.parametrize("pattern,what", CELL_SPECIFIC_COUNTS)
def test_api_doc_states_no_cell_specific_violation_count(gds_api_doc, pattern, what):
    hits = re.findall(pattern, gds_api_doc)
    assert not hits, (
        f"GDS_PYTHON_API.md states {what}: {hits}.\nThe reference manual is read "
        "for every cell the loop ever builds.  A number measured on one of them "
        "reads as a target: the model stops when it has matched the count in the "
        "documentation instead of when the layout is clean."
    )


def test_api_doc_still_explains_the_latchup_rules(gds_api_doc):
    """Anti-vacuity control for the guards above.

    Stripping the counts must not strip the explanation with them: the model
    needs to know *why* LU.a and LU.b fire and that the fix is a tap, which is
    exactly the part that generalises.
    """
    for needle in ("LU.a", "LU.b", "draw_tap"):
        assert needle in gds_api_doc, (
            f"{needle!r} is gone from GDS_PYTHON_API.md; the guards above are "
            "meant to remove this cell's numbers, not the rule the numbers came "
            "from"
        )


# ---------------------------------------------------------------------------
# F7 -- the orchestration document sends the model nowhere it cannot go
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def orchestration_doc(repo_root) -> str:
    path = repo_root / "ORCHESTRATION.md"
    assert path.is_file(), f"{path} is missing"
    return path.read_text()


def test_orchestration_doc_has_no_at_context_reference(orchestration_doc):
    assert "@context" not in orchestration_doc, (
        "ORCHESTRATION.md still carries an '@context' reference.  Nothing "
        "resolves it: the model spends a turn hunting for a path that does not "
        "exist, and the turns are the budget."
    )


#: Verbs that turn a mention of the PNG into an instruction to go and look at it.
_INSPECTION_VERBS = (
    "look at", "look into", "inspect", "examine", "view the", "open the",
    "check the", "read the", "study the", "see the",
)


def test_orchestration_doc_never_tells_the_model_to_inspect_the_png(orchestration_doc):
    """The model is text-only; a picture carries nothing it can act on."""
    offenders = []
    for number, line in enumerate(orchestration_doc.split("\n"), start=1):
        low = line.lower()
        if "png" not in low and "image" not in low:
            continue
        if any(verb in low for verb in _INSPECTION_VERBS):
            offenders.append(f"{number}: {line.strip()}")

    assert not offenders, (
        "ORCHESTRATION.md tells the model to inspect the rendered image:\n"
        + "\n".join(offenders)
        + "\nThe model cannot see it.  The layout digest exists precisely because "
        "the PNG carried no information for it; pointing at the picture spends a "
        "turn and returns nothing."
    )


def test_orchestration_doc_still_explains_the_digest_that_replaced_the_png(
    orchestration_doc,
):
    """Anti-vacuity control: the PNG is still rendered, for humans."""
    assert "layout digest" in orchestration_doc.lower(), (
        "the document no longer explains what replaced the rendered PNG as the "
        "model's view of its own geometry"
    )


# ---------------------------------------------------------------------------
# F8 -- the model wrapper stays outside this repository
# ---------------------------------------------------------------------------

def test_no_copilot_wrapper_inside_the_repository(repo_root):
    found = [
        path
        for path in repo_root.rglob("copilot-rcp.sh")
        if ".git" not in path.parts
    ]
    assert not found, (
        f"copilot-rcp.sh exists inside the repository: {found}.\nThe wrapper is "
        "the operator's, and orchestrate.sh reaches it through $COPILOT_RCP.  A "
        "copy in the tree is a second entry point to the model that nothing "
        "keeps in step with the real one -- and it sits in the directory the "
        "model itself can edit."
    )


def test_orchestrate_reaches_the_wrapper_through_an_overridable_variable(repo_root):
    text = (repo_root / "orchestrate.sh").read_text()
    assert 'COPILOT_RCP="${COPILOT_RCP:-' in text, (
        "orchestrate.sh must take the wrapper path from an overridable "
        "$COPILOT_RCP; hardcoding it is what makes an in-tree copy tempting"
    )
    assert '[[ -x "$COPILOT_RCP" ]] || fatal' in text, (
        "the wrapper must be checked before anything is spent, not discovered "
        "missing after the deterministic pipeline has already run"
    )


# ---------------------------------------------------------------------------
# Stage 5 -- the curriculum tells the model its objective, not its layout
# ---------------------------------------------------------------------------

import importlib.util
import sys

from aion_layout.spice_parser import parse_spice


def _load_curriculum(repo_root):
    path = repo_root / "scripts" / "curriculum.py"
    spec = importlib.util.spec_from_file_location("aion_scope_curriculum", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def curriculum(repo_root):
    return _load_curriculum(repo_root)


@pytest.fixture(scope="module")
def curriculum_source(repo_root) -> str:
    path = repo_root / "scripts" / "curriculum.py"
    assert path.is_file(), f"{path} is missing"
    return path.read_text()


def _objectives(curriculum, subckt) -> dict:
    """Every rung's objective text for one netlist, keyed by rung."""
    return {gate.key: gate.objective for gate in curriculum.gates(subckt)}


def _code_only(source: str) -> str:
    """Strip comments and docstrings: prose about a number is not the number.

    The module's own docstring quotes the measurements that motivated Stage 5,
    and a guard that could not tell a quoted measurement from an emitted
    coordinate would force those measurements out of the file -- which is where
    the reasoning for every constant in it lives.
    """
    import io
    import tokenize

    out = []
    previous = tokenize.INDENT
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            continue
        if token.type == tokenize.STRING and previous in (
            tokenize.INDENT, tokenize.NEWLINE, tokenize.NL, tokenize.DEDENT,
        ):
            continue  # a docstring
        out.append(token.string)
        if token.type not in (tokenize.NL, tokenize.NEWLINE):
            previous = token.type
    return "\n".join(out)


def test_curriculum_source_names_no_cell(curriculum_source):
    """The ladder is derived per netlist; a cell name in it is a hardcoded cell."""
    assert "AION_inv_nand2_nor2_1" not in curriculum_source, (
        "scripts/curriculum.py names the one cell this run happens to build.  "
        "Every objective must be derived from the netlist it is given, or the "
        "second cell the user generates gets the first cell's instructions."
    )


def test_curriculum_source_emits_no_placement_coordinate(curriculum_source):
    """No number at or above the frame threshold may be emitted as geometry.

    The same threshold ``GDS_PYTHON_API.md`` is held to: below it are process
    rules a reference may state, at and above it are placement decisions that
    belong to the generator and differ for every cell.
    """
    code = _code_only(curriculum_source)
    numbers = {float(tok) for tok in re.findall(r"\b\d+\.\d+\b", code)}
    leaked = sorted(v for v in numbers if v >= FRAME_COORD_MIN_NM)
    assert not leaked, (
        f"scripts/curriculum.py carries the placement coordinates {leaked} in "
        "code.  An objective that states where to put a shape is the scaffold's "
        "answer pasted into the instruction; the model has to derive placement "
        "from its own netlist."
    )


@pytest.mark.parametrize("n_inputs", [1, 2, 3, 4, 5, 6])
def test_generated_objectives_state_no_scaffold_geometry(
    curriculum, synthetic_netlist, scaffold_frame, n_inputs
):
    """Nothing the ladder generates may restate the scaffold's own frame."""
    subckt = parse_spice(synthetic_netlist(n_inputs))[0]
    for key, objective in _objectives(curriculum, subckt).items():
        numbers = {float(tok) for tok in re.findall(r"\b\d+(?:\.\d+)?\b", objective)}
        leaked = sorted(scaffold_frame & numbers)
        assert not leaked, (
            f"the {key!r} objective for a {n_inputs}-input cell states the "
            f"scaffold's frame coordinates {leaked}:\n{objective}"
        )


def test_generated_objectives_name_only_this_netlists_own_nets(
    curriculum, synthetic_netlist
):
    """An objective may name nets, and only nets this netlist actually has.

    Anti-vacuity for the guard above: the objectives are *supposed* to be
    specific -- to the netlist in front of them.  This is what separates
    "derived from the netlist" from "says nothing at all".
    """
    subckt = parse_spice(synthetic_netlist(3), )[0]
    objectives = _objectives(curriculum, subckt)
    own = set(subckt.pins) | set(subckt.nets)

    gates_rung = objectives["gates"]
    named = set(re.findall(r"\b(?:I\d+|O\d+|n\d+|VDD|VSS)\b", gates_rung))
    assert named, f"the gates objective names no net at all:\n{gates_rung}"
    assert named <= own, (
        f"the gates objective names {sorted(named - own)}, which this netlist "
        f"does not contain; its nets are {sorted(own)}"
    )


def test_the_curriculum_still_says_what_each_rung_is_for(curriculum, netlist_path):
    """Anti-vacuity control for every guard above.

    Stripping the geometry must not strip the instruction with it: each rung
    still has to say what to do and what clears it, which is the part that
    generalises.
    """
    subckt = parse_spice_file(netlist_path)[0]
    for gate in curriculum.gates(subckt):
        assert len(gate.objective) > 200, (
            f"rung {gate.key} has been reduced to {len(gate.objective)} characters; "
            "the guards are meant to remove this cell's geometry, not the "
            "objective the geometry was standing in for"
        )
        assert gate.exit_text.strip(), f"rung {gate.key} states no exit criterion"
