# Issue #213 - External Strategy Surface Policy And Deterministic Coverage

## Goal
Define the supported strategy surface for external Stepbit consumers and back that decision with deterministic coverage.

## Why this matters
The checked-in Stepbit external provider currently exposes only `rsi_ma_cross_v2`. That may be acceptable as an MVP, but leaving the supported strategy surface implicit makes the boundary look broader than it really is and invites accidental regressions.

## Scope

### In scope
- define the minimum supported strategy set for the external boundary
- document whether the boundary remains intentionally narrow or is being widened
- add or align deterministic tests for the chosen supported surface
- ensure unsupported strategies fail in a deliberate and documented way

### Out of scope
- exposing every QuantLab strategy automatically
- changing QuantLab's internal strategy architecture
- turning external strategy support into the main product roadmap

## Relevant files

- `.agents/current-state.md`
- `.agents/stepbit-io-v1.md`
- `docs/stepbit-integration.md`
- `test/test_cli_run.py`
- `test/test_strategy_rsi_ma_atr.py`

## Expected deliverable

An explicit policy for external strategy support, plus deterministic validation that matches that policy.

## Done when

- the supported strategy set for external consumers is explicit
- the chosen strategy surface is covered by deterministic tests
- unsupported-strategy behavior is documented and reviewable
- QuantLab no longer implies a broader external strategy surface than it actually guarantees

## Notes

If the right decision is to keep the external boundary narrow for now, the repo should say that plainly instead of implying generic support.
