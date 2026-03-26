# Execution Context Layer

Status: accepted  
Date: 2026-03-26

## Goal

Add a minimal execution-context layer beside `ExecutionIntent` so QuantLab can model Hyperliquid-style venue semantics without overloading the core strategy-facing intent object.

## What Was Added

The Stage D.0 boundary now includes `ExecutionContext` in code.

It currently models:

- `execution_account_id`
- `signer_id`
- `signer_type`
- `routing_target`
- `transport_preference`
- `expires_after`
- `nonce_hint`

The current allowed shape is intentionally small:

- `signer_type`
  - `direct`
  - `api_wallet`
  - `agent_wallet`
- `routing_target`
  - `account`
  - `subaccount`
  - `vault`
- `transport_preference`
  - `rest`
  - `websocket`
  - `either`

## Why This Exists

`ExecutionIntent` is still the right place for venue-agnostic trading intent:

- symbol
- side
- quantity
- notional
- strategy identity

But a venue like Hyperliquid adds other concerns that are not purely strategy intent:

- signer identity may differ from the traded account
- API wallets or agent wallets may sign on behalf of another address
- routing may target a subaccount or vault rather than the signer directly
- websocket-first transport preferences may matter
- expiry windows such as `expiresAfter` may be execution metadata rather than strategy metadata
- signer-scoped nonce hints may need to live beside routing metadata rather than inside strategy intent

Those pressures should not be hidden inside one venue adapter as undocumented local fields.

## What This Does Not Do Yet

This layer is intentionally minimal.

It does not yet:

- add Hyperliquid runtime integration
- change Kraken behavior
- introduce websocket execution logic
- implement nonce management
- enforce routing or signer validation rules

## Current Architectural Meaning

The current boundary should now be read as:

1. `ExecutionIntent` carries strategy-facing order intent
2. `ExecutionContext` carries execution-venue-specific signer and routing context
3. local policy still decides whether the action is acceptable
4. adapters may then translate both intent and context into venue-specific transport or payload behavior

## Why Kraken Still Works Unchanged

Kraken can ignore `ExecutionContext` for now.

That is expected and desirable.
The point of this slice is not to make Kraken more complex, but to stop the shared contract from being too CEX-shaped before Hyperliquid runtime work starts.

## Next Step

The next Hyperliquid-related runtime slice should build on this layer by deciding:

- which parts of `ExecutionContext` remain adapter-agnostic
- which parts need venue-local validation
- where signer-scoped nonce handling should live

## Related Documents

- [broker-safety-boundary.md](./broker-safety-boundary.md)
- [execution-venue-strategy.md](./execution-venue-strategy.md)
- [roadmap.md](./roadmap.md)
