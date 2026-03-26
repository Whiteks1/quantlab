# Hyperliquid Boundary Review

Status: accepted  
Date: 2026-03-26

## Goal

Evaluate whether the current `BrokerAdapter` boundary is sufficient for a future Hyperliquid integration, without adding any Hyperliquid runtime code yet.

## Current Read

The current boundary in [`src/quantlab/brokers/boundary.py`](../src/quantlab/brokers/boundary.py) is strong enough for the first Kraken path, but it is still shaped around a simple CEX-like request model:

- `ExecutionIntent`
- `ExecutionPolicy`
- `ExecutionPreflight`
- `BrokerAdapter.preflight()`
- `BrokerAdapter.build_order_payload()`

That is enough for:

- local execution policy checks
- deterministic payload translation
- dry-run audit generation
- validate-only order checks
- supervised submit discipline

It is not yet expressive enough for a venue like Hyperliquid without adapter-local workarounds.

## What Hyperliquid Pressures

According to the official Hyperliquid docs, the first important pressures on the boundary are:

1. Nonces are tracked per signer, and signer identity changes when using API wallets or agent wallets rather than a master address. Source: [Nonces and API wallets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets)
2. API wallets can sign on behalf of master accounts and subaccounts, while account data queries must still use the actual master or subaccount address. Source: [Nonces and API wallets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets)
3. Subaccounts and vaults do not have private keys and require master-account signing plus a target vault/subaccount address in the request. Source: [Exchange endpoint](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint)
4. WebSocket is a first-class path not only for market data but also as an alternative to HTTP request sending, and automated users are expected to reconnect gracefully. Source: [WebSocket](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket)
5. Rate limits are not only per IP; there are also user/address-based action limits and order limits that materially affect execution architecture. Source: [Rate limits and user limits](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits)

## Where The Current Boundary Already Fits

The current boundary is still good in several important ways:

- a venue-independent `ExecutionIntent` remains the right starting point
- local policy must still decide whether an action is acceptable before any venue-specific signing or submission
- a separate adapter layer is still the right place for venue-specific payload translation
- supervised submit, reconciliation, and operator review remain valid even for an onchain venue

So the right move is not to replace the current boundary.

## Main Gaps

### 1. Signer identity is not modeled explicitly

`ExecutionIntent` currently carries `account_id`, but not the distinction between:

- account being traded
- signer actually producing the signature
- whether the signer is a master wallet or an API/agent wallet

That is acceptable for Kraken, but too narrow for Hyperliquid.

### 2. Subaccount / vault routing is not a first-class concept

The current intent has no explicit concept for:

- master account
- subaccount or vault target
- execution on behalf of another address under the same authority

Today that would end up hidden in adapter-specific fields, which would weaken the shared contract.

### 3. Nonce strategy is outside the contract

For Kraken this is fine.

For Hyperliquid, nonce management is part of execution correctness.
The current boundary has no place to express:

- signer-scoped nonce source
- batch-safe nonce generation
- expiry windows such as `expiresAfter`

This does not mean nonce logic should live in `ExecutionIntent`, but it does mean the boundary needs a clearer place for signer/runtime execution metadata.

### 4. The contract is request/payload oriented, not session/transport aware

`build_order_payload()` assumes a simple one-shot translation step.
Hyperliquid pushes toward:

- REST and WebSocket coexistence
- reconnect-aware execution flows
- batching and post-message transport semantics

The current boundary can still survive this, but it should stop implying that one payload build equals one sufficient transport abstraction.

### 5. Rate-limit shape is too venue-local today

The local policy covers notional and symbol constraints, but nothing in the boundary acknowledges venue-level execution constraints such as:

- address-based request budgets
- websocket connection budgets
- batch-size tradeoffs

These should remain venue-specific, but the architecture should explicitly allow adapters to surface readiness limits in a normalized way.

## Minimal Contract Direction

Before Hyperliquid runtime work, the smallest coherent next step is:

1. keep `BrokerAdapter` as the current name
2. preserve `ExecutionIntent` as the strategy-facing intent
3. add a small execution-context layer rather than overload `ExecutionIntent`

That future execution-context layer should be able to express at least:

- `execution_account_id`
- `signer_id`
- `signer_type`
  - for example `direct`, `api_wallet`, `agent_wallet`
- `routing_target`
  - for example `account`, `subaccount`, `vault`
- optional `expires_after`
- optional `transport_preference`
  - for example `rest`, `websocket`, `either`

This would let QuantLab adapt to Hyperliquid without turning the core intent model into a venue-specific object.

## Recommendation

The next Hyperliquid-related slice should not be runtime integration yet.

It should be a narrow contract slice that:

- introduces or designs an execution-context layer
- leaves Kraken behavior working as-is
- does not rename the existing adapter family yet
- keeps the change reversible

## Non-goals

- no Hyperliquid runtime integration in this document
- no rename of `BrokerAdapter`
- no websocket execution implementation yet
- no subaccount or vault implementation yet

## Related Documents

- [execution-venue-strategy.md](./execution-venue-strategy.md)
- [broker-safety-boundary.md](./broker-safety-boundary.md)
- [roadmap.md](./roadmap.md)
