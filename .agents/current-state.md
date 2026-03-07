# Current State - QuantLab

## Active Stage
- **Stage**: M.3 — Portfolio Selection / Session Inclusion Rules
- **Last Updated**: 2026-03-07
- **Task File**: `.agents/tasks/stage-m3-selection-rules.md`

## Completed Stages

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

## Active Work
- **M.3**: Add a configurable selection layer that filters which forward sessions are included in the aggregated portfolio, before any allocation weighting is applied.
- Selection controls: top-N, rank metric, min-return, max-drawdown, include/exclude by ticker or strategy, latest-per-source-run.

## Known Issues / Technical Debt
- Some test files in `test/` may need alignment with runner API changes from Stage G.
- Duplicate workflow files in `.agents/workflows/`: `strategy-research.md` vs `strategy_research.md` — the underscore version is stale.
