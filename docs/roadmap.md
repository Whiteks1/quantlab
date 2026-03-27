# QuantLab Roadmap

This roadmap updates the original QuantLab plan to reflect the current repository state and the remaining stages needed to reach a broker-connected, automated, live-operating system without compromising QuantLab autonomy.

Public product framing:

- QuantLab should now be read as a `web3 app` in direction
- but still as a supervised execution system in maturity
- the roadmap therefore prioritizes execution safety, signer correctness, and operator control before broader onchain runtime power

QuantLab should continue to evolve in this order:

1. research reliability
2. paper-trading discipline
3. execution safety
4. broker boundary hardening
5. supervised live execution
6. controlled automation

Performance rule:

- stay Python-first by default
- treat native acceleration as a measured hotspot tactic, not as a product-wide rewrite plan
- prefer narrow compute kernels over multi-module language migration

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
- a first repository-level decision on native acceleration strategy, with the backtest engine identified as the first realistic hotspot candidate if profiling justifies it

### In progress / partially completed

- paper-trading operationalization
- supervised broker submit safety, reconciliation, and post-submit visibility
- initial real-execution safety and Kraken boundary work
- initial supervised Hyperliquid signed-submit work behind the shared execution boundary
- optional Stepbit-facing automation readiness at the external boundary

### Not started as production capability

- broad multi-venue live routing beyond the first implemented boundary
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

## Stage P.0 - Auxiliary Pre-Trade Risk Workbench

Status: proposed auxiliary subsystem track

Goal:

- add a bounded pre-trade planning layer to QuantLab without folding it into the
  backtest engine or venue execution adapters

Scope:

- new `src/quantlab/pretrade/` package
- deterministic trade-plan artifacts under `outputs/pretrade_sessions/`
- optional conversion into draft `ExecutionIntent`
- policy-aware pre-trade validation before adapter interaction
- bounded artifact-driven visualization in `research_ui`

Architectural rule:

- the workbench remains auxiliary
- QuantLab CLI and safety boundary remain sovereign
- the UI may visualize and compare plans, but must not own execution policy

See also:

- [docs/pretrade-risk-workbench-roadmap.md](./pretrade-risk-workbench-roadmap.md)
- [docs/pretrade-calculator-boundary.md](./pretrade-calculator-boundary.md)

Exit condition:

- QuantLab can generate and inspect deterministic pre-trade plans that improve
  operator discipline before paper or broker-facing actions without changing
  core engine responsibilities

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

Status: initial boundary slice implemented

Goal:

- define the safety layer before allowing real broker-connected order flow

Scope:

- `BrokerAdapter` as the broker-agnostic execution boundary
- execution-policy model
- max position size rules
- daily / session loss limits
- max concurrent exposure rules
- circuit-breaker and kill-switch behavior
- explicit failure-state handling
- broker credential boundaries and secret handling
- dry-run execution audit format

Initial slice already present:

- `ExecutionIntent`
- `ExecutionContext`
- `ExecutionPolicy`
- `ExecutionPreflight`
- `BrokerAdapter` contract
- deterministic local rejection before any exchange-specific adapter work

Exit condition:

- the system has a credible safety envelope and a broker abstraction that can reject unsafe execution decisions before a broker is connected

## Broker Integration Strategy

The first real execution-venue integration should follow this decision framework:

- start with Kraken as the first real broker target
- define and stabilize `BrokerAdapter` before integrating any exchange-specific backend
- keep `Kraken` as the first implemented backend and safety proving ground
- move `Hyperliquid` ahead of `Binance` as the first next venue intended for personal connection and supervised practical use
- treat `Binance` as optional later comparison work, not the default next venue
- treat CCXT as optional acceleration for prototypes, smoke tests, or broad exchange experimentation, not as the authority of the execution design

Rationale:

- Kraken is the preferred first integration because it is a credible first real boundary for disciplined execution work
- Hyperliquid is the preferred next venue because it tests whether the current abstraction can handle a high-performance onchain order-book venue, not only a conventional CEX-style broker
- Binance remains useful later as an additional comparison backend, but it is no longer the default next strategic target
- CCXT is useful when speed matters, but native integrations remain preferable when QuantLab needs tighter control over errors, rate limits, retries, and private execution flows

Architectural rule:

- strategies, risk policy, and execution safety must depend on `BrokerAdapter`, never on exchange-specific code
- `BrokerAdapter` remains the current code name, but it should now be interpreted as an execution-venue boundary rather than only a traditional broker boundary

## Stage D.1 - Broker Dry-Run Integration

Status: first dry-run adapter slice implemented

Goal:

- connect QuantLab to a real broker API in dry-run style without sending live risk-bearing orders

Scope:

- broker adapter abstraction
- implement `KrakenBrokerAdapter` as the first concrete backend
- dry-run order translation from QuantLab signals
- request/response logging for broker interactions
- idempotency and retry discipline
- broker-side clock/status/preflight validation

