# Task: End-to-End Integration Flow

## Goal
Verify the complete lifecycle of a research task initiated by Stepbit and executed by QuantLab.

## Why
The ultimate proof of integration is a successful end-to-end loop where Stepbit identifies a research need, invokes QuantLab, and correctly interprets the resulting artifacts.

## Scope
- Define a "Smoke Test" research scenario (e.g., "Run RSI strategy on BTC/USDT for Jan 2024").
- Execute the scenario via the Stepbit `QuantLabTool`.
- Verify that metadata, metrics, and reports are correctly generated and parsed.
- Validate that the Stepbit agent can make a follow-up decision based on the JSON results.

## Non-goals
- Performance benchmarking of the data pipeline.
- Testing every possible strategy combination.

## Inputs
- All previous integration tasks.
- A sample strategy in QuantLab.

## Expected outputs
- A recorded walkthrough of a successful E2E research loop.
- A "Green" status for the Stepbit-QuantLab bridge.

## Acceptance criteria
- Zero manual intervention required during the flow.
- All artifacts are produced deterministically.
- Error cases (e.g., missing data) are handled as per the error policy.

## Constraints
- Must use the "Stable CLI" and "report.json" as the source of truth.
- No hardcoded test paths.

## GitHub issue
- #27 test: integration - End-to-end Reasoning Engine -> QuantLabTool flow

## Suggested next step
Read [task-stepbit-runbook-stepbit.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-runbook-stepbit.md).
