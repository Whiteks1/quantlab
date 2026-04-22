# Run Analysis Entrypoint Contract

Status: internal pilot (`quantlab.agents.run_analysis`)

## Invocation

```bash
python -m quantlab.agents.run_analysis <run_id>
```

No flags are supported in this entrypoint slice.

## Inputs

- Positional `run_id` (required).
- Reads run artifacts from `outputs/runs/<run_id>/`.
- Required files:
  - `metadata.json`
  - `metrics.json`
  - `report.json`
- Optional file:
  - `config.json`

## Outputs

Writes to `outputs/agent_reports/`:

- `outputs/agent_reports/<run_id>_analysis.md`
- `outputs/agent_reports/<run_id>_analysis.log.json`

## Exit Behavior

- `0`: successful run.
- `2`: invalid invocation (missing/extra args). Prints:
  - `Usage: python -m quantlab.agents.run_analysis <run_id>`
- Non-zero error (typically `1`) for runtime validation/extraction/output exceptions.

## Overwrite Policy

- Strict no-overwrite.
- If report or log target already exists, execution fails before writing.
- On write failure, partial report/log artifacts are cleaned up.

## Scope Boundary

- Internal-only pilot entrypoint.
- Not wired into `quantlab/cli`.
- No `console_scripts` entry for run-analysis.
