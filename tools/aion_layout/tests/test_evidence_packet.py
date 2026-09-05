# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Golden tests for the evidence packet builder
# ================================================================

"""The evidence packet is the only thing the model is shown.

The historical defect: ``pipeline.sh`` built the payload by grepping
``report.txt`` for ``^(DRC|LVS|RESULT):`` and for ``violation|mismatch|...``.
Against the real, verdict-free ``report.txt`` both greps matched nothing and the
entire payload injected into the prompt was three characters -- a line reading
``---``.  Every test here asserts that some specific fact the model needs to fix
the cell actually reaches it.
"""

from __future__ import annotations

import re
import sys

import pytest

from conftest import run

FOOTER_TRUNCATED_RE = re.compile(r"^truncated blocks:\s*(.*)$", re.MULTILINE)
BLOCK_OPEN_RE = re.compile(r"^===== \[(\d+)\] (?!END)(.*) =====$", re.MULTILINE)


def _packet(evidence, netlist_path, iter0_dir, cell_name, iter0_module, **kw):
    return evidence.build_evidence(
        netlist=netlist_path,
        iter_dir=iter0_dir,
        cell_name=cell_name,
        module_path=iter0_module,
        **kw,
    )


def _block(packet: str, index: int) -> str:
    """Return the body of one labelled block."""
    match = re.search(
        rf"^===== \[{index}\] (?P<title>.*) =====$(?P<body>.*?)"
        rf"^===== \[{index}\] END (?P=title) =====$",
        packet,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"block [{index}] is missing from the packet"
    return match.group("body")


# ---------------------------------------------------------------------------
# Content the model cannot fix the cell without
# ---------------------------------------------------------------------------

def test_packet_is_not_three_characters(evidence, netlist_path, iter0_dir, cell_name, iter0_module):
    packet = _packet(evidence, netlist_path, iter0_dir, cell_name, iter0_module)
    assert len(packet) > 5000, (
        f"the packet is only {len(packet)} characters; the payload the loop used "
        "to inject was three ('---') and the model was shown nothing"
    )
    indices = [int(i) for i, _title in BLOCK_OPEN_RE.findall(packet)]
    assert indices == sorted(indices) and indices[:7] == [1, 2, 3, 4, 5, 6, 7], (
        f"blocks must be present and in order, got {indices}; a missing block "
        "is a whole class of evidence the model never sees"
    )


def test_packet_carries_the_target_netlist(evidence, netlist_path, iter0_dir, cell_name, iter0_module):
    packet = _packet(evidence, netlist_path, iter0_dir, cell_name, iter0_module)
    block = _block(packet, 1)
    assert f".subckt {cell_name}" in block, (
        "the .subckt line must be inlined verbatim; the prompt told the model to "
        "implement 'the topology implied by the SPICE netlist' and then never "
        "showed it the netlist, named its path or @-referenced it"
    )
    assert "I1_bar" in block, (
        "the internal node I1_bar must be visible; it is the fourth gate net, "
        "and the scaffold that gates only the three external inputs is exactly "
        "one device per type short because of it"
    )
    assert re.search(r"4 distinct gate nets", block), (
        f"the packet must state how many distinct gate nets there are, got:\n"
        f"{block}; 4 gate nets against 3 input pins is the diagnosis"
    )


def test_packet_carries_both_latchup_rule_codes(evidence, netlist_path, iter0_dir, cell_name, iter0_module):
    packet = _packet(evidence, netlist_path, iter0_dir, cell_name, iter0_module)
    assert "LU.a" in packet and "LU.b" in packet, (
        "both latch-up rule codes must reach the model; they are the only DRC "
        "violations in the run and the fix (well/substrate taps) is not "
        "guessable from a bare violation count"
    )
    verdict = _block(packet, 2)
    assert "LU.a x4" in verdict and "LU.b x4" in verdict, (
        f"the verdict block must carry the measured histogram, got:\n{verdict}"
    )
    assert "MAGIC DRC   : FAIL" in verdict, (
        f"the recomputed Magic verdict must be FAIL, got:\n{verdict}; it is "
        "recomputed from the raw report precisely so a broken report.txt cannot "
        "make it read PASS"
    )
    assert "[INFO] COUNT: 8" in _block(packet, 3), (
        "the Magic report is inlined verbatim, trailer included, so the model "
        "can check the parser against the tool"
    )


def test_packet_carries_the_lvs_mismatch(evidence, netlist_path, iter0_dir, cell_name, iter0_module):
    packet = _packet(evidence, netlist_path, iter0_dir, cell_name, iter0_module)
    block = _block(packet, 5)
    assert "layout=3" in block and "schematic=4" in block, (
        f"the 3-vs-4 per-type device mismatch must be in the packet, got:\n"
        f"{block}; without it the model cannot tell a missing device from a "
        "miswired one"
    )
    assert "a_155_82#" in packet, (
        "the extracted node a_155_82# must reach the model; it is the single "
        "node that both I1 and I2 map onto and the only place the LVS log names "
        "the Metal1 short"
    )
    assert "MISMATCH" in block, "mismatched counts must be labelled as such"


# ---------------------------------------------------------------------------
# The layout digest: what a rendered PNG cannot show
# ---------------------------------------------------------------------------

def test_layout_digest_names_the_i1_o0_short(evidence, netlist_path, iter0_dir, cell_name, iter0_module):
    digest = _block(
        _packet(evidence, netlist_path, iter0_dir, cell_name, iter0_module), 7
    )
    assert "cross-net overlaps on routing layers" in digest, (
        f"the digest must have a cross-net overlap section, got:\n{digest}"
    )
    overlap_section = digest.split("cross-net overlaps on routing layers", 1)[1]
    overlap_section = overlap_section.split("--- poly/active", 1)[0]
    assert "(none found)" not in overlap_section, (
        f"the iteration_0 generator emits the I1 Metal1 input bar at "
        f"(1295,1390)-(1585,1820) and the O0 output stub at "
        f"(1310,1330)-(1570,2060); they overlap, so I1 and O0 are ONE Metal1 "
        f"node.  Reporting no overlap means the short detector is blind:\n"
        f"{overlap_section}"
    )
    assert re.search(r"\bI1\b", overlap_section) and re.search(r"\bO0\b", overlap_section), (
        f"the overlap row must name both shorted nets, got:\n{overlap_section}"
    )
    assert "1310" in overlap_section and "1820" in overlap_section, (
        f"the overlap row must give the intersection rectangle so the model can "
        f"move the right edge, got:\n{overlap_section}"
    )
    assert "SHORT" in overlap_section, (
        "the section must say plainly that an overlap is a short; a table of "
        "coordinates with no verdict was ignored by the model"
    )


def test_layout_digest_counts_poly_active_crossings(evidence, netlist_path, iter0_dir, cell_name, iter0_module):
    digest = _block(
        _packet(evidence, netlist_path, iter0_dir, cell_name, iter0_module), 7
    )
    assert "poly/active crossings" in digest, (
        f"the digest must count the transistors the geometry implies, got:\n{digest}"
    )
    match = re.search(
        r"crossings=(\d+)\s+devices required by netlist=(\d+)\s+->\s+(.*)", digest
    )
    assert match is not None, (
        f"the crossings/required summary line is missing from:\n{digest}"
    )
    crossings, required, verdict = int(match.group(1)), int(match.group(2)), match.group(3)
    assert (crossings, required) == (6, 8), (
        f"the iteration_0 geometry has 3 gates crossing 2 active areas = 6 "
        f"crossings against the netlist's 8 devices, got {crossings} vs "
        f"{required}; this pair is what tells the model it is two transistors "
        "short before any tool runs"
    )
    assert "2 missing" in verdict, (
        f"the shortfall must be stated, not left as two numbers, got {verdict!r}"
    )


def test_layout_digest_lists_labels_and_ports(evidence, netlist_path, iter0_dir, cell_name, iter0_module):
    digest = _block(
        _packet(evidence, netlist_path, iter0_dir, cell_name, iter0_module), 7
    )
    assert "text shapes" in digest and "ports" in digest, (
        f"labels and ports are invisible in a rendered PNG, which is why the "
        f"digest replaces it; got:\n{digest}"
    )
    for net in ("I0", "I1", "I2", "O0", "VDD", "VSS"):
        assert re.search(rf"^{net}\s", digest, re.MULTILINE), (
            f"port/label {net} is missing from the digest:\n{digest}"
        )


# ---------------------------------------------------------------------------
# The byte budget
# ---------------------------------------------------------------------------

def test_packet_fits_the_default_budget(evidence, netlist_path, iter0_dir, cell_name, iter0_module):
    packet = _packet(evidence, netlist_path, iter0_dir, cell_name, iter0_module)
    size = len(packet.encode("utf-8"))
    assert size <= evidence.DEFAULT_MAX_BYTES, (
        f"the packet is {size} bytes against a {evidence.DEFAULT_MAX_BYTES} byte "
        "budget; an oversized packet crowds the model's context out of the "
        "actual layout work"
    )
    footer = FOOTER_TRUNCATED_RE.search(packet)
    assert footer is not None and footer.group(1).strip() == "none", (
        f"nothing should need truncating at the default budget, footer says "
        f"{footer.group(1) if footer else None!r}"
    )
    assert f"/ budget {evidence.DEFAULT_MAX_BYTES}" in packet, (
        "the footer must state the budget it was measured against"
    )


def test_the_example_is_given_up_before_any_measurement_is_cut(
    evidence, netlist_path, iter0_dir, cell_name, iter0_module
):
    """Block [11] goes whole, and says so, rather than the squeeze reaching [7].

    ``enforce_budget`` shortens block [11] first -- correctly, it is the only
    block that is not evidence about this run -- but it floors every block at
    160 bytes and then moves on to the next entry in ``TRIM_ORDER``, the layout
    digest.  Measured, that traded the poly/active crossing table, which a
    curriculum rung is graded on, for a 160-byte stub of a cell the packet
    explicitly tells the model is not the answer.

    Both halves are asserted: that the example is given up, and that the packet
    *says* it was.  A block that vanishes without a word is the same defect as
    one that is truncated without a word.
    """
    packet = _packet(evidence, netlist_path, iter0_dir, cell_name, iter0_module)
    reference = _block(packet, 11)
    assert reference, "block [11] must still be present, even when given up"
    if "no reference cell available" in reference or "not available" in reference:
        # orchestrate.sh's context_lock moves context/ aside for the duration of
        # a model call, so a live run makes the corpus unreadable.  Without a
        # reference cell the packet is under budget anyway and there is nothing
        # for this rule to do.
        pytest.skip("context/ corpus is unavailable, so block [11] is empty")
    assert "(dropped:" in reference, (
        "block [11] survived whole at the default budget, so this test no longer "
        f"exercises the rule it exists for:\n{reference[:400]}"
    )
    digest = _block(packet, 7)
    assert "crossings=" in digest, (
        "the layout digest lost its crossing table while the reference cell -- an "
        "example of a different cell -- kept its bytes.  An example is worth less "
        "than any measurement: it is given up first, and given up whole."
    )


def test_absurdly_small_budget_keeps_blocks_one_to_three(
    evidence, netlist_path, iter0_dir, cell_name, iter0_module
):
    """Over budget, the task and the verdict survive; the bulk is cut and named."""
    packet = _packet(
        evidence, netlist_path, iter0_dir, cell_name, iter0_module, max_bytes=600
    )
    assert f".subckt {cell_name}" in _block(packet, 1), (
        "block 1 is the specification: without the netlist the task is "
        "unspecified, so it is never trimmed however tight the budget"
    )
    assert "MAGIC DRC" in _block(packet, 2) and "NETGEN LVS" in _block(packet, 2), (
        "block 2 is three lines of verdict and is never trimmed"
    )
    assert "[INFO] COUNT: 8" in _block(packet, 3), (
        "block 3 is the Magic report; trimming it would leave the model with a "
        "violation count and no coordinates to act on"
    )
    for index in (1, 2, 3):
        assert "TRUNCATED" not in _block(packet, index), (
            f"block [{index}] was truncated at a 600-byte budget; blocks 1-3 "
            "must be the ones that survive"
        )

    footer = FOOTER_TRUNCATED_RE.search(packet)
    assert footer is not None, "the footer must always be present"
    named = footer.group(1)
    assert named.strip() not in ("", "none"), (
        f"the footer must name what was cut, got {named!r}; silent truncation is "
        "how the model ends up reasoning from a fragment it thinks is complete"
    )
    for keyword in ("KLAYOUT", "NETGEN", "EXTRACTED", "LAYOUT DIGEST"):
        assert keyword in named, (
            f"the footer must name the {keyword} block as truncated, got {named!r}"
        )
    assert "OVER BUDGET" in packet, (
        "when the packet cannot be squeezed into the budget the footer must say "
        "so rather than quietly exceeding it"
    )
    for index in (4, 5, 6, 7):
        assert "TRUNCATED" in _block(packet, index), (
            f"block [{index}] was over its target but carries no TRUNCATED note; "
            "every cut has to print how many bytes it dropped"
        )


def test_cap_text_reports_the_bytes_it_dropped(evidence):
    body = "".join(f"line {i}\n" for i in range(500))
    capped, truncated = evidence.cap_text(body, 200, "DEMO")
    assert truncated is True, (
        "cap_text must report that it truncated; a cut it does not admit to "
        "is a cut the footer cannot name"
    )
    assert len(capped.encode("utf-8")) <= 200, (
        f"cap_text returned {len(capped.encode('utf-8'))} bytes for a 200-byte "
        "limit; a cap that does not cap makes the whole budget advisory"
    )
    assert "TRUNCATED DEMO" in capped and "bytes dropped" in capped, (
        f"the drop note must name the block and the byte count, got:\n{capped}"
    )
    assert capped.split("\n... [TRUNCATED")[0].endswith("\n"), (
        "truncation must cut on a line boundary so the model never reads half a "
        "coordinate row as a whole one"
    )


# ---------------------------------------------------------------------------
# Never fail, never imply clean from absence
# ---------------------------------------------------------------------------

def test_missing_artifacts_read_as_not_available_not_pass(evidence, netlist_path, cell_name, tmp_path):
    packet = evidence.build_evidence(
        netlist=netlist_path, iter_dir=tmp_path, cell_name=cell_name, module_path=None
    )
    verdict = _block(packet, 2)
    assert "PASS" not in verdict, (
        f"an iteration with no artifacts at all must never read as PASS, got:\n"
        f"{verdict}; absence is the one thing that must not look like success"
    )
    assert "NOT AVAILABLE" in verdict.upper(), (
        f"missing artifacts must be labelled explicitly, got:\n{verdict}"
    )


def test_cli_exits_zero_and_writes_the_packet(netlist_path, iter0_dir, cell_name, iter0_module):
    proc = run(
        [
            sys.executable, "scripts/evidence.py",
            "--netlist", str(netlist_path),
            "--iter-dir", str(iter0_dir),
            "--cell", cell_name,
            "--module", str(iter0_module),
        ]
    )
    assert proc.returncode == 0, (
        f"evidence.py must never fail -- a non-zero exit makes the pipeline fall "
        f"back to no evidence at all.  stderr:\n{proc.stderr}"
    )
    assert proc.stdout.startswith("===== AION EVIDENCE PACKET ====="), (
        f"the packet header is what orchestrate.sh checks before accepting a "
        f"summary; got:\n{proc.stdout[:200]}"
    )
    assert "LU.a" in proc.stdout and "crossings=" in proc.stdout, (
        "the CLI path must produce the same evidence as the library path"
    )


def test_cli_max_bytes_flag_enforces_the_cap(netlist_path, iter0_dir, cell_name, iter0_module):
    """The same cap, exercised through the --max-bytes flag the pipeline passes."""
    proc = run(
        [
            sys.executable, "scripts/evidence.py",
            "--netlist", str(netlist_path),
            "--iter-dir", str(iter0_dir),
            "--cell", cell_name,
            "--module", str(iter0_module),
            "--max-bytes", "600",
        ]
    )
    assert proc.returncode == 0, (
        f"an unmeetable budget must still produce a packet, not an error:\n"
        f"{proc.stderr}"
    )
    out = proc.stdout
    assert f".subckt {cell_name}" in _block(out, 1), (
        "block 1 survives any budget: without the netlist the task is unspecified"
    )
    assert "[INFO] COUNT: 8" in _block(out, 3), (
        "block 3 survives any budget: a violation count with no coordinates is "
        "not actionable"
    )
    footer = FOOTER_TRUNCATED_RE.search(out)
    assert footer is not None and footer.group(1).strip() != "none", (
        f"the footer must name the cut blocks, got {footer.group(1) if footer else None!r}"
    )
    assert "OVER BUDGET" in out, (
        "the footer must admit the packet could not be squeezed into the budget "
        "rather than pretending it fit"
    )
