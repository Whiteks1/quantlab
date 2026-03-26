# QuantLab CLI Guide

QuantLab is a CLI-first research system.
`main.py` is the public entrypoint and routes requests into the specialized CLI modules under `src/quantlab/cli/`.

This guide documents the current repository behavior, grouped by command family.

## 1. Health And Integration

### `--help`

```bash
python main.py --help
```

Prints the available flags and exits.

### `--version`

```bash
python main.py --version
```

Prints the current QuantLab version string.

### `--check`

```bash
python main.py --check
```

Prints a deterministic JSON health summary for runtime validation.

### `--json-request`

Machine-facing request entrypoint for:

- `run`
- `sweep`
- `forward`
- `portfolio`

Example:

```bash
python main.py --json-request "{\"schema_version\":\"1.0\",\"request_id\":\"req_demo_001\",\"command\":\"run\",\"params\":{\"ticker\":\"ETH-USD\",\"start\":\"2023-01-01\",\"end\":\"2023-12-31\"}}"
```

Optional lifecycle signalling:

```bash
python main.py --json-request "{\"schema_version\":\"1.0\",\"request_id\":\"req_demo_002\",\"command\":\"sweep\",\"params\":{\"config_path\":\"configs/experiments/eth_2023_grid.yaml\"}}" --signal-file logs/quantlab-signals.jsonl
```

## 2. Run Execution

Plain run:

```bash
python main.py --ticker ETH-USD --start 2022-01-01 --end 2023-12-31 --report
```

Successful plain runs write canonical artifacts under:

```text
outputs/runs/<run_id>/
```

Canonical files:

- `metadata.json`
- `config.json`
- `metrics.json`
- `report.json`

### `--paper`

Paper-backed run:

```bash
python main.py --ticker ETH-USD --start 2022-01-01 --end 2023-12-31 --paper --report
```

Paper execution is currently still entered through the `run` command surface, but it writes a dedicated paper-session artifact set under:

```text
outputs/paper_sessions/<session_id>/
  session_metadata.json
  session_status.json
  config.json
  metrics.json
  report.json
  trades.csv
  run_report.md
```

Important contract note:

- externally, a JSON request still uses `command: "run"`
- lifecycle signals still emit `mode = "run"` for compatibility
- internally, the result is a paper session and `report.json.machine_contract.contract_type` is `quantlab.paper.result`

For the formal artifact contract, see [run-artifact-contract.md](./run-artifact-contract.md).

## 3. Run Registry And Inspection

### `--runs-list`

List runs under a root:

```bash
python main.py --runs-list outputs/runs
```

### `--runs-show`

Show one run:

```bash
python main.py --runs-show outputs/runs/20260324_005008_run_a468850
```

### `--runs-best`

Rank runs by a metric:

```bash
python main.py --runs-best outputs/runs --metric sharpe_simple
```

Shared index artifacts are refreshed automatically after successful:

- `run`
- `sweep`
- `forward`

Paper sessions do not currently refresh `outputs/runs/runs_index.*`.

Index files:

- `outputs/runs/runs_index.csv`
- `outputs/runs/runs_index.json`
- `outputs/runs/runs_index.md`

## 4. Paper Session Inspection

### `--paper-sessions-list`

List paper sessions under a root:

```bash
python main.py --paper-sessions-list outputs/paper_sessions
```

### `--paper-sessions-show`

Show one paper session:

```bash
python main.py --paper-sessions-show outputs/paper_sessions/<session_id>
```

### `--paper-sessions-health`

Summarize paper-session health:

```bash
python main.py --paper-sessions-health outputs/paper_sessions
```

The health summary is operator-facing and currently includes:

- total sessions
- count by status
- latest session id / activity time
- latest non-success session if present

### `--paper-sessions-alerts`

Emit a deterministic alert snapshot for paper sessions:

```bash
python main.py --paper-sessions-alerts outputs/paper_sessions --paper-stale-minutes 60
```

The alert snapshot is machine-readable JSON and currently makes these situations explicit:

- latest success visibility
- failed sessions
- aborted sessions
- running sessions that have become stale relative to the chosen threshold

For the recommended operating loop and response guidance, see [paper-session-runbook.md](./paper-session-runbook.md).

### `--paper-sessions-index`

Refresh the shared paper-session index:

```bash
python main.py --paper-sessions-index outputs/paper_sessions
```

