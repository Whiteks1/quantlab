# Issue #208 — Right Rail Evidence Panel Maturity

## Goal
Turn the right-side panels into stronger evidence rails with better summary structure, continuity cues, and higher-value context.

## Why this matters
The workstation direction depends on the right rail being useful, stable, and information-dense. Right now it is structurally correct, but still not fully mature.

## Scope

### In scope
- right-rail panel hierarchy
- evidence summaries
- compact context blocks
- optional mini-visuals only if they add operator value

### Out of scope
- heavy charting as decoration
- new runtime endpoints
- replacing the main table with visual cards

## Relevant files

- `desktop/renderer/modules/tab-renderers.js`
- `desktop/renderer/styles.css`

## Expected deliverable

A right rail that behaves like an evidence surface rather than just a secondary card stack.

## Done when

- the right rail gives better selected-context value
- continuity and evidence are easier to understand without leaving the active tab
- any visual summaries remain sober and operational

## Notes

Mini visualizations are optional and should only be used if they improve reviewability.
