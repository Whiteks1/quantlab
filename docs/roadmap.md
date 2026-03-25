# QuantLab Roadmap

This roadmap reflects the current repository state and the remaining stages needed to reach a broker-connected, supervised live-capable system without compromising QuantLab autonomy.

QuantLab should continue to evolve in this order:

1. research reliability
2. paper-trading discipline
3. execution safety
4. broker boundary hardening
5. supervised live execution
6. controlled automation

The key rule remains the same:

- do not move into broker-connected execution before the paper, safety, and observability layers are mature

## Current Position

QuantLab has already completed most of the original research foundation and quantitative robustness work.

### Effectively completed

- project packaging and modular source layout
- data ingestion and local artifact persistence
- indicators and feature preparation
- strategy abstraction and research execution flows
- backtesting and baseline metrics
- walk-forward and forward-evaluation flows
- canonical run artifacts and run history indexing
- stable machine-facing CLI and contract surfaces for integration

### In progress / partially completed

- paper-trading operationalization
- optional Stepbit-facing automation readiness at the external boundary

### Not started as production capability

- real execution safety boundary
- broker dry-run integration
- supervised live routing
- controlled automation over real execution

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
- clear signal and export surface for paper actions
- alerting hooks for paper sessions
- stronger distinction between research backtests and paper sessions
- explicit session health and failure reasons for paper mode

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

- `BrokerAdapter` interface as the common execution boundary
- execution-policy model
- max position size rules
- daily and session loss limits
- max concurrent exposure rules
- circuit-breaker and kill-switch behavior
- explicit failure-state handling
- broker credential boundaries and secret handling
- dry-run execution audit format

Exit condition:

- the system has a credible safety envelope and a broker abstraction that can reject unsafe execution decisions before a broker is connected

## Broker Integration Strategy

The first real broker integration should follow this decision framework:

- start with Kraken as the first real broker target
- define and stabilize `BrokerAdapter` before integrating any exchange-specific backend
- add Binance as the second backend to compare slippage, fill rate, rejects, and operating costs
- treat CCXT as optional acceleration for prototypes, smoke tests, or broad exchange experimentation, not as the authority of the execution design

Rationale:

- Kraken is the preferred first integration because it is a credible first real boundary for disciplined execution work
- Binance remains valuable as the second integration because it gives a meaningful comparison point after the first adapter is proven
- CCXT is useful when speed matters, but native integrations remain preferable when QuantLab needs tighter control over errors, rate limits, retries, and private execution flows

Architectural rule:

- strategies, risk policy, and execution safety must depend on `BrokerAdapter`, never on exchange-specific code

## Stage D.1 - Broker Dry-Run Integration

Status: not started

Goal:

- connect QuantLab to a real broker API in dry-run style without sending live risk-bearing orders

Scope:

- implement `KrakenBrokerAdapter` as the first concrete backend
- dry-run order translation from QuantLab signals
- request and response logging for broker interactions
- idempotency and retry discipline
- broker-side clock, status, and preflight validation

Exit condition:

- QuantLab can build, validate, and log Kraken order intent safely without yet operating with live capital

## Stage D.1.b - Second Broker Comparison

Status: not started

Goal:

- validate that the broker abstraction is real by integrating a second backend and comparing operational behavior

Scope:

- implement `BinanceBrokerAdapter`
- compare slippage, fill quality, rejects, and operating assumptions against Kraken
- identify any abstraction leaks that should be fixed in `BrokerAdapter`

Exit condition:

- QuantLab can support a second exchange without moving strategy or risk authority into exchange-specific code

## Stage D.2 - Broker Sandbox / Simulated Execution

Status: not started

Goal:

- test the broker boundary under realistic API conditions before live capital is involved

Scope:

- sandbox or equivalent broker-simulation mode where available
- reconciliation between intended orders and broker responses
- handling partial fills, rejects, rate limits, and transient API failures
- execution-state persistence
- restart and resume behavior

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
- operator dashboard or runbook support through QuantLab artifacts and optional external tooling

Exit condition:

- the system can trade live in a tightly supervised, low-risk mode with full auditability and emergency stop capability

## Stage F - Controlled Automation

Status: not started

Goal:

- move from supervised live execution to controlled automation only after paper, safety, broker, and supervised-live layers have proved stable

Scope:

- guarded automation policies
- explicit promotion gates from supervised to automated execution
- stronger monitoring and recovery rules
- bounded operator override model

Exit condition:

- QuantLab can automate execution within a controlled envelope without surrendering safety or product authority to external orchestration
