# Task: QuantLabTool Adapter Implementation

## Goal
Implement the internal logic for the `QuantLabTool` in Stepbit-core.

## Why
After the interface is defined and the QuantLab-side bridge is stable (Steps 1-5), the adapter implementation provides the actual execution power to Stepbit agents.

## Scope
- Implement shell command invocation for the QuantLab CLI.
- Implement JSON parsing for `metadata.json`, `config.json`, and `report.json`.
- Implement robust `venv` resolution logic using the standards from Step 5.
- Connect QuantLab's exit codes to the Stepbit error handling system.
- Implement the "Fetch Results" logic to pull artifacts into Stepbit's context.

## Non-goals
- Adding "intelligence" to the tool (it should be a reliable pipe).
- Managing QuantLab's internal data directories.

## Inputs
- `.agents/tasks/task-stepbit-adapter-interface.md`
- `.agents/tasks/task-stepbit-io-contract.md`
- `.agents/tasks/task-stepbit-venv-resolution.md`

## Expected outputs
- A fully functional `QuantLabTool` in the Stepbit-core repository.
- Unit tests for the adapter (mocking the CLI).

## Acceptance criteria
- The tool can start a run and retrieve the `report.json` correctly.
- Errors in QuantLab are caught and re-raised according to the Stepbit adapter policy.

## Constraints
- Do not replicate business logic.
- Ensure cross-platform path compatibility (Windows/Linux).

## GitHub issue
- #19 meta: backlog consolidado QuantLab ↔ Stepbit

## Derived from
- `.agents/tasks/stage-stepbit-integration-roadmap.md`

## Suggested next step
Move to [task-stepbit-e2e-flow.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-e2e-flow.md).
