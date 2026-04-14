# Current State - QuantLab

## Active Stage
- **Stage**: Stage D.2 — Supervised Broker Submit Safety
- **Last Updated**: 2026-04-14
- **Focus**: Stage D.2 has now closed the main ambiguity around supervised Hyperliquid submit, especially idempotency, reconciliation, and post-submit operator safety. The remaining posture is residual hardening by evidence, not broadening execution by default.
- **Authority Note**: Stepbit-facing integration remains a secondary boundary track. QuantLab stays autonomous and external consumer needs do not override QuantLab-owned priorities.
- **Signal Intake Note**: Quant Pulse is an upstream signal layer, not a controller. QuantLab should only consume Quant Pulse output when it can be translated into a research intent, risk filter, or product priority.
- **Product Identity Note**: Publicly, QuantLab should now be described as a `web3 app` in direction, but still as a supervised and safety-first execution system in current maturity.
- **Performance Note**: QuantLab remains Python-first. Native acceleration is now treated as a measured hotspot tactic, with the backtest engine as the first realistic candidate if profiling justifies escalation.

## Document Role and Maintenance Policy

- `current-state.md` is a **curated operational snapshot**, not a live Git inventory of every local branch, worktree, or transient CI state.
- It is authoritative for:
  - active stage and current product/system posture
  - repo-level priorities that should guide the next slices
  - the current interpretation of canonical direction across roadmap, integration, and execution work
- It is **not** authoritative for:
  - exact local branch lists
  - exact local worktree posture on a specific machine
  - ephemeral PR/check state
- Minimum maintenance rule:
  - update this file after structural merges that change active stage, repo-level priority, or document authority
  - do not store machine-specific branch or worktree inventories here unless they are intentionally temporary and date-bounded
  - use live `git` state for sanitation decisions, not this file alone

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
- **Stage Open**: Stage D.2 remains the active execution-safety stage, but it has moved from broad ambiguity closure into residual hardening and monitoring.
- **Current Priority**: Hold the first supervised Hyperliquid submit path narrow and auditable; only open new D.2 slices when a concrete operator-safety gap is demonstrated.
- **Parallel Track Note**: Desktop/UI now exists as an explicit operator-workspace track that should improve evidence review and promotion visibility without replacing engine authority.
- **Active Focus Areas**:
  - keep broker execution auditable before any broader live routing or retry logic
  - preserve paper-session discipline as a prerequisite, not the current bottleneck
  - keep Hyperliquid as the active execution boundary while positioning Kraken as legacy compatibility and Hyperliquid as the first next venue intended for personal connection
  - treat Bitget as a later optional comparison venue after Hyperliquid, not a current priority
  - Quant Pulse intake is valid only when it improves research, validation, or product priorities
  - review whether the current boundary can express Hyperliquid signer, wallet, routing, and websocket semantics without ad hoc adapter leaks
  - keep the first Hyperliquid supervised submit path intentionally narrow and auditable before adding richer session, status, or websocket execution work
  - prefer operator-visible hardening and regression coverage over new execution breadth
