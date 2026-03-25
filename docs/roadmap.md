# QuantLab Roadmap

This roadmap updates the original QuantLab plan to reflect the current repository state and the remaining stages needed to reach a broker-connected, automated, live-operating system.

QuantLab should continue to evolve in this order:

1. research reliability
2. paper-trading discipline
3. execution safety
4. broker boundary hardening
5. supervised live execution
6. controlled automation

The key rule remains the same:

- do not move into live execution before the paper, safety, and observability layers are mature

## Current Position

QuantLab has already completed most of the original research foundation and quantitative robustness work.

### Effectively completed

- project packaging and modular source layout
- data ingestion and local artifact persistence
- indicators and feature preparation
- strategy abstraction and research execution flows
- backtesting and baseline metrics
- walk-forward / forward-evaluation flows
- canonical run artifacts and run history indexing
- stable machine-facing CLI and contract surfaces for integration

### In progress / partially completed

- paper-trading operationalization
- optional Stepbit-facing automation readiness at the external boundary

### Not started as production capability

- broker execution boundary
- live order routing
- automated live trading

## Stage A - Foundations

Status: completed

Scope:

- `pyproject.toml` packaging
- modular `src/` layout
- core data ingestion
- indicator layer
- strategy interface
- backtest engine
- minimal metrics

Exit condition:

- the system runs end-to-end and strategies can be compared reproducibly

## Stage B - Quantitative Robustness

Status: completed

Scope:

- slippage and fee handling
- report generation
- walk-forward style evaluation
- stronger artifact traceability
- run comparison and indexing

Exit condition:

- research outputs are strong enough to reject weak strategies and compare plausible ones without obvious bias or operational ambiguity

## Stage C - Paper Trading Foundation

Status: mostly completed

Scope already present in the repo:

- paper-oriented execution path
- trade logging
- forward-session artifacts
- portfolio aggregation over forward sessions

Remaining gap:

- this still needs to behave like an operational paper-trading system, not only a research extension

Exit condition:

- QuantLab can simulate live behavior without capital at risk and preserve a complete audit trail for each paper session

## Stage O - Stepbit Automation Readiness

Status: in progress

This is a parallel integration stage layered on top of A/B/C, not a replacement for them.

It is a secondary track, not the main product authority of QuantLab.

Scope:

- stable `--json-request`
- stable `--signal-file`
- stable `report.json.machine_contract`
- canonical run artifacts
- deterministic `--check` and `--version`
- automatic refresh of `runs_index.*`

Exit condition:

- external orchestration can invoke QuantLab as a reliable local execution engine without guessing at output structure

## Next Remaining Stages

## Stage C.1 - Paper Trading Operationalization

Status: next QuantLab-owned product stage

Goal:

- turn the existing paper-trading capabilities into an operationally disciplined layer

Scope:

- stable paper session lifecycle and session naming rules
- operator-facing paper runbook
- clear signal/export surface for paper actions
- alerting hooks for paper sessions
- stronger distinction between research backtests and paper sessions
- explicit session health / failure reasons for paper mode

Exit condition:

- QuantLab can run paper sessions repeatedly with traceability, alerts, and enough operator confidence to treat them as a real dry operational environment

## Stage O.1 - Integration Hardening

Status: secondary follow-up, driven by consumer feedback

Goal:

- reduce friction for external consumers such as Stepbit once they begin consuming the QuantLab contract in earnest

Scope:

- deterministic integration fixtures for `run` and `sweep`
- stronger contract tests for machine-facing outputs
- runbook improvements for consumer-side validation
- any small producer-side contract hardening needed after real adapter feedback

Exit condition:

- consumer systems can validate QuantLab integration deterministically and repeatedly without live-market dependence

## Stage D.0 - Real Execution Safety Boundary

Status: not started

Goal:

- define the safety layer before allowing real broker-connected order flow

Scope:

