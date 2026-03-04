import os
import yaml
import pandas as pd
import itertools
from typing import List, Dict, Any, Optional

from quantlab.data.sources import fetch_ohlc
from quantlab.features.indicators import add_indicators
from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
from quantlab.backtest.engine import run_backtest
from quantlab.backtest.metrics import compute_metrics
from quantlab.execution.paper import run_paper_broker
from quantlab.reporting.trade_analytics import compute_round_trips, aggregate_trade_metrics

def load_experiment_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def expand_grid(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Expand param_grid into a list of individual run configurations.
    """
    grid = config.get("param_grid", {})
    if not grid:
        return [config.copy()]

    # Extract keys and values
    keys = sorted(grid.keys())
    values = [grid[k] for k in keys]

    # Generate Cartesian product
    product = itertools.product(*values)

    runs = []
    for p in product:
        run = config.copy()
        # Remove grid from run config
        run.pop("param_grid", None)
        # Apply specific parameters
        params = dict(zip(keys, p))
        run.update(params)
        runs.append(run)
    
    return runs

def run_one(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single configuration through the pipeline.
    """
    # 1) Data
    df = fetch_ohlc(config["ticker"], config["start"], config["end"], interval=config["interval"])
    
    # 2) Indicators
    df = add_indicators(df)
    
    # 3) Strategy
    strat = RsiMaAtrStrategy(
        rsi_buy_max=config.get("rsi_buy_max", 60.0),
        rsi_sell_min=config.get("rsi_sell_min", 75.0),
        cooldown_days=config.get("cooldown_days", 0)
    )
    signals = pd.Series(strat.generate_signals(df))
    
    # 4) Backtest (for total_return, drawdown, sharpe)
    bt = run_backtest(
        df=df,
        signals=signals,
        fee_rate=config.get("fee", 0.002),
        slippage_bps=config.get("slippage_bps", 8.0),
        slippage_mode=config.get("slippage_mode", "fixed"),
        k_atr=config.get("k_atr", 0.05)
    )
    bt_metrics = compute_metrics(bt)
    
    # 5) Paper Broker (to get trade-level metrics)
    trades_df = run_paper_broker(
        df=df,
        signals=signals,
        initial_cash=config.get("initial_cash", 1000.0),
        fee_rate=config.get("fee", 0.002),
        slippage_bps=config.get("slippage_bps", 8.0),
        slippage_mode=config.get("slippage_mode", "fixed"),
        k_atr=config.get("k_atr", 0.05)
    )
    
    trade_metrics = {}
    if not trades_df.empty:
        rt = compute_round_trips(trades_df)
        trade_metrics = aggregate_trade_metrics(rt)

    # Flatten result
    res = config.copy()
    res.update({
        "total_return": bt_metrics.get("total_return", 0.0),
        "max_drawdown": bt_metrics.get("max_drawdown", 0.0),
        "sharpe_simple": bt_metrics.get("sharpe_simple", 0.0),
        "trades": bt_metrics.get("trades", 0),  # Trades from backtest
        "trade_trades": trade_metrics.get("trades", 0), # Trades from paper broker (round trips)
        "win_rate_trades": trade_metrics.get("win_rate_trades", 0.0),
        "profit_factor": trade_metrics.get("profit_factor", 0.0),
        "expectancy_net": trade_metrics.get("expectancy_net", 0.0),
        "avg_holding_days": trade_metrics.get("avg_holding_days", 0.0),
        "exposure": trade_metrics.get("exposure", 0.0)
    })
    
    return res

def run_experiments(config_path: str, out_csv: str = "outputs/experiments.csv") -> pd.DataFrame:
    config = load_experiment_config(config_path)
    runs = expand_grid(config)
    
    results = []
    print(f"Running {len(runs)} experiments...")
    for i, run in enumerate(runs):
        print(f"[{i+1}/{len(runs)}] Running rsi_buy_max={run.get('rsi_buy_max')}, rsi_sell_min={run.get('rsi_sell_min')}, cooldown={run.get('cooldown_days')}...")
        res = run_one(run)
        results.append(res)
    
    res_df = pd.DataFrame(results)
    
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    res_df.to_csv(out_csv, index=False)
    print(f"Saved all results to: {out_csv}")
    
    return res_df