- **Implemented Direction**:
  - canonical run artifacts now center on `metadata.json`, `config.json`, `metrics.json`, and `report.json`
  - successful plain `run` executions now write that canonical artifact pack under `outputs/runs/<run_id>/`
  - legacy `meta.json` / `run_report.json` remain read-compatible only
  - machine-facing `run` and `sweep` outputs are exposed through canonical `report.json.machine_contract`
  - the package now owns the primary CLI app under `src/quantlab/app.py`, while root `main.py` remains a compatibility bootstrap
  - `quantlab --version` and `main.py --version` both return a stable CLI version string
  - `quantlab --check` and `main.py --check` both return a deterministic JSON health summary for runtime preflight
  - the packaged CLI app now also has extracted helpers for parser construction, JSON request overlay, session-mode inference, and dispatch ordering, with dedicated CLI helper modules now carrying most of that routing shape instead of `src/quantlab/app.py` alone
  - the CLI keeps the existing `--json-request` `sweep` path as the smoke-validation surface
  - the shared `runs_index.csv/json/md` registry is refreshed automatically after successful run-producing commands
  - paper-backed `run` executions now write dedicated artifacts under `outputs/paper_sessions/<session_id>/`
  - paper sessions persist `session_metadata.json` and `session_status.json`
  - external signal mode for paper-backed `run` remains `run` to preserve contract stability
  - public operator guidance for paper sessions now lives in `docs/paper-session-runbook.md`
  - paper sessions now support a shared index surface under `outputs/paper_sessions/paper_sessions_index.*`
  - paper sessions now also support a broker-promotion report that highlights sessions ready to bridge toward the broker boundary
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
  - canonical Hyperliquid submit sessions now reject duplicate replay once a persisted submit response already exists
  - Hyperliquid submit sessions can now also materialize `hyperliquid_order_status.json` with normalized post-submit state from direct `orderStatus` queries
  - Hyperliquid submit sessions can now also materialize `hyperliquid_reconciliation.json` so ambiguous post-submit states can be reconciled against direct status, historical-order, open-order, and fill surfaces with richer fill/close-state detail
  - Hyperliquid submit sessions can now also materialize `hyperliquid_fill_summary.json` for richer post-submit fill accounting, fee totals, and closed-PnL visibility as a separate artifact beside broader supervision
  - Hyperliquid submit sessions can now also materialize `hyperliquid_supervision.json` for bounded continuous supervision with websocket-aware monitoring metadata plus refreshed status, reconciliation, and fill-summary artifacts
  - Hyperliquid submit sessions can now also materialize `hyperliquid_cancel_response.json` as a first supervised cancel boundary with explicit reviewer confirmation
  - Hyperliquid submit sessions now also support aggregate health summaries and deterministic alert snapshots for operator visibility
  - ambiguous Hyperliquid submit acknowledgements that return no `oid` and no `cloid` now escalate explicitly to `reconciliation_required` with a dedicated critical alert instead of looking like normal `submitted_remote`
  - Hyperliquid status refresh now preserves known reconciliation truth instead of degrading canonical session state when a fresh `orderStatus` probe is still `unknown`
  - aggregate Hyperliquid health and submit indexes now surface `reconciliation_required` sessions and `submitted_remote_identifier_missing` counts explicitly
  - aggregate Hyperliquid `latest_alert_*` selection now uses explicit urgency precedence, with regression coverage locking representative critical-state ordering across reconciliation, cancel, and submit branches
  - Hyperliquid boundary review now documents the main contract gaps around signer identity, API wallets, subaccounts/vaults, and websocket-first venue interaction
  - native acceleration strategy now documents `Numba` as the first acceleration experiment and the backtest engine as the first realistic hotspot candidate before any broader `C++` or `Rust` move
  - a local backtest profiling surface now exists to measure the Python engine before any `Numba` or native extraction work
  - the backtest engine now also has an optional `Numba` pilot backend for the extracted inner loop while keeping Python as the default path
  - the pre-trade subsystem now has an explicit boundary ADR: the calculator may act as an upstream workbench, but QuantLab remains the owner of policy, draft execution bridging, and all execution authority
  - QuantLab now also has a bounded intake for `calculadora_riego_trading` handoff artifacts, validating external machine contracts and required context before any future draft execution bridging
  - QuantLab now also has a deterministic broker evidence readiness artifact so the first supervised broker evidence pass can fail early on secrets, identity inputs, or corridor selection before any live execution attempt


## Known Issues / Technical Debt

- The canonical machine-facing contract is now shared by `run` and `sweep`, but downstream consumers may still carry old assumptions about `run` using only top-level `summary` / `kpi_summary`.

## Repository and Workspace Posture

- `origin/main` remains the authoritative integration branch.
- Repo sanitation, stale worktree cleanup, and post-merge branch hygiene should be decided from live Git state, not from frozen inventories in this file.
- Governance and workflow authority now lives in:
  - `.agents/workflow.md` for execution rules
  - `docs/roadmap.md` for product/system direction
  - issue-driven sanitation slices for machine-specific cleanup when needed

## Validation and Coverage Posture

- Validation should be recorded in issue/PR/session continuity for the slice that actually ran it.
- This file may summarize stable coverage posture at a high level, but it should not pretend to be the current source of truth for transient check status on a specific branch.
