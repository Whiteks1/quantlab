# Issue #206 — Desktop Topbar and Global Chrome Maturity

## Goal
Make the desktop chrome feel more like a mature workstation by strengthening the topbar, global context, and shell framing.

## Why this matters
The workstation layout is already in place, but the top-level chrome still reads more like an internal shell than a polished research product.

## Scope

### In scope
- topbar hierarchy
- shell-level labels and framing
- global actions presentation
- workspace context visibility

### Out of scope
- tab-specific table redesign
- backend or runtime state changes
- landing or public web branding

## Relevant files

- `desktop/renderer/index.html`
- `desktop/renderer/styles.css`
- `desktop/renderer/modules/shell-chrome.js`
- `.agents/tasks/issue-block-desktop-visual-maturity.md`

## Expected deliverable

A clearer topbar and shell chrome that make the desktop feel like a dedicated QuantLab research instrument.

## Done when

- the topbar communicates stronger workspace identity
- global controls feel deliberate rather than provisional
- shell chrome is visually consistent with the workstation direction

## Notes

This issue should improve maturity without changing tab behavior.
