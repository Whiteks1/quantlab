# QuantLab

QuantLab is a CLI-first quantitative research system for running reproducible strategy experiments, forward evaluation workflows, run indexing, and portfolio-level reporting.

It is intentionally split from Stepbit:

- QuantLab is the primary system for research, paper-trading discipline, execution safety, and future broker-connected operation.
- Stepbit is an optional external system that can provide AI, reasoning, workflow, and automation capabilities.

The architectural rule is simple:

- QuantLab remains autonomous
- Stepbit does not govern QuantLab
- QuantLab may consume Stepbit capabilities through a narrow, reversible boundary

## Current Status

QuantLab is currently transitioning from **Stage C.1** into **Stage D.2 - supervised broker submit safety and reconciliation**.

The paper layer is now materially operational, and the current broker-facing focus is:

- reconcile the first supervised Kraken submit path before widening live execution
- close idempotency and ambiguous-submit gaps before adding more broker power
- keep paper-session discipline as a prerequisite, not as the current bottleneck

A secondary contract boundary track remains active:

- stable `run` and `sweep` behavior
- stable `report.json.machine_contract`
- automatic refresh of `outputs/runs/runs_index.*`
- reliable health/version surfaces via `--check` and `--version`

External integration work remains subordinate to QuantLab-owned priorities.
Stepbit-facing hardening is valid when it reduces real boundary friction, but it does not set the product roadmap.

Known technical debt still tracked internally:

- duplicate workflow docs in `.agents/workflows/`: `strategy-research.md` vs `strategy_research.md`

## Requirements

- Windows 11 or Ubuntu
- Python 3.10+
- Git

Documented support starts at Python 3.10. The recommended target remains Python 3.11 or 3.12.
As of 2026-03-25, the local CLI preflight in this repository also passes on Python 3.13.3.

## Clean Installation

```bash
git clone <your-fork-or-repo-url>
cd quant_lab
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Linux / macOS:

```bash
source .venv/bin/activate
pip install -e .
```

Developer dependencies:

```bash
pip install -e .[dev]
```

## Quick Health Check

Version:

```bash
python main.py --version
```

Typical output:

```text
0.1.0
```

Preflight health:

```bash
python main.py --check
```

Typical output shape:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "quantlab_import": true,
  "project_root": "..."
}
```

CLI help:

```bash
python main.py --help
```

## Current Capabilities

- `--json-request`: machine-facing request entrypoint for `run`, `sweep`, `forward`, and `portfolio`
- `--signal-file`: optional JSONL lifecycle signalling for machine-driven execution
- `--version`: stable CLI version string
- `--check`: deterministic runtime health summary
- `--runs-list`: list indexed runs under a root directory
- `--runs-show`: inspect a single run directory
- `--runs-best`: rank runs by a metric such as `sharpe_simple`
- `--paper-sessions-list`: list paper sessions under a root directory
- `--paper-sessions-show`: inspect a single paper session directory
- `--paper-sessions-health`: summarize health across paper sessions
- `--paper-sessions-alerts`: emit a deterministic alert snapshot for paper sessions
- `--paper-sessions-index`: refresh a shared paper-session index under the paper root
- `--kraken-preflight-outdir`: persist a read-only Kraken public preflight artifact
- `--kraken-auth-preflight-outdir`: persist a read-only Kraken authenticated preflight artifact
- `--kraken-account-readiness-outdir`: persist a read-only Kraken account snapshot and intent readiness artifact
- `--kraken-order-validate-outdir`: persist a Kraken validate-only order probe artifact
- `--kraken-order-validate-session`: persist a canonical broker order-validation session
- `--kraken-dry-run-outdir`: persist a local Kraken dry-run audit artifact
- `--kraken-dry-run-session`: persist a canonical broker dry-run session
- `--broker-dry-runs-list`: inspect broker dry-run sessions under a root
- `--broker-dry-runs-show`: inspect one broker dry-run session
- `--broker-order-validations-list`: inspect broker order-validation sessions under a root
- `--broker-order-validations-show`: inspect one broker order-validation session
- `--broker-order-validations-approve`: persist a local approval decision for one broker order-validation session
- `--broker-order-validations-bundle`: materialize a pre-submit bundle from an approved broker order-validation session
- `--broker-order-validations-submit-gate`: materialize a supervised submit gate artifact from a pre-submit bundle
- `--broker-order-validations-submit-stub`: materialize a supervised submit stub artifact from a submit gate
- `--broker-order-validations-submit-real`: submit a first tightly gated real Kraken order and persist the broker response artifact
- `--broker-order-validations-reconcile`: reconcile an existing submit response against Kraken order state
- `--broker-order-validations-status`: refresh normalized post-submit order status for a submitted broker validation session
- `--broker-order-validations-health`: summarize broker submission health across broker validation sessions
- `--broker-order-validations-alerts`: emit a deterministic alert snapshot for notable broker submission states
- `--forward-eval`: launch a forward evaluation from a prior run directory
- `--portfolio-report`: aggregate forward sessions into a portfolio report
- `--portfolio-compare`: compare allocation modes across forward sessions

