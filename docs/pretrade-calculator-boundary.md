# QuantLab Pre-Trade Calculator Boundary

Status: accepted
Date: 2026-03-27

## Decision

`calculadora_riego_trading` may support QuantLab as an upstream pre-trade
workbench, but it must remain a bounded auxiliary tool.

The integration rule is:

- the calculator proposes
- QuantLab validates
- QuantLab decides
- QuantLab executes

This boundary exists so the calculator can evolve independently without turning
into an accidental owner of QuantLab core behavior.

## Why this boundary is needed

QuantLab is now large enough that a useful adjacent tool can create real value
and real architectural risk at the same time.

The calculator is useful because it can improve:

- position sizing discipline
- fee and slippage awareness
- operator review before paper or broker-facing work
- deterministic pre-trade planning artifacts

The calculator is dangerous if its UI, local state, or roadmap starts shaping:

- execution policy
- execution authority
- venue adapter behavior
- backtest responsibilities
- release cadence of QuantLab core

This ADR exists to keep the value and reject the drift.

## Allowed integration

The calculator may provide:

- reusable risk and trade-planning logic
- deterministic trade-plan artifacts
- a headless export path that QuantLab can consume later
- operator-facing UX for scenario exploration
- parity fixtures for alternate runtimes such as JS and C++

QuantLab may consume:

- documented pre-trade artifact contracts
- stable machine-readable exports
- deterministic scenario metadata that can be bridged into draft
  `ExecutionIntent`

## Disallowed integration

The calculator must not become:

- the owner of `ExecutionPolicy`
- the owner of `ExecutionIntent`
- the owner of submit approval or broker authority
- a required runtime dependency for basic QuantLab operation
- a substitute for QuantLab backtest, paper, or broker session lifecycles

QuantLab must not:

- import browser UI state directly from the calculator
- import calculator UI code into core packages
- move the calculator mini-backtester into QuantLab backtest
- let calculator output bypass the existing broker safety boundary
- block QuantLab releases on calculator UX or UI work

## Contract rule

The calculator may hand off only through stable artifacts.

The preferred integration shape is:

```text
calculator artifact -> QuantLab pretrade artifact -> draft ExecutionIntent -> ExecutionPolicy -> venue adapter
```

This means:

- the calculator is not trusted as an execution authority
- QuantLab revalidates all incoming planning data
- all execution-facing steps remain QuantLab-owned

## Ownership split

The calculator repository owns:

- pre-trade planning UX
- scenario ergonomics
- reusable planning logic
- optional alternate runtime implementations
- export convenience for trade plans

QuantLab owns:

- `src/quantlab/pretrade/`
- canonical pre-trade session artifacts
- conversion into draft execution models
- policy checks and rejection reasons
- all paper and broker-facing execution paths

## Independence rule

The calculator must be able to grow on its own without forcing QuantLab to
change.

QuantLab must be able to ignore calculator changes unless they preserve an
accepted contract.

This implies:

- calculator roadmap and QuantLab roadmap stay separate
- integration is reversible
- QuantLab treats calculator artifacts as external inputs, not internal truth
- calculator features that do not improve the contract are not automatically
  QuantLab work

## Practical sequencing

When both repos move forward, the recommended order is:

1. calculator reusable core and deterministic exports
2. calculator headless CLI and contract hardening
3. QuantLab `pretrade` artifact intake
4. QuantLab bridge into `ExecutionPolicy` and draft `ExecutionIntent`
5. optional bounded UI surfaces inside QuantLab

The UI comes last because it is not the authority of the system.

## Success condition

The calculator becomes a good upstream pre-trade tool.

QuantLab gains pre-trade planning value.

Neither repo loses its own identity or absorbs responsibilities that belong to
the other.
