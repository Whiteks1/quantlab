# Current State - QuantLab

## Active Stage
- **Stage**: Stage D.2 — Supervised Broker Submit Safety
- **Last Updated**: 2026-03-27
- **Focus**: Stage D.2 is centered on closing ambiguity around supervised Kraken submit, especially idempotency, reconciliation, and post-submit operator safety.
- **Authority Note**: Stepbit-facing integration remains a secondary boundary track. QuantLab stays autonomous and external consumer needs do not override QuantLab-owned priorities.
- **Product Identity Note**: Publicly, QuantLab should now be described as a `web3 app` in direction, but still as a supervised and safety-first execution system in current maturity.
- **Performance Note**: QuantLab remains Python-first. Native acceleration is now treated as a measured hotspot tactic, with the backtest engine as the first realistic candidate if profiling justifies escalation.

## Completed/Planned Stages

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
| M.3 | Portfolio Selection / Session Inclusion Rules | ✅ Done |
| M.4 | Portfolio Mode Comparison | ✅ Done |
| N | Run Lifecycle Management (`quantlab runs`) | ✅ Done |
| C.1 | Paper Trading Operationalization | 🟨 In Progress |
| O | Stepbit Automation Readiness (I/O & CLI Stability) | 🟨 In Progress |

## Active Work
- **Stage Open**: Stage D.2 is now the primary execution-safety focus.
- **Current Priority**: Close ambiguous-submit risk before widening broker execution beyond the first supervised Kraken submit path.
- **Active Focus Areas**:
  - make the first supervised broker submit path idempotency-safer
  - reconcile ambiguous submit states against real Kraken order state
  - add aggregate health and alert visibility over canonical broker submission sessions
  - keep broker execution auditable before any broader live routing or retry logic
  - preserve paper-session discipline as a prerequisite, not the current bottleneck
  - keep Kraken as the first implemented execution boundary while positioning Hyperliquid as the first next venue intended for personal connection
  - review whether the current boundary can express Hyperliquid signer, wallet, routing, and websocket semantics without ad hoc adapter leaks
  - keep the first Hyperliquid supervised submit path intentionally narrow and auditable before adding richer session, status, or websocket execution work
  - add local operator visibility over canonical Hyperliquid submit sessions before widening execution further
- **Implemented Direction**:
  - canonical run artifacts now center on `metadata.json`, `config.json`, `metrics.json`, and `report.json`
  - successful plain `run` executions now write that canonical artifact pack under `outputs/runs/<run_id>/`
  - legacy `meta.json` / `run_report.json` remain read-compatible only
  - machine-facing `run` and `sweep` outputs are exposed through canonical `report.json.machine_contract`
  - `main.py --version` returns a stable CLI version string
  - `main.py --check` returns a deterministic JSON health summary for runtime preflight
  - the CLI keeps the existing `--json-request` `sweep` path as the smoke-validation surface
  - the shared `runs_index.csv/json/md` registry is refreshed automatically after successful run-producing commands
  - paper-backed `run` executions now write dedicated artifacts under `outputs/paper_sessions/<session_id>/`
  - paper sessions persist `session_metadata.json` and `session_status.json`
  - external signal mode for paper-backed `run` remains `run` to preserve contract stability
  - public operator guidance for paper sessions now lives in `docs/paper-session-runbook.md`
  - paper sessions now support a shared index surface under `outputs/paper_sessions/paper_sessions_index.*`
  - Stage D.0 now has an initial broker-agnostic safety boundary in `src/quantlab/brokers/boundary.py`
  - Stage D.1 now has a first dry-run `KrakenBrokerAdapter` built on that boundary
  - Kraken dry-run can now materialize a local `broker_dry_run.json` audit artifact
  - broker dry-run now supports canonical sessions and a shared registry under `outputs/broker_dry_runs/`
  - Kraken preflight can now materialize a read-only public `broker_preflight.json` artifact
  - Kraken auth preflight can now materialize a read-only private `broker_auth_preflight.json` artifact
  - Kraken account readiness can now materialize a read-only `broker_account_snapshot.json` artifact with balance-aware intent readiness
  - Kraken validate-only probes can now materialize `broker_order_validate.json` without placing a live order
  - broker order validation now supports canonical sessions and a shared registry under `outputs/broker_order_validations/`
  - broker order validation sessions now support local approval artifacts as an explicit human gate
  - approved broker order validation sessions can now materialize `broker_pre_submit_bundle.json` as the final local handoff artifact before any future supervised submit path
  - pre-submit bundles can now materialize `broker_submit_gate.json` as the final local supervised confirmation step before any future submit implementation
  - submit gates can now materialize `broker_submit_attempt.json` in `stub` mode as the first operational shape of a future supervised submit path
  - supervised submit gates can now materialize `broker_submit_response.json` as the first tightly gated real Kraken submit artifact, including remote submit status and returned `txid` values where available
  - broker submit now writes a pending local response artifact before the remote submit path and supports explicit reconciliation against Kraken order state using session-derived `userref`
  - submitted broker validation sessions can now materialize `broker_order_status.json` as the first persistent post-submit status surface with normalized local state
  - broker submission sessions now support aggregate health summaries and deterministic alert snapshots for operator visibility
  - execution-venue strategy now keeps `Kraken` as the first implemented backend while moving `Hyperliquid` ahead of `Binance` as the first next venue intended for personal supervised use
  - Stage D.0 now also exposes a minimal `ExecutionContext` layer beside `ExecutionIntent` for signer identity, routing target, transport preference, and expiry metadata
  - Hyperliquid now has a first read-only venue preflight slice that resolves signer/routing context and checks `meta` / `spotMeta` / `allMids` without opening order placement work
  - Hyperliquid now also has a read-only account/signer readiness artifact that checks role resolution and basic execution-account visibility before any future signed action path
  - Hyperliquid now also has a local action/signature-envelope build surface with resolved nonce and `expiresAfter`
  - Hyperliquid signer backend integration can now produce a real local L1 action signature while still leaving submit for a later slice
  - Hyperliquid signed-action artifacts can now also drive a first supervised submit path that materializes `hyperliquid_submit_response.json` with explicit reviewer confirmation and exchange response capture
  - Hyperliquid supervised submit can now also materialize canonical local submit sessions and a shared index under `outputs/hyperliquid_submits/`
  - Hyperliquid submit sessions can now also materialize `hyperliquid_order_status.json` with normalized post-submit state from direct `orderStatus` queries
  - Hyperliquid submit sessions now also support aggregate health summaries and deterministic alert snapshots for operator visibility
  - Hyperliquid boundary review now documents the main contract gaps around signer identity, API wallets, subaccounts/vaults, and websocket-first venue interaction
  - native acceleration strategy now documents `Numba` as the first acceleration experiment and the backtest engine as the first realistic hotspot candidate before any broader `C++` or `Rust` move
  - a local backtest profiling surface now exists to measure the Python engine before any `Numba` or native extraction work
  - the backtest engine now also has an optional `Numba` pilot backend for the extracted inner loop while keeping Python as the default path
  - the pre-trade subsystem now has an explicit boundary ADR: the calculator may act as an upstream workbench, but QuantLab remains the owner of policy, draft execution bridging, and all execution authority


## Known Issues / Technical Debt
- Duplicate workflow files in `.agents/workflows/`: `strategy-research.md` vs `strategy_research.md` — the underscore version is stale.
- The canonical machine-facing contract is now shared by `run` and `sweep`, but downstream consumers may still carry old assumptions about `run` using only top-level `summary` / `kpi_summary`.