This writes:

- `outputs/paper_sessions/paper_sessions_index.csv`
- `outputs/paper_sessions/paper_sessions_index.json`

The index is intentionally separate from `outputs/runs/runs_index.*` and is meant for repeated paper-session operations.

## 5. Broker Dry-Run

### `--kraken-preflight-outdir`

Persist a read-only Kraken public preflight artifact:

```bash
python main.py --kraken-preflight-outdir outputs/broker_preflight/demo --broker-symbol ETH-USD
```

This writes:

- `outputs/broker_preflight/demo/broker_preflight.json`

The artifact currently includes:

- adapter name
- generated timestamp
- input and normalized symbol
- public API reachability
- server time snapshot
- pair support result against Kraken public asset-pair metadata
- matched pair identifiers where available
- explicit errors when support or reachability checks fail

This surface is read-only and does not use private Kraken authentication.

### `--kraken-auth-preflight-outdir`

Persist a read-only Kraken authenticated preflight artifact:

```bash
python main.py --kraken-auth-preflight-outdir outputs/broker_preflight/auth_demo
```

By default this reads credentials from:

- `KRAKEN_API_KEY`
- `KRAKEN_API_SECRET`

Optional overrides:

- `--kraken-api-key`
- `--kraken-api-secret`
- `--kraken-api-key-env`
- `--kraken-api-secret-env`

This writes:

- `outputs/broker_preflight/auth_demo/broker_auth_preflight.json`

The artifact currently includes:

- whether credentials were present
- whether private authentication succeeded
- key name where available
- permissions snapshot where available
- restrictions snapshot where available
- created/updated timestamps where available
- explicit auth or credential errors

This surface is read-only and does not place or cancel orders.

### `--kraken-account-readiness-outdir`

Persist a read-only Kraken account snapshot and intent readiness artifact:

```bash
python main.py --kraken-account-readiness-outdir outputs/broker_preflight/account_demo --broker-symbol ETH-USD --broker-side buy --broker-quantity 0.25 --broker-notional 500 --broker-account-id acct_demo
```

By default this reads credentials from:

- `KRAKEN_API_KEY`
- `KRAKEN_API_SECRET`

It reuses the existing broker intent flags:

- `--broker-symbol`
- `--broker-side`
- `--broker-quantity`
- `--broker-notional`
- `--broker-account-id`
- `--broker-max-notional`
- `--broker-allowed-symbols`
- `--broker-kill-switch`
- `--broker-allow-missing-account-id`

This writes:

- `outputs/broker_preflight/account_demo/broker_account_snapshot.json`

The artifact currently includes:

- public pair support and matched Kraken pair identifiers
- base / quote asset mapping for the chosen pair
- pair minimums such as `ordermin` and `costmin` where available
- authenticated preflight summary
- extended balance snapshot where authentication and permissions allow it
- local preflight result for the provided `ExecutionIntent`
- balance-aware readiness result for that intent
- explicit reasons such as:
  - `private_auth_not_ready`
  - `account_snapshot_unavailable`
  - `funding_asset_missing`
  - `insufficient_available_balance`
  - `below_pair_ordermin`
  - `below_pair_costmin`

This surface is read-only and does not place or cancel orders.

### `--kraken-order-validate-outdir`

Persist a validate-only Kraken order probe artifact:

```bash
python main.py --kraken-order-validate-outdir outputs/broker_preflight/validate_demo --broker-symbol ETH-USD --broker-side buy --broker-quantity 0.25 --broker-notional 500 --broker-account-id acct_demo
```

By default this reads credentials from:

- `KRAKEN_API_KEY`
- `KRAKEN_API_SECRET`

It reuses the existing broker intent flags:

- `--broker-symbol`
- `--broker-side`
- `--broker-quantity`
- `--broker-notional`
- `--broker-account-id`
- `--broker-max-notional`
- `--broker-allowed-symbols`
- `--broker-kill-switch`
- `--broker-allow-missing-account-id`

This writes:

- `outputs/broker_preflight/validate_demo/broker_order_validate.json`

The artifact currently includes:

- authenticated preflight summary
- local policy preflight result
- Kraken validate-only payload
- whether the remote validate call was attempted
- whether Kraken accepted the validate-only order probe
- explicit validation reasons from local or exchange-side rejection
- raw exchange response where available

Important note:

