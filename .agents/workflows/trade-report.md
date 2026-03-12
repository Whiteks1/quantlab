---
description: 
---

# Workflow: Generate Trade Analytics Report

Use this workflow when trade execution logs produced by the QuantLab paper broker need to be analyzed and converted into trade-level performance artifacts.

## Purpose
This workflow generates structured trade analytics from paper broker execution logs and produces both detailed and summarized reporting artifacts.

## Context
QuantLab follows a modular research architecture:

`data -> indicators -> strategy -> backtest -> paper broker`

The paper broker is expected to produce:

- `outputs/trades.csv`

## Goal
Generate deterministic trade-level analytics and summary artifacts without modifying strategy logic or execution behavior.

## Input
Required input file:

- `outputs/trades.csv`

## Expected Outputs
This workflow should generate the following artifacts under `outputs/`:

- `trades_enriched.csv`
- `report.md`
- `report.json` *(optional, but recommended when structured reporting is available)*

## Workflow Steps
1. Load `outputs/trades.csv`.
2. Validate that the required columns for trade reconstruction are present.
3. Pair `BUY -> SELL` events into completed trades using deterministic rules.
4. Compute per-trade metrics, including:
   - gross PnL
   - net PnL
   - return percentage
   - holding period
   - MAE / MFE, if feasible from available data
5. Compute aggregated statistics, including:
   - trade win rate
   - average win
   - average loss
   - profit factor
   - expectancy
   - maximum consecutive losses
   - exposure (time in market)
   - average holding time
   - drawdown based on `equity_after`, if available
6. Generate the required output artifacts under `outputs/`.
7. Run a smoke test using:
   - ticker: `ETH-USD`
   - period: `2023-01-01 -> 2024-01-01`
8. Verify that artifacts are readable, internally consistent, and aligned with the computed results.

## Constraints
- Do not modify strategy logic.
- Do not implement live trading.
- Respect the modular structure under `src/quantlab/`.
- Do not introduce non-deterministic behavior into trade pairing or analytics.
- Do not write artifacts outside the `outputs/` directory.

## Validation Requirements
Before considering the workflow complete, confirm that:

- trades are paired correctly
- incomplete or unmatched events are handled explicitly
- metrics are deterministic and reproducible
- all expected artifacts are created
- `report.md` and `report.json`, if both exist, are consistent with one another

## Edge Cases to Consider
- empty `trades.csv`
- unmatched `BUY` or `SELL` events
- partial trade sequences
- missing cost or fee information
- missing `equity_after`
- zero-trade scenarios
- non-standard execution ordering

## Success Criteria
The workflow is successful when:

- trades are paired correctly
- metrics match deterministic results
- all required artifacts are created under `outputs/`
- results are suitable for stage review and reporting

## Expected Output Format
After execution, Antigravity should provide:

1. **Input Validation**  
   Whether `outputs/trades.csv` was found and whether required fields were present.

2. **Trade Pairing Summary**  
   Number of raw events, completed trades, and unmatched events.

3. **Artifacts Generated**  
   Which output files were created.

4. **Metric Summary**  
   Key aggregated results.

5. **Smoke Test Status**  
   Whether the smoke test was executed and passed.

6. **Open Issues**  
   Any limitations, assumptions, or unresolved edge cases.

## Guiding Principle
Trade analytics should be reproducible, explicit, and strictly derived from execution artifacts — never inferred loosely or mixed with strategy changes.