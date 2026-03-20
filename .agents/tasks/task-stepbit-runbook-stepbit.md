# Task: Stepbit Runbook for QuantLab Operations

## Goal
Create an operational runbook within Stepbit-core that guides Stepbit agents on how to leverage the `QuantLabTool` for research.

## Why
While the QuantLab-side runbook explains the CLI, the Stepbit-side runbook explains the *orchestration patterns*. It ensures agents know when to run a sweep vs a single backtest, how to interpret KPIs for ranking, and how to handle research failures.

## Scope
- Document standard Stepbit agent "thought patterns" for strategy research.
- Explain how to use QuantLab results to feed the next Stepbit optimization loop.
- Provide "If-This-Then-That" (IFTTT) operational patterns for common research scenarios.
- List Stepbit-side environment configurations required for the QuantLab bridge.

## Non-goals
- Documenting Stepbit-core's internal LLM orchestration logic.
- Creating a separate UI for Stepbit operations.

## Inputs
- `.agents/tasks/task-stepbit-adapter-impl.md`
- `.agents/stepbit-runbook.md` (QuantLab-side)

## Expected outputs
- A new runbook file in the Stepbit-core repository: `docs/runbooks/quantlab-ops.md`.

## Acceptance criteria
- A new Stepbit agent can read this runbook and immediately begin orchestrating QuantLab research.
- The runbook aligns with Stepbit-core's broader operational standards.

## Constraints
- Must be referencable by Stepbit's system prompts.
- Maintain high-level abstraction (refer to the QuantLab runbook for CLI details).

## GitHub issue
- #28 docs: integration - Add QuantLab integration runbook

## Suggested next step
Move to [task-stepbit-events-signals.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-events-signals.md).
