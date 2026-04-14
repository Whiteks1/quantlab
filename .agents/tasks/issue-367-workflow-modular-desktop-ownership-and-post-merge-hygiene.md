# Issue #367 — Workflow for Modular Desktop Ownership and Post-Merge Hygiene

## Goal

Update workflow rules so they match the current architecture and enforce explicit post-merge hygiene.

## In scope

- update Desktop/UI ownership to cover `desktop/main/**`
- update boundary-sensitive file guidance after main modularization
- define mandatory post-merge closeout
- align public workflow docs if required

## Out of scope

- runtime changes
- renderer changes
- refactors outside workflow documentation

## Done when

- ownership rules reflect the modular desktop main process
- post-merge hygiene is explicit and mandatory
- workflow docs no longer assume `desktop/main.js` is the only main-process boundary
