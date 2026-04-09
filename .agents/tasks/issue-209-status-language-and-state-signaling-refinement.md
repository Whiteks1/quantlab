# Issue #209 — Status Language and State Signaling Refinement

## Goal
Refine state presentation so status, readiness, validation, and continuity signals are more consistent across the desktop.

## Why this matters
The desktop now exposes many operational states, but the signaling language is still partially mixed between chips, prose, and generic labels.

## Scope

### In scope
- status chip language
- tone consistency
- validation/readiness wording
- cross-surface state semantics

### Out of scope
- backend state model changes
- new health endpoints
- broad copy rewrite outside the desktop

## Relevant files

- `desktop/renderer/modules/tab-renderers.js`
- `desktop/renderer/modules/shell-chrome.js`
- `desktop/renderer/styles.css`

## Expected deliverable

A more coherent state-signaling system that makes the desktop easier to operate and review.

## Done when

- similar states use similar visual treatment
- status wording feels QuantLab-specific and deliberate
- warning, success, and review-needed states are easier to distinguish

## Notes

This issue should tighten semantics, not add decorative noise.
