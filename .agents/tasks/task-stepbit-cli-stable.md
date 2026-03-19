# Task: Stable CLI for Machine Interaction

## Goal
Refactor or harden the QuantLab CLI to ensure it is predictable and robust when called by headless orchestration tools. [DONE]

## Why
Standard library CLI parsers or interactive prompts can break machine-to-machine integration. A "stable" CLI mode ensures consistent behavior, machine-readable errors, and no blocking prompts.

## Scope
- [x] Ensure all commands support a non-interactive mode.
- [x] Standardize `--config` flag to accept JSON strings or file paths (`--json-request`).
- [x] Ensure logging output does not interfere with stdout for data extraction.
- [x] Implement consistent exit codes for success, configuration errors, and execution failures.

## Non-goals
- Completely rewriting the CLI (e.g., switching from `argparse` to `click`).
- Adding new user-facing features to the CLI.

## Inputs
- `main.py`
- `src/quantlab/cli/`

## Expected outputs
- [x] Updated `main.py` with stable routing.
- [x] Tests for CLI exit codes and machine-readable error output.

## Acceptance criteria
- [x] Substituted `print` statements with proper logging where appropriate (Refactored `main.py`).
- [x] CLI tests passing for all major commands (run, sweep, forward, report).
- [x] Zero interactive-only modes for core research tasks.

## Constraints
- [x] Do not remove existing human-facing CLI flags; maintain backward compatibility.
- [x] Adhere to "No business logic in main.py".

## Suggested next step
Read [task-stepbit-report-json.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-report-json.md).
