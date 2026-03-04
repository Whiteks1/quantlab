---
description: 
---

# Workflow: Strategy Research Automation

Mission:
Implement a research module to automatically evaluate multiple parameter combinations for the RSI + MA strategy.

Context
The QuantLab repository already contains:

data -> indicators -> strategy -> backtest -> paper broker

Goal
Create a research framework to test many strategy parameter combinations and rank them.

Deliverables

1) Create module:

src/quantlab/research/grid_search.py

2) Implement parameter sweep for:

RSI thresholds
MA short window
MA long window
ATR filter multiplier

Example grid:

RSI_BUY = [25, 30, 35, 40]
RSI_SELL = [60, 65, 70]
MA_SHORT = [10, 20, 30]
MA_LONG = [80, 100, 120]

3) For each combination:

- run backtest
- collect metrics

Metrics:

total_return  
sharpe  
max_drawdown  
trades  
winrate  

4) Store results:

outputs/strategy_research.csv

5) Rank strategies by:

Sharpe ratio

6) Output top 10 strategies.

Constraints

- Use existing backtest engine
- Do not duplicate logic
- Keep module under src/quantlab/research/

Success Criteria

The workflow generates:

outputs/strategy_research.csv

with all tested parameter combinations and metrics.