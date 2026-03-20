# Task: QuantLab Runbook for Stepbit

## Goal
Create a human-readable and machine-referenceable "Runbook" within the QuantLab repository that describes how to operate the system via Stepbit.

## Why
Clear operational documentation is essential for maintaining the integration. The runbook acts as the source of truth for Stepbit agents on how to invoke QuantLab, troubleshoot common issues, and interpret results.

## Scope
- Document standard CLI command patterns for basic tasks (run, sweep, forward).
- Reference the **I/O Contract** and **report.json** schemas from Steps 1 & 3.
- List required environment variables and configuration files.
- Explain the significance of key artifacts (metadata, config, metrics).
- Provide troubleshooting steps for common error codes defined in the **Error Policy** (Step 4).

## Non-goals
- Documenting every internal function (use code docstrings for that).
- Creating a separate wiki or external site.

## Inputs
- `.agents/tasks/task-stepbit-io-contract.md`
- `.agents/tasks/task-stepbit-report-json.md`
- `.agents/tasks/task-stepbit-cli-stable.md`
- `.agents/tasks/task-stepbit-error-policy.md`

## Expected outputs
- A new file: `.agents/stepbit-runbook.md`.

## Acceptance criteria
- The runbook is concise and action-oriented.
- An AI agent reading the runbook can successfully execute a backtest using the CLI.

## Constraints
- Must reside within the `.agents/` directory to be accessible to AI agents.
- Follow the "reproducibility" principle.

## GitHub issue
- #26 docs: integración - Completar runbook QuantLab <-> Stepbit

## Suggested next step
Move to [task-stepbit-adapter-interface.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-adapter-interface.md).
