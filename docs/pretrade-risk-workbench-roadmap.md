# Pre-Trade Risk Workbench Roadmap

Status: proposed
Date: 2026-03-27

## Goal

Add the trading risk calculator into the QuantLab ecosystem as an auxiliary
pre-trade and risk-planning tool, not as part of the central backtest or
execution engine.

The target product shape is:

- QuantLab remains the sovereign CLI-first research and execution system
- the calculator evolves into a reusable pre-trade workbench
- the workbench produces deterministic artifacts that QuantLab can consume
- the UI remains an optional operator surface, never the owner of policy

## Core Position

This integration should not place calculator logic inside:

- `backtest`
- `strategies`
- `execution`
- venue adapters

Instead, it should introduce a bounded auxiliary subsystem:

- `pretrade`

This subsystem should sit beside QuantLab's main research and execution flow and
support operator decisions before paper or broker-facing actions occur.

## Product Definition

Recommended product name:

- `QuantLab Pre-Trade Risk Workbench`

Recommended responsibility:

- size a position from capital, risk percent, entry, stop, and target
- estimate fees and slippage impact
- validate pre-trade policy assumptions before submit
- generate deterministic trade-plan artifacts
- optionally derive a draft `ExecutionIntent`, but never submit directly

## Architectural Rules

### 1. CLI-first

The workbench must be invokable through QuantLab's CLI and/or machine-facing
request surface.

### 2. Artifact-first

The canonical output should be a pre-trade artifact directory, not UI state.

Suggested root:

```text
outputs/pretrade_sessions/<session_id>/
```

Suggested files:

```text
outputs/pretrade_sessions/<session_id>/
  input.json
  plan.json
  summary.json
  plan.md
```

### 3. Read-only or bounded UI

The UI may:

- visualize plans
- compare scenarios
- browse saved artifacts
- show policy rejection reasons

The UI must not:

- own risk policy
- decide execution authority
- submit directly to venue adapters

### 4. Reversible integration

QuantLab should consume the workbench through narrow contracts that remain
useful even if the UI or calculator implementation changes later.

## Suggested Machine Contract

Recommended contract marker:

```text
contract_type = "quantlab.pretrade.plan"
```

Suggested minimum fields:

- `session_id`
- `symbol`
- `venue`
- `side`
- `entry_price`
- `stop_price`
- `target_price`
- `risk_amount`
- `risk_percent`
- `position_size`
- `estimated_fees`
- `estimated_slippage`
- `notional`
- `policy_checks`
- `draft_execution_intent`

## Ownership Split

QuantLab should own:

- the `pretrade` package
- CLI entrypoints
- artifact writing and validation
- safety-boundary bridging into `ExecutionPolicy` and `ExecutionIntent`

The calculator repository should own:

- operator-friendly scenario planning UX
- reusable risk-calculation logic
- fixture parity with any alternate runtime implementations
- export surfaces that are convenient for QuantLab ingestion

## What Not To Do

Do not:

- merge this into the backtest engine
- treat the calculator as the owner of execution policy
- let the UI become the path that governs broker submission
- use this feature to bypass the broker safety boundary

## Delivery Phases

### Phase 1 - Roadmap and boundary definition

- publish this roadmap
- define the product boundary
- align follow-up issues across QuantLab and calculator repos

### Phase 2 - Pre-trade package and canonical artifacts

- add `src/quantlab/pretrade/`
- implement deterministic plan generation
- persist canonical artifact directories under `outputs/pretrade_sessions/`

### Phase 3 - Safety-boundary bridge

- convert pre-trade plans into draft `ExecutionIntent`
- validate them against `ExecutionPolicy`
- surface deterministic rejection reasons before adapter interaction

### Phase 4 - Bounded UI surface

- expose artifact browsing and scenario comparison in `research_ui`
- keep the surface read-only or narrowly bounded
- preserve QuantLab CLI and core as the authority

## Success Condition

QuantLab gains a useful pre-trade planning subsystem that improves operator
discipline and execution readiness without turning the calculator or UI into the
center of the product.
