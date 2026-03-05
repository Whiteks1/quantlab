import os
import itertools
from typing import List, Dict, Any

import yaml
import pandas as pd

from quantlab.data.sources import fetch_ohlc
from quantlab.features.indicators import add_indicators
from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
from quantlab.backtest.engine import run_backtest
from quantlab.backtest.metrics import compute_metrics
from quantlab.execution.paper import run_paper_broker
from quantlab.reporting.trade_analytics import compute_round_trips, aggregate_trade_metrics


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


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

    keys = sorted(grid.keys())
    values = [grid[k] for k in keys]

    runs: List[Dict[str, Any]] = []
    for p in itertools.product(*values):
        run = config.copy()
        run.pop("param_grid", None)  # IMPORTANT: remove grid from individual run configs
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
        cooldown_days=config.get("cooldown_days", 0),
    )

    raw_signals = strat.generate_signals(df)
    # IMPORTANT: align signals to df.index to avoid subtle misalignment bugs
    signals = pd.Series(raw_signals, index=df.index, dtype="int64")

    # 4) Backtest metrics
    bt = run_backtest(
        df=df,
        signals=signals,
        fee_rate=config.get("fee", 0.002),
        slippage_bps=config.get("slippage_bps", 8.0),
        slippage_mode=config.get("slippage_mode", "fixed"),
        k_atr=config.get("k_atr", 0.05),
    )
    bt_metrics = compute_metrics(bt)

    # 5) Paper broker -> trade analytics
    trades_df = run_paper_broker(
        df=df,
        signals=signals,
        initial_cash=config.get("initial_cash", 1000.0),
        fee_rate=config.get("fee", 0.002),
        slippage_bps=config.get("slippage_bps", 8.0),
        slippage_mode=config.get("slippage_mode", "fixed"),
        k_atr=config.get("k_atr", 0.05),
    )

    trade_metrics: Dict[str, Any] = {}
    if not trades_df.empty:
        rt = compute_round_trips(trades_df)
        trade_metrics = aggregate_trade_metrics(rt)

    # Flatten result
    res = config.copy()
    res.update(
        {
            "total_return": bt_metrics.get("total_return", 0.0),
            "max_drawdown": bt_metrics.get("max_drawdown", 0.0),
            "sharpe_simple": bt_metrics.get("sharpe_simple", 0.0),
            "trades": bt_metrics.get("trades", 0),  # backtest "fills" / signal trades
            "trade_trades": trade_metrics.get("trades", 0),  # round trips from paper broker
            "win_rate_trades": trade_metrics.get("win_rate_trades", 0.0),
            "profit_factor": trade_metrics.get("profit_factor", 0.0),
            "expectancy_net": trade_metrics.get("expectancy_net", 0.0),
            "avg_holding_days": trade_metrics.get("avg_holding_days", 0.0),
            "exposure": trade_metrics.get("exposure", 0.0),
        }
    )

    return res


def is_walkforward_config(config: Dict[str, Any]) -> bool:
    splits = config.get("splits", None)
    return isinstance(splits, list) and len(splits) > 0


def _print_grid_leaderboard(df: pd.DataFrame, top: int = 10) -> None:
    if df.empty:
        print("\n(No results)")
        return

    sort_cols = [c for c in ["sharpe_simple", "total_return"] if c in df.columns]
    if not sort_cols:
        print("\n(No sortable metrics found)")
        return

    lb = df.sort_values(sort_cols, ascending=[False] * len(sort_cols)).head(top)

    cols = [c for c in ["rsi_buy_max", "rsi_sell_min", "cooldown_days", "sharpe_simple", "total_return", "max_drawdown", "trades"] if c in lb.columns]
    print(f"\n=== EXPERIMENT LEADERBOARD (Top {top} by Sharpe) ===")
    print(lb[cols].to_string(index=False))


def run_experiments_grid(config: Dict[str, Any], out_csv: str = "outputs/experiments.csv") -> pd.DataFrame:
    runs = expand_grid(config)

    results: List[Dict[str, Any]] = []
    print(f"Running {len(runs)} experiments...")
    for i, run in enumerate(runs):
        print(
            f"[{i+1}/{len(runs)}] Running "
            f"rsi_buy_max={run.get('rsi_buy_max')}, rsi_sell_min={run.get('rsi_sell_min')}, cooldown={run.get('cooldown_days')}..."
        )
        res = run_one(run)
        results.append(res)

    res_df = pd.DataFrame(results)

    _ensure_parent_dir(out_csv)
    res_df.to_csv(out_csv, index=False)
    print(f"Saved all results to: {out_csv}")

    _print_grid_leaderboard(res_df, top=10)
    return res_df


