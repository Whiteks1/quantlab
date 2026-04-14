# QuantLab Roadmap

This roadmap updates the original QuantLab plan to reflect the current product and system direction plus the remaining stages needed to reach a broker-connected, automated, live-operating system without compromising QuantLab autonomy.

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

Minimum promotion policy:

- do not promote a stage if live or broker-facing work still depends on ad hoc local secret handling
- do not promote a stage if canonical critical alert coverage is missing for the failures that stage is supposed to survive
- treat missing alert artifacts or unclear secret boundaries as promotion blockers, not polish debt

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
- Desktop/UI operator workspace architecture and shell hardening

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

## Transversal Capability Track - Desktop / Operator Workspace

Status: in progress

Goal:

- provide a stable operator workspace for reviewing research, paper, and broker evidence without moving authority out of the engine

Scope:

- desktop shell architecture and typed desktop contracts
- operator-facing workstation surfaces for runs, compare, artifacts, paper ops, and system continuity
- workspace hierarchy, focus, and promotion visibility across native desktop surfaces
- browser-backed continuity only where the desktop still depends on transitional `research_ui` behavior

Architectural rule:

- Desktop/UI is a transversal capability track, not a primary linear stage
- the engine, contracts, and canonical artifacts remain the authority
- the workspace should reduce operator ambiguity, not introduce a second product authority
- the accepted desktop target architecture now lives in [docs/desktop-target-architecture.md](./desktop-target-architecture.md)
- `research_ui` should be treated as transitional continuity, not as the permanent shell target

Exit condition:

- QuantLab can expose research, paper, and execution evidence through a stable operator workspace with clear ownership, continuity, and promotion visibility

## Next Remaining Stages

## Stage C.1 - Paper Trading Operationalization

Status: supporting stage, no longer the primary bottleneck

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

Minimum promotion signals:

- paper sessions produce canonical session artifacts with explicit terminal status
- the operator can distinguish research outputs from paper sessions without ambiguity
- paper-critical failures emit canonical alert artifacts instead of requiring log archaeology

Current interpretation:

- `Stage C.1` still matters because paper-session discipline remains the promotion floor for broker-facing work
- but it is no longer the main unresolved runtime frontier
- from the current repository state, paper work should now be prioritized when it strengthens operator visibility, promotion discipline, or broker-readiness handoff rather than treated as the dominant roadmap stage

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

## Stage O.2 - Quant Pulse Signal Intake

Status: proposed auxiliary signal boundary

Goal:

- consume upstream Quant Pulse research intents without making QuantLab dependent on an external editorial authority

Scope:

- structured signal intake for `signal_summary`, `priority`, `affected_universe`, `bias`, `horizon`, `hypothesis_type`, `validation_goal`, and `invalidation_condition`
- routing signals into research workflows only when they improve validation, risk filters, or product priorities
- keeping QuantLab autonomous while allowing Quant Pulse to act as a signal filter and prioritization layer

Exit condition:

- QuantLab can ingest upstream signals as structured research prompts while still deciding independently what is worth testing, filtering, or ignoring

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

- define and stabilize `BrokerAdapter` before integrating any exchange-specific backend
- keep `Hyperliquid` as the active execution-venue target for personal connection and supervised practical use
- keep `Kraken` as implemented compatibility/history rather than the active next target
- consider `Bitget` as optional later comparison work after `Hyperliquid`, not the default next venue
- treat `Binance` as optional later comparison work, not the default next venue
- treat CCXT as optional acceleration for prototypes, smoke tests, or broad exchange experimentation, not as the authority of the execution design

Rationale:

- Hyperliquid is the preferred active venue because it tests whether the current abstraction can handle a high-performance onchain order-book venue, not only a conventional CEX-style broker
- Kraken remains useful as compatibility history and a reference implementation, but it is no longer the active next strategic target
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
- read-only and validate-only Kraken preflight, account, and dry-run audit surfaces
- read-only Hyperliquid readiness, signing, supervised submit, cancel, and reconciliation surfaces behind the same execution boundary
- canonical session registries and artifact persistence for both broker dry-run and Hyperliquid submit flows

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

- supervised submit gates, review stubs, and first tightly gated real submit artifacts
- persistent order-status, reconciliation, and supervision artifacts over submitted sessions
- artifact-first health and alert snapshots for Kraken and Hyperliquid submit corridors
- bounded post-submit supervision built around repeated artifacts rather than daemon-first runtime state

Current interpretation:

- `Stage D.2` remains the central QuantLab-owned execution frontier
- it should now be read as a hardening, evidence, and promotion-discipline stage rather than an automatic expansion stage
- the highest-value next steps are evidence-producing and ambiguity-reducing: real artifact runs, tighter runbooks, promotion criteria, and focused fixes on whichever supervised path still fails under realistic use

Exit condition:

- QuantLab can survive operational broker edge cases in a controlled environment

Minimum promotion signals:

- repeated supervised submit sessions can be reconciled without unresolved ambiguous state
- canonical post-submit status and alert artifacts stay current enough to support operator decisions
- restart or resume behavior does not lose pending supervision context for active sessions

## Stage D.3 - Micro-Live Promotion Gate

Status: proposed

Goal:

- validate the supervised execution stack with minimal real exposure before opening broader supervised live operation

Scope:

- smallest-allowed live sizing and explicit venue or strategy allowlists
- manual promotion checklist from `D.2` hardening into real execution
- canonical secret-boundary discipline for live credentials
- canonical alert coverage for submit, reject, fill, and failure-critical states
- immediate stop-on-ambiguity rule when reconciliation or operator visibility is unclear

Exit condition:

- QuantLab has passed a bounded micro-live gate with low-risk real sessions, explicit operator review, canonical alert artifacts, and no unresolved promotion blockers around secrets, reconciliation, or stop control

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

Minimum promotion signals:

- supervised live runs inherit the secret and alert discipline already proven in `D.3`
- operator review, stop control, and auditability remain intact under repeated low-risk live use
- live supervision no longer depends on ad hoc local interpretation to understand order or risk state

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

From the current strategic position, the most rational order is:

1. harden `Stage D.2` supervised broker corridors with real operator evidence, reconciliation discipline, and post-submit clarity
2. continue `Stage C.1` paper-trading polish where it directly improves promotion discipline, runbooks, and paper-to-broker readiness
3. continue the Desktop/UI operator workspace track where it reduces review ambiguity or improves promotion visibility across research, paper, and broker evidence
4. continue `Stage O` producer-side stabilization only where real integration friction requires it
5. harden `Stage O.1` integration fixtures only if consumer feedback justifies them
6. avoid reopening `Stage D.0` / `D.1` as primary stages unless a real hardening gap proves the current boundary insufficient
7. pass an explicit `Stage D.3` micro-live promotion gate before opening `Stage E`
8. only then move into `Stage F` controlled automation

## What Should Not Happen Early

- no direct jump from research success to live automated broker execution
- no live broker work before safety limits and kill-switch behavior exist
- no exchange-specific strategy or risk logic outside `BrokerAdapter`
- no expansion of external orchestration before the paper and safety layers are operationally trustworthy
- no new venue or operator-workspace expansion that is disconnected from credible supervised-corridor evidence
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
