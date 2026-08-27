// Copyright 2024 IHP PDK Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// -----------------------------------------------------------------------
// Behavioral (non-UDP) replacements for the ihp_* primitives.
//
// The original `primitive`/`table` models encode a "notifier" input
// (`v`, and/or `xcr`) whose sole purpose is to force q to x when a
// setup/hold timing check fails during event-driven simulation. That has
// no counterpart in synthesis or formal equivalence checking (2-state,
// no concept of a clock edge "going to x"), so notifier columns are
// dropped here and the real functional table rows are turned into
// ordinary always/assign blocks. Port order/names are preserved so
// existing positional instantiations elsewhere in the library still
// connect correctly.
// -----------------------------------------------------------------------

`timescale 1ns/10ps

// ---------------------------------------------------------------------
// Transparent latch (v = notifier, unused)
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_latch_
`else
`define _udp_def_ihp_latch_
module ihp_latch (q, v, clk, d);
  output reg q;
  input v, clk, d;
  always @*
    if (clk) q = d;
endmodule
`endif

// ---------------------------------------------------------------------
// Notifier-only X-generator. Fires only on clk transitioning to x
// during simulation timing checks -- no synthesizable/formal meaning.
// Stubbed out; verify it isn't wired into a real functional net.
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_dff_err_
`else
`define _udp_def_ihp_dff_err_
module ihp_dff_err (q, clk, d);
  output reg q;
  input clk, d;
  // notifier-only stub -- see file header
endmodule
`endif

// ---------------------------------------------------------------------
// Plain positive-edge D flip-flop (v, xcr = notifiers, unused)
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_dff_
`else
`define _udp_def_ihp_dff_
module ihp_dff (q, v, clk, d, xcr);
  output reg q;
  input v, clk, d, xcr;
  always @(posedge clk)
    q <= d;
endmodule
`endif

// ---------------------------------------------------------------------
// Notifier-only stub (see ihp_dff_err note above)
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_dff_r_err_
`else
`define _udp_def_ihp_dff_r_err_
module ihp_dff_r_err (q, clk, d, r);
  output reg q;
  input clk, d, r;
  // notifier-only stub -- see file header
endmodule
`endif

// ---------------------------------------------------------------------
// D flip-flop, asynchronous active-high reset
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_dff_r_
`else
`define _udp_def_ihp_dff_r_
module ihp_dff_r (q, v, clk, d, r, xcr);
  output reg q;
  input v, clk, d, r, xcr;
  always @(posedge clk or posedge r)
    if (r) q <= 1'b0;
    else   q <= d;
endmodule
`endif

// ---------------------------------------------------------------------
// Notifier-only stub (see ihp_dff_err note above)
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_dff_s_err_
`else
`define _udp_def_ihp_dff_s_err_
module ihp_dff_s_err (q, clk, d, s);
  output reg q;
  input clk, d, s;
  // notifier-only stub -- see file header
endmodule
`endif

// ---------------------------------------------------------------------
// D flip-flop, asynchronous active-high set
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_dff_s_
`else
`define _udp_def_ihp_dff_s_
module ihp_dff_s (q, v, clk, d, s, xcr);
  output reg q;
  input v, clk, d, s, xcr;
  always @(posedge clk or posedge s)
    if (s) q <= 1'b1;
    else   q <= d;
endmodule
`endif

// ---------------------------------------------------------------------
// Notifier-only stub (see ihp_dff_err note above)
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_dff_sr_err_
`else
`define _udp_def_ihp_dff_sr_err_
module ihp_dff_sr_err (q, clk, d, s, r);
  output reg q;
  input clk, d, s, r;
  // notifier-only stub -- see file header
endmodule
`endif

// ---------------------------------------------------------------------
// D flip-flop, async set + reset, RESET has priority when both asserted
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_dff_sr_0
`else
`define _udp_def_ihp_dff_sr_0
module ihp_dff_sr_0 (q, v, clk, d, s, r, xcr);
  output reg q;
  input v, clk, d, s, r, xcr;
  always @(posedge clk or posedge s or posedge r)
    if (r)      q <= 1'b0;
    else if (s) q <= 1'b1;
    else        q <= d;
endmodule
`endif