See also:

- [docs/cli.md](./docs/cli.md)
- [docs/broker-safety-boundary.md](./docs/broker-safety-boundary.md)
- [docs/paper-session-runbook.md](./docs/paper-session-runbook.md)
- [docs/roadmap.md](./docs/roadmap.md)
- [docs/workflow-operativo-codex.md](./docs/workflow-operativo-codex.md)
- [docs/run-artifact-contract.md](./docs/run-artifact-contract.md)
- [docs/stepbit-io-v1.md](./docs/stepbit-io-v1.md)
- [docs/quantlab-stepbit-boundaries.md](./docs/quantlab-stepbit-boundaries.md)

## Real CLI Usage

### Run

Single research run:

```bash
python main.py --ticker ETH-USD --start 2022-01-01 --end 2023-12-31 --report
```

This produces a canonical research run directory under:

```text
outputs/runs/<run_id>/
```

Paper-backed run:

```bash
python main.py --ticker ETH-USD --start 2022-01-01 --end 2023-12-31 --paper --report
```

This produces a canonical paper session directory under:

```text
outputs/paper_sessions/<session_id>/
```

### Runs

List all runs:

```bash
python main.py --runs-list outputs/runs
```

Show one run:

```bash
python main.py --runs-show outputs/runs/20260324_005008_run_a468850
```

Best run by metric:

```bash
python main.py --runs-best outputs/runs --metric sharpe_simple
```

### Paper Sessions

List paper sessions:

```bash
python main.py --paper-sessions-list outputs/paper_sessions
```

Show one paper session:

```bash
python main.py --paper-sessions-show outputs/paper_sessions/<session_id>
```

Summarize paper session health:

```bash
python main.py --paper-sessions-health outputs/paper_sessions
```

Emit a paper-session alert snapshot:

```bash
python main.py --paper-sessions-alerts outputs/paper_sessions --paper-stale-minutes 60
```

Refresh the shared paper-session index:

```bash
python main.py --paper-sessions-index outputs/paper_sessions
```

Operational guidance:

- see [docs/paper-session-runbook.md](./docs/paper-session-runbook.md) for the recommended paper-session operating loop and response guidance

### Forward

Forward evaluation from a prior grid/walkforward run directory:

```bash
python main.py --forward-eval outputs/runs/<grid_or_walkforward_run_id> --forward-start 2024-01-01 --forward-end 2024-06-01 --forward-outdir outputs/forward_runs/fwd_demo
```

Resume a previous forward session:

```bash
python main.py --resume-forward outputs/forward_runs/<session_id>
```

### Portfolio

Aggregate forward sessions:

```bash
python main.py --portfolio-report outputs/forward_runs
```

Compare allocation modes:

```bash
python main.py --portfolio-compare outputs/forward_runs
```

Portfolio selection and weighting example:

```bash
python main.py --portfolio-report outputs/forward_runs --portfolio-mode custom_weight --portfolio-weights path/to/weights.json --portfolio-top-n 5 --portfolio-rank-metric total_return
```

## Canonical Artifact Structure

Canonical research run artifacts are centered on:

```text
outputs/runs/<run_id>/
  metadata.json
  config.json
  metrics.json
  report.json
  run_report.md
  trades.csv                 # optional
  artifacts/                 # optional
```

Canonical paper session artifacts are centered on:

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

Shared paper-session index artifacts:

```text
outputs/paper_sessions/
  paper_sessions_index.csv
  paper_sessions_index.json
```

Shared run history index:

```text
outputs/runs/
  runs_index.csv
  runs_index.json
  runs_index.md
```

`report.json` is the canonical public artifact.
Its machine-facing result block lives at:

```text
report.json.machine_contract
```

Legacy read-compatible artifacts still exist for older consumers:

- `meta.json` -> canonical replacement: `metadata.json`
- `run_report.json` -> canonical replacement: `report.json`

## Machine Request Example

Short `run` request:

```bash
python main.py --json-request "{\"schema_version\":\"1.0\",\"request_id\":\"req_demo_001\",\"command\":\"run\",\"params\":{\"ticker\":\"ETH-USD\",\"start\":\"2023-01-01\",\"end\":\"2023-12-31\",\"interval\":\"1d\"}}"
```

With lifecycle signalling:

```bash
python main.py --json-request "{\"schema_version\":\"1.0\",\"request_id\":\"req_demo_002\",\"command\":\"sweep\",\"params\":{\"config_path\":\"configs/experiments/eth_2023_grid.yaml\",\"out_dir\":\"outputs/stepbit\"}}" --signal-file logs/quantlab-signals.jsonl
```

## Recent Stabilization Highlights

