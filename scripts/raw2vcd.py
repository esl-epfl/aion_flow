#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Davide Schiavone
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1
"""
Convert an ngspice ASCII rawfile to a VCD that GTKWave can open. Each node becomes a
VCD `real` variable, which GTKWave displays as an analog trace (so both the analog
signals like ro_clk/nbias and the bridged digital signals like dac_code/fout show up).

Produce an ASCII raw from ngspice with:  set filetype=ascii  (before `write file.raw`).

Usage:  python3 raw2vcd.py <in.raw> <out.vcd>
"""
import sys


def read_ascii_raw(path):
    names, values, npts, nvars = [], [], 0, 0
    with open(path) as f:
        lines = f.read().splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("No. Variables:"):
            nvars = int(ln.split(":")[1])
        elif ln.startswith("No. Points:"):
            npts = int(ln.split(":")[1])
        elif ln.startswith("Variables:"):
            for j in range(nvars):
                parts = lines[i + 1 + j].split()
                names.append(parts[1])          # idx name type
            i += nvars
        elif ln.startswith("Values:"):
            i += 1
            cur = None
            # Point header "<idx>\t<time>" has no leading whitespace; value lines
            # are indented; blank lines may separate points.
            while i < len(lines):
                parts = lines[i].split()
                i += 1
                if not parts:                        # blank line between points
                    continue
                if len(parts) >= 2:                  # point header: "<idx> <time>"
                    cur = [float(parts[-1])]
                    values.append(cur)
                else:                                # one signal value of this point
                    cur.append(float(parts[0]))
            break
        i += 1
    return names, values


def vcd_id(n):
    # printable identifier codes starting at '!'
    return chr(33 + n)


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: raw2vcd.py <in.raw> <out.vcd>")
    names, values = read_ascii_raw(sys.argv[1])
    # column 0 is time; the rest are signals
    sig = list(range(1, len(names)))

    def clean(s):
        return s.replace("v(", "").replace("V(", "").replace(")", "").replace("#", "_")

    with open(sys.argv[2], "w") as o:
        o.write("$timescale 1fs $end\n$scope module ngspice $end\n")
        for k in sig:
            o.write(f"$var real 1 {vcd_id(k)} {clean(names[k])} $end\n")
        o.write("$upscope $end\n$enddefinitions $end\n")
        last_tick = -1
        for row in values:
            tick = int(round(row[0] / 1e-15))   # seconds -> fs
            if tick <= last_tick:
                tick = last_tick + 1
            last_tick = tick
            o.write(f"#{tick}\n")
            for k in sig:
                o.write(f"r{row[k]:.6g} {vcd_id(k)}\n")
    print(f"wrote {sys.argv[2]}: {len(sig)} signals, {len(values)} points")


if __name__ == "__main__":
    main()
