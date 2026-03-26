# Broker Safety Boundary

This document defines the first Stage D.0 execution safety boundary for QuantLab.

It is intentionally small.

The goal is not to connect a real broker yet.
The goal is to make future broker work pass through a local QuantLab-owned safety contract first.

## Scope

Stage D.0 currently defines:

- `ExecutionIntent`: normalized broker-bound order intent
- `ExecutionContext`: optional signer/routing/transport execution metadata
- `ExecutionPolicy`: local safety policy for execution approval
- `ExecutionPreflight`: deterministic allow/reject result
- `BrokerAdapter`: broker-agnostic adapter contract

For continuity, the code still uses the name `BrokerAdapter`.
Architecturally, it should now be read as an execution-venue boundary, not only a traditional CEX broker boundary.

## Architectural Rule

Strategies, risk policy, and execution safety must depend on `BrokerAdapter`, never on exchange-specific code.

This means:

- no strategy should talk directly to Kraken, Binance, or any other exchange client
- the same rule should eventually hold for venue types such as Hyperliquid as well
- no exchange-specific risk checks should become the primary safety authority
- no broker dry-run integration should happen before local preflight exists

## Current Safety Checks

The Stage D.0 preflight currently rejects execution intent when:

- the kill switch is active
- `account_id` is missing and policy requires it
- quantity is not positive
- notional is not positive
- order notional exceeds policy limit
- symbol is outside the allowed policy universe
- side is not supported

## What This Boundary Is For

This boundary is meant to be the local gate that future integrations must cross before any broker-specific payload is built or any API call is made.

In practical terms:

1. QuantLab produces an `ExecutionIntent`
2. QuantLab validates it against `ExecutionPolicy`
3. only approved intent may proceed to a concrete adapter
4. exchange-specific adapters then translate validated intent into broker payloads

## What This Boundary Is Not

- not a Kraken integration
- not a Binance integration
- not a CCXT integration
- not live order routing
- not credential wiring
- not a control-plane UI

## Dry-Run Adapter Status

The first concrete dry-run backend now exists as:

- `KrakenBrokerAdapter`

The next architecture pressure now documented for this boundary is Hyperliquid-style venue support, especially around signer identity, API wallets, subaccounts/vaults, and websocket-first execution semantics.

Current Stage D.1 scope covered:

- shared preflight validation through the Stage D.0 boundary
- minimal `ExecutionContext` support in the shared boundary so future venue work can model signer and routing concerns without overloading `ExecutionIntent`
- read-only Hyperliquid venue preflight with execution-context resolution over signer identity, routing target, transport preference, and nonce scope
- read-only Hyperliquid account/signer readiness with role resolution and account-visibility checks before any future signed action work
- local Hyperliquid action and signature-envelope artifacts with resolved nonce and `expiresAfter`
- local Hyperliquid signer backend integration for real L1 action signing, still without submit
- deterministic Kraken-style payload translation
- read-only Kraken public preflight probes for pair support and basic readiness
- read-only Kraken authenticated preflight probes for private boundary readiness
- read-only Kraken account snapshot and balance-aware intent readiness
- Kraken validate-only order probes for exchange-side order acceptance checks
- canonical broker order-validation sessions and shared registry under `outputs/broker_order_validations/`
- local human approval artifacts for reviewed broker order-validation sessions
- local pre-submit bundles generated only from approved validation sessions
- local supervised submit gate artifacts generated only from pre-submit bundles
- local supervised submit stub artifacts generated only from submit gates
- first real supervised submit response artifacts generated only from previously validated sessions that already have a supervised submit gate and explicit live confirmation
- Kraken submit reconciliation over canonical broker order-validation sessions using stable session-derived `userref`
- persistent post-submit order status artifacts for broker order-validation sessions
- broker submission health summaries and alert snapshots over canonical broker order-validation sessions
- stable dry-run audit snapshot for local review
- local `broker_dry_run.json` artifact generation through the CLI
- canonical broker dry-run sessions and shared registry under `outputs/broker_dry_runs/`

Still intentionally out of scope:

- websocket/private stream handling
- live credential wiring
- live order routing

Boundary note:

- validate-only order probes are more sensitive than read-only preflight because they use Kraken's order-validation path, but they still do not place live orders
- approval artifacts are a local QuantLab gate only; they do not submit anything to Kraken by themselves
- pre-submit bundles are the final local handoff artifact before any future supervised submit path, but they still do not submit anything by themselves
- supervised submit gate artifacts are the final local confirmation step before any future submit implementation, but they still do not submit anything by themselves
- supervised submit stub artifacts are the first operational shape of a future submit path, but they still remain local and do not hit the broker
- supervised real-submit response artifacts are the first intentionally narrow path that can hit Kraken's real order endpoint, and they still require explicit confirmation plus a previously validated source session
- reconciliation is now the required safety path for ambiguous submit states before any future retry logic is introduced
- persistent order-status refresh is now the first operator-facing post-submit visibility layer before any future continuous supervision or cancel flow
- broker submission health and alerts are local operator surfaces only; they summarize risky states but do not trigger broker-side actions by themselves

## Next Step

After this submit-safety slice is stable, the next logical implementation step is:

- deeper post-submit supervision such as cancel boundaries and richer order-state reconciliation behind the same boundary

## Related Documents

- [roadmap.md](./roadmap.md)
- [execution-context-layer.md](./execution-context-layer.md)
- [execution-venue-strategy.md](./execution-venue-strategy.md)
- [hyperliquid-boundary-review.md](./hyperliquid-boundary-review.md)
- [paper-session-runbook.md](./paper-session-runbook.md)
- [quantlab-stepbit-boundaries.md](./quantlab-stepbit-boundaries.md)
