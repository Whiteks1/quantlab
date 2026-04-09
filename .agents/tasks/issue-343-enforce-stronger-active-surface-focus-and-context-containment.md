# Issue #343 — Enforce stronger active-surface focus and context containment

## Goal
Stop the shell from reading like a stack of open context and make the current active surface unambiguous after a short navigation sequence.

---

## Why this matters
Containment improved in earlier slices, but `Focused work surfaces` can still accumulate enough context to weaken ownership and reduce clarity. The shell needs stronger replace-vs-append discipline in practice, not just in intent.

---

## Scope

### In scope
- active-surface emphasis
- context-tab accumulation discipline
- collapse or demotion of stale context
- clearer replace-vs-append outcomes in the shell

### Out of scope
- support-lane semantics already handled by Issue #287
- new navigation features not tied to focus
- legacy embedded views as target-state
- engine or CLI changes

---

## Relevant files

- `desktop/renderer/app.js`
- `desktop/renderer/index.html`
- `desktop/renderer/styles.css`

---

## Expected deliverable

A shell where sidebar navigation and contextual actions preserve continuity without leaving the operator unsure which surface currently owns the workspace.

---

## Done when

- one primary surface is always obvious
- context tabs remain useful without taking over the shell
- duplicate or stale surface context is collapsed or demoted
- the shell is easier to read after several navigation steps, not harder
