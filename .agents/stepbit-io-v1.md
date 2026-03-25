# Stepbit I/O Contract — Version 1.0

## Purpose

This document defines the formal communication contract between **Stepbit-core** (external AI/workflow consumer) and **QuantLab** (research and execution system).

QuantLab is a research-first, CLI-driven system that remains autonomous. This contract provides a stable, machine-readable wrapper for optional headless integration.

Each field and section is labeled with its current implementation status:

- `[done]` — implemented and stable in the current codebase
- `[planned]` — defined here but not yet implemented (tracked in linked issues)

> The published version of this document lives in `docs/stepbit-io-v1.md`. Both files must remain identical.

---

## 1. Invocation

Stepbit invokes QuantLab as an external consumer via its CLI boundary.

```bash
<EXPLICIT_PYTHON_INTERPRETER> main.py --json-request '<JSON_PAYLOAD>'
```

**Recommended Configuration Examples:**
- **Windows**: `.venv\Scripts\python.exe`
- **POSIX**: `.venv/bin/python`

`[done]` — The `--json-request` flag is registered and parsed in `main.py`.

`[done]` — Runtime resolution has been hardened for local automated execution:
- `main.py` anchors `src/` into `sys.path`.
- `PROJECT_ROOT` is resolved from the entrypoint.
- Default `outdir` is anchored to the project root when not explicitly provided.

---

## 2. Request Schema (Input)

### JSON Fields

| Field | Type | Status | Description |
|---|---|---|---|
| `schema_version` | `string` | `[done]` | Must be `"1.0"`. Validated by `main.py`. |
| `request_id` | `string` | `[done]` | Caller-generated ID for tracking. Captured as `args._request_id`. |
| `command` | `string` | `[done]` | One of: `run`, `sweep`, `forward`, `portfolio`. |
| `params` | `dict` | `[done]` | Command-specific parameters mapped to CLI args. |

`[done]` `params` keys are mapped to argparse namespace attributes via `setattr` in `main.py`.

`[done]` `schema_version` validation and `request_id` propagation are implemented.

### `command: "sweep"` contract `[done]`

Required under `params`:

- `config_path` — non-empty string path to the sweep YAML file

Optional under `params`:

- `out_dir` — target parent directory for the generated run directory
- `sweep_outdir` — legacy-compatible alias for `out_dir`

Invalid or missing `config_path` fails deterministically with exit code `2`.

---

## 3. Response (Output)

### Current Behavior `[done]`

QuantLab writes artifacts to a mode-specific output directory upon completion. Stepbit reads results from these files.

QuantLab does **not** emit a JSON response envelope to stdout. This is by current design.

For `command: "run"`, a successful execution now writes a canonical run directory under
`outputs/runs/<run_id>/` and returns the resolved `run_id`, `artifacts_path`, and canonical
`report_path` through the existing session-completion context. Its canonical `report.json`
now also includes:

- `machine_contract.schema_version = "1.0"`
- `machine_contract.contract_type = "quantlab.run.result"`
- `machine_contract.command = "run"`
- `machine_contract.status`
- `machine_contract.request_id` when provided
- `machine_contract.run_id`
- `machine_contract.mode`
- `machine_contract.summary`
- `machine_contract.artifacts`

For plain `run`, the top-level `summary` block also mirrors the same core KPI values for compatibility, but `report.json.machine_contract` remains the canonical machine-facing result surface.

For `command: "sweep"`, the canonical machine-readable artifact is `report.json`, and it includes:

- `machine_contract.schema_version = "1.0"`
- `machine_contract.contract_type = "quantlab.sweep.result"`
- `machine_contract.command = "sweep"`
- `machine_contract.status`
- `machine_contract.request_id` when provided
- `machine_contract.run_id`
- `machine_contract.mode`
- `machine_contract.summary`
- `machine_contract.best_result` when available
- `machine_contract.artifacts`

### JSON Response Envelope `[planned]`

A future version may emit a structured JSON envelope to stdout on completion.

**Example success shape:**
```json
{
  "schema_version": "1.0",
  "request_id": "req_550e8400",
  "status": "success",
  "run_id": "20260320_162100_run_a1b2c3d",
  "artifacts_path": "outputs/runs/20260320_162100_run_a1b2c3d",
  "summary": {
    "total_return": 0.45,
    "sharpe_simple": 1.82,
    "max_drawdown": -0.15,
    "trades": 12,
    "win_rate": 0.62
  }
}
```

