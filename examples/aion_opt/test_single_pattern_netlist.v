/* Fake netlist to test single-output pattern extraction.
 *
 * Pattern: inv -> nand2 -> nor2 (3 cells, sg13g2_inv_1 / sg13g2_nand2_1 / sg13g2_nor2_1)
 *
 * Instances:
 *   - single_0, single_1, single_2: only the nor2 output is used externally.
 *   - multi_inv_0: the inverter output is also used to drive an extra xor2.
 *   - multi_nand_0: the nand2 output is also used to drive an extra xor2.
 *
 * With --max-outputs 1, aion_opt should extract exactly the 3 single-output
 * occurrences and ignore the 2 multi-output ones.
 */

module test_single_pattern_netlist (
    input  [8:0] a,
    input  [8:0] b,
    input  [2:0] c,
    output [6:0] y
);

    wire s0_inv, s0_nand, s0_nor;
    wire s1_inv, s1_nand, s1_nor;
    wire s2_inv, s2_nand, s2_nor;

    wire m_inv_inv, m_inv_nand, m_inv_nor, m_inv_xor;
    wire m_nand_inv, m_nand_nand, m_nand_nor, m_nand_xor;

    // Single-output patterns (3 occurrences): only the nor2 output leaves the pattern.
    sg13g2_inv_1  single_i0  (.Y(s0_inv),  .A(a[0]));
    sg13g2_nand2_1 single_n0 (.Y(s0_nand), .A(s0_inv),  .B(b[0]));
    sg13g2_nor2_1 single_r0 (.Y(s0_nor),  .A(s0_nand), .B(c[0]));

    sg13g2_inv_1  single_i1  (.Y(s1_inv),  .A(a[1]));
    sg13g2_nand2_1 single_n1 (.Y(s1_nand), .A(s1_inv),  .B(b[1]));
    sg13g2_nor2_1 single_r1 (.Y(s1_nor),  .A(s1_nand), .B(c[1]));

    sg13g2_inv_1  single_i2  (.Y(s2_inv),  .A(a[2]));
    sg13g2_nand2_1 single_n2 (.Y(s2_nand), .A(s2_inv),  .B(b[2]));
    sg13g2_nor2_1 single_r2 (.Y(s2_nor),  .A(s2_nand), .B(c[2]));

    // Multi-output variant: inverter output also leaves the pattern (drives an xor2).
    sg13g2_inv_1  multi_inv_i  (.Y(m_inv_inv),  .A(a[3]));
    sg13g2_nand2_1 multi_inv_n (.Y(m_inv_nand), .A(m_inv_inv),  .B(b[3]));
    sg13g2_nor2_1 multi_inv_r  (.Y(m_inv_nor),  .A(m_inv_nand), .B(c[2]));
    sg13g2_xor2_1 multi_inv_x  (.X(m_inv_xor),  .A(m_inv_inv),  .B(b[4]));
    // Extra load on the nor2 output so the full 3-cell pattern has 2 boundary outputs.
    sg13g2_xor2_1 multi_inv_x2 (.X(m_inv_nor2), .A(m_inv_nor),  .B(b[7]));

    // Multi-output variant: nand2 output also leaves the pattern (drives an xor2).
    sg13g2_inv_1  multi_nand_i  (.Y(m_nand_inv),  .A(a[4]));
    sg13g2_nand2_1 multi_nand_n (.Y(m_nand_nand), .A(m_nand_inv),  .B(b[5]));
    sg13g2_nor2_1 multi_nand_r  (.Y(m_nand_nor),  .A(m_nand_nand), .B(c[2]));
    sg13g2_xor2_1 multi_nand_x  (.X(m_nand_xor),  .A(m_nand_nand),  .B(b[6]));
    // Extra load on the nor2 output so the full 3-cell pattern has 2 boundary outputs.
    sg13g2_xor2_1 multi_nand_x2 (.X(m_nand_nor2), .A(m_nand_nor),  .B(b[8]));

    wire y3_xor, y4_xor, y3_out, y4_out;
    sg13g2_xor2_1 y3_xor_inst (.X(y3_xor), .A(m_inv_xor),  .B(m_inv_nor2));
    sg13g2_xor2_1 y4_xor_inst (.X(y4_xor), .A(m_nand_xor), .B(m_nand_nor2));
    sg13g2_xor2_1 y3_out_inst (.X(y3_out), .A(m_inv_nor),  .B(y3_xor));
    sg13g2_xor2_1 y4_out_inst (.X(y4_out), .A(m_nand_nor), .B(y4_xor));

    assign y[0] = s0_nor;
    assign y[1] = s1_nor;
    assign y[2] = s2_nor;
    assign y[3] = y3_out;
    assign y[4] = y4_out;
    assign y[5] = m_inv_nor2;
    assign y[6] = m_nand_nor2;

endmodule

