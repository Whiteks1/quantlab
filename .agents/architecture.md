# Architecture Overview — QuantLab

## Purpose

This document defines the architectural structure of QuantLab and the dependency rules between modules.

QuantLab is designed as a **research-first, CLI-driven quantitative laboratory** focused on reproducible strategy experimentation and portfolio analysis.

The architecture prioritizes:

- clarity
- deterministic behavior
- reproducibility
- modular design
- strict separation of concerns

---

# Architectural Layers

QuantLab follows a layered architecture where responsibilities flow in one direction:
`data -> indicators -> strategies -> backtest -> execution -> reporting`

The system explicitly separates **Orchestration** (CLI) from **Core Domain Logic**.

---

# Layer Responsibilities

## data
Responsible for acquiring and preparing market data.

Typical tasks:
- OHLC loading
- data cleaning
- timeframe normalization
- dataset preparation

Outputs:
DataFrames ready for analysis.

---

## indicators
Computes technical indicators and derived features.

Examples:
- RSI
- moving averages
- ATR
- volatility metrics

Indicators must be **pure functions** whenever possible.

---

## strategies
Implements signal generation logic.

Responsibilities:
- combine indicators
- generate BUY / SELL signals
- define entry and exit logic

Strategies must remain **stateless and deterministic**.

---

## backtest
Simulates historical trading using strategy signals.

Responsibilities:
- trade simulation
- position management
- capital tracking
- trade log generation

Outputs:
- trade logs
- performance metrics

---

## execution
Handles **paper trading / forward evaluation**.

Responsibilities:
- simulate real-time decision making
- maintain forward session logs
- record trades
- provide the future execution boundary that real broker adapters will implement

Outputs:
- forward run artifacts
- trade logs

---

## portfolio
Aggregates multiple strategy runs into a portfolio.

Responsibilities:
- combine runs
- apply allocation rules
- compute portfolio-level metrics

Examples:
- equal weight
- capital weight
- custom weight

---

## reporting
Produces human-readable and machine-readable outputs.

Artifacts include:

- markdown reports
- JSON summaries
- enriched CSV outputs
- charts and analytics

Reporting must **not contain business logic**.

---

# Dependency Rules

Allowed dependency direction:

---

# Forbidden Patterns

The following architectural violations must be avoided:

### Reporting importing strategy logic
Reporting must only consume results, never compute them.

### Business logic in CLI
`main.py` and the modules in `src/quantlab/cli/` should only orchestrate commands. They should delegate all quantitative and domain logic to the core modules.

### Execution modifying strategy definitions
Execution must treat strategies as immutable.

### Cross-layer shortcuts
Lower layers must not import higher layers.

Example of forbidden dependency:

---

# Architectural Principles

QuantLab architecture follows these principles:

**Deterministic behavior**
Results must be reproducible.

**Separation of concerns**
Each module has a single responsibility.

**Explicit artifacts**
All outputs must be stored and traceable.

**Small composable modules**
Large monolithic logic should be avoided.

---

# Future Architectural Evolution

Possible future expansions include:

- research automation modules
- portfolio risk policies
- strategy benchmarking frameworks
- experiment orchestration

However, QuantLab will remain **CLI-first** for the foreseeable roadmap.

No service layer or SaaS architecture is currently planned.
# Dependency Rules

Allowed dependency direction:

`data -> indicators -> strategies -> backtest -> execution -> reporting`

`portfolio` may consume results from backtest and execution, but should not introduce cross-layer shortcuts.
# Forbidden Patterns

The following architectural violations should be avoided:

- business logic in `main.py`
- reporting code containing strategy logic
- execution code modifying strategy definitions
- lower layers importing higher layers
- portfolio logic mixed into reporting or CLI code
# Architectural Principles

QuantLab architecture follows these principles:

- deterministic behavior
- separation of concerns
- explicit artifacts
- modular evolution
- research-first design# Future Architectural Evolution

Possible future extensions may include:

- broker integrations through a common `BrokerAdapter` boundary
- research automation
- portfolio risk policies
- experiment orchestration

These should remain future extensions and should not compromise the current CLI-first research architecture.

If real broker support is introduced, the preferred order is:

- define `BrokerAdapter` first
- implement Kraken as the first concrete backend
- add Binance as the second backend to validate that the abstraction is real
- keep CCXT optional for prototyping rather than making it the authority of execution design

---

# Desktop / Operator Workspace Boundary

QuantLab Desktop is a transversal workstation layer, not a second product authority.

The target Desktop architecture is:

- Electron shell as host runtime
- typed preload plus stable IPC surface as the process boundary
- shared contracts under `desktop/shared/` as the only owned cross-process contract source
- native desktop workstation surfaces as the target UI

Desktop may:

- visualize canonical artifacts
- provide bounded launch and review flows
- expose runtime continuity and operator visibility

Desktop must not:

- redefine engine or artifact truth
- move business logic out of the engine into renderer code
- treat `research_ui` as the permanent target shell

`research_ui` is a transitional continuity layer only. It may remain available where migration is incomplete, but native desktop surfaces are the target state.