**Example failure shape:**
```json
{
  "schema_version": "1.0",
  "request_id": "req_550e8400",
  "status": "error",
  "error": {
    "code": "DATA_ERROR",
    "message": "OHLC data missing for requested range"
  }
}
```

`[planned]` Response envelope tracked in [Issue #22](https://github.com/Whiteks1/quantlab/issues/22).

---

## 4. Session Signalling `[done]`

QuantLab supports optional, file-based session signalling to notify Stepbit of lifecycle events without polling.

### Invocation
```bash
python main.py --json-request '...' --signal-file path/to/signals.jsonl
```

### Behavior
- **Format**: JSON Lines (one JSON object per line).
- **Mode**: Append-only.
- **Reliability**: Best-effort writes; signal failures do not abort the session.

### Event Models

#### Common Fields (All Events)
| Field | Type | Description |
|---|---|---|
| `schema_version` | `string` | Always `"1.0"`. |
| `event` | `string` | `SESSION_STARTED`, `SESSION_COMPLETED`, or `SESSION_FAILED`. |
| `status` | `string` | `running`, `success`, or `error`. |
| `mode` | `string` | The command type (e.g., `run`, `sweep`). |
| `request_id` | `string` | Propagated from request if available. |
| `timestamp` | `string` | ISO 8601 local time. |

#### SESSION_COMPLETED
Includes result location metadata (when available):
- `run_id`: Unique identifier for the run.
- `artifacts_path`: Directory containing the run artifacts.
- `report_path`: Path to the canonical `report.json`.
- `runs_index_json`: Refreshed registry artifact for `outputs/runs/` after successful `run`, `sweep`, and `forward`.

#### SESSION_FAILED
Includes failure metadata:
- `exit_code`: Numeric process exit code (1-4).
- `error_type`: Exception class name.
- `message`: Human-readable error description.

---

## 5. Exit Codes `[done]`

| Code | Label | Meaning |
|---|---|---|
| `0` | `SUCCESS` | Task completed normally. |
| `1` | `GENERAL_ERROR` | Unexpected crash or unhandled exception. |
| `2` | `INVALID_CONFIG` | JSON payload or CLI flags are invalid. |
| `3` | `DATA_ERROR` | OHLC data missing or invalid state (e.g. empty or unusable data). |
| `4` | `STRATEGY_ERROR` | Strategy-specific logic failure or parameter/runtime error. |

---

## 6. Artifact Paths `[done]`

The canonical machine-readable artifact for integration is **`report.json`**.

For session-oriented flows, it is expected inside the produced run/session directory.

- **Typical pattern**: `outputs/runs/<run_id>/report.json`

Canonical run artifact set for new `run`- and `sweep`-produced runs:

- `outputs/runs/<run_id>/metadata.json`
- `outputs/runs/<run_id>/config.json`
- `outputs/runs/<run_id>/metrics.json`
- `outputs/runs/<run_id>/report.json`

Successful `run`, `sweep`, and `forward` executions refresh the shared registry:

- `outputs/runs/runs_index.csv`
- `outputs/runs/runs_index.json`
- `outputs/runs/runs_index.md`

Legacy `meta.json` and `run_report.json` remain read-compatible only.

---

## 7. Health and Versioning `[done]`

QuantLab provides machine-verifiable flags for runtime validation.

| Flag | Status | Description |
|---|---|---|
| `--version` | `[done]` | Prints the current QuantLab version as a stable string. |
| `--check` | `[done]` | Prints a deterministic JSON health summary and exits `0` on success or `2` on runtime/config failure. |

`--check` currently reports:

- `status`
- `project_root`
- `main_path`
- `src_root`
- `interpreter`
- `venv_active`
- `quantlab_import`
- `python_version`
- `version`

---

## 8. Known Gaps → Follow-Up Issues

| Gap | Issue |
|---|---|
| JSON response envelope emitted to stdout | #22 |
| `strategy` param mapping in `run` command | #21 |
| Webhook delivery for signals | #25 (Deferred) |
