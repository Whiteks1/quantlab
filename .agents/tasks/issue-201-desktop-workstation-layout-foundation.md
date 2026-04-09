# Issue #201 — Desktop Workstation Layout Foundation

## Goal
Establish the desktop shell layout direction for a workstation-style QuantLab UI, including the correct hierarchy between primary work surface, secondary context, and assistant tooling.

## Why this matters
The current desktop still reads as a shell in evolution. QuantLab needs a clearer workstation grammar before deeper tab-level redesigns land.

## Scope

### In scope
- define the target shell hierarchy
- reduce ambiguity about primary vs secondary panels
- align desktop layout with research workstation semantics

### Out of scope
- full visual redesign of every tab
- landing or public brand work
- backend contract changes

## Relevant files

- `desktop/renderer/index.html`
- `desktop/renderer/styles.css`
- `.agents/tasks/issue-block-desktop-workstation-ui.md`

## Expected deliverable

A shell layout direction that clearly distinguishes:

- main work surface
- context/evidence rail
- assistant tooling

## Done when

- the desktop no longer presents chat as the implicit main product surface
- the shell layout supports denser workstation flows
- the change remains compatible with current renderer tabs

## Notes

This issue is the structural foundation for issues #202 to #205.
