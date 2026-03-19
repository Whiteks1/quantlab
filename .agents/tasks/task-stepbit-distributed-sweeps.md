# Task: Distributed Sweeps (Scaling Step)

## Goal
Enable QuantLab to execute large-scale parameter sweeps across multiple nodes or threads, orchestrated by Stepbit.

## Why
As strategy complexity and parameter counts grow, single-threaded sweeps become a bottleneck. Distributing work allows for faster discovery and more robust sensitivity analysis.

## Scope
- Define a "Work Unit" (single run within a sweep).
- Implement a way to "split" a sweep config into independent run configs.
- Implement a "Merge/Collect" step to aggregate results from multiple nodes into a single sweep report.
- Ensure `registry.csv` remains consistent across distributed writes (or use a post-collection step).

## Non-goals
- Implementing a custom cluster manager (use existing tools like `Ray`, `Dask`, or simple Stepbit orchestration).
- Real-time synchronization of state between nodes.

## Inputs
- `src/quantlab/cli/sweep.py`
- `src/quantlab/runs/registry.py`

## Expected outputs
- CLI support for `--split` and `--merge` operations.
- A "Scaling Guide" for distributed research.

## Acceptance criteria
- A sweep of 100 runs can be split into 4 batches of 25, executed in parallel, and merged into a single valid report.
- Results are identical to a single-threaded sweep.

## Constraints
- Preserve "Determinism" across nodes.
- Do not introduce complex distributed lock management if simple aggregations suffice.

## Suggested next step
The Stepbit Integration Roadmap is now complete. Review [stage-stepbit-integration-roadmap.md](file:///c:/Users/marce/Documents/QUANT%20LAB%20PERSONAL/quant_lab/.agents/tasks/stage-stepbit-integration-roadmap.md) to begin implementation of the first phase.
