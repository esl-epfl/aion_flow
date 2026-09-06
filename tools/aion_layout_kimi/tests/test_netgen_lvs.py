# ================================================================
#  SPDX-FileCopyrightText:    2026 Filippo Quadri
#  SPDX-License-Identifier:   Apache-2.0 WITH SHL-2.1
#  Created:                   2026-09-03
#  Description:               Golden tests for Netgen LVS log parsing
# ================================================================

"""Netgen's verdict sentence must be classified, not pattern-matched by luck.

The historical defect: the parser recognised only ``Circuits match uniquely``
and ``Circuits do not match``.  The real run ends with ``Final result: Top level
cell failed pin matching.``, which matched neither, so the result was reported
"inconclusive" -- correct only by accident, and one wording change away from
reading as a pass.
"""

from __future__ import annotations

import pytest

from aion_layout.verification import (
    LVS_VERDICTS,
    VerificationError,
    parse_netgen_lvs_report,
)


# ---------------------------------------------------------------------------
# The captured run
# ---------------------------------------------------------------------------

def test_fixture_verdict_is_failed_pin_matching(netgen_out):
    report = parse_netgen_lvs_report(netgen_out)
    assert report.verdict == "failed_pin_matching", (
        f"the captured log ends 'Top level cell failed pin matching.', got "
        f"verdict={report.verdict!r}; classifying it as 'uncertain' was right "
        "only by accident and gives the model no idea what to fix"
    )
    assert report.clean is False, (
        "only 'match_uniquely' is clean; anything else passing the gate would "
        "let the loop stop on a layout whose ports do not match the schematic"
    )
    assert report.tool == "netgen", (
        f"the report must name the tool that produced the verdict, got "
        f"{report.tool!r}; the reader has to know whether Magic or Netgen "
        "is speaking"
    )
    assert "pin matching" in report.message.lower(), (
        f"the message must say what failed, got {report.message!r}"
    )


def test_fixture_device_counts_show_one_missing_of_each_type(netgen_out):
    report = parse_netgen_lvs_report(netgen_out)
    assert report.device_counts == {
        "sg13_lv_nmos": (3, 4),
        "sg13_lv_pmos": (3, 4),
    }, (
        f"expected the measured 3-vs-4 per-type mismatch, got "
        f"{report.device_counts}; this pair is the whole diagnosis -- the "
        "scaffold gates only the three external inputs and never the internal "
        "node I1_bar, so one device of each type is missing"
    )
    assert report.device_total == (6, 8), (
        f"expected 6 layout / 8 schematic devices, got {report.device_total}; "
        "the totals are what tell the model the layout is short, not rewired"
    )


def test_fixture_net_counts_and_disconnected_nodes(netgen_out):
    report = parse_netgen_lvs_report(netgen_out)
    assert report.net_counts == (13, 9), (
        f"expected 13 layout / 9 schematic nets, got {report.net_counts}; more "
        "layout nets than schematic nets is the signature of unrouted stubs"
    )
    assert report.disconnected_nodes == ["I0", "I2", "O0", "VSS", "VDD"], (
        f"expected the five measured disconnected nodes in log order, got "
        f"{report.disconnected_nodes}; note I1 is absent because it merged with "
        "O0 into a single Metal1 node, which is the scaffold self-short"
    )


def test_fixture_unmatched_pins_name_the_shorted_node(netgen_out):
    report = parse_netgen_lvs_report(netgen_out)
    left_sides = [left for left, _right in report.unmatched_pins]
    assert any("a_155_82#" in side for side in left_sides), (
        f"the extracted node a_155_82# must appear among the unmatched pins, got "
        f"{left_sides}; it is the single node both I1 and I2 map onto and is the "
        "only direct evidence of the Metal1 short in the LVS log"
    )
    assert len(report.unmatched_pins) == 11, (
        f"expected the 11 unmatched pin rows the log lists, got "
        f"{len(report.unmatched_pins)}; a short list means the pin table scan "
        "stopped early"
    )


# ---------------------------------------------------------------------------
# Verdict classification, table driven
# ---------------------------------------------------------------------------

_HEADER = "Contents of circuit 1:  Circuit: 'layout'\n"

