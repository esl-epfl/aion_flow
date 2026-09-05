"""A corpus of small gate netlists used across the tests."""

from __future__ import annotations

#: name -> (SPICE text, transistors in the original standard cells)
CORPUS = {
    "inv_nand2_nor2": (
        """
.subckt T I0 I1 I2 O0 VDD VSS
Xg0 net1 I0 VDD VSS sg13g2_inv_1
Xg2 net2 net1 I1 VDD VSS sg13g2_nand2_1
Xg1 O0 net2 I2 VDD VSS sg13g2_nor2_1
.ends
""",
        10,
    ),
    "and3": (
        """
.subckt T I0 I1 I2 O0 VDD VSS
Xg0 net1 I0 I1 VDD VSS sg13g2_and2_1
Xg1 O0 net1 I2 VDD VSS sg13g2_and2_1
.ends
""",
        12,
    ),
    "or3": (
        """
.subckt T I0 I1 I2 O0 VDD VSS
Xg0 net1 I0 I1 VDD VSS sg13g2_or2_1
Xg1 O0 net1 I2 VDD VSS sg13g2_or2_1
.ends
""",
        12,
    ),
    "aoi_tree": (
        """
.subckt T I0 I1 I2 I3 O0 VDD VSS
Xg0 net1 I0 I1 VDD VSS sg13g2_nand2_1
Xg1 net2 I2 I3 VDD VSS sg13g2_nand2_1
Xg2 O0 net1 net2 VDD VSS sg13g2_nand2_1
.ends
""",
        12,
    ),
    "xor2": (
        """
.subckt T I0 I1 O0 VDD VSS
Xg0 O0 I0 I1 VDD VSS sg13g2_xor2_1
.ends
""",
        10,
    ),
    "xor3": (
        """
.subckt T I0 I1 I2 O0 VDD VSS
Xg0 net1 I0 I1 VDD VSS sg13g2_xor2_1
Xg1 O0 net1 I2 VDD VSS sg13g2_xor2_1
.ends
""",
        20,
    ),
    "xor4": (
        """
.subckt T I0 I1 I2 I3 O0 VDD VSS
Xg0 net1 I0 I1 VDD VSS sg13g2_xor2_1
Xg1 net2 I2 I3 VDD VSS sg13g2_xor2_1
Xg2 O0 net1 net2 VDD VSS sg13g2_xor2_1
.ends
""",
        30,
    ),
    "xor_then_and": (
        """
.subckt T I0 I1 I2 I3 O0 VDD VSS
Xg0 net1 I0 I1 VDD VSS sg13g2_xor2_1
Xg1 net2 net1 I2 VDD VSS sg13g2_and2_1
Xg2 O0 net2 I3 VDD VSS sg13g2_and2_1
.ends
""",
        22,
    ),
    "nand_chain": (
        """
.subckt T I0 I1 I2 I3 I4 O0 VDD VSS
Xg0 net1 I0 I1 VDD VSS sg13g2_nand2_1
Xg1 net2 net1 I2 VDD VSS sg13g2_nand2_1
Xg2 net3 net2 I3 VDD VSS sg13g2_nand2_1
Xg3 O0 net3 I4 VDD VSS sg13g2_nand2_1
.ends
""",
        16,
    ),
    "reconvergent_constant": (
        # O0 is identically 1: net2 = NOR(net1, I2) can never be high with net1.
        """
.subckt T I0 I1 I2 O0 VDD VSS
Xg0 net1 I0 I1 VDD VSS sg13g2_nand2_1
Xg1 net2 net1 I2 VDD VSS sg13g2_nor2_1
Xg2 O0 net1 net2 VDD VSS sg13g2_nand2_1
.ends
""",
        12,
    ),
    "reconvergent_blob": (
        """
.subckt T I0 I1 I2 I3 I4 I5 O0 VDD VSS
Xg0 n0 I0 I1 VDD VSS sg13g2_nand2_1
Xg1 n1 I2 I3 VDD VSS sg13g2_nor2_1
Xg2 n2 n0 n1 VDD VSS sg13g2_nand2_1
Xg3 n3 n0 I4 VDD VSS sg13g2_nor2_1
Xg4 n4 n2 n3 VDD VSS sg13g2_nand2_1
Xg5 n5 n1 I5 VDD VSS sg13g2_nand2_1
Xg6 n6 n4 n5 VDD VSS sg13g2_nor2_1
Xg7 O0 n6 n2 VDD VSS sg13g2_nand2_1
.ends
""",
        32,
    ),
    "tied_input": (
        """
.subckt T I0 I1 O0 VDD VSS
Xg0 O0 I0 VSS VDD VSS sg13g2_nand2_1
.ends
""",
        4,
    ),
    "buffer": (
        """
.subckt T I0 O0 VDD VSS
Xg0 net1 I0 VDD VSS sg13g2_inv_1
Xg1 O0 net1 VDD VSS sg13g2_inv_1
.ends
""",
        4,
    ),
    "multi_output": (
        """
.subckt T I0 I1 I2 I3 I4 O0 O1 O2 VDD VSS
Xg0 O0 I0 I1 VDD VSS sg13g2_and2_1
Xg1 O1 I2 O0 O2 VDD VSS sg13g2_a21o_1
Xg2 O2 I3 I4 VDD VSS sg13g2_xor2_1
.ends
""",
        24,
    ),
}