// ---------------------------------------------------------------------
// D flip-flop, async set + reset, SET has priority when both asserted
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_dff_sr_1
`else
`define _udp_def_ihp_dff_sr_1
module ihp_dff_sr_1 (q, v, clk, d, s, r, xcr);
  output reg q;
  input v, clk, d, s, r, xcr;
  always @(posedge clk or posedge s or posedge r)
    if (s)      q <= 1'b1;
    else if (r) q <= 1'b0;
    else        q <= d;
endmodule
`endif

// ---------------------------------------------------------------------
// Transparent latch, level-sensitive async active-high reset
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_latch_r_
`else
`define _udp_def_ihp_latch_r_
module ihp_latch_r (q, v, clk, d, r);
  output reg q;
  input v, clk, d, r;
  always @*
    if (r)        q = 1'b0;
    else if (clk) q = d;
endmodule
`endif

// ---------------------------------------------------------------------
// Transparent latch, level-sensitive async active-high set
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_latch_s_
`else
`define _udp_def_ihp_latch_s_
module ihp_latch_s (q, v, clk, d, s);
  output reg q;
  input v, clk, d, s;
  always @*
    if (s)        q = 1'b1;
    else if (clk) q = d;
endmodule
`endif

// ---------------------------------------------------------------------
// Transparent latch, async set + reset, RESET priority
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_latch_sr_0
`else
`define _udp_def_ihp_latch_sr_0
module ihp_latch_sr_0 (q, v, clk, d, s, r);
  output reg q;
  input v, clk, d, s, r;
  always @*
    if (r)        q = 1'b0;
    else if (s)   q = 1'b1;
    else if (clk) q = d;
endmodule
`endif

// ---------------------------------------------------------------------
// Transparent latch, async set + reset, SET priority
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_latch_sr_1
`else
`define _udp_def_ihp_latch_sr_1
module ihp_latch_sr_1 (q, v, clk, d, s, r);
  output reg q;
  input v, clk, d, s, r;
  always @*
    if (s)        q = 1'b1;
    else if (r)   q = 1'b0;
    else if (clk) q = d;
endmodule
`endif

// ---------------------------------------------------------------------
// 2:1 mux
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_mux2
`else
`define _udp_def_ihp_mux2
module ihp_mux2 (z, a, b, s);
  output z;
  input a, b, s;
  assign z = s ? b : a;
endmodule
`endif

// ---------------------------------------------------------------------
// 4:1 mux, select index = {s1,s0} -> 0:a 1:b 2:c 3:d
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_mux4
`else
`define _udp_def_ihp_mux4
module ihp_mux4 (z, a, b, c, d, s0, s1);
  output z;
  input d, c, b, a, s1, s0;
  assign z = ({s1, s0} == 2'd0) ? a :
             ({s1, s0} == 2'd1) ? b :
             ({s1, s0} == 2'd2) ? c : d;
endmodule
`endif

// ---------------------------------------------------------------------
// 8:1 mux, select index = {s2,s1,s0} -> 0:a ... 7:h
// ---------------------------------------------------------------------
`ifdef _udp_def_ihp_mux8
`else
`define _udp_def_ihp_mux8
module ihp_mux8 (z, a, b, c, d, e, f, g, h, s0, s1, s2);
  output z;
  input h, g, f, e, d, c, b, a, s2, s1, s0;
  assign z = ({s2, s1, s0} == 3'd0) ? a :
             ({s2, s1, s0} == 3'd1) ? b :
             ({s2, s1, s0} == 3'd2) ? c :
             ({s2, s1, s0} == 3'd3) ? d :
             ({s2, s1, s0} == 3'd4) ? e :
             ({s2, s1, s0} == 3'd5) ? f :
             ({s2, s1, s0} == 3'd6) ? g : h;
endmodule
`endif