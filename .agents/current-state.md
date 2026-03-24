# Current State - QuantLab

## Active Stage
- **Stage**: Stage O — Stepbit Automation Readiness
- **Last Updated**: 2026-03-24
- **Focus**: Canonical `run` outputs and automatic `runs_index` refresh for run-producing commands

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
- **Current Priority**: Align plain `run` with the canonical run artifact model and keep `outputs/runs/runs_index.*` synchronized automatically after successful `run`, `sweep`, and `forward` executions.
- **Implemented Direction**:
  - canonical run artifacts now center on `metadata.json`, `config.json`, `metrics.json`, and `report.json`
  - successful plain `run` executions now write that canonical artifact pack under `outputs/runs/<run_id>/`
  - legacy `meta.json` / `run_report.json` remain read-compatible only
  - machine-facing `sweep` output is exposed through canonical `report.json` plus CLI/session context metadata
  - `main.py --version` returns a stable CLI version string
  - `main.py --check` returns a deterministic JSON health summary for runtime preflight
  - the CLI keeps the existing `--json-request` `sweep` path as the smoke-validation surface
  - the shared `runs_index.csv/json/md` registry is refreshed automatically after successful run-producing commands

## Known Issues / Technical Debt
- Duplicate workflow files in `.agents/workflows/`: `strategy-research.md` vs `strategy_research.md` — the underscore version is stale.
- The canonical machine-facing contract is still formally stabilized only for `sweep`; `run` now emits canonical artifacts but does not yet expose a dedicated `machine_contract` block.
