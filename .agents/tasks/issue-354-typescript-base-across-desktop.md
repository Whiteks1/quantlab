# Issue #354 — TypeScript Base Across Desktop

## Goal
Establish the real TypeScript base for `desktop/` without changing runtime behavior or opening the renderer migration yet.

---

## Why this matters
- turns `desktop/shared` into a first-class typed contract layer
- prepares the modularization of `main.js` without spreading JS debt into more files first
- keeps the migration sequence disciplined: contracts first, tooling second, architecture refactor third

---

## Scope

### In scope
- `desktop/tsconfig.json`
- `desktop/types/global.d.ts`
- `desktop/package.json`
- minimal typecheck-driven edits in `desktop/main.js`, `desktop/preload.js`, and `desktop/renderer/app.js`
- native consumption of `desktop/shared/ipc` and `desktop/shared/models`

### Out of scope
- modularizing `main.js`
- React
- Vite
- `research_ui`
- new shared models
- functional behavior changes
- visible UI changes

---

## Relevant files

- `desktop/package.json`
- `desktop/tsconfig.json`
- `desktop/types/global.d.ts`
- `desktop/main.js`
- `desktop/preload.js`
- `desktop/renderer/app.js`
- `desktop/shared/`

---

## Expected deliverable

- TypeScript base configuration for the current Desktop shell
- current Desktop entrypoints passing `typecheck` while staying in JS
- no runtime behavior change

---

## Done when

- `npm run typecheck` passes in `desktop/`
- `node --check` passes for touched JS entrypoints
- `smoke:fallback` and `smoke:real-path` stay green
- `main.js`, `preload.js`, and `renderer/app.js` consume `desktop/shared` natively through the TS base
