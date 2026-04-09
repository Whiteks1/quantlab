# Issue #202 — Runs as Primary Work Surface

## Goal
Make `Runs` the default operating home of QuantLab Desktop and strengthen its visual hierarchy so it behaves like the main workstation list, not a secondary tab.

## Why this matters
Runs are the most legible anchor for QuantLab's research identity: explicit runs, metrics, artifacts, and decisions.

## Scope

### In scope
- default desktop entry behavior
- stronger runs summary and evidence context
- denser run explorer presentation

### Out of scope
- run detail redesign
- compare redesign
- public web copy changes

## Relevant files

- `desktop/renderer/app.js`
- `desktop/renderer/modules/tab-renderers.js`
- `desktop/renderer/styles.css`

## Expected deliverable

A desktop startup path that defaults to `Runs` when data is available, plus a stronger runs tab with:

- summary cards
- dense table
- evidence/context rail

## Done when

- cold boot prefers `Runs` instead of an empty shell/chat-first state
- the runs tab reads as the main workbench
- actions from the runs context remain functional
