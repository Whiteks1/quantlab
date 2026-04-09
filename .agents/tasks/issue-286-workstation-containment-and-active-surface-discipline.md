# Issue #286 — Workstation containment and active-surface discipline

## Goal
Stop the desktop shell from behaving like an accumulating container and make the primary work surface explicit and stable.

---

## Why this matters
The desktop already has working surfaces and real data, but focus drifts as tabs accumulate and layout containment weakens. The result is a shell that works but does not yet behave like a disciplined workstation.

---

## Scope

### In scope
- active surface rules
- replace vs append policy
- tab accumulation discipline
- sidebar/workbench/right-rail containment
- scroll policy
- command palette containment where it affects workstation stability

### Out of scope
- broker/core fixes
- CLI or Python contract changes
- right-rail assistant semantics beyond what is required for containment

---

## Relevant files

- `desktop/renderer/index.html`
- `desktop/renderer/styles.css`
- `desktop/renderer/app.js`

---

## Expected deliverable

A desktop shell where navigation rules are explicit, the active surface is clear, and layout containment stays stable through extended use.

---

## Done when

- sidebar navigation defaults are clear
- the active surface is visually obvious
- accumulation is reduced or disciplined
- nested scroll and containment problems are materially reduced
- command palette no longer feels visually detached from the workstation
