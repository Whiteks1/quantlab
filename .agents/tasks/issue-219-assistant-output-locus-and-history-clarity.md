# Issue #219 — Assistant output locus and history clarity

## Goal
Make the lower assistant panel the single obvious output and history surface for support interactions.

---

## Why this matters
Right now a user can type in one place and see the answer appear in another without strong visual explanation. That breaks the correspondence between where input happens and where output is expected.

---

## Scope

### In scope
- assistant panel title and copy
- response-log framing
- history labels and empty-state clarity
- visual cues that the lower panel is the only conversation log

### Out of scope
- new assistant capabilities
- Stepbit protocol changes
- global desktop layout changes outside the support lane

---

## Relevant files

- `desktop/renderer/index.html`
- `desktop/renderer/styles.css`
- `desktop/renderer/app.js`

---

## Expected deliverable

A lower support panel that is unmistakably the single assistant history and response surface.

---

## Done when

- users no longer need to infer where replies will appear
- the lower panel clearly owns assistant history
- helper text, labels, and empty states reinforce the single-output model