- this does not place an order
- but it still uses Kraken's order-validation path and therefore may require order-related API permissions

### `--kraken-order-validate-session`

Persist a canonical broker order-validation session:

```bash
python main.py --kraken-order-validate-session --broker-symbol ETH-USD --broker-side buy --broker-quantity 0.25 --broker-notional 500 --broker-account-id acct_demo
```

This writes a canonical session under:

```text
outputs/broker_order_validations/<session_id>/
  broker_order_validate.json
  session_metadata.json
  session_status.json
```

And refreshes the shared registry:

- `outputs/broker_order_validations/broker_order_validations_index.csv`
- `outputs/broker_order_validations/broker_order_validations_index.json`

### `--broker-order-validations-list`

List broker order-validation sessions:

```bash
python main.py --broker-order-validations-list outputs/broker_order_validations
```

### `--broker-order-validations-show`

Show one broker order-validation session:

```bash
python main.py --broker-order-validations-show outputs/broker_order_validations/<session_id>
```

### `--broker-order-validations-index`

Refresh the shared broker order-validation registry explicitly:

```bash
python main.py --broker-order-validations-index outputs/broker_order_validations
```

### `--broker-order-validations-approve`

Persist a local approval decision for one broker order-validation session:

```bash
python main.py --broker-order-validations-approve outputs/broker_order_validations/<session_id> --broker-approval-reviewer marce --broker-approval-note "Approved after validate-only review"
```

This writes:

- `outputs/broker_order_validations/<session_id>/approval.json`

The approval artifact currently includes:

- `status = approved`
- `reviewed_by`
- `reviewed_at`
- optional `note`
- validation context fields carried forward from the reviewed session

Important note:

- this is a local human approval gate only
- it does not place an order
- it does not imply broker submission has happened

### `--broker-order-validations-bundle`

Generate a pre-submit bundle from an approved broker order-validation session:

```bash
python main.py --broker-order-validations-bundle outputs/broker_order_validations/<session_id>
```

This writes:

- `outputs/broker_order_validations/<session_id>/broker_pre_submit_bundle.json`

The bundle currently includes:

- source `session_metadata.json`
- source `session_status.json`
- source `broker_order_validate.json`
- source `approval.json`
- source session id
- generation timestamp
- `bundle_state = ready_for_supervised_submit`

Important note:

- this command fails if the source validation session is not approved
- it still does not place an order
- it is the final local handoff artifact before any future supervised submit path

### `--broker-order-validations-submit-gate`

Generate a supervised submit gate artifact from a session that already has a pre-submit bundle:

```bash
python main.py --broker-order-validations-submit-gate outputs/broker_order_validations/<session_id> --broker-submit-reviewer marce --broker-submit-confirm --broker-submit-note "Ready for supervised submit review"
```

This writes:

- `outputs/broker_order_validations/<session_id>/broker_submit_gate.json`

The submit gate currently includes:

- source session id
- generation timestamp
- `submit_state = ready_for_supervised_submit_gate`
- reviewer identity
- optional reviewer note
- embedded source `broker_pre_submit_bundle.json`

Important note:

- this command fails if the source session does not already have a pre-submit bundle
- `--broker-submit-confirm` is required
- it still does not place an order
- it is the final local supervised gate before any future submit implementation

### `--broker-order-validations-submit-stub`

Generate a supervised submit stub artifact from a session that already has a submit gate:

```bash
python main.py --broker-order-validations-submit-stub outputs/broker_order_validations/<session_id>
```

This writes:

- `outputs/broker_order_validations/<session_id>/broker_submit_attempt.json`

The submit stub currently includes:

- source session id
- generation timestamp
- `submit_mode = stub`
- `would_submit = true`
- final submit payload derived from the validated session
- embedded source `broker_submit_gate.json`

Important note:

- this command fails if the source session does not already have a submit gate
- it still does not place an order
- it is the first operational shape of a future supervised submit path, but still entirely local

### `--kraken-dry-run-outdir`

Persist a local Kraken dry-run audit artifact:

```bash
python main.py --kraken-dry-run-outdir outputs/broker_dry_runs/demo --broker-symbol ETH-USD --broker-side buy --broker-quantity 0.25 --broker-notional 500 --broker-account-id acct_demo --broker-max-notional 1000 --broker-allowed-symbols ETH/USD,BTC/USD
```

This writes:

