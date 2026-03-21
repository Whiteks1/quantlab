# Task: Virtual Environment & Runtime Resolution

## Goal
Make QuantLab invocable in a predictable way for automated Stepbit execution by reducing interpreter, path, and current-working-directory fragility.

## Why
After validating the first usable Stepbit ↔ QuantLab integration slice, the next bottleneck is operational reliability: the integration should not depend on launching QuantLab from one specific shell context or manually guessing the correct interpreter and import path.

## Scope
- define the minimal runtime resolution strategy for automated QuantLab execution
- make QuantLab execution robust against current working directory differences where practical
- define how the correct Python interpreter should be supplied or resolved for local automated execution
- add a minimal CLI health/version check suitable for automation
- document the expected invocation contract for local automated use

## Non-goals
- full packaging redesign
- Docker or container orchestration
- global Python management
- remote environment management
- broad deployment tooling
- runbook authoring beyond what is strictly needed to document the runtime contract

## Inputs
- `main.py`
- current repo layout
- current Stepbit integration assumptions
- `pyproject.toml` / `requirements.txt` if present
- completed integration work from issues #20, #21, #22, #23, and #27

## Expected outputs
- a stable local runtime resolution approach for Stepbit-driven execution
- a minimal health/version CLI command
- reduced dependence on fragile CWD assumptions
- clear documentation of the expected interpreter/runtime contract

## Acceptance criteria
- QuantLab can be invoked reliably using an explicit interpreter path
- invocation does not depend on launching from one specific working directory where avoidable
- CLI can expose a simple health/version check for automation
- no hardcoded absolute paths are introduced
- runtime behavior is documented clearly enough for future runbooks

## Constraints
- prefer minimal, reviewable changes
- follow standard Python project conventions where practical
- do not broaden into packaging overhaul
- do not broaden into response envelopes or orchestration redesign
- no hardcoded machine-specific paths

## GitHub issue
- #24 core: integración - Detectar y usar virtualenv local para ejecución automatizada

## Suggested next step
Inspect the current invocation assumptions in `main.py` and the repo layout, then identify the smallest set of changes needed to make automated local execution predictable.
