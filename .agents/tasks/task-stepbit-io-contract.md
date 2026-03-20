# Task: Stepbit I/O Contract

## Goal
Define and document the standard input/output interface for Stepbit-QuantLab communication. [DONE]

## Why
A well-defined contract ensures that the orchestration layer (Stepbit) can reliably pass parameters to and read results from the research engine (QuantLab) without versioning conflicts or parsing errors.

## Scope
- [x] Define JSON structure for strategy parameters.
- [x] Define standard return codes and exit signals.
- [x] Specify artifact paths for results retrieval.
- [x] Document expected presence of `metadata.json`, `config.json`, and `report.json`.

## Non-goals
- Implementation of the parsing logic itself.
- Modification of existing artifact structures.

## Inputs
- `.agents/artifact-contracts.md`
- `src/quantlab/runs/serializers.py`

## Expected outputs
- [x] A draft of the Stepbit I/O JSON schema ([stepbit-io-v1.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/stepbit-io-v1.md)).
- [x] Documentation of the CLI interaction contract.

## Acceptance criteria
- [x] The contract covers both input (CLI flags, JSON config) and output (exit codes, run artifacts).
- [x] It follows the "Explicit Artifacts" principle.

## Constraints
- Must remain compatible with current QuantLab results structure.
- No breaking changes to existing `registry.csv`.

## GitHub issue
- #20 feat: integración - Definir contrato input/output QuantLab <-> Stepbit

## Suggested next step
Move to [task-stepbit-cli-stable.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-cli-stable.md) to ensure the CLI can fulfill this contract.