- `outputs/broker_dry_runs/demo/broker_dry_run.json`

The artifact currently includes:

- adapter name
- generated timestamp
- normalized execution intent
- execution policy
- preflight allow/reject result
- translated Kraken-style payload if preflight passes

If preflight rejects the intent, the artifact is still written with explicit rejection reasons and `payload = null`.

### `--kraken-dry-run-session`

Persist a canonical Kraken dry-run session:

```bash
python main.py --kraken-dry-run-session --broker-symbol ETH-USD --broker-side buy --broker-quantity 0.25 --broker-notional 500 --broker-account-id acct_demo --broker-max-notional 1000 --broker-allowed-symbols ETH/USD,BTC/USD
```

This writes a canonical session under:

```text
outputs/broker_dry_runs/<session_id>/
  broker_dry_run.json
  session_metadata.json
  session_status.json
```

And refreshes the shared registry:

- `outputs/broker_dry_runs/broker_dry_runs_index.csv`
- `outputs/broker_dry_runs/broker_dry_runs_index.json`

### `--broker-dry-runs-list`

List broker dry-run sessions:

```bash
python main.py --broker-dry-runs-list outputs/broker_dry_runs
```

### `--broker-dry-runs-show`

Show one broker dry-run session:

```bash
python main.py --broker-dry-runs-show outputs/broker_dry_runs/<session_id>
```

### `--broker-dry-runs-index`

Refresh the shared broker dry-run registry explicitly:

```bash
python main.py --broker-dry-runs-index outputs/broker_dry_runs
```

## 6. Forward Evaluation

### `--forward-eval`

Launch a forward session from a prior candidate-producing run directory:

```bash
python main.py --forward-eval outputs/runs/<grid_or_walkforward_run_id> --forward-start 2024-01-01 --forward-end 2024-06-01 --forward-outdir outputs/forward_runs/fwd_demo
```

### `--resume-forward`

Resume a prior forward session:

```bash
python main.py --resume-forward outputs/forward_runs/<session_id>
```

Typical forward session artifacts:

```text
outputs/forward_runs/<session_id>/
  portfolio_state.json
  forward_trades.csv
  forward_equity_curve.csv
  forward_returns_series.csv
  report.json
  forward_report.json
  forward_report.md
```

## 7. Portfolio Workflows

### `--portfolio-report`

Aggregate forward sessions:

```bash
python main.py --portfolio-report outputs/forward_runs
```

Selection/weighting example:

```bash
python main.py --portfolio-report outputs/forward_runs --portfolio-mode custom_weight --portfolio-weights path/to/weights.json --portfolio-top-n 5 --portfolio-rank-metric total_return
```

### `--portfolio-compare`

Compare allocation modes on the same forward-session universe:

```bash
python main.py --portfolio-compare outputs/forward_runs
```

Portfolio report artifacts are written in the target root, for example:

```text
outputs/forward_runs/
  report.json
  portfolio_report.json
  portfolio_report.md
  portfolio_compare.json
  portfolio_compare.md
```

## 8. Sweep Workflows

Flag-driven sweep:

```bash
python main.py --sweep configs/experiments/eth_2023_grid.yaml --sweep_outdir outputs/stepbit
```

Machine-facing sweep:

```bash
python main.py --json-request "{\"schema_version\":\"1.0\",\"request_id\":\"req_sweep_001\",\"command\":\"sweep\",\"params\":{\"config_path\":\"configs/experiments/eth_2023_grid.yaml\",\"out_dir\":\"outputs/stepbit\"}}"
```

`report.json.machine_contract` is the canonical machine-facing result surface for automated sweep consumption.

## 9. Legacy Flags

These remain accepted for backward compatibility, but should not be expanded further in docs or integrations:

- `--list-runs` -> legacy alias of `--runs-list`
- `--best-from` -> legacy alias of `--runs-best`

Legacy read-compatible artifacts also remain in the codebase:

- `meta.json`
- `run_report.json`
- `forward_report.json`
- `portfolio_report.json`

The preferred public surface is the canonical contract documented in [run-artifact-contract.md](./run-artifact-contract.md).

## 9. Design Rules

- `main.py` and `src/quantlab/cli/` should remain orchestration-only
- domain and quantitative logic belong outside the entrypoint
- new public behavior must be documented with executable examples
- new machine-facing behavior should prefer canonical artifacts over legacy outputs
