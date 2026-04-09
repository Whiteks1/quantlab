# Issue #214 — Renderer Tab Binding Registry Hardening

## Goal
Replace the long `bindTabContentEvents` conditional chain with a tab-kind binding registry so renderer event wiring stays easier to maintain.

## Why this matters
The workstation renderer has grown substantially. The next maintainability risk is leaving all tab event wiring in one large conditional block inside `desktop/renderer/app.js`.

## Scope

### In scope
- `bindTabContentEvents` refactor only
- local handler registry by `tab.kind`
- no behavior change

### Out of scope
- visual changes
- module extraction
- runtime or IPC logic
- changing tab rendering behavior

## Relevant files

- `desktop/renderer/app.js`

## Expected deliverable

A smaller and easier-to-extend tab-content binding path in the renderer, with existing behavior preserved.

## Done when

- `bindTabContentEvents` no longer depends on a long sequence of `if (tab.kind === ...)`
- each supported tab kind binds through a clear local handler
- desktop smoke still passes

## Notes

Keep this slice narrow. Do not mix it with renderer visuals, new surfaces, or runtime work.
