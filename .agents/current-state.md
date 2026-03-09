# Current State - QuantLab

## Project Identity
QuantLab is a **CLI-first personal quantitative research laboratory**. It is designed for research reproducibility, experiment traceability, and portfolio-level reasoning. It is NOT a SaaS platform, public API, or multi-user system.

## Architectural Direction
- **Layered Architecture**: `data/`, `indicators/`, `strategies/`, `backtest/`, `execution/` (paper broker), `reporting/`.
- **CLI Orchestration**: `main.py` serves as the entrypoint for all research and backtesting pipelines.
- **Data-Driven**: Research is backed by deterministic processes and verifiable artifacts in `outputs/`.

## Roadmap Stages
- **Stage M**: Portfolio Engine (Current focus)
- **Stage N**: Allocation & Risk Policies
- **Stage O**: Research Intelligence
- **Stage P**: Lab Automation

## Development Workflow
QuantLab follows a strict "Plan-Execute-Verify" workflow:
1. **Architect (ChatGPT)**: Designs changes and provides implementation plans.
2. **Execution Agent (Antigravity)**: Implements plans in dedicated branches.
3. **Verification**: Automated tests (`pytest`) and manual output validation.
4. **Stable Main**: No direct commits to `main`.

## Out-of-Scope (for now)
- External APIs or Web Frontends
- Authentication or Multi-user support
- Live trading execution (Paper-only by default)
- Microservices infrastructure

---

## Active Stage
- **Stage**: M.3 — Portfolio Selection / Session Inclusion Rules
- **Last Updated**: 2026-03-10
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