Initial slice already present:

- `KrakenBrokerAdapter` behind `BrokerAdapter`
- read-only Hyperliquid venue preflight backed by the shared `ExecutionContext` layer
- read-only Hyperliquid account/signer readiness backed by the shared `ExecutionContext` layer
- local Hyperliquid action/signature-envelope build surface backed by the shared `ExecutionContext` layer
- local Hyperliquid signer backend integration for real L1 action signing without submit
- first supervised Hyperliquid submit response artifacts generated from previously signed Hyperliquid action artifacts with explicit reviewer confirmation
- canonical Hyperliquid submit sessions and shared registry under `outputs/hyperliquid_submits/`
- persistent Hyperliquid post-submit order-status artifacts over canonical submit sessions
- explicit Hyperliquid reconciliation artifacts over canonical submit sessions using direct status, historical order, open-order, and fill surfaces
- dedicated Hyperliquid fill-summary artifacts over canonical submit sessions for richer fee, fill-size, and closed-PnL visibility
- bounded continuous-supervision artifacts over canonical Hyperliquid submit sessions with websocket-aware monitoring metadata and repeated local snapshots
- supervised Hyperliquid cancel response artifacts over canonical submit sessions with explicit reviewer confirmation
- Hyperliquid submission health summaries and deterministic alert snapshots over canonical submit sessions
- read-only Kraken public preflight probes
- read-only Kraken authenticated preflight probes
- read-only Kraken account snapshot and balance-aware intent readiness
- Kraken validate-only order probes before any real order placement work
- canonical broker order-validation sessions and shared registry for repeated review
- local approval gate artifacts before any future submit path
- local pre-submit bundles generated only from approved validation sessions
- local supervised submit gate artifacts generated only from pre-submit bundles
- local supervised submit stub artifacts generated only from submit gates
- first real supervised submit response artifacts generated only from previously validated sessions that already have a supervised submit gate and explicit live confirmation
- deterministic Kraken payload translation for validated intent
- dry-run audit snapshot without real broker connectivity
- local dry-run artifact persistence via `broker_dry_run.json`
- canonical broker dry-run sessions and shared registry for repeated review

Exit condition:

- QuantLab can build, validate, and log broker-intent orders safely against Kraken without yet operating with live capital

## Stage D.1.b - Second Venue Comparison

Status: initial runtime slices implemented

Goal:

- validate that the execution boundary is real by integrating a second venue with materially different execution semantics

Scope:

- implement a `Hyperliquid` venue adapter behind the existing boundary
- support the venue-specific needs that matter for Hyperliquid-style execution, such as signer-scoped nonces, API/agent wallets, and websocket-driven venue interaction
- compare operational assumptions and abstraction pressure against Kraken
- identify any abstraction leaks that should be fixed in `BrokerAdapter`
- keep `Binance` as optional later comparison work if a second CEX-style contrast still adds value

Before runtime work, a narrow boundary-review slice should clarify the minimal contract support needed for:

- signer identity distinct from execution account
- API / agent wallets
- subaccounts or vault routing
- websocket-first transport preferences

Exit condition:

- QuantLab can support a second materially different venue without moving strategy or risk authority into venue-specific code

## Stage D.2 - Broker Sandbox / Simulated Execution

Status: in progress

Goal:

- test the broker boundary under realistic API conditions before live capital is involved

Scope:

- sandbox or equivalent broker-simulation mode where available
- reconciliation between intended orders and broker responses
- handling partial fills, rejects, rate limits, and transient API failures
- execution-state persistence
- restart/resume behavior

Initial slice already present:

- supervised submit gate artifacts ahead of any real submit call
- supervised submit stub artifacts for payload review before live submission
- first tightly gated real Kraken submit response artifacts
- local pre-write of submit response state before the remote submit path
- explicit refusal of blind re-submit when a prior submit response artifact already exists
- authenticated reconciliation of submit sessions against Kraken order state using stable session-derived `userref`
- persistent broker order-status artifacts with normalized local state for submitted sessions
- broker submission health summaries and alert snapshots over broker order-validation sessions

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

- move from supervised live execution to controlled automation only after paper, safety, broker, and supervised-live layers have proved stable

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
5. add Stage D.1 broker dry-run integration, starting with Kraken
6. add the second venue comparison layer with Hyperliquid once the Kraken boundary is stable enough to generalize
7. validate broker behavior in Stage D.2
8. enter Stage E supervised live execution
9. only then move into Stage F controlled automation

## What Should Not Happen Early

- no direct jump from research success to live automated broker execution
- no live broker work before safety limits and kill-switch behavior exist
- no exchange-specific strategy or risk logic outside `BrokerAdapter`
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
- [execution-context-layer.md](./execution-context-layer.md)
- [execution-venue-strategy.md](./execution-venue-strategy.md)
- [hyperliquid-boundary-review.md](./hyperliquid-boundary-review.md)
