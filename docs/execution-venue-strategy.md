# Execution Venue Strategy

Status: accepted  
Date: 2026-03-26

## Decision

QuantLab keeps `Kraken` as the first implemented real-execution backend.

At the same time, `Hyperliquid` becomes the first venue intended for personal connection and supervised practical use once the execution boundary is ready for that step.

This means:

- `Kraken` remains the first backend used to prove the safety boundary, validation flow, submit discipline, and reconciliation model
- `Hyperliquid` becomes the first next venue to target for real personal use
- `Binance` is no longer the default next comparison venue ahead of `Hyperliquid`
- the current code name `BrokerAdapter` stays in place for continuity, but the architecture should be read as an `execution venue` boundary, not only a centralized-exchange broker boundary

## Why This Decision Exists

The first implemented backend and the first venue worth using personally do not need to be the same thing.

`Kraken` is still a strong first implementation target because it is a disciplined and familiar boundary for:

- local execution policy
- authenticated preflight
- validate-only order checks
- supervised submit safety
- reconciliation and post-submit state tracking

But for actual personal connection and future execution design, `Hyperliquid` is strategically more interesting.

According to the official documentation, Hyperliquid is a performant L1 built around a fully onchain financial system, with HyperCore and HyperEVM secured by HyperBFT. HyperCore includes fully onchain spot and perpetual order books where orders, cancels, trades, and liquidations happen with one-block finality, and the docs state current support for up to 200k orders per second. Source: [About Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs).

For automated trading, the official developer docs make several properties especially relevant:

- WebSocket and API endpoints are documented for mainnet and testnet: [WebSocket](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket), [Exchange endpoint](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint)
- nonces are designed for high-frequency onchain order flow, not Ethereum-style sequential transaction ordering: [Nonces and API wallets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets)
- API wallets / agent wallets are first-class and can sign on behalf of master accounts and subaccounts: [Nonces and API wallets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets)
- rate limits are explicit and infrastructure-relevant, including REST weight limits, websocket caps, and per-user order constraints: [Rate limits and user limits](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits)
- builder-fee support exists onchain for products that monetize routed order flow: [Builder codes](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/builder-codes)

That combination makes Hyperliquid materially different from a standard CEX adapter comparison.

## Architectural Interpretation

The architectural lesson is not "replace Kraken."

The lesson is:

- `Kraken` is the first safety proving ground
- `Hyperliquid` is the first next venue that tests whether the QuantLab boundary is genuinely venue-agnostic

If the current `BrokerAdapter` only feels natural for CEX-style REST brokers, then the abstraction is still too narrow.
If it can also support:

- signer-scoped nonces
- agent wallets / API wallets
- subaccounts or vault-style routing
- websocket-first market data and execution feedback
- onchain order-book semantics

then the abstraction is becoming strong enough for the direction QuantLab actually wants.

## Practical Consequences

For roadmap and implementation sequencing:

1. keep Kraken as the first implemented backend and finish its submit-safety boundary cleanly
2. do not rename `BrokerAdapter` in code yet just for terminology
3. update architecture and roadmap language so it is clear that this boundary is really an execution-venue boundary
4. move `Hyperliquid` ahead of `Binance` as the next venue target for real personal connection and future comparison work
5. treat `Binance` as optional later comparison work, not the default second venue

## What This Does Not Mean

- it does not mean Hyperliquid runtime integration is being added in this document
- it does not mean Kraken work was a mistake
- it does not mean QuantLab should jump immediately into a new venue before closing safety gaps
- it does not mean compliance, regulatory, or operational constraints disappear because a venue is onchain

## Related Documents

- [README.md](../README.md)
- [roadmap.md](./roadmap.md)
- [broker-safety-boundary.md](./broker-safety-boundary.md)
