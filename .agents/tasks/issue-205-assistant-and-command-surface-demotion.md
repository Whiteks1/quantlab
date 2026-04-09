# Issue #205 — Assistant and Command Surface Demotion

## Goal
Reposition chat and command entry so they support the workstation instead of visually defining it.

## Why this matters
QuantLab should feel research-first and evidence-first. The assistant is useful, but it should not read as the main product surface.

## Scope

### In scope
- assistant panel hierarchy
- command bar emphasis
- prompt suggestions cleanup
- secondary-surface styling

### Out of scope
- Stepbit protocol changes
- LLM backend changes
- landing or branding changes

## Relevant files

- `desktop/renderer/index.html`
- `desktop/renderer/styles.css`
- `desktop/renderer/app.js`

## Expected deliverable

A calmer assistant surface that remains useful without dominating the desktop.

## Done when

- chat reads as support tooling
- core workstation flows remain visible without entering chat
- command entry stays available but not visually central
