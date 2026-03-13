````md
# QuantLab Code Map

This document defines the structural boundaries of the QuantLab repository.

Its purpose is to help execution agents understand where logic belongs before making changes.

Agents should consult this file before modifying code.

---

## 1. Entry point

### `main.py`

**Allowed responsibilities**
- Parse CLI arguments
- Route commands
- Delegate execution to the CLI layer

**Not allowed**
- Business logic
- Quantitative logic
- Report generation logic
- Data processing pipelines

`main.py` must remain thin.

---

## 2. CLI orchestration layer

**Location**
```text
src/quantlab/cli/
````

**Purpose**
This layer coordinates command execution and delegates work into the proper domain modules.

**Allowed responsibilities**

* Command-specific orchestration
* Early-exit command handling
* Input normalization
* Delegation into core modules

**Typical modules**

* `report.py`
* `forward.py`
* `portfolio.py`
* `sweep.py`
* `run.py`
* `runs.py`

**Not allowed**

* Heavy quantitative logic
* Core backtesting logic
* Indicator implementations
* Strategy rules that belong in domain modules

CLI modules may coordinate behavior, but should not become business-logic containers.

---

## 3. Core research modules

### `src/quantlab/data/`

**Responsibility**
Market data loading, acquisition, and caching.

**Typical contents**

* Data source adapters
* OHLC loading utilities
* Data normalization helpers
* Cache helpers

---

### `src/quantlab/features/`

**Responsibility**
Indicator computation and feature engineering.

**Examples**

* RSI
* Moving averages
* ATR

**Typical contents**

* Indicator functions
* Feature pipelines
* Signal inputs derived from price data

---

### `src/quantlab/strategies/`

**Responsibility**
Signal generation and trading rule definitions.

**Typical contents**

* Entry/exit rule definitions
* Strategy parameter handling
* Buy/sell/hold signal production

---

### `src/quantlab/backtest/`

**Responsibility**
Simulation engine, trade tracking, and performance metrics.

**Typical contents**

* Backtest execution
* Trade lifecycle simulation
* Equity curve generation
* Performance statistics

---

### `src/quantlab/execution/`

**Responsibility**
Paper execution, forward testing, and simulated trading.

**Typical contents**

* Forward evaluation flows
* Simulated execution state
* Fill modeling for paper runs
* Execution logs

---

### `src/quantlab/reporting/`

**Responsibility**
Report generation, artifact writing, and output formatting.

**Typical contents**

* Run reports
* Metrics summaries
* JSON/CSV/Markdown artifacts
* Serialization helpers for outputs

---

### `src/quantlab/portfolio/`

**Responsibility**
Portfolio aggregation, multi-run comparison, and allocation logic.

**Typical contents**

* Position aggregation
* Portfolio-level metrics
* Allocation and weighting rules
* Multi-strategy combination logic

---

### `src/quantlab/runs/`

**Responsibility**
Run tracking, storage, registry, metadata management, and serialization.

**Typical contents**

* Run IDs
* Experiment registry
* Metadata persistence
* Run folder structure
* Reproducibility helpers

This layer supports reproducibility and experiment traceability.

---

## 4. Testing

### `test/`

Tests should validate observable behavior.

**Rules**

* Refactors should preserve existing behavior unless the task explicitly changes functionality
* Tests should verify outcomes, not internal implementation details, unless necessary
* `pytest` must pass after changes

---

## 5. Documentation and project memory

### `.agents/`

This directory stores persistent project context for AI-assisted workflow.

**Important files**

* `project-brief.md`
* `architecture.md`
* `artifact-contracts.md`
* `current-state.md`
* `implementation-rules.md`
* `workflow.md`
* `session-log.md`
* `tasks/`

Agents should treat these files as the project memory layer.

---

## 6. Change boundaries

### Safer zones for refactors

* `src/quantlab/cli/`
* `src/quantlab/runs/`
* Documentation in `.agents/`

### Sensitive areas

Use extra caution when modifying:

* `main.py`
* Reporting and artifact-related modules
* Forward evaluation modules
* Portfolio aggregation modules

These areas may affect artifact integrity, coordination flow, or experiment reproducibility.

---

## 7. Required explanation before changes

Before modifying a file, the execution agent should explain:

1. Why that file is the correct place for the change
2. What behavior may be affected

---

## 8. Placement rule

When adding new functionality, prefer the layer that matches the responsibility of the change:

* Put CLI wiring in `src/quantlab/cli/`
* Put market/data access in `src/quantlab/data/`
* Put indicators in `src/quantlab/features/`
* Put strategy rules in `src/quantlab/strategies/`
* Put simulation logic in `src/quantlab/backtest/`
* Put forward/paper execution in `src/quantlab/execution/`
* Put artifact/report generation in `src/quantlab/reporting/`
* Put portfolio-level logic in `src/quantlab/portfolio/`
* Put run metadata and registry logic in `src/quantlab/runs/`

If a change touches multiple layers, the execution agent should keep each concern in its own module rather than collapsing everything into one file.

---

## 9. Architectural intent

QuantLab is structured so that:

* the CLI layer orchestrates
* the core modules implement domain behavior
* the reporting layer writes artifacts
* the runs layer preserves reproducibility
* the test suite protects observable behavior

The repository should evolve toward clearer boundaries, thinner entry points, and modular domain logic.

---

## 10. Working rule for execution agents

Before starting implementation, the execution agent should check:

* whether the target file already owns that responsibility
* whether the change belongs in orchestration or domain logic
* whether artifact or reproducibility behavior could be affected
* whether tests need to be added or updated to cover the change

If the answer is unclear, prefer preserving architectural boundaries over short-term convenience.