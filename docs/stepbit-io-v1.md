# Stepbit I/O Contract — Version 1.0

## Purpose

This document defines the formal communication contract between **Stepbit-core** (Orchestrator) and **QuantLab** (Research Engine).

QuantLab is a research-first, CLI-driven system. This contract provides a stable, machine-readable wrapper for headless integration.

Each field and section is labeled with its current implementation status:

- `[done]` — implemented and stable in the current codebase
- `[planned]` — defined here but not yet implemented (tracked in linked issues)

> The published version of this document lives in `docs/stepbit-io-v1.md`. Both files must remain identical.

---

## 1. Invocation

Stepbit invokes QuantLab as a subprocess via its CLI.

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

### Mapped `params` Keys (command: `run`)

| Key | CLI equivalent | Status |
|---|---|---|
| `ticker` | `--ticker` | `[done]` |
| `start` | `--start` | `[done]` |
| `end` | `--end` | `[done]` |
| `interval` | `--interval` | `[done]` |
| `fee` | `--fee` | `[done]` |
| `config_path` (sweep) | `--sweep` | `[done]` |
| `run_dir` (forward) | `--forward-eval` | `[done]` |
| `strategy` | _(no direct mapping)_ | `[planned]` |

### Example Request

```json
{
  "schema_version": "1.0",
  "request_id": "req_550e8400",
  "command": "run",
  "params": {
    "ticker": "ETH-USD",
    "start": "2023-01-01",
    "end": "2023-12-31",
    "fee": 0.002
  }
}
```

---

## 3. Response (Output)

### Current Behavior `[done]`

QuantLab writes artifacts to a mode-specific output directory upon completion. Stepbit reads results from these files.

QuantLab does **not** emit a JSON response envelope to stdout. This is by current design.

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

## 4. Exit Codes `[done]`

| Code | Label | Meaning |
|---|---|---|
| `0` | `SUCCESS` | Task completed normally. |
| `1` | `GENERAL_ERROR` | Unexpected crash or unhandled exception. |
| `2` | `INVALID_CONFIG` | JSON payload or CLI flags are invalid. |
| `3` | `DATA_ERROR` | OHLC data missing or invalid state (e.g. empty or unusable data). |
| `4` | `STRATEGY_ERROR` | Strategy-specific logic failure or parameter/runtime error. |

> Exit codes are implemented via a central exception hierarchy in `src/quantlab/errors.py`.

---

## 5. Artifact Paths `[done]`

The canonical machine-readable artifact for integration is **`report.json`**.

For session-oriented flows, it is expected inside the produced run/session directory.

- **Typical pattern**: `outputs/runs/<run_id>/report.json`

Additional legacy artifacts may still exist for backward compatibility, but Stepbit should prefer `report.json` whenever available.

---

## 6. Run Identity

| Field | Status | Notes |
|---|---|---|
| `run_id` | `[done]` | Present in run/session-oriented flows where applicable. |
| `fingerprint` | `[planned]` | Not yet emitted as part of the runtime response surface. |

---

## 7. Known Gaps → Follow-Up Issues

| Gap | Issue |
|---|---|
| JSON response envelope emitted to stdout | #22 |
| `strategy` param mapping in `run` command | #21 |
| `metadata.json` / `config.json` wired into `run.py` | #21 |
| `fingerprint` field in output | #22 |

---

## 8. Health and Versioning `[done]`

QuantLab provides machine-verifiable flags for runtime validation.

| Flag | Status | Description |
|---|---|---|
| `--version` | `[done]` | Prints the current QuantLab version. |
| `--check` | `[done]` | Performs a minimal runtime health check. |

**Typical `--check` output includes:**
- `project_root`
- `interpreter`
- `venv_active`
- `quantlab_import`
- `python_version`