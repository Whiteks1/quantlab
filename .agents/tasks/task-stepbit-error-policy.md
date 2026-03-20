# Task: Stepbit Error & Exception Policy

## Goal
Define how QuantLab should communicate failures to Stepbit-core to ensure the orchestration layer can gracefully handle and retry errors.

## Why
Silent failures or generic traceback outputs make automated orchestration brittle. A clear error policy ensures that "Configuration Error" is distinguished from "Data Loading Failure" or "Strategy Crash."

## Scope
- Define a hierarchy of custom exceptions in QuantLab.
- Map exceptions to specific exit codes for CLI consumers.
- Ensure error messages in stdout/stderr are structured or easily parsable.
- Document the policy for "fail-fast" vs "fail-soft" in different session types.

## Non-goals
- Implementing a complete logging service or remote error tracking.
- Modifying core strategy logic to handle every possible edge case internally.

## Inputs
- `.agents/implementation-rules.md`
- `src/quantlab/cli/`

## Expected outputs
- A new `src/quantlab/errors.py` or equivalent for centralized error definitions.
- Documentation of exit codes and error categories.

## Acceptance criteria
- Failures due to invalid config return a different exit code than runtime crashes.
- Errors are logged clearly without cluttering the artifact outputs.

## Constraints
- Maintain the "Correctness before convenience" principle.
- No side effects on error (e.g., do not leave partial/broken run directories).

## GitHub issue
- #23 core: integración - Política de errores y reintentos QuantLab <-> Stepbit

## Suggested next step
Read [task-stepbit-venv-resolution.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-venv-resolution.md).
