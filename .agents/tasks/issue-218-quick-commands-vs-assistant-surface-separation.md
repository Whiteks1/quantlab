# Issue #218 — Quick commands versus assistant surface separation

## Goal
Make the upper right-rail entry a true quick-command surface instead of a second pseudo-assistant input.

---

## Why this matters
The desktop currently exposes two inputs that appear similar but route into the same support log. That breaks input/output clarity and makes the right rail feel duplicated.

---

## Scope

### In scope
- rename and reposition the upper support entry
- restrict that upper surface to deterministic QuantLab commands
- clarify the difference between quick commands and assistant prompts
- align button labels and helper copy with the new semantics

### Out of scope
- Stepbit backend changes
- new command vocabulary
- renderer architecture refactors outside the right rail

---

## Relevant files

- `desktop/renderer/index.html`
- `desktop/renderer/styles.css`
- `desktop/renderer/app.js`

---

## Expected deliverable

A right-rail top block that reads as `Quick commands` or equivalent, and no longer behaves like an unlabeled second assistant.

---

## Done when

- the upper block is clearly command-only
- the upper block no longer reads like a conversational assistant input
- the difference between top and bottom support surfaces is obvious at a glance

---

## Notes (optional)

This slice should preserve deterministic workstation actions such as opening runs, compare, artifacts, system, or related surfaces.
