# Current State - QuantLab

## Active Stage
- **Stage**: Stage N — Run Lifecycle Management
- **Last Updated**: 2026-03-20
- **Task File**: `.agents/tasks/task-runs-cli-interface.md`

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
| N | Run Lifecycle Management (`quantlab runs`) | 🟦 Planned |
| O | Stepbit Automation Readiness (I/O & CLI Stability) | 🟦 Planned |

## Active Work
- **Stage Open**: Stage N is the current focus. It aims to clarify and implement the `runs.py` command interface for run inspection and comparison.

## Known Issues / Technical Debt
- Some test files in `test/` may need alignment with runner API changes from Stage G.
- Duplicate workflow files in `.agents/workflows/`: `strategy-research.md` vs `strategy_research.md` — the underscore version is stale.
