# Current State - QuantLab

## Active Stage
- **Stage**: Stage C.1 — Paper Trading Operationalization
- **Last Updated**: 2026-03-25
- **Focus**: Stage C.1 is centered on turning the existing paper-oriented flows into a repeatable operational paper-trading discipline.
- **Authority Note**: Stepbit-facing integration remains a secondary boundary track. QuantLab stays autonomous and external consumer needs do not override QuantLab-owned priorities.

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
| C.1 | Paper Trading Operationalization | 🟨 In Progress |
| O | Stepbit Automation Readiness (I/O & CLI Stability) | 🟨 In Progress |

## Active Work
- **Stage Open**: Stage C.1 is the primary product focus.
- **Current Priority**: Strengthen paper-session discipline, traceability, and operator confidence before advancing into real execution safety work.
- **Active Focus Areas**:
  - define a clearer paper-session lifecycle and operator expectations
  - strengthen distinction between research artifacts and paper-trading artifacts
  - make paper-mode failures and health signals more explicit
  - keep the external execution contract stable only where real consumer friction appears
- **Implemented Direction**:
  - canonical run artifacts now center on `metadata.json`, `config.json`, `metrics.json`, and `report.json`
  - successful plain `run` executions now write that canonical artifact pack under `outputs/runs/<run_id>/`
  - legacy `meta.json` / `run_report.json` remain read-compatible only
  - machine-facing `run` and `sweep` outputs are exposed through canonical `report.json.machine_contract`
  - `main.py --version` returns a stable CLI version string
  - `main.py --check` returns a deterministic JSON health summary for runtime preflight
  - the CLI keeps the existing `--json-request` `sweep` path as the smoke-validation surface
  - the shared `runs_index.csv/json/md` registry is refreshed automatically after successful run-producing commands
  - paper-backed `run` executions now write dedicated artifacts under `outputs/paper_sessions/<session_id>/`
  - paper sessions persist `session_metadata.json` and `session_status.json`
  - external signal mode for paper-backed `run` remains `run` to preserve contract stability
  - public operator guidance for paper sessions now lives in `docs/paper-session-runbook.md`
  - paper sessions now support a shared index surface under `outputs/paper_sessions/paper_sessions_index.*`
  - Stage D.0 now has an initial broker-agnostic safety boundary in `src/quantlab/brokers/boundary.py`
  - Stage D.1 now has a first dry-run `KrakenBrokerAdapter` built on that boundary
  - Kraken dry-run can now materialize a local `broker_dry_run.json` audit artifact


## Known Issues / Technical Debt
- Duplicate workflow files in `.agents/workflows/`: `strategy-research.md` vs `strategy_research.md` — the underscore version is stale.
- The canonical machine-facing contract is now shared by `run` and `sweep`, but downstream consumers may still carry old assumptions about `run` using only top-level `summary` / `kpi_summary`.
