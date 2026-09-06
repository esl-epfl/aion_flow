---
name: draw-layout-AI
description: Draw the layout of a standard cell using an iterative AI flow
---

# Standard-Cell Layout Debugging Reference

Domain knowledge for diagnosing and fixing a standard-cell layout: what to look at, in what order, and
why. It is deliberately independent of who runs the DRC/LVS loop or how. The flow itself — execution
modes, `state.json`, the step-by-step pipeline, docker rules and finalisation — is documented for human
readers in `ORCHESTRATION.md`.

---

# Layout Debugging Strategy

When deciding what to modify, prioritize problems in this order:

1. **Incorrect transistor topology**
2. **Missing or incorrect source/drain connections**
3. **Missing contacts/vias**
4. **Missing power connections**
5. **Missing input/output connections**
6. **LVS connectivity mismatches**
7. **DRC shorts**
8. **DRC spacing violations**
9. **DRC enclosure violations**
10. **Other geometric/design-rule issues**
11. **Layout compactness and visual quality**

Do not optimize area before connectivity and verification are correct.

---

## First Iteration Special Rule

On `iteration == 0`, do not spend significant effort performing detailed DRC/LVS diagnosis. The automatically generated scaffold provides limited information.

Instead, focus on completing the obvious physical implementation: source connections, drain connections, transistor interconnect, missing devices, contacts, vias, input routing, output routing, power routing, topology implied by the SPICE netlist.

After the first iteration, use detailed DRC/LVS feedback to drive optimization.

---

# LVS Debugging

When LVS fails, determine whether the problem is:

### Missing connection

A net exists in SPICE but is disconnected in the layout. Fix the physical routing.

### Incorrect connection

Two nets are accidentally shorted. Fix the metal/poly/diffusion geometry.

### Missing device

A MOS device exists in SPICE but cannot be extracted from the layout. Check: active region, poly gate, source/drain geometry, contacts, layer combinations, transistor dimensions.

### Incorrect device parameters

Check the extracted transistor geometry against the SPICE instance. Do not alter the SPICE netlist to hide the mismatch.

---

# DRC Debugging

Use the exact DRC violation information to determine which geometry is incorrect. Typical fixes include: increasing spacing, enlarging enclosure, correcting via/contact placement, extending metal, moving poly, separating nets, correcting diffusion geometry, removing accidental overlaps, respecting minimum widths.

Prefer small, targeted modifications over completely redesigning the cell.

## Latch-up: `LU.a` and `LU.b`

These two rules are different in kind from the rest, and they are the ones this
flow hits most: they are not violated by geometry that is in the wrong place, but
by geometry that is *missing*.

- `LU.a` — *P-diff distance to N-tap*: every p-diffusion region (the PMOS active
  inside the NWell) must have an n+ tap within the rule distance.
- `LU.b` — *N-diff distance to P-tap*: every n-diffusion region (the NMOS active
  in the substrate) must have a p+ tap within the rule distance.

A cell that draws no taps is infinitely far from one, so each rule fires once per
uncovered diffusion region. Poly gates split an active area into separate regions
and each region is reported on its own, so the item count tracks the drawn
geometry rather than the number of transistors. A tap ties the substrate or the
well to a supply; without it the parasitic thyristor formed by the neighbouring
n and p regions has nothing holding it off, which is what the rule guards against.

Do not try to fix `LU.a` / `LU.b` by moving or shrinking diffusion — no amount of
moving reduces an infinite distance. Add tap rows: an n+ tap inside the NWell tied
to VDD, and a p+ tap in the substrate tied to VSS. Taps conventionally live in the
strip alongside each power rail, where the tap's Metal1 landing overlaps the rail
it ties to; that placement also gives the extractor the bulk connection LVS wants,
so one addition clears both the DRC rule and the bulk net. `draw_tap` in
`aion_layout.building_blocks` draws implant, contact row, landing, label and port
in one call — see `GDS_PYTHON_API.md` for its contract.

---

# Iteration Philosophy

Each iteration should make a concrete improvement. Do not randomly modify geometry. For every modification, have a reason such as:

```text
LVS reports OUT disconnected from drain → add metal connection.
DRC reports M1 spacing violation → move routing by minimum legal spacing.
LVS reports missing PMOS → correct active/poly/contact geometry.
```

Keep the generated layout structurally simple unless the topology requires otherwise. Preserve working portions of the previous iteration.

---

# Layout Rules

## Do Not Modify the Netlist

The SPICE netlist is the source of truth for connectivity. Fix the layout, not the netlist.
