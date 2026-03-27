# QuantLab Research UI Product Direction

Status: active  
Date: 2026-03-27

## Product Definition

QuantLab should not look like a broker terminal, a crypto dashboard, or a marketing site.

It should look like a small research operating system for reproducible quantitative work.

The primary job of the UI is to help an operator:

- explore runs
- inspect metrics
- compare results
- open artifacts
- separate research surfaces from operational surfaces

## Core References

The useful inspiration is not one product copied literally.
It is a weighted blend of several mature patterns:

### 1. MLflow as the primary structural reference

Use MLflow as the main model for:

- experiments
- runs
- metrics
- parameters
- artifacts
- filtering and comparison

This is the closest match to QuantLab's actual artifact model.

### 2. QuantConnect as the workflow framing reference

Use QuantConnect for the sense of product flow:

- research
- backtesting
- optimization / comparison
- live trading

This helps QuantLab feel like a coherent quantitative workflow, not a pile of pages.

### 3. Weights & Biases as the comparison/workspace reference

Use W&B for:

- side-by-side comparisons
- analytical workspaces
- flexible table-first analysis

Do not copy W&B literally.
Borrow the idea that comparison is a first-class action, not a decorative extra.

### 4. FreqUI / Freqtrade as the operational reference

Use FreqUI only for the operational layer:

- live state
- events
- fills
- health
- REST / WebSocket-backed supervision

This is a secondary surface.
It must not dominate the research UI.

## Design Principle

QuantLab should be:

- 70% analytics SaaS structure
- 20% premium fintech / AI lab visual identity
- 10% restrained web3 futurism

That means:

- structure must stay classical and usable
- visual identity can still feel modern, dark, technical, and premium

## Information Hierarchy

### Primary

- Runs Explorer
- Run Detail
- Compare

### Secondary

- Pre-Trade Intake
- Paper / broker / live operational surfaces
- Stepbit boundary visibility

### Rule

If a screen competes visually with the run registry without helping the user choose, inspect, or compare runs, it is probably too loud.

## Main Screens

### 1. Runs Explorer

This should be the main screen of the product.

It should center on:

- searchable table
- mode filters
- sorting
- compare selection
- recent/high-value run visibility

Suggested columns:

- run_id
- mode
- ticker
- date range
- return
- sharpe
- drawdown
- trades
- created_at
- actions

### 2. Run Detail

Run detail should be organized into:

- executive summary
- key metrics
- configuration / inputs
- artifacts
- result tables / plots

The graph is useful, but it should support interpretation of the run.
It should not become the whole product.

### 3. Compare

Comparison should be a first-class research action.

Users should be able to:

- select 2 to 4 runs
- compare metrics side by side
- jump into detail from comparison

### 4. Operational Surfaces

Paper, broker, Hyperliquid, and similar runtime surfaces should be clearly separated from run exploration.

They should feel like:

- secondary
- operational
- read-only unless explicitly needed otherwise

### 5. Boundary Surfaces

Pre-trade intake and Stepbit visibility should remain honest and bounded.

They should communicate:

- what exists
- current status
- why it matters
- what QuantLab still owns

They should not dominate the home screen.

## Visual Direction

QuantLab can absolutely feel futuristic.
The rule is that the visual layer must not damage usability.

Use:

- dark theme by default
- soft gradients
- glow used sparingly
- premium, crisp typography
- restrained accent colors
- cards that feel like system panels, not widgets for their own sake

Avoid:

- crypto-neon overload
- chart obsession
- dense widget walls
- decorative copy without function
- landing-page theatrics

## Structural Rules

- Sidebar should be stable and predictable.
- Topbar should focus on search, filters, and refresh.
- Registry table should be the main visual mass of the home screen.
- KPI cards should be few and useful.
- Secondary surfaces should collapse or sit below the main registry.
- Dead navigation and placeholder-heavy sections should be removed or hidden.

## Product Sentence

QuantLab is not a trading app with charts.

QuantLab is a research workspace for quantitative runs, comparison, artifact inspection, and bounded operational visibility.

## Source References

- QuantConnect: https://www.quantconnect.com/
- QuantConnect Research: https://www.quantconnect.com/docs/v2/cloud-platform/research
- QuantConnect Backtesting: https://www.quantconnect.com/docs/v2/cloud-platform/backtesting/getting-started
- QuantConnect Live Trading: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading
- MLflow Tracking: https://mlflow.org/docs/latest/ml/tracking/
- Weights & Biases Panels: https://docs.wandb.ai/models/app/features/panels
- Weights & Biases Tables: https://docs.wandb.ai/models/tables
- Weights & Biases Table Visualization: https://docs.wandb.ai/models/tables/visualize-tables
- Freqtrade / FreqUI REST API: https://docs.freqtrade.io/en/joss_v3/rest-api/
- Freqtrade Docs: https://docs.freqtrade.io/
