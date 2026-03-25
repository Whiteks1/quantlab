# Broker Safety Boundary

This document defines the first Stage D.0 execution safety boundary for QuantLab.

It is intentionally small.

The goal is not to connect a real broker yet.
The goal is to make future broker work pass through a local QuantLab-owned safety contract first.

## Scope

Stage D.0 currently defines:

- `ExecutionIntent`: normalized broker-bound order intent
- `ExecutionPolicy`: local safety policy for execution approval
- `ExecutionPreflight`: deterministic allow/reject result
- `BrokerAdapter`: broker-agnostic adapter contract

## Architectural Rule

Strategies, risk policy, and execution safety must depend on `BrokerAdapter`, never on exchange-specific code.

This means:

- no strategy should talk directly to Kraken, Binance, or any other exchange client
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

Current Stage D.1 scope covered:

- shared preflight validation through the Stage D.0 boundary
- deterministic Kraken-style payload translation
- read-only Kraken public preflight probes for pair support and basic readiness
- read-only Kraken authenticated preflight probes for private boundary readiness
- read-only Kraken account snapshot and balance-aware intent readiness
- stable dry-run audit snapshot for local review
- local `broker_dry_run.json` artifact generation through the CLI
- canonical broker dry-run sessions and shared registry under `outputs/broker_dry_runs/`

Still intentionally out of scope:

- real Kraken HTTP calls
- websocket/private stream handling
- live credential wiring
- live order routing

## Next Step

After this dry-run adapter slice is stable, the next logical implementation step is:

- richer authenticated account capability checks and, only after that, more sensitive broker connectivity work behind the same boundary

## Related Documents

- [roadmap.md](./roadmap.md)
- [paper-session-runbook.md](./paper-session-runbook.md)
- [quantlab-stepbit-boundaries.md](./quantlab-stepbit-boundaries.md)
