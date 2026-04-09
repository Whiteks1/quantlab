# Issue #342 — Collapse empty panes and restore primary workbench ownership

## Goal
Make the active work surface reclaim the desktop window instead of leaving large empty panes while useful content is compressed into a narrow column.

---

## Why this matters
The shell now has better semantics than before, but the composition still fails in real use. Empty or low-value panes keep too much width, so the workstation feels worse than the underlying UX improvements warrant.

---

## Scope

### In scope
- collapse or demote empty panes
- restore width to the active workbench
- ensure the primary surface dominates the central area
- tighten left/right lane ownership when the center needs the space

### Out of scope
- new runtime or backend behavior
- `research_ui` changes
- core contract changes
- new product surfaces

---

## Relevant files

- `desktop/renderer/index.html`
- `desktop/renderer/app.js`
- `desktop/renderer/styles.css`
- `desktop/renderer/modules/tab-renderers.js` only if required by pane ownership

---

## Expected deliverable

A desktop shell where empty space no longer outranks the active work surface, and the primary workbench owns the window by default.

---

## Done when

- empty panes collapse instead of reserving large blank columns
- active surfaces reclaim width automatically
- the central workbench remains visually dominant in `Runs`, `Candidates`, `Compare`, and `Paper Ops`
- low-data or single-surface states still look intentional instead of broken
