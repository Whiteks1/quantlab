# Issue #287 — Simplify right-rail support lane semantics

## Goal
Remove the duplicated assistant semantics in the right rail and turn it into a support lane with one clear command surface and one clear assistant surface.

---

## Why this matters
The current right rail behaves like two overlapping assistants: one entry above and one real assistant below, both feeding the same history. That breaks input/output clarity and competes with the main workstation.

---

## Scope

### In scope
- quick commands versus assistant separation
- single visible output/history locus
- explicit Stepbit mode separation
- right-rail density and helper-copy reduction

### Out of scope
- new Stepbit capabilities
- LLM backend changes
- non-right-rail layout redesign

---

## Relevant files

- `desktop/renderer/index.html`
- `desktop/renderer/styles.css`
- `desktop/renderer/app.js`

---

## Expected deliverable

A right rail where:

- the top block is command-oriented and deterministic
- the lower block is the single assistant/history surface
- Stepbit routing is explicit when used
- support no longer competes visually with the workbench

---

## Done when

- users no longer see two assistant-like inputs
- the output locus is obvious
- Stepbit mode is explicit instead of blended
- right-rail noise is reduced
