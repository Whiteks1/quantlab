# Issue #221 — Right-rail density and vertical-noise reduction

## Goal
Reduce wasted height and repeated framing in the right rail after the command and assistant semantics are separated.

---

## Why this matters
The right rail currently spends too much vertical space on duplicated headings, helper text, and controls for a support lane that should stay compact beside the workstation.

---

## Scope

### In scope
- support-column spacing
- card height and vertical rhythm
- duplicate helper copy cleanup
- compacting the right rail after semantic cleanup

### Out of scope
- workbench-column redesign
- topbar redesign
- new right-rail features

---

## Relevant files

- `desktop/renderer/index.html`
- `desktop/renderer/styles.css`

---

## Expected deliverable

A right rail that is lighter, shorter, and easier to scan without losing support functionality.

---

## Done when

- the support lane takes less vertical space for the same function
- repeated explanatory copy is reduced
- the rail feels secondary to the workstation instead of competing with it
