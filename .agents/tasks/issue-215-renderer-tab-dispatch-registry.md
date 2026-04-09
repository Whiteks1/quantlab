# Issue #215 — Renderer Tab Dispatch Registry

## Goal
Replace the long `renderTabs()` tab-kind conditional chain with a local dispatch registry so the renderer stays easier to extend and audit.

## Why this matters
The desktop renderer already has multiple tab surfaces. The next maintainability hotspot is the long render-time tab-kind branch in `desktop/renderer/app.js`.

## Scope

### In scope
- `renderTabs()` dispatch refactor in `desktop/renderer/app.js`
- local render registry by `tab.kind`
- no behavior change

### Out of scope
- renderer module extraction
- styling changes
- runtime, smoke, bootstrap, or IPC logic
- `research_ui`
- core Python or contract work

## Relevant files

- `desktop/renderer/app.js`

## Expected deliverable

A clearer render dispatch path that preserves existing desktop behavior while reducing conditional sprawl in the renderer shell.

## Done when

- `renderTabs()` no longer depends on the long `if / else if` tab-kind chain
- fallback placeholder behavior still works
- desktop smoke still passes
