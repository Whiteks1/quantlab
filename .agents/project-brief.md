# Project Brief - QuantLab

## Project Name
QuantLab - Modular Research Environment for Trading Algorithmic Strategies

## Purpose
QuantLab is a research-oriented trading and portfolio analysis project.
Its purpose is to support systematic experimentation, backtesting, forward evaluation, portfolio aggregation, and reporting through staged development.

## Core Goals
- Enable rapid research and backtesting of trading indicators and strategies
- Provide a modular architecture with clear separation of concerns
- Ensure reproducibility through strict artifact management and deterministic logic
- Support paper trading and forward evaluation before any live deployment
- Maintain high-quality outputs in JSON, Markdown, CSV, and chart form
- Evolve the system through explicit, verifiable stages

## Technical Stack
- **Language**: Python 3.x
- **Data Analysis**: Pandas, NumPy
- **Testing**: Pytest
- **Reporting**: Markdown, JSON, Matplotlib

## High-Level Components
1. **data/** - Data acquisition and OHLC handling
2. **features/** - Indicators and feature engineering
3. **strategies/** - Signal generation and trading logic
4. **backtest/** - Historical simulation engine
5. **execution/** - Paper execution and forward evaluation
6. **reporting/** - Human-readable and machine-readable reporting
7. **portfolio/** - Portfolio primitives and aggregation support

## Current Roadmap Status
### Completed
- Stage I: Standardized Run Reports
- Stage J: Run Registry and Comparison
- Stage K: Advanced Metrics and Run Analytics
- Stage L: Forward Evaluation
- Stage L.1: Forward Transparency Improvements
- Stage L.2: Resume / Incremental Forward Sessions
- Stage L.2.a: Session Bounds Cleanup
- Stage L.2.b: Resume Idempotence
- Stage M: Portfolio Aggregation
- Stage M.1: Portfolio Hygiene and Deduplication
- Stage M.2: Allocation Controls / Weighted Aggregation

### Active Next Stage
- Stage M.3: Portfolio Selection / Session Inclusion Rules

## Engineering Principles
- Correctness before convenience
- Clear stage boundaries
- Small reversible changes
- Tests for every behavior change
- No silent contract drift
- Markdown and JSON reporting should stay aligned
- Backward compatibility should be preserved unless explicitly changed

## Workflow Principle for Antigravity
Antigravity should not rely on long chat context.
It should read workflow files first, propose a plan, execute only the next approved step, and leave clear continuity for the next session.