import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from quantlab.data.sources import fetch_ohlc
from quantlab.features.indicators import add_indicators
from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
from quantlab.backtest.engine import run_backtest
from quantlab.backtest.metrics import compute_metrics
from quantlab.execution.paper import run_paper_broker, save_trades_csv
from quantlab.reporting.charts import plot_basic_equity, plot_price_signals
from quantlab.reporting.run_report import write_report as write_run_report
from quantlab.reporting.trade_analytics import (
    aggregate_trade_metrics,
    compute_round_trips,
)
from quantlab.runs.run_id import generate_run_id
from quantlab.runs.run_store import RunStore


def _build_run_config(args) -> dict[str, Any]:
    return {
        "ticker": args.ticker,
        "start": args.start,
        "end": args.end,
        "interval": args.interval,
        "fee": args.fee,
        "rsi_buy_max": args.rsi_buy_max,
        "rsi_sell_min": args.rsi_sell_min,
        "cooldown_days": args.cooldown_days,
        "paper": bool(args.paper),
        "initial_cash": args.initial_cash,
        "slippage_bps": args.slippage_bps,
        "slippage_mode": args.slippage_mode,
        "k_atr": args.k_atr,
    }


def _config_hash(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _get_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _load_external_trades_csv(args, run_dir: Path) -> pd.DataFrame | None:
    trades_csv = getattr(args, "trades_csv", None)
    if not trades_csv:
        return None

    source = Path(trades_csv)
    if not source.exists():
        print(f"ERROR: No existe trades.csv para report. Esperado en: {source}")
        return None

    destination = run_dir / "trades.csv"
    shutil.copyfile(source, destination)
    return pd.read_csv(destination)


def _build_metrics_payload(
    *,
    bt_metrics: dict[str, Any],
    trade_metrics: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    best_result = {
        "total_return": bt_metrics.get("total_return", 0.0),
        "max_drawdown": bt_metrics.get("max_drawdown", 0.0),
        "sharpe_simple": bt_metrics.get("sharpe_simple", 0.0),
        "trades": bt_metrics.get("trades", 0),
        "days": bt_metrics.get("days", 0),
    }
    if trade_metrics:
        best_result.update(
            {
                "trade_trades": trade_metrics.get("trades", 0),
                "win_rate_trades": trade_metrics.get("win_rate_trades", 0.0),
                "profit_factor": trade_metrics.get("profit_factor", 0.0),
                "expectancy_net": trade_metrics.get("expectancy_net", 0.0),
                "avg_holding_days": trade_metrics.get("avg_holding_days", 0.0),
                "exposure": trade_metrics.get("exposure", 0.0),
            }
        )

    summary = {
        "total_return": best_result["total_return"],
        "sharpe_simple": best_result["sharpe_simple"],
        "max_drawdown": best_result["max_drawdown"],
        "trades": best_result["trades"],
        "win_rate": (
            trade_metrics.get("win_rate_trades")
            if trade_metrics
            else bt_metrics.get("winrate_active_days", 0.0)
        ),
    }

    payload = {
        "mode": "run",
        "command": "run",
        "status": "success",
        "summary": summary,
        "best_result": best_result,
        "leaderboard_size": 1,
    }
    return payload, summary


def handle_run_command(args) -> bool:
    """
    Execute the standard single-run backtest simulation.

    Returns True because this is the fallback executable run mode.
    """

    # 1) Data
    df = fetch_ohlc(args.ticker, args.start, args.end, interval=args.interval)

    # 2) Indicators
    df = add_indicators(df)
    if df.empty:
        print("ERROR: No data remaining after applying indicators (need more history for lookbacks).")
        return False

    # 3) Signals
    strat = RsiMaAtrStrategy(
        rsi_buy_max=args.rsi_buy_max,
        rsi_sell_min=args.rsi_sell_min,
        cooldown_days=args.cooldown_days,
    )
    signals = pd.Series(strat.generate_signals(df))

    buys = int((signals == 1).sum())
    sells = int((signals == -1).sum())
    print("\n=== SIGNALS ===")
    print(f"strategy: {strat.name}")
    print(f"BUY signals:  {buys}")
    print(f"SELL signals: {sells}")

    # 4) Backtest
    bt = run_backtest(
        df=df,
        signals=signals,
        fee_rate=args.fee,
        slippage_bps=args.slippage_bps,
        slippage_mode=args.slippage_mode,
        k_atr=args.k_atr,
    )
    metrics = compute_metrics(bt)

    print("\n=== BACKTEST METRICS ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    # 5) Paper broker (optional)
    trades_df = None
    if args.paper:
        trades_df = run_paper_broker(
            df=df,
            signals=signals,
            initial_cash=args.initial_cash,
            fee_rate=args.fee,
            slippage_bps=args.slippage_bps,
            slippage_mode=args.slippage_mode,
            k_atr=args.k_atr,
        )

        print("\n=== PAPER BROKER ===")
        print(f"Initial cash: {args.initial_cash}")
        print(f"Trades logged: {len(trades_df)}")

        if not trades_df.empty:
            print("\nLast trades (paper broker):")
            print(trades_df.tail(5))

    config = _build_run_config(args)
    run_id = generate_run_id("run", config)
    runs_root = (Path("outputs") / "runs").resolve()
    store = RunStore(run_id, base_dir=str(runs_root))
    run_dir = store.initialize().resolve()
    artifacts_dir = run_dir / "artifacts"

    created_at = dt.datetime.now().isoformat()
    config_hash = _config_hash(config)

    trade_metrics: dict[str, Any] = {}
    if args.paper:
        trades_path = run_dir / "trades.csv"
        save_trades_csv(trades_df, str(trades_path))
        print(f"Saved: {trades_path}")
    elif getattr(args, "trades_csv", None):
        trades_df = _load_external_trades_csv(args, run_dir)
        if trades_df is None:
            return None

    if trades_df is not None and not trades_df.empty:
        round_trips = compute_round_trips(trades_df)
        trade_metrics = aggregate_trade_metrics(round_trips)

    metrics_payload, summary = _build_metrics_payload(
        bt_metrics=metrics,
        trade_metrics=trade_metrics,
    )

    metadata = {
        "run_id": run_id,
        "mode": "run",
        "command": "run",
        "status": "success",
        "created_at": created_at,
        "git_commit": _get_git_commit(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "config_path": "inline_cli",
        "config_hash": config_hash,
        "request_id": getattr(args, "_request_id", None),
        "summary": summary,
    }

    store.write_metadata(metadata)
    store.write_config(config)
    store.write_metrics(metrics_payload)

    equity_path = artifacts_dir / "equity.png"
    plot_basic_equity(bt, str(equity_path), args.ticker, strat.name)
    print(f"\nSaved: {equity_path}")

    if args.save_price_plot:
        price_path = artifacts_dir / "price_signals.png"
        plot_price_signals(df, signals, str(price_path), args.ticker, strat.name)
        print(f"Saved: {price_path}")

    report_md_path, report_path = write_run_report(str(run_dir))
    print(f"Saved: {report_md_path}")
    print(f"Saved: {report_path}")

    if args.report is True:
        print("\n=== REPORT ===")
        print("Canonical run report generated for the current execution.")

    return {
        "run_id": run_id,
        "artifacts_path": str(run_dir),
        "report_path": str(report_path),
        "status": "success",
        "summary": summary,
        "mode": "run",
        "runs_index_root": str(runs_root),
    }


# Backward-compatible alias for older refactor paths / tests
run_classic_pipeline = handle_run_command
