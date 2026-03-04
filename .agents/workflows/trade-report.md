---
description: 
---

# Workflow: Generate Trade Analytics Report

Mission:
Analyze trade execution logs produced by the QuantLab paper broker and generate trade-level performance reports.

Context
The repository contains a modular quantitative research environment:

data → indicators → strategy → backtest → paper broker

The paper broker produces `outputs/trades.csv`.

Goal
Generate trade-level analytics and a summarized report.

Steps
1. Load `outputs/trades.csv`.
2. Pair BUY → SELL events into completed trades.
3. Compute per-trade metrics:
   - gross PnL
   - net PnL
   - return %
   - holding period
   - MAE/MFE if feasible.

4. Compute aggregated statistics:
   - trade win rate
   - average win / average loss
   - profit factor
   - expectancy
   - maximum consecutive losses
   - exposure (time in market)
   - average holding time
   - drawdown based on equity_after.

5. Generate artifacts:
   - `outputs/trades_enriched.csv`
   - `outputs/report.md`
   - `outputs/report.json` (optional)

6. Run a smoke test using:
   ticker: ETH-USD  
   period: 2023-01-01 → 2024-01-01

Constraints
- Do not modify the strategy logic.
- Do not implement live trading.
- Respect modular structure in `src/quantlab/`.

Success Criteria
- Trades are paired correctly.
- Metrics match deterministic results.
- All artifacts are created under `outputs/`.