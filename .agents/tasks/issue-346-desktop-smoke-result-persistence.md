# Issue #346 — Desktop smoke result persistence in CI

## Goal
Prevent `desktop-smoke` from failing with a raw missing-file error before the smoke harness can read or emit a structured result.

---

## Why this matters
Planning-only Desktop/UI PRs are being blocked by a smoke harness failure that occurs before `result.json` exists. The harness needs a reliable failure path even when Electron exits before the normal smoke callback completes.

---

## Scope

### In scope
- smoke result persistence
- early-exit and renderer-failure handling for smoke runs
- minimal harness hardening in `desktop/scripts/smoke.js`

### Out of scope
- renderer UI changes
- `research_ui` changes
- core, broker, CLI, or CI workflow edits

---

## Relevant files

- `desktop/main.js`
- `desktop/scripts/smoke.js`

---

## Expected deliverable

A smoke harness that always produces a structured result or a clear structured failure message instead of crashing with `ENOENT` on missing `result.json`.

---

## Done when

- CI no longer fails with raw `ENOENT` for missing smoke output
- smoke runs persist a result even when Electron exits too early
- local smoke validation still passes for normal fallback and real-path cases
