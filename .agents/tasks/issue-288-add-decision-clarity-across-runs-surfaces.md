# Issue #288 — Add decision clarity across runs surfaces

## Goal
Make the desktop tell the operator what is known, what is missing, and what the next recommended action is across `Runs`, `Run Detail`, and `Artifacts`.

---

## Why this matters
The desktop already exposes real runs, metrics, artifacts, and actions, but it does not yet synthesize decision readiness. Users can inspect data, but still have to infer too much about what to do next.

---

## Scope

### In scope
- evidence state
- decision state
- next-step guidance
- continuity between `Runs`, `Run Detail`, and `Artifacts`
- visible feedback for candidate / shortlist / baseline actions
- Compare prerequisites signaling

### Out of scope
- canonical engine contract redesign
- non-runs desktop surfaces unless they directly affect this flow
- backend scoring or strategy logic changes

---

## Relevant files

- `desktop/renderer/modules/tab-renderers.js`
- `desktop/renderer/styles.css`
- `desktop/renderer/app.js`

---

## Expected deliverable

A shell that makes evidence readiness, decision state, and recommended next action explicit instead of leaving them implicit.

---

## Done when

- runs surfaces expose readiness and missing-evidence state clearly
- candidate / shortlist / baseline actions provide immediate visible feedback
- Compare prerequisites are signaled before failure or empty state
- continuity between `Runs`, `Run Detail`, and `Artifacts` is materially clearer
