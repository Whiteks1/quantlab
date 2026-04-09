# Issue #275 — Real-path desktop validation and smoke semantics

## Goal
Restore CI coverage over the real desktop operating path while keeping the local-shell fallback smoke useful and explicitly named.

---

## Why this matters
The current desktop smoke accepts the local fallback path and no longer guarantees that `research_ui` actually booted and became reachable. Desktop validation needs a second mode that fails when the live shell-to-server path is broken.

---

## Scope

### In scope
- `desktop/scripts/smoke.js`
- `desktop/main.js`
- `desktop/preload.js` only as a blocker fix required to make desktop smoke executable from the current `main` base
- `desktop/package.json`
- `.github/workflows/ci.yml`
- `.agents` continuity

### Out of scope
- renderer or UX refactors
- broker/core fixes
- `research_ui` behavior changes
- broad CI cleanup outside the desktop validation path

---

## Relevant files

- `desktop/scripts/smoke.js`
- `desktop/main.js`
- `desktop/package.json`
- `.github/workflows/ci.yml`

---

## Expected deliverable

An explicit fallback smoke, an explicit real-path desktop validation, and CI coverage that makes the distinction visible.

---

## Done when

- fallback smoke still exists
- real-path smoke fails if `research_ui` does not become reachable
- CI runs the real-path desktop validation explicitly
- script and CI naming make the semantics obvious
