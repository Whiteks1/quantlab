# Project Brief - QuantLab

## Project Name
**QuantLab** — Modular Research Environment for Algorithmic Trading Strategies

## Purpose
QuantLab is a **research-oriented quantitative trading and portfolio analysis project**.

Its purpose is to support:

- systematic experimentation
- backtesting
- forward evaluation
- portfolio aggregation
- structured reporting

The system is being developed through **explicit, verifiable stages**, with an emphasis on research quality, reproducibility, and modular growth.

## Core Goals
- Enable rapid research and backtesting of trading indicators and strategies.
- Provide a modular architecture with clear separation of concerns.
- Ensure reproducibility through disciplined artifact management and deterministic logic.
- Support paper trading and forward evaluation before any live deployment.
- Produce high-quality outputs in JSON, Markdown, CSV, and chart form.
- Evolve the system through explicit, testable, and reviewable stages.

## Technical Stack
- **Language**: Python 3.x
- **Core libraries**: pandas, numpy
- **Visualization**: matplotlib
- **Testing**: pytest
- **Reporting**: Markdown, JSON, CSV, charts

## High-Level Components
1. **data/** — Data acquisition, normalization, and OHLC handling
2. **features/** — Indicators and feature engineering
3. **strategies/** — Signal generation and trading logic
4. **backtest/** — Historical simulation engine
5. **execution/** — Paper execution and forward evaluation
6. **reporting/** — Human-readable and machine-readable reporting
7. **portfolio/** — Portfolio primitives, aggregation, and selection support

## Current Development Focus
QuantLab is evolving from a strategy-level backtesting environment into a broader **quantitative research laboratory** with stronger support for:

- forward evaluation
- run comparison
- portfolio aggregation
- selection and weighting logic
- artifact consistency
- research traceability

Detailed stage-by-stage progress belongs in `.agents/current-state.md`, not in this brief.

## Engineering Principles
- Correctness before convenience
- Clear stage boundaries
- Small, reversible changes
- Tests for every behavior change
- No silent contract drift
- Markdown and JSON reporting must remain aligned
- Backward compatibility should be preserved unless explicitly changed
- Research clarity should take priority over premature infrastructure complexity

## Workflow Principle for Antigravity
Antigravity should not rely on long chat context alone.

Before implementation, it should:
1. read the relevant workflow files
2. review the current project state
3. propose a scoped implementation plan
4. execute only the next approved step
5. leave clear continuity for the next session

Antigravity should work with **strict scope discipline**, avoid unrelated changes, and preserve repository clarity.

## Notes
QuantLab is currently being developed as a **CLI-first quantitative research laboratory**, not as a SaaS platform or public service layer.

Future extensions may include broker integrations, broader automation, API layers, or user-facing capabilities, but these are **not current priorities** and should only be introduced when they strengthen the research mission of the project.