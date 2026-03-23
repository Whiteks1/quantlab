# Current State - QuantLab

## Active Stage
- **Stage**: Stage O — Stepbit Automation Readiness
- **Last Updated**: 2026-03-23
- **Focus**: Stable machine-facing `sweep` contract and canonical run artifacts

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
- **Current Priority**: Issue #53 — stable `sweep` output contract for Stepbit consumption.
- **Implemented Direction**:
  - canonical run artifacts now center on `metadata.json`, `config.json`, `metrics.json`, and `report.json`
  - legacy `meta.json` / `run_report.json` remain read-compatible only
  - machine-facing `sweep` output is exposed through canonical `report.json` plus CLI/session context metadata

## Known Issues / Technical Debt
- Duplicate workflow files in `.agents/workflows/`: `strategy-research.md` vs `strategy_research.md` — the underscore version is stale.
- Local validation currently depends on a venv that does not include `pytest`; syntax and smoke validation are available, but full automated test execution requires installing the test dependency set first.
