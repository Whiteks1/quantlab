# Task — Desktop Shared Contracts Foundation

## Goal
Establish the first shared Desktop contracts for the current Electron shell without opening the TypeScript base slice yet.

After this work:
- `desktop/shared` contains the first typed shared models used by the current shell
- `main.js`, `preload.js`, `renderer/app.js`, and `desktop/scripts/smoke.js` consume those contracts through narrow JSDoc typing
- no functional desktop behavior changes

---

## Why this matters
- fixes the first real Desktop contract boundary before the TypeScript base slice
- reduces risk for the upcoming `desktop-typescript-base` branch
- keeps the migration ordered: contracts first, build/tooling next

---

## Scope

### In scope
- add `desktop/shared/ipc/channels.ts`
- add `desktop/shared/ipc/envelope.ts`
- add `desktop/shared/models/workspace.ts`
- add `desktop/shared/models/runtime.ts`
- add `desktop/shared/models/snapshot.ts`
- add `desktop/shared/models/smoke.ts`
- type only the already-existing workspace, runtime/snapshot, and smoke boundaries

### Out of scope
- TypeScript base setup
- `tsconfig.json`
- `global.d.ts`
- React or Vite
- main modularization
- new UI models such as runs/compare/launch
- functional desktop behavior changes

---

## Relevant files

- `desktop/main.js`
- `desktop/preload.js`
- `desktop/renderer/app.js`
- `desktop/scripts/smoke.js`
- `desktop/shared/`

---

## Expected deliverable

- minimal shared contract layer for the current desktop shell
- typed workspace push/pull boundary
- typed runtime/snapshot shell state
- typed smoke result boundary

---

## Done when

- current desktop shell consumes the shared contract files without behavior change
- `node --check` passes for touched JS files
- the next slice can start cleanly as `desktop-typescript-base`
