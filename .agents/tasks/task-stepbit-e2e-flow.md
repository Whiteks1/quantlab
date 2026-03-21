# Task: End-to-End Integration Flow Validation

## Goal
Validate the first usable end-to-end integration slice between Stepbit and QuantLab using the current stable CLI, canonical `report.json`, and implemented exit code policy.

## Why
After defining the contract, stabilizing the JSON request path, standardizing machine-readable reporting, and implementing the error policy, the next step is to verify that these pieces work together as one coherent integration flow.

## Scope
- define one minimal smoke-test research scenario
- execute the scenario through the current Stepbit -> QuantLab invocation path
- verify that QuantLab:
  - accepts the request correctly
  - exits with the expected code
  - generates the expected artifacts
  - exposes machine-readable summary data in `report.json`
- verify that the integration layer can read the resulting JSON artifact and determine the next action from it
- verify at least one controlled failure case and confirm it follows the implemented error policy

## Non-goals
- benchmarking performance
- validating every strategy or market combination
- testing distributed execution
- validating event emission
- validating venv resolution logic
- validating advanced orchestration behaviors not yet implemented

## Inputs
- `.agents/stepbit-io-v1.md`
- `.agents/artifact-contracts.md`
- the completed integration slices from issues #20, #21, #22, and #23
- one sample strategy / one deterministic research scenario

## Expected outputs
- a documented smoke-test scenario
- a recorded walkthrough of the integration slice
- explicit verification of:
  - request input
  - exit code
  - generated artifacts
  - `report.json` summary
  - follow-up decision basis
- a clear pass/fail conclusion for the current integration slice

## Acceptance criteria
- the smoke-test scenario completes through the current integration path
- `report.json` is produced and readable as the source of truth
- the exit code matches the observed outcome
- the success path is reproducible
- at least one failure path is verified against the current error policy
- the result clearly identifies what is already integration-ready vs what remains deferred

## Constraints
- must use the current stable CLI contract
- must use `report.json` as the canonical machine-readable artifact
- must use current implemented exit code behavior
- no hardcoded machine-specific paths
- keep the scenario minimal and repeatable

## GitHub issue
- #27 test: integration - End-to-end Reasoning Engine -> QuantLabTool flow

## Suggested next step
Define one success scenario and one failure scenario, then verify the full path from request payload to exit code to `report.json`.
