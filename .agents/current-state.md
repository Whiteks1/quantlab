# Current State - QuantLab

## Active Stage
- **Stage**: Stage O — Stepbit Automation Readiness
- **Last Updated**: 2026-03-25
- **Focus**: Stage O is centered on execution-surface stability for local automation and machine-to-machine integration.
- **Authority Note**: Stage O is a secondary integration track. QuantLab remains autonomous, and this stage does not override QuantLab-owned product priorities such as paper-trading operationalization.

## Completed/Planned Stages

| Stage | Description | Status |
|-------|-------------|--------|
| I | Standardized Run Reports | ✅ Done |
| J | Run Registry and Comparison | ✅ Done |
| K | Advanced Metrics and Run Analytics (K.1–K.3) | ✅ Done |
| L | Forward Evaluation Pipeline | ✅ Done |
| L.1 | Forward Transparency Improvements | ✅ Done |
| L.2 | Resume / Incremental Forward Sessions | ✅ Done |
| L.2.a | Session Bounds Cleanup | ✅ Done |
| L.2.b | Resume Idempotence (no-op metadata fix) | ✅ Done |
| M | Portfolio Aggregation scaffold | ✅ Done |
| M.1 | Portfolio Hygiene and Deduplication | ✅ Done |
| M.2 | Allocation Controls / Weighted Aggregation | ✅ Done |
| M.3 | Portfolio Selection / Session Inclusion Rules | ✅ Done |
| M.4 | Portfolio Mode Comparison | ✅ Done |
| N | Run Lifecycle Management (`quantlab runs`) | ✅ Done |
| O | Stepbit Automation Readiness (I/O & CLI Stability) | 🟨 In Progress |

## Active Work
- **Stage Open**: Stage O is the current focus.
- **Current Priority**: Keep the public execution contract stable for the next integration step without letting external integration redefine QuantLab's core authority.
- **Active Focus Areas**:
  - stabilize plain `run` output behavior around the canonical run artifact model
  - preserve `sweep` contract stability as the existing machine-facing automation path
  - keep `report.json.machine_contract` as the shared canonical machine-facing surface for `run` and `sweep`
  - keep `outputs/runs/runs_index.*` refreshed automatically after successful `run`, `sweep`, and `forward` executions
- **Implemented Direction**:
  - canonical run artifacts now center on `metadata.json`, `config.json`, `metrics.json`, and `report.json`
  - successful plain `run` executions now write that canonical artifact pack under `outputs/runs/<run_id>/`
  - legacy `meta.json` / `run_report.json` remain read-compatible only
  - machine-facing `run` and `sweep` outputs are exposed through canonical `report.json.machine_contract`
  - `main.py --version` returns a stable CLI version string
  - `main.py --check` returns a deterministic JSON health summary for runtime preflight
  - the CLI keeps the existing `--json-request` `sweep` path as the smoke-validation surface
  - the shared `runs_index.csv/json/md` registry is refreshed automatically after successful run-producing commands
  - Stepbit-facing integration is treated as optional and boundary-based rather than as a control plane for QuantLab

## Known Issues / Technical Debt
- Duplicate workflow files in `.agents/workflows/`: `strategy-research.md` vs `strategy_research.md` — the underscore version is stale.
- The canonical machine-facing contract is now shared by `run` and `sweep`, but downstream consumers may still carry old assumptions about `run` using only top-level `summary` / `kpi_summary`.