- execution-policy model
- max position size rules
- daily / session loss limits
- max concurrent exposure rules
- circuit-breaker and kill-switch behavior
- explicit failure-state handling
- broker credential boundaries and secret handling
- dry-run execution audit format

Exit condition:

- the system has a credible safety envelope that can reject unsafe execution decisions before a broker is connected

## Stage D.1 - Broker Dry-Run Integration

Status: not started

Goal:

- connect QuantLab to a real broker API in dry-run style without sending live risk-bearing orders

Scope:

- broker adapter abstraction
- first broker target, e.g. Coinbase Advanced Trade
- dry-run order translation from QuantLab signals
- request/response logging for broker interactions
- idempotency and retry discipline
- broker-side clock/status/preflight validation

Exit condition:

- QuantLab can build, validate, and log broker-intent orders safely without yet operating with live capital

## Stage D.2 - Broker Sandbox / Simulated Execution

Status: not started

Goal:

- test the broker boundary under realistic API conditions before live capital is involved

Scope:

- sandbox or equivalent broker-simulation mode where available
- reconciliation between intended orders and broker responses
- handling partial fills, rejects, rate limits, and transient API failures
- execution-state persistence
- restart/resume behavior

Exit condition:

- QuantLab can survive operational broker edge cases in a controlled environment

## Stage E - Supervised Live Execution

Status: not started

Goal:

- enable live execution with a human still explicitly supervising the system

Scope:

- live broker credentials under strict safety controls
- manual approval or supervised execution gate
- low-risk initial sizing
- real-time alerts for order placement, rejects, and risk events
- operator dashboard / runbook support through QuantLab artifacts and optional external tooling

Exit condition:

- the system can trade live in a tightly supervised, low-risk mode with full auditability and emergency stop capability

## Stage F - Controlled Automation

Status: not started

Goal:

- move from supervised live execution to controlled automation

Scope:

- scheduler / orchestrator-driven recurring execution
- automated decision-to-order flow within approved strategy boundaries
- automated risk gate evaluation before each live action
- post-trade reconciliation and anomaly detection
- automated pause-on-failure behavior
- live performance monitoring against expected risk and drawdown limits

Exit condition:

- QuantLab can operate as an automated broker-connected system with bounded risk, observability, and deterministic stop conditions

## Stage G - Mature Live System

Status: long-term

Goal:

- become a resilient, operator-trustworthy live trading system rather than a research tool with execution attached

Scope:

- stronger portfolio-level capital controls
- multi-strategy deployment governance
- operational incident review workflow
- broker abstraction for additional venues if justified
- formal promotion flow from research -> paper -> supervised live -> automated live

Exit condition:

- strategy promotion, execution, monitoring, and rollback all behave like one coherent operating system rather than a collection of scripts

## Recommended Execution Order

From the current repository state, the most rational order is:

1. complete Stage C.1 paper-trading operationalization
2. continue Stage O producer-side stabilization only where real integration friction requires it
3. harden Stage O.1 integration fixtures only if consumer feedback justifies them
4. design and implement Stage D.0 safety boundary
5. add Stage D.1 broker dry-run integration
6. validate broker behavior in Stage D.2
7. enter Stage E supervised live execution
8. only then move into Stage F controlled automation

## What Should Not Happen Early

- no direct jump from research success to live automated broker execution
- no live broker work before safety limits and kill-switch behavior exist
- no expansion of external orchestration before the paper and safety layers are operationally trustworthy
- no collapsing of QuantLab and Stepbit responsibilities into one codebase

## Related Documents

- [README.md](../README.md)
- [cli.md](./cli.md)
- [run-artifact-contract.md](./run-artifact-contract.md)
- [stepbit-io-v1.md](./stepbit-io-v1.md)
- [stepbit-integration.md](./stepbit-integration.md)
- [quantlab-stepbit-boundaries.md](./quantlab-stepbit-boundaries.md)
- [advantages-and-future.md](./advantages-and-future.md)
