# Issue #211 - QuantLab-Owned Stepbit External-Provider Compatibility Smoke

## Goal
Add one QuantLab-owned compatibility smoke that mirrors the checked-in Stepbit external provider's expectations against the current QuantLab CLI boundary.

## Why this matters
QuantLab already has granular tests for `--json-request`, `--signal-file`, `report.json`, and `machine_contract`, but there is still no single QuantLab-owned slice that proves the exact external-consumer boundary end-to-end.

## Scope

### In scope
- one compatibility-oriented smoke path for external consumption
- canonical `--json-request` execution for at least `run` and `sweep`
- verification of `SESSION_COMPLETED` metadata used to resolve:
  - `report_path`
  - `artifacts_path`
  - `run_id` when available
- verification that machine-facing KPIs come from `report.json.machine_contract.summary`
- one controlled failure case for missing report or invalid machine contract

### Out of scope
- editing `stepbit-core`
- adding a new runtime surface in QuantLab
- broad strategy expansion

## Relevant files

- `test/test_machine_sweep_smoke.py`
- `test/test_signals.py`
- `test/test_cli_run.py`
- `test/test_sweep_contract.py`
- `.agents/stepbit-io-v1.md`
- `docs/stepbit-integration.md`

## Expected deliverable

One reviewable smoke test or tightly scoped fixture-backed test slice that proves QuantLab satisfies the external provider contract already assumed in Stepbit.

## Done when

- QuantLab has one compatibility smoke that is clearly Stepbit-boundary oriented
- the success path asserts `report_path`, `artifacts_path`, and `machine_contract.summary`
- the failure path asserts a deterministic boundary failure instead of an ambiguous runtime error
- the slice reuses existing fixtures where possible instead of duplicating lower-level tests

## Notes

This issue should consolidate the boundary guarantee, not re-test every existing integration behavior independently.
