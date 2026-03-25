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
python main.py --ticker ETH-USD --start 2022-01-01 --end 2023-12-31 --paper --report
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

Index files:

- `outputs/runs/runs_index.csv`
- `outputs/runs/runs_index.json`
- `outputs/runs/runs_index.md`

## 4. Forward Evaluation

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

## 5. Portfolio Workflows

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

## 6. Sweep Workflows

Flag-driven sweep:

```bash
python main.py --sweep configs/experiments/eth_2023_grid.yaml --sweep_outdir outputs/stepbit
```

Machine-facing sweep:

```bash
python main.py --json-request "{\"schema_version\":\"1.0\",\"request_id\":\"req_sweep_001\",\"command\":\"sweep\",\"params\":{\"config_path\":\"configs/experiments/eth_2023_grid.yaml\",\"out_dir\":\"outputs/stepbit\"}}"
```

`report.json.machine_contract` is the canonical machine-facing result surface for automated sweep consumption.

## 7. Legacy Flags

These remain accepted for backward compatibility, but should not be expanded further in docs or integrations:

- `--list-runs` -> legacy alias of `--runs-list`
- `--best-from` -> legacy alias of `--runs-best`

Legacy read-compatible artifacts also remain in the codebase:

- `meta.json`
- `run_report.json`
- `forward_report.json`
- `portfolio_report.json`

The preferred public surface is the canonical contract documented in [run-artifact-contract.md](./run-artifact-contract.md).

## 8. Design Rules

- `main.py` and `src/quantlab/cli/` should remain orchestration-only
- domain and quantitative logic belong outside the entrypoint
- new public behavior must be documented with executable examples
- new machine-facing behavior should prefer canonical artifacts over legacy outputs
