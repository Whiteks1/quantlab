# QuantLab Code Map

## Entry points

### main.py
Responsibilities:
- parse CLI arguments
- route commands
- delegate execution to src/quantlab/cli/

Must remain thin.

Do not place business logic here.

---

## CLI orchestration

### src/quantlab/cli/
Responsibilities:
- command-specific orchestration
- early-exit command handling
- delegation into core modules

Modules:
- report.py
- forward.py
- portfolio.py
- sweep.py
- run.py
- runs.py

This layer may coordinate behavior, but should not contain core quantitative logic.

---

## Core research logic

### src/quantlab/data/
Market data loading and acquisition.

### src/quantlab/features/
Indicators and feature engineering.

### src/quantlab/strategies/
Signal generation and strategy definitions.

### src/quantlab/backtest/
Backtesting engine and metrics.

### src/quantlab/execution/
Paper execution and forward evaluation.

### src/quantlab/reporting/
Report generation and output artifacts.

### src/quantlab/portfolio/
Portfolio aggregation and portfolio-level logic.

### src/quantlab/runs/
Run tracking, storage, registry, and serialization.

---

## Testing

### test/
Tests should validate observable behavior.
Refactors should preserve test behavior unless the task explicitly changes functionality.

---

## Documentation / project memory

### .agents/
Persistent project context for AI-assisted workflow.

Important files:
- project-brief.md
- architecture.md
- artifact-contracts.md
- current-state.md
- implementation-rules.md
- workflow.md
- session-log.md
- tasks/

---

## Change boundaries

### Safe places for refactors
- src/quantlab/cli/
- src/quantlab/runs/
- documentation in .agents/

### Files that require extra caution
- main.py
- artifact-related reporting modules
- forward evaluation modules
- portfolio aggregation modules

---

## Rule
Before changing a file, the execution agent should explain why that file is the correct place for the change.