VERDICT_CASES = [
    ("match_uniquely", "Final result: Circuits match uniquely.\n", True),
    (
        "match_with_warnings",
        "Final result: Circuits match uniquely with property errors.\n",
        False,
    ),
    ("match_with_warnings", "Final result: Circuits match, but not uniquely.\n", False),
    ("do_not_match", "Final result: Circuits do not match.\n", False),
    (
        "failed_pin_matching",
        "Final result: Top level cell failed pin matching.\n",
        False,
    ),
    ("no_final_result", "Netgen ran out of memory and died.\n", False),
    ("uncertain", "Final result: Something else entirely.\n", False),
]


@pytest.mark.parametrize("expected,body,clean", VERDICT_CASES)
def test_verdict_classification(tmp_path, expected, body, clean):
    path = tmp_path / f"{expected}.lvs.out"
    path.write_text(_HEADER + body)
    report = parse_netgen_lvs_report(path)
    assert report.verdict == expected, (
        f"{body.strip()!r} must classify as {expected!r}, got {report.verdict!r}; "
        "an unclassified sentence is how a real failure was reported as "
        "'inconclusive' and never fed a fix back to the model"
    )
    assert report.clean is clean, (
        f"clean must be {clean} for verdict {expected!r}; only a unique match is "
        "a pass, and every other token that reads as clean lets the loop stop "
        "on a broken layout"
    )
    assert report.verdict in LVS_VERDICTS, (
        f"{report.verdict!r} is not one of the declared LVS_VERDICTS; an "
        "undeclared token cannot be handled by callers that switch on it"
    )


def test_every_declared_verdict_is_exercised():
    covered = {expected for expected, _body, _clean in VERDICT_CASES}
    assert covered == set(LVS_VERDICTS), (
        f"the table must cover every declared verdict; missing "
        f"{set(LVS_VERDICTS) - covered}, unexpected {covered - set(LVS_VERDICTS)}. "
        "An unexercised token is one nobody has checked cannot read as a pass."
    )


def test_last_final_result_wins(tmp_path):
    """Netgen prints one 'Final result' per compared cell; only the last counts."""
    path = tmp_path / "multi.lvs.out"
    path.write_text(
        _HEADER
        + "Subcircuit summary:\n"
        + "Final result: Circuits match uniquely.\n"
        + "Cell pin lists are equivalent.\n"
        + "Final result: Top level cell failed pin matching.\n"
    )
    report = parse_netgen_lvs_report(path)
    assert report.verdict == "failed_pin_matching", (
        f"the LAST 'Final result:' line is the top-level verdict, got "
        f"{report.verdict!r}; taking the first would let a matching subcell "
        "declare the whole cell clean"
    )
    assert report.clean is False, (
        "a matching subcell must not turn a failing top-level cell into a pass"
    )


def test_wrapped_final_result_line(tmp_path):
    """In *.lvs.log the verdict is wrapped onto the following line."""
    path = tmp_path / "wrapped.lvs.log"
    path.write_text(_HEADER + "Final result:\nCircuits match uniquely.\n")
    report = parse_netgen_lvs_report(path)
    assert report.verdict == "match_uniquely", (
        f"a verdict wrapped onto the next line must still be read, got "
        f"{report.verdict!r}; *.lvs.log is the fallback report and dropping its "
        "verdict makes the fallback useless"
    )


def test_log_prose_totals_are_parsed(tmp_path):
    """*.lvs.log states the totals in prose instead of a two-column table."""
    path = tmp_path / "prose.lvs.log"
    path.write_text(
        _HEADER
        + "Circuit 1 contains 13 nets, Circuit 2 contains 9 nets.\n"
        + "Circuit 1 contains 6 devices, Circuit 2 contains 8 devices.\n"
        + "Final result: Circuits do not match.\n"
    )
    report = parse_netgen_lvs_report(path)
    assert report.net_counts == (13, 9), (
        f"prose net totals must be parsed, got {report.net_counts}; without them "
        "a *.lvs.log fallback carries a verdict but no numbers to act on"
    )
    assert report.device_total == (6, 8), (
        f"prose device totals must be parsed, got {report.device_total}"
    )


def test_missing_report_raises_rather_than_passing(tmp_path):
    with pytest.raises(VerificationError):
        parse_netgen_lvs_report(tmp_path / "absent.lvs.out")
