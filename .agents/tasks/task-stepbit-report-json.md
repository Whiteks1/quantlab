# Task: Machine-Readable Reporting (report.json)

## Goal
Ensure every Run, Sweep, and Forward session produces a standardized `report.json` for Stepbit to consume.

## Why
Human-readable Markdown and charts are excellent for researchers, but automated agents require structured data to evaluate results, rank candidates, and make orchestration decisions.

## Scope
- Formalize the schema for `report.json` across all session types.
- Ensure consistency between Markdown and JSON outputs.
- Include key performance indicators (KPIs) like Sharpe, Max Drawdown, and Total Return in a top-level summary object.
- Document any deviations from the standard schema for specific session types.

## Non-goals
- Adding new metrics that are not currently calculated.
- Implementing the JSON serialization logic (this should use `quantlab.runs.serializers`).

## Inputs
- `.agents/artifact-contracts.md`
- `src/quantlab/reporting/`
- `src/quantlab/runs/serializers.py`

## Expected outputs
- Updated reporting modules that consistently output `report.json`.
- A JSON Schema file or living documentation for `report.json`.

## Acceptance criteria
- `report.json` is present in every run directory after execution.
- KPIs in `report.json` exactly match those in the Markdown report.
- Zero manual parsing required for Stepbit to extract core results.

## Constraints
- Do not bloat `report.json` with multi-megabyte dataframes; keep it for summaries and metadata.
- Follow "Reporting must not contain business logic".

## GitHub issue
- #22 feat: quantlab - Generar report.json consistente para integración

## Suggested next step
Read [task-stepbit-error-policy.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/task-stepbit-error-policy.md).
