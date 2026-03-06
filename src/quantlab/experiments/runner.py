import os
import itertools
import datetime
import hashlib
import json
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

import yaml
import math
import pandas as pd

from quantlab.data.sources import fetch_ohlc
from quantlab.features.indicators import add_indicators
from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
from quantlab.backtest.engine import run_backtest
from quantlab.backtest.metrics import compute_metrics
from quantlab.execution.paper import run_paper_broker
from quantlab.reporting.trade_analytics import compute_round_trips, aggregate_trade_metrics
from quantlab.reporting.run_report import write_report as write_run_report


def _sanitize_for_json(obj):
    """Recursively convert non-finite floats to None for strict JSON."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(x) for x in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_experiment_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_git_commit() -> str:
    try:
        import subprocess

        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "unknown"


def make_run_dir(base: str = "outputs/runs", mode: str = "grid", config_path: str = "config.yaml") -> Path:
    """
    Generate a unique run directory: <base>/YYYYMMDD_HHMMSS_mode_shortsha
    """
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Hash of config content for uniqueness
    try:
        with open(config_path, "rb") as f:
            config_bytes = f.read()
            config_hash = hashlib.sha1(config_bytes).hexdigest()[:7]
    except Exception:
        config_hash = "unknown"

    run_id = f"{now}_{mode}_{config_hash}"

    path = Path(base) / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch_ohlc_cached(
    ticker: str, start: str, end: str, interval: str = "1d", cache_dir: str = "data/cache"
) -> pd.DataFrame:
    """
    Fetch OHLC data with parquet caching.
    """
    safe_ticker = ticker.replace("-", "_").replace("/", "_").replace(" ", "_")
    cache_key = f"{safe_ticker}_{start}_{end}_{interval}".replace(":", "_")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = Path(cache_dir) / f"{cache_key}.parquet"

    if cache_file.exists():
        df = pd.read_parquet(cache_file)
        return df

    df = fetch_ohlc(ticker, start, end, interval=interval)

    # Ensure deterministic index and sort
    df.index.name = "timestamp"
    df = df.sort_index()

    df.to_parquet(cache_file)
    return df


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
    df = fetch_ohlc_cached(config["ticker"], config["start"], config["end"], interval=config["interval"])

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

    cols = [
        c
        for c in [
            "rsi_buy_max",
            "rsi_sell_min",
            "cooldown_days",
            "sharpe_simple",
            "total_return",
            "max_drawdown",
            "trades",
        ]
        if c in lb.columns
    ]
    print(f"\n=== EXPERIMENT LEADERBOARD (Top {top} by Sharpe) ===")
    print(lb[cols].to_string(index=False))


def _sanitize_for_json(obj: Any) -> Any:
    """
    Recursively convert non-finite floats (NaN, Inf) to None for strict JSON.
    """
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(x) for x in obj]
    elif isinstance(obj, float):
        if not math.isfinite(obj):
            return None
    return obj


def _save_reproducibility_pack(
    out_dir: Path,
    config: Dict[str, Any],
    mode: str,
    metrics_summary: List[Dict[str, Any]],
    config_path: str = "unknown",
    extra_meta: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save meta.json and config_resolved.yaml to the run directory.
    """
    # config_hash of the actual resolved config
    config_json = json.dumps(config, sort_keys=True)
    config_hash = hashlib.sha1(config_json.encode()).hexdigest()

    meta = {
        "run_id": out_dir.name,
        "mode": mode,
        "created_at": datetime.datetime.now().isoformat(),
        "git_commit": _get_git_commit(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "config_path": config_path,
        "config_hash": config_hash,
        "top10": metrics_summary[:10],
    }
    if extra_meta:
        meta.update(extra_meta)

    meta = _sanitize_for_json(meta)

    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False, allow_nan=False)

    with open(out_dir / "config_resolved.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)


def _persist_grid_rich_artifacts(
    out_dir: Path,
    lb_df: pd.DataFrame,
) -> None:
    """
    Persist additional analysis-ready artifacts for grid runs.

    Writes:
    - ``best_config.json`` – the top-ranked config and its metrics
    """
    if lb_df.empty:
        return
    try:
        best_row = lb_df.iloc[0].to_dict()
        best_row = _sanitize_for_json(best_row)
        with open(out_dir / "best_config.json", "w", encoding="utf-8") as fh:
            json.dump(best_row, fh, indent=2, ensure_ascii=False, allow_nan=False)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: Could not persist grid rich artifacts: {exc}")


def _persist_walkforward_rich_artifacts(
    out_dir: Path,
    final_df: pd.DataFrame,
    summary_records: List[Dict[str, Any]],
) -> None:
    """
    Persist additional analysis-ready artifacts for walkforward runs.

    Writes:
    - ``oos_equity_curve.csv``   – stitched OOS equity across splits (normalised)
    - ``selected_configs.csv``  – one row per split per selected config
    - ``split_metrics.csv``     – summary per split (alias kept for legacy)

    The OOS equity is computed from the mean total_return of the selected
    (phase=test) configs per split, stitched chronologically into a
    cumulative equity series starting at 1.0.
    """
    try:
        # --- selected configs ---
        if not final_df.empty and "phase" in final_df.columns:
            sel = final_df[(final_df["phase"] == "test") & final_df.get("selected", True)].copy()
            sel.to_csv(out_dir / "selected_configs.csv", index=False)

            # --- OOS equity curve ---
            if "split_name" in sel.columns and "total_return" in sel.columns:
                # Average total_return per split (handles top_k > 1)
                avg_ret = (
                    sel.groupby("split_name", sort=False)["total_return"]
                    .mean()
                    .reset_index()
                    .rename(columns={"total_return": "avg_test_return"})
                )
                # Stitch equity: start = 1.0
                equity = 1.0
                equity_rows = []
                for _, row in avg_ret.iterrows():
                    equity = equity * (1 + float(row["avg_test_return"]))
                    equity_rows.append({
                        "split_name": row["split_name"],
                        "avg_test_return": float(row["avg_test_return"]),
                        "cumulative_equity": equity,
                    })
                pd.DataFrame(equity_rows).to_csv(out_dir / "oos_equity_curve.csv", index=False)

        # --- split_metrics (convenience copy of summary_records) ---
        if summary_records:
            pd.DataFrame(summary_records).to_csv(out_dir / "split_metrics.csv", index=False)

    except Exception as exc:  # noqa: BLE001
        print(f"Warning: Could not persist walkforward rich artifacts: {exc}")


def run_experiments_grid(config: Dict[str, Any], out_dir: Optional[str] = None, config_path: str = "unknown") -> pd.DataFrame:
    base = out_dir if out_dir else "outputs/runs"
    out_dir_path = make_run_dir(base=base, mode="grid", config_path=config_path)

    out_csv = out_dir_path / "experiments.csv"
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

    res_df.to_csv(out_csv, index=False)
    print(f"Saved all results to: {out_csv}")

    # Leaderboard
    sort_cols = [c for c in ["sharpe_simple", "total_return"] if c in res_df.columns]
    lb_df = res_df.sort_values(sort_cols, ascending=[False] * len(sort_cols)) if sort_cols else res_df
    lb_csv = out_dir_path / "leaderboard.csv"
    lb_df.to_csv(lb_csv, index=False)

    _print_grid_leaderboard(res_df, top=10)

    summary_data = lb_df.head(10).to_dict(orient="records")
    _save_reproducibility_pack(
        out_dir=out_dir_path,
        config=config,
        mode="grid",
        metrics_summary=summary_data,
        config_path=config_path,
        extra_meta={"n_runs": len(runs)},
    )
    try:
        write_run_report(str(out_dir_path))
    except Exception as e:
        print(f"Warning: Failed to generate run report: {e}")
    _persist_grid_rich_artifacts(out_dir_path, lb_df)
    print(f"Run directory: {out_dir_path}")

    return res_df


def run_walkforward(config: Dict[str, Any], out_dir: Optional[str] = None, config_path: str = "unknown") -> pd.DataFrame:
    """
    Execute walkforward validation: train -> select -> test for each split.
    """
    base = out_dir if out_dir else "outputs/runs"
    out_dir_path = make_run_dir(base=base, mode="walkforward", config_path=config_path)

    out_csv = out_dir_path / "walkforward.csv"
    summary_csv = out_dir_path / "walkforward_summary.csv"
    oos_lb_csv = out_dir_path / "oos_leaderboard.csv"

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

    final_df.to_csv(out_csv, index=False)

    summary_df = pd.DataFrame(summary_records)
    summary_df.to_csv(summary_csv, index=False)

    # OOS Leaderboard
    test_results = final_df[final_df["phase"] == "test"]
    oos_lb = pd.DataFrame()
    if not test_results.empty:
        sort_cols = [c for c in ["sharpe_simple", "total_return"] if c in test_results.columns]
        oos_lb = test_results.sort_values(sort_cols, ascending=[False] * len(sort_cols)) if sort_cols else test_results
        oos_lb.to_csv(oos_lb_csv, index=False)
        print(f"OOS Leaderboard saved to: {oos_lb_csv}")

    # Repro pack
    lb_summary = oos_lb.head(10).to_dict(orient="records") if not oos_lb.empty else []

    total_train = sum(r["n_train_runs"] for r in summary_records)
    total_sel = sum(r["n_selected"] for r in summary_records)
    total_test = sum(r["n_test_runs"] for r in summary_records)

    _save_reproducibility_pack(
        out_dir=out_dir_path,
        config=config,
        mode="walkforward",
        metrics_summary=lb_summary,
        config_path=config_path,
        extra_meta={
            "n_train_runs": total_train,
            "n_selected": total_sel,
            "n_test_runs": total_test,
        },
    )
    try:
        write_run_report(str(out_dir_path))
    except Exception as e:
        print(f"Warning: Failed to generate run report: {e}")
    _persist_walkforward_rich_artifacts(out_dir_path, final_df, summary_records)

    print(f"\nWalkforward results saved to: {out_dir_path}")
    return final_df
def run_sweep(config_path: str, out_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Unified entry point: loads YAML and dispatches to grid or walkforward.

    If out_dir is provided (e.g. outputs/sweeps), we create a unique run
    directory INSIDE it to avoid overwriting artifacts.
    """
    config = load_experiment_config(config_path)
    if is_walkforward_config(config):
        return run_walkforward(config, out_dir=out_dir, config_path=config_path)
    return run_experiments_grid(config, out_dir=out_dir, config_path=config_path)

# Backwards-compat alias (if main.py or other code still calls run_experiments)
def run_experiments(config_path: str, out_csv: str = "outputs/experiments.csv") -> pd.DataFrame:
    """
    Backward compatible:
    - If config is walkforward -> outputs/walkforward*.csv (under outputs/)
    - Else grid -> outputs/experiments.csv (or provided out_csv)

    IMPORTANT:
    - This function preserves the older behavior of writing directly into the directory
      implied by out_csv (not into a unique run dir).
    """
    config = load_experiment_config(config_path)

    # If out_csv is a file, we use its parent as out_dir
    out_dir = os.path.dirname(out_csv) if out_csv else None

    if is_walkforward_config(config):
        return run_walkforward(config, out_dir=out_dir, config_path=config_path)

    return run_experiments_grid(config, out_dir=out_dir, config_path=config_path)