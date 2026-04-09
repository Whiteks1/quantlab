# Issue #207 — Runs Table Visual Semantics and Density Polish

## Goal
Polish the `Runs` surface so the main table reads faster, carries clearer state semantics, and feels closer to a mature analytical desk.

## Why this matters
`Runs` is now the primary work surface. It already has the right structure, but its table and row semantics can still become clearer and more glanceable.

## Scope

### In scope
- runs table row polish
- column clarity and hierarchy
- metric readability
- state chips, markers, or semaphores where justified

### Out of scope
- changing run data contracts
- adding new backend-derived metrics
- redesigning non-runs tabs

## Relevant files

- `desktop/renderer/modules/tab-renderers.js`
- `desktop/renderer/styles.css`
- `desktop/renderer/modules/view-primitives.js`

## Expected deliverable

A denser and more legible `Runs` surface with clearer visual ranking of state, metrics, and actions.

## Done when

- important run signals are easier to scan row by row
- actions remain available without cluttering the table
- the table feels more like a product workbench than a placeholder registry

## Notes

This issue is the main visual bridge toward the screenshot reference, but using QuantLab semantics.
