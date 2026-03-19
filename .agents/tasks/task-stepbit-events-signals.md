# Task: Event Signalling & Session Hooks (Optimization)

## Goal
Implement a lightweight "event" or "hook" system in QuantLab to signal progress or completion to Stepbit without requiring constant polling.

## Why
For long-running sweeps or complex forward evaluations, polling the filesystem is inefficient. This optimization allows QuantLab to "push" state changes to Stepbit, reducing latency in the research loop.

## Scope
- Define "Key Events" to signal (e.g., `RUN_STARTED`, `RUN_COMPLETED`, `RUN_FAILED`).
- Implement an optional `--webhook` or `--signal-file` flag in the CLI.
- Ensure signals include the `run_id` and a path to the `report.json`.

## Non-goals
- Implementing a complex message broker (Kafka, RabbitMQ).
- Real-time streaming of trade-by-trade status (keep it to session-level events).

## Inputs
- `.agents/tasks/task-stepbit-cli-stable.md`
- `src/quantlab/cli/`

## Expected outputs
- Updated CLI parser and orchestration logic supporting signals/hooks.
- Documentation of the event payload structure.

## Acceptance criteria
- Stepbit can receive a signal immediately upon session completion.
- Signals are optional and do not break the "Strictly Offline" / "CLI-first" research mode.

## Constraints
- Use standard Python libraries (e.g., `requests` for webhooks) or simple file-based signals.
- No heavy infrastructure dependencies.

## Suggested next step
Move to [task-stepbit-distributed-sweeps.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-distributed-sweeps.md).
