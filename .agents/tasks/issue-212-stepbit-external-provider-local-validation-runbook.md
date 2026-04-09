# Issue #212 - Local Sibling Validation Runbook For The External Provider Path

## Goal
Document a repeatable local validation path for the checked-in Stepbit external provider when `quant_lab` and `stepbit-core` are available side by side.

## Why this matters
The external provider pattern is already real in Stepbit, but local cross-repo validation is still too implicit. Operators should be able to validate the boundary without reverse-engineering environment variables, expected outputs, or pass/fail criteria.

## Scope

### In scope
- sibling-checkout validation flow for QuantLab plus Stepbit-core
- required environment variables and what each one controls
- local commands for boundary validation
- expected success artifacts and expected failure signals
- Windows and POSIX interpreter-path notes where they materially differ

### Out of scope
- remote CI design in Stepbit-core
- store-distribution or packaging work
- network-dependent integration checks as the default path

## Relevant files

- `.agents/stepbit-runbook.md`
- `.agents/stepbit-io-v1.md`
- `docs/stepbit-integration.md`
- `docs/quantlab-stepbit-boundaries.md`

## Expected deliverable

A short runbook update that lets a developer or reviewer validate the external provider path locally with minimal guesswork.

## Done when

- the local validation path is written down end to end
- the documentation names the required env vars and expected artifact locations
- the documentation distinguishes local boundary validation from broader product validation
- a reviewer can follow the runbook without inferring hidden setup

## Notes

This issue is about reproducibility and operator clarity, not about introducing a new integration mode.
