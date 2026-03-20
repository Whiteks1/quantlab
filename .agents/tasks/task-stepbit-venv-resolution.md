# Task: Virtual Environment & Runtime Resolution

## Goal
Ensure QuantLab can be invoked reliably by Stepbit in different environments (dev, CI, headless nodes) by standardizing runtime resolution.

## Why
Path issues, dependency mismatches, and incorrect Python interpreters are common integration bottlenecks. A stable runtime resolution ensures that "running QuantLab" works identically for humans and AI agents.

## Scope
- Develop a standard method for Stepbit to locate the QuantLab `venv`.
- Ensure QuantLab can resolve its own internal paths regardless of the current working directory (CWD).
- Standardize the `PYTHONPATH` requirements for the project.
- Implement a version/health check command (e.g., `python main.py --version` or `--check`).

## Non-goals
- Implementing a full containerization layer (Docker).
- Managing global Python installations.

## Inputs
- `pyproject.toml` / `requirements.txt`
- `main.py`

## Expected outputs
- A stable runtime resolution strategy (e.g., a wrapper script or standardized env vars).
- A health-check command in the CLI.

## Acceptance criteria
- QuantLab can be invoked from any directory by providing a full path to the interpreter.
- Version and dependency status are easily verifiable via CLI.

## Constraints
- Follow `PEP8` and standard Python packaging practices.
- No hardcoded absolute paths in the codebase.

## GitHub issue
- #24 core: integración - Detectar y usar virtualenv local para ejecución automatizada
## Suggested next step
Move to [task-stepbit-runbook-quantlab.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-runbook-quantlab.md).