def run_walkforward(
    config: Dict[str, Any],
    out_csv: str = "outputs/walkforward.csv",
    summary_csv: str = "outputs/walkforward_summary.csv",
) -> pd.DataFrame:
    """
    Execute walkforward validation: train -> select -> test for each split.
    """
    splits = config.get("splits", [])
    selection = config.get("selection", {})
    sort_by = selection.get("sort_by", ["sharpe_simple", "total_return"])
    ascending = selection.get("ascending", [False, False])
    top_k = selection.get("top_k", 3)

    constraints = config.get("constraints", {})
    min_trades = constraints.get("min_trade_trades", 0)

    all_results = []
    summary_records = []

    for split in splits:
        split_name = split["name"]
        train_win = split["train"]
        test_win = split["test"]

        print(f"\n--- Split: {split_name} ---")

        # a) TRAIN
        train_config = config.copy()
        train_config.update(train_win)
        runs = expand_grid(train_config)

        print(f"TRAIN phase: running {len(runs)} configurations...")
        train_results = []
        for run in runs:
            res = run_one(run)
            res["split_name"] = split_name
            res["phase"] = "train"
            res["selected"] = False
            train_results.append(res)

        train_df = pd.DataFrame(train_results)

        # b) APPLY constraints
        filtered_train = train_df.copy()
        if min_trades > 0 and "trade_trades" in filtered_train.columns:
            filtered_train = filtered_train[filtered_train["trade_trades"] >= min_trades]

        # c) SELECT (on filtered train)
        selected_df = filtered_train.sort_values(sort_by, ascending=ascending).head(top_k)
        selected_indices = selected_df.index

        train_df.loc[selected_indices, "selected"] = True
        train_df.loc[selected_indices, "rank_in_train"] = range(1, len(selected_indices) + 1)

        print(f"Selected {len(selected_df)} configs from TRAIN (after constraints).")

        # d) TEST only selected
        test_results = []
        if not selected_df.empty:
            print(f"TEST phase: evaluating {len(selected_df)} selected configs...")
            grid_keys = list(config.get("param_grid", {}).keys())

            for i, (_, row) in enumerate(selected_df.iterrows()):
                test_run_config = config.copy()
                test_run_config.pop("param_grid", None)  # IMPORTANT: keep schema consistent
                test_run_config.update(test_win)

                for k in grid_keys:
                    if k in row:
                        test_run_config[k] = row[k]

                res = run_one(test_run_config)
                res["split_name"] = split_name
                res["phase"] = "test"
                res["selected"] = True
                res["rank_in_train"] = i + 1
                test_results.append(res)

        test_df = pd.DataFrame(test_results)

        # e) Collect per split
        split_all = pd.concat([train_df, test_df], ignore_index=True)
        all_results.append(split_all)

        # Summary (use filtered_train for "best train" so it matches your constraints)
        best_train_sharpe = float(filtered_train["sharpe_simple"].max()) if not filtered_train.empty else 0.0
        best_train_ret = float(filtered_train["total_return"].max()) if not filtered_train.empty else 0.0

        avg_test_sharpe = float(test_df["sharpe_simple"].mean()) if not test_df.empty else 0.0
        avg_test_ret = float(test_df["total_return"].mean()) if not test_df.empty else 0.0
        best_test_sharpe = float(test_df["sharpe_simple"].max()) if not test_df.empty else 0.0
        best_test_ret = float(test_df["total_return"].max()) if not test_df.empty else 0.0

        summary_records.append(
            {
                "split_name": split_name,
                "best_train_sharpe": best_train_sharpe,
                "best_train_return": best_train_ret,
                "avg_test_sharpe_topk": avg_test_sharpe,
                "avg_test_return_topk": avg_test_ret,
                "best_test_sharpe": best_test_sharpe,
                "best_test_return": best_test_ret,
                "n_train_runs": len(runs),
                "n_selected": len(selected_df),
                "n_test_runs": len(test_df),
            }
        )

        print(
            f"Summary split={split_name} | "
            f"n_train={len(runs)}, n_sel={len(selected_df)}, n_test={len(test_df)} | "
            f"train_best_sharpe={best_train_sharpe:.4f} | "
            f"test_best_sharpe={best_test_sharpe:.4f} | "
            f"test_best_return={best_test_ret:.4f}"
        )

    final_df = pd.concat(all_results, ignore_index=True)

    _ensure_parent_dir(out_csv)
    final_df.to_csv(out_csv, index=False)

    summary_df = pd.DataFrame(summary_records)
    _ensure_parent_dir(summary_csv)
    summary_df.to_csv(summary_csv, index=False)

    print(f"\nWalkforward combined results saved to: {out_csv}")
    print(f"Walkforward summary saved to: {summary_csv}")

    return final_df


def run_sweep(config_path: str) -> pd.DataFrame:
    """
    Unified entry point: loads YAML and dispatches to grid or walkforward.
    """
    config = load_experiment_config(config_path)
    if is_walkforward_config(config):
        df = run_walkforward(config)
        
        # Print FINAL test leaderboard (Top 10 by sharpe_simple)
        test_results = df[df["phase"] == "test"]
        if not test_results.empty:
            print("\n" + "="*50)
            print("WALKFORWARD FINAL TEST LEADERBOARD (OOS)")
            _print_grid_leaderboard(test_results, top=10)
        return df
        
    return run_experiments_grid(config)


# Backwards-compat alias (if main.py or other code still calls run_experiments)
def run_experiments(config_path: str, out_csv: str = "outputs/experiments.csv") -> pd.DataFrame:
    """
    Backward compatible:
    - If config is walkforward -> outputs/walkforward*.csv
    - Else grid -> outputs/experiments.csv (or provided out_csv)
    """
    config = load_experiment_config(config_path)
    if is_walkforward_config(config):
        return run_walkforward(config)
    return run_experiments_grid(config, out_csv=out_csv)