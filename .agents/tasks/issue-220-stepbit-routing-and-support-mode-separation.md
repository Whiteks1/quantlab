# Issue #220 — Stepbit routing and support-mode separation

## Goal
Clarify when the right rail is using deterministic QuantLab support versus explicit Stepbit reasoning.

---

## Why this matters
The current right rail mixes deterministic helper responses and Stepbit routing inside one visual area without enough mode separation. That weakens operator trust and makes the support lane harder to reason about.

---

## Scope

### In scope
- Stepbit route affordance labels
- assistant status copy
- support-mode signaling inside the right rail
- clear distinction between deterministic responses and Stepbit-backed reasoning

### Out of scope
- Stepbit backend connectivity changes
- new reasoning features
- non-right-rail Stepbit surfaces

---

## Relevant files

- `desktop/renderer/index.html`
- `desktop/renderer/styles.css`
- `desktop/renderer/app.js`

---

## Expected deliverable

A support lane where deterministic QuantLab actions and Stepbit-routed reasoning are visibly separate modes instead of blended semantics.

---

## Done when

- Stepbit routing is explicit instead of implied
- deterministic support messages do not masquerade as Stepbit reasoning
- support status copy matches actual runtime behavior
