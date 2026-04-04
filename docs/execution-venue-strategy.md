# Execution Venue Strategy

Status: accepted  
Date: 2026-03-26

## Decision

QuantLab keeps `Hyperliquid` as the active execution venue direction.

`Kraken` remains implemented compatibility/history and can still serve as a reference backend, but it is no longer the active next target.

This means:

- `Hyperliquid` is the venue used to prove the active safety boundary, validation flow, submit discipline, and reconciliation model
- `Kraken` remains a reference implementation and compatibility boundary
- `Binance` is no longer the default next comparison venue ahead of `Hyperliquid`
- the current code name `BrokerAdapter` stays in place for continuity, but the architecture should be read as an `execution venue` boundary, not only a centralized-exchange broker boundary

## Why This Decision Exists

The first implemented backend and the first venue worth using personally do not need to be the same thing.

`Hyperliquid` is the active implementation target because it is the boundary the project is currently using to prove:

- local execution policy
- authenticated preflight
- validate-only order checks
- supervised submit safety
- reconciliation and post-submit state tracking

`Kraken` remains a useful reference boundary, but it is not the active next target.

According to the official documentation, Hyperliquid is a performant L1 built around a fully onchain financial system, with HyperCore and HyperEVM secured by HyperBFT. HyperCore includes fully onchain spot and perpetual order books where orders, cancels, trades, and liquidations happen with one-block finality, and the docs state current support for up to 200k orders per second. Source: [About Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs).

For automated trading, the official developer docs make several properties especially relevant:

- WebSocket and API endpoints are documented for mainnet and testnet: [WebSocket](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket), [Exchange endpoint](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint)
- nonces are designed for high-frequency onchain order flow, not Ethereum-style sequential transaction ordering: [Nonces and API wallets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets)
- API wallets / agent wallets are first-class and can sign on behalf of master accounts and subaccounts: [Nonces and API wallets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets)
- rate limits are explicit and infrastructure-relevant, including REST weight limits, websocket caps, and per-user order constraints: [Rate limits and user limits](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits)
- builder-fee support exists onchain for products that monetize routed order flow: [Builder codes](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/builder-codes)

That combination makes Hyperliquid materially different from a standard CEX adapter comparison.

## Architectural Interpretation

The architectural lesson is not "delete all historical Kraken work."

The lesson is:

- `Hyperliquid` is the active safety proving ground
- `Kraken` remains a compatibility/reference boundary

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

1. keep Hyperliquid as the active backend focus and finish its submit-safety boundary cleanly
2. do not rename `BrokerAdapter` in code yet just for terminology
3. update architecture and roadmap language so it is clear that this boundary is really an execution-venue boundary
4. keep `Kraken` as compatibility/reference and move `Hyperliquid` ahead of `Binance` as the next venue target for real personal connection and future comparison work
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
