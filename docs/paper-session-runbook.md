# Paper Session Runbook

This runbook explains how to operate QuantLab paper sessions as a repeatable dry-run workflow.

It is intended for:

- local operators
- maintainers validating Stage C.1
- future automation work that needs a human-readable operating baseline

## 1. Goal

Paper sessions are the operational bridge between research runs and future broker-connected safety work.

They should be treated as:

- a dry operational environment
- traceable and diagnosable
- separate from the shared research run registry

They should not be treated as:

- live execution
- a broker integration
- an external orchestration authority

## 2. Launch A Paper Session

Launch a paper-backed run through the standard `run` surface:

```bash
python main.py --ticker ETH-USD --start 2022-01-01 --end 2023-12-31 --paper --report
```

Machine-facing invocation still uses `command: "run"`:

```bash
python main.py --json-request "{\"schema_version\":\"1.0\",\"request_id\":\"req_paper_001\",\"command\":\"run\",\"params\":{\"ticker\":\"ETH-USD\",\"start\":\"2022-01-01\",\"end\":\"2023-12-31\",\"paper\":true}}" --signal-file logs/quantlab-signals.jsonl
```

Important contract note:

- the external command surface remains `run`
- signal events still emit `mode = "run"` for compatibility
- the paper identity is expressed by the artifact root and by `report.json.machine_contract.contract_type = "quantlab.paper.result"`

## 3. Where Artifacts Land

Paper sessions write to:

```text
outputs/paper_sessions/<session_id>/
```

Canonical paper-session files:

```text
outputs/paper_sessions/<session_id>/
  session_metadata.json
  session_status.json
  config.json
  metrics.json
  report.json
  run_report.md
  trades.csv
  artifacts/
```

The minimum operator-facing files are:

- `session_metadata.json`: identity, creation context, request id
- `session_status.json`: latest lifecycle status, last update time, error info if present
- `report.json`: canonical result artifact
- `trades.csv`: paper trade log

## 4. Inspect Sessions

List all paper sessions:

```bash
python main.py --paper-sessions-list outputs/paper_sessions
```

Inspect one session:

```bash
python main.py --paper-sessions-show outputs/paper_sessions/<session_id>
```

Use `--paper-sessions-show` when you need:

- the exact session id
- current status
- request id
- artifact paths
- error type or failure message

## 5. Check Overall Health

Summarize paper-session health:

```bash
python main.py --paper-sessions-health outputs/paper_sessions
```

This compact summary is useful for answering:

- how many sessions exist
- how many succeeded, failed, aborted, or are still running
- what the latest session is
- what the latest visible issue is

Use this command first when you want a quick operational pulse.

## 6. Read Alerts

Emit a deterministic paper-session alert snapshot:

```bash
python main.py --paper-sessions-alerts outputs/paper_sessions --paper-stale-minutes 60
```

This returns machine-readable JSON and currently classifies:

- `PAPER_SESSION_FAILED`
- `PAPER_SESSION_ABORTED`
- `PAPER_SESSION_STALE`

Use `--paper-stale-minutes` to tighten or relax how long a running session can remain active before it is considered stale.

Recommended default:

- `60` minutes for general local operation

## 7. Refresh The Shared Paper Index

Refresh the shared paper-session index:

```bash
python main.py --paper-sessions-index outputs/paper_sessions
```

This writes:

```text
outputs/paper_sessions/
  paper_sessions_index.csv
  paper_sessions_index.json
```

Use this when you want a compact export surface for repeated review, local handoff, or downstream local tooling.

## 8. Operator Response Guide

### `success`

Meaning:

- the paper session completed normally

What to do:

- review `report.json` and `run_report.md`
- inspect `trades.csv` if trade-level behavior matters
- compare the result with recent sessions if you are validating repeatability

### `failed`

Meaning:

- the session ended with an exception

What to do:

- inspect `session_status.json`
- note `error_type` and `message`
- confirm whether the problem is data-related, config-related, or runtime-related
- rerun only after the cause is understood

### `aborted`

Meaning:

- the session was interrupted before normal completion

What to do:

- confirm whether the interruption was operator-initiated or environmental
- inspect `session_status.json` for the last recorded state
- rerun if the interruption does not indicate a deeper runtime problem

### `running`

Meaning:

- the session has started and has not yet reached a terminal state

What to do:

- use `--paper-sessions-show` for the specific session
- check the `updated_at` timestamp in `session_status.json`
- compare the runtime duration with your expected session length

### `stale`

Meaning:

- the session is still marked `running`, but the alert threshold says it has been active too long

What to do:

- inspect the session with `--paper-sessions-show`
- confirm whether the process is genuinely still progressing
- if not, treat it as an operational issue and rerun only after checking logs, data, and the local environment

## 9. Recommended Operating Loop

For routine paper operation:

1. launch the paper-backed `run`
2. inspect recent session creation with `--paper-sessions-list`
3. check pulse with `--paper-sessions-health`
4. check alert state with `--paper-sessions-alerts`
5. refresh `--paper-sessions-index` if you want a shared export of the current paper root
6. inspect any non-success or stale session with `--paper-sessions-show`
7. review `report.json` and `trades.csv` for the sessions worth keeping

## 10. Boundary Notes

- paper sessions are operationally distinct from research runs
- paper sessions do not refresh `outputs/runs/runs_index.*`
- paper sessions are not yet broker-connected execution
- Stepbit or other external systems may consume QuantLab outputs, but they do not define this runbook or the operating authority

## 11. Related Documents

- [README.md](../README.md)
- [cli.md](./cli.md)
- [run-artifact-contract.md](./run-artifact-contract.md)
- [roadmap.md](./roadmap.md)