- PR #63 added the canonical `report.json.machine_contract` for plain `run`
- PR #60 aligned plain `run` with canonical artifacts and automatic `runs_index` refresh
- PR #58 added CLI preflight checks and smoke validation for the machine-facing sweep path
- PR #55 stabilized the sweep contract for Stepbit-oriented consumption

## Repo Signals

The repository already exposes a professional baseline for continued integration work:

- Apache-2.0 licensed
- GitHub Actions CI under `.github/workflows`
- source under `src/quantlab`
- public docs in `docs/`
- internal architecture memory in `.agents/`
- automated test coverage in `test/`

## Design Principles

- research-first before productization
- modular boundaries over monolithic growth
- reproducibility over ad hoc experimentation
- explicit contracts over implicit behavior
- extensibility without collapsing QuantLab/Stepbit separation

## Current Execution Boundary

Real broker work is still gated behind Stage D.0.

The current local safety boundary is documented in [docs/broker-safety-boundary.md](./docs/broker-safety-boundary.md) and defines the broker-agnostic execution contract that future adapters must follow.

The first dry-run backend slice now exists behind that boundary as a `KrakenBrokerAdapter`, still without real broker connectivity.

QuantLab can now also materialize a local Kraken dry-run review artifact with:

```bash
python main.py --kraken-dry-run-outdir outputs/broker_dry_runs/demo --broker-symbol ETH-USD --broker-side buy --broker-quantity 0.25 --broker-notional 500 --broker-account-id acct_demo --broker-max-notional 1000 --broker-allowed-symbols ETH/USD,BTC/USD
```

And it can run a read-only public preflight probe with:

```bash
python main.py --kraken-preflight-outdir outputs/broker_preflight/demo --broker-symbol ETH-USD
```

And it can run a read-only authenticated preflight probe with Kraken credentials available in `KRAKEN_API_KEY` and `KRAKEN_API_SECRET`:

```bash
python main.py --kraken-auth-preflight-outdir outputs/broker_preflight/auth_demo
```

And it can run a read-only account readiness probe for a specific broker intent:

```bash
python main.py --kraken-account-readiness-outdir outputs/broker_preflight/account_demo --broker-symbol ETH-USD --broker-side buy --broker-quantity 0.25 --broker-notional 500 --broker-account-id acct_demo
```

And it can run a validate-only Kraken order probe for a specific broker intent:

```bash
python main.py --kraken-order-validate-outdir outputs/broker_preflight/validate_demo --broker-symbol ETH-USD --broker-side buy --broker-quantity 0.25 --broker-notional 500 --broker-account-id acct_demo
```

And it can now persist canonical broker order-validation sessions under:

```text
outputs/broker_order_validations/<session_id>/
```

And it can now persist a local approval decision for a reviewed validation session:

```bash
python main.py --broker-order-validations-approve outputs/broker_order_validations/<session_id> --broker-approval-reviewer marce --broker-approval-note "Approved after validate-only review"
```

And it can materialize a pre-submit bundle only from an approved validation session:

```bash
python main.py --broker-order-validations-bundle outputs/broker_order_validations/<session_id>
```

And it can materialize a supervised submit gate only from a session that already has a pre-submit bundle:

```bash
python main.py --broker-order-validations-submit-gate outputs/broker_order_validations/<session_id> --broker-submit-reviewer marce --broker-submit-confirm --broker-submit-note "Ready for supervised submit review"
```

And it can materialize a supervised submit stub that shows the final payload it would submit:

```bash
python main.py --broker-order-validations-submit-stub outputs/broker_order_validations/<session_id>
```

And it can perform a first tightly gated real Kraken submit from a session that already has a supervised submit gate:

```bash
python main.py --broker-order-validations-submit-real outputs/broker_order_validations/<session_id> --broker-submit-reviewer marce --broker-submit-confirm --broker-submit-live --broker-submit-note "First supervised live submit"
```

This writes:

```text
outputs/broker_order_validations/<session_id>/broker_submit_response.json
```

The response artifact captures the final submit payload, auth preflight context, remote submit status, broker response, and any returned `txid` values.

And it can reconcile an existing submit response against Kraken order state using the stable session-derived `userref`:

```bash
python main.py --broker-order-validations-reconcile outputs/broker_order_validations/<session_id>
```

And it can refresh normalized post-submit order state for a submitted session:

```bash
python main.py --broker-order-validations-status outputs/broker_order_validations/<session_id>
```

This writes:

```text
outputs/broker_order_validations/<session_id>/broker_order_status.json
```

And it can now summarize broker submission health:

```bash
python main.py --broker-order-validations-health outputs/broker_order_validations
```

And emit a deterministic broker submission alert snapshot:

```bash
python main.py --broker-order-validations-alerts outputs/broker_order_validations
```

And it can now persist canonical broker dry-run sessions under:

```text
outputs/broker_dry_runs/<session_id>/
```

## License

Licensed under the Apache License, Version 2.0.
