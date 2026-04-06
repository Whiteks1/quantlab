# Quant Pulse -> QuantLab Signal Intake Contract

## Purpose

Quant Pulse is an upstream signal layer for QuantLab.

Its job is not to produce trade picks directly.
Its job is to emit prioritized research intents, regime filters, and product priorities that QuantLab can validate through reproducible research.

## Core relationship

- Quant Pulse filters and structures signals.
- QuantLab validates those signals through `run`, `forward_eval`, paper sessions, and controlled execution boundaries.
- QuantLab remains autonomous.
- Quant Pulse only matters to QuantLab when it improves the research and validation cycle.

## What Quant Pulse may provide

Allowed outputs from Quant Pulse:

- `signal_summary`
- `priority`
- `affected_universe`
- `bias`
- `horizon`
- `hypothesis_type`
- `validation_goal`
- `invalidation_condition`
- `risk_filter_hint`
- `product_priority_hint`

## When QuantLab should consume a signal

QuantLab should consume a Quant Pulse signal only if it can be translated into at least one of these:

- a testable research hypothesis
- a risk filter
- a product or instrumentation priority

If a signal cannot become one of those three things, it should not drive QuantLab's roadmap or execution behavior.

## Recommended hypothesis families

Quant Pulse signals should usually map into one of these QuantLab families:

- trend
- mean reversion
- event-driven
- regime filter
- rotation

## Strong signal categories

Especially useful Quant Pulse input categories for QuantLab:

- Crypto & Markets
- Web3 market structure
- venue and execution-rail risk
- Technology only when it affects infra, security, or market structure
- Macro only when it materially changes crypto or technology conditions

## Non-goals

This contract does not mean:

- Quant Pulse decides trades
- Quant Pulse governs QuantLab
- Quant Pulse replaces QuantLab research
- QuantLab must act on every signal

## Example translation

Quant Pulse signal:

- "Regulatory pressure is improving the case for majors"

QuantLab research intent:

- validate trend-following on BTC and ETH versus the rest of the universe
- compare against baseline and mean-reversion alternatives
- forward-evaluate before any paper or execution use

## Operational rule

Quant Pulse should only influence QuantLab when the signal can be expressed clearly enough to support:

- research
- validation
- risk control
- product prioritization

Otherwise, it stays as context, not as a driver.
