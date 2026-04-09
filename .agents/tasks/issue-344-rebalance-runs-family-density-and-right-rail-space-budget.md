# Issue #344 — Rebalance runs-family density and right-rail space budget

## Goal
Bring `Runs`, `Candidates`, and `Compare` closer to workstation density by reducing low-value chrome and restoring space to the information that actually matters.

---

## Why this matters
The shell now explains more, but the runs-family surfaces still waste space. Some rows and cards are too sparse, key data columns are too compressed, and the right rail can still claim more width than its value justifies.

---

## Scope

### In scope
- run-row and card density
- width allocation inside runs-family surfaces
- tighter right-rail space budget
- intentional empty-state composition for low-data views

### Out of scope
- changing research semantics
- artifact contract changes
- support-lane semantic cleanup beyond space budget
- core-side data shape changes

---

## Relevant files

- `desktop/renderer/modules/tab-renderers.js`
- `desktop/renderer/styles.css`
- `desktop/renderer/index.html` only if needed for grid balance

---

## Expected deliverable

Runs-family surfaces where primary content reads as dense and deliberate, and auxiliary chrome no longer steals space from the data.

---

## Done when

- `Runs`, `Candidates`, and `Compare` feel denser and better balanced
- key run information gets more usable width than decorative or low-value chrome
- the right rail respects a tighter budget without breaking low-data states
- sparse states still look designed instead of unfinished
