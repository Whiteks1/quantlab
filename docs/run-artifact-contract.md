# Run Artifact Contract

This document defines the public artifact contract for QuantLab run-producing workflows.

It is intended for:

- local CLI users
- machine-to-machine integrations
- Stepbit adapter work
- downstream tools that read run history from disk

## Contract Root

Canonical run artifacts live under:

```text
outputs/runs/<run_id>/
```

The shared run history index lives under:

```text
outputs/runs/
```

Paper-session artifacts live under:

```text
outputs/paper_sessions/<session_id>/
```

## Canonical Run Directory

The canonical artifact set for a run directory is:

```text
outputs/runs/<run_id>/
  metadata.json
  config.json
  metrics.json
  report.json
```

Additional artifacts may also exist, for example:

```text
outputs/runs/<run_id>/
  run_report.md
  trades.csv
  artifacts/
  leaderboard.csv
  walkforward.csv
```

## Canonical Paper Session Directory

Paper-backed executions currently produce a dedicated session directory:

```text
outputs/paper_sessions/<session_id>/
  session_metadata.json
  session_status.json
  config.json
  metrics.json
  report.json
  trades.csv
  run_report.md
  artifacts/
```

Paper sessions are operationally distinct from research runs and are not part of the shared run registry under `outputs/runs/`.

## Canonical Files

### `metadata.json`

Execution identity and context.

Typical fields:

- `run_id`
- `created_at`
- `mode`
- `status`
- `command`
- `config_path`
- `config_hash`
- `request_id`

### `config.json`

Resolved configuration used for the run.

Typical fields:

- `ticker`
- `start`
- `end`
- `interval`
- fee and slippage settings
- resolved strategy/runtime parameters

### `metrics.json`

Machine-readable summary metrics for ranking and comparison.

Typical fields:

- `status`
- `summary`
- `best_result`
- `leaderboard_size`

### `report.json`

Canonical public report artifact for downstream consumption.

Typical top-level sections:

- `schema_version`
- `artifact_type`
- `status`
- `header`
- `config_resolved`
- `results`
- `artifacts`
- `summary`

## `report.json.machine_contract`

The machine-facing contract is published inside `report.json` at:

```text
report.json.machine_contract
```

This is the shared public result surface for machine-driven `run` and `sweep` flows.

Expected fields include:

- `schema_version`
- `contract_type`
- `command`
- `status`
- `request_id`
- `run_id`
- `mode`
- `summary`
- `artifacts`

For plain `run`, `contract_type` is:

```text
quantlab.run.result
```

For plain `run`, the top-level `report.json.summary` should mirror the same core KPI block exposed through `report.json.machine_contract.summary`. The machine-facing canonical source remains `machine_contract`.

For `sweep`, `contract_type` is:

```text
quantlab.sweep.result
```

For paper-backed execution entered through `command: "run"`, `contract_type` is:

```text
quantlab.paper.result
```

In that case:

- the external invocation surface still remains `command: "run"`
- the produced artifact root is `outputs/paper_sessions/<session_id>/`
- the returned `run_id` is the paper session identifier

## Shared Run Index

QuantLab maintains a shared run-history index under:

```text
outputs/runs/
  runs_index.csv
  runs_index.json
  runs_index.md
```

These files are refreshed automatically after successful:

- `run`
- `sweep`
- `forward`

Paper sessions are excluded from this shared run index.

They are intended as the read-only shared registry for browsing and integration.

## Legacy Compatibility

QuantLab keeps legacy read compatibility for older consumers:

- `meta.json` remains readable as a legacy predecessor of `metadata.json`
- `run_report.json` remains readable as a legacy predecessor of `report.json`

New run-producing flows should treat these as legacy compatibility surfaces, not as the canonical write target.

## Health Surfaces

QuantLab exposes stable machine-facing health surfaces through the CLI.

### Version

```bash
python main.py --version
```

Returns a stable version string.

### Preflight

```bash
python main.py --check
```

Returns a deterministic JSON health summary for runtime validation.

Typical fields include:

- `status`
- `project_root`
- `main_path`
- `src_root`
- `interpreter`
- `venv_active`
- `quantlab_import`
- `python_version`
- `version`

### Machine Request Surface

```bash
python main.py --json-request '<payload>'
```

`--json-request` remains the primary smoke-validation and machine-to-machine invocation surface for integration work.

Optional lifecycle signalling:

```bash
python main.py --json-request '<payload>' --signal-file path/to/signals.jsonl
```

Signal compatibility note:

- when `command: "run"` is combined with paper execution, signals still use `mode = "run"` to preserve the external contract
- paper-specific identity should be inferred from the paper-session artifact root and from `report.json.machine_contract.contract_type`

## Stability Notes

- `report.json` is the canonical public artifact
- `report.json.machine_contract` is the canonical machine-facing result block
- for plain `run`, top-level `summary` mirrors `machine_contract.summary` for compatibility
- `runs_index.csv/json/md` is the canonical shared run registry
- paper sessions use a separate artifact root and do not currently participate in the shared run registry
- legacy artifacts remain readable but are not the preferred write target for new flows
