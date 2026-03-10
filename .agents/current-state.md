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
| M | Portfolio Aggregation Scaffold | ✅ Done |
| M.1 | Portfolio Hygiene and Deduplication | ✅ Done |
| M.2 | Allocation Controls / Weighted Aggregation | ✅ Done |

## Active Work
- **M.3** focuses on adding a configurable selection layer that determines which forward sessions are included in the aggregated portfolio before allocation weighting is applied.
- Current selection controls include:
  - top-N selection
  - ranking by metric
  - minimum return thresholds
  - maximum drawdown thresholds
  - include / exclude filters by ticker
  - include / exclude filters by strategy
  - latest-per-source-run selection

## Known Issues / Technical Debt
- Some test files in `test/` may still require alignment with runner API changes introduced after Stage G.
- Duplicate workflow files currently exist in `.agents/workflows/`: `strategy-research.md` and `strategy_research.md`. The underscore version is stale and should be removed or consolidated.

## Immediate Next Step
- Complete Stage M.3 and verify that the selection layer behaves correctly across different portfolio aggregation scenarios.
- Once M.3 is closed, proceed to Stage M.4 for portfolio mode comparison across `raw_capital`, `equal_weight`, and `custom_weight`.

## Notes
- The current project focus remains on **portfolio-level research workflows**, not service-layer expansion.
- QuantLab is still being developed as a **CLI-first quantitative research laboratory**, with future extensibility preserved but not prioritized ahead of research quality and reproducibility.