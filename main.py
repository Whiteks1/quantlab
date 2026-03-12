import argparse
import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
import matplotlib.pyplot as plt


from quantlab.cli.portfolio import handle_portfolio_commands
from quantlab.cli.forward import handle_forward_commands
from quantlab.cli.report import handle_report_commands
from quantlab.data.sources import fetch_ohlc
from quantlab.features.indicators import add_indicators
from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
from quantlab.backtest.engine import run_backtest
from quantlab.backtest.metrics import compute_metrics
from quantlab.execution.paper import run_paper_broker, save_trades_csv
from quantlab.reporting.portfolio_report import write_portfolio_report
from quantlab.reporting.portfolio_mode_compare import write_mode_comparison_report
from quantlab.reporting.report import write_report as write_trade_report
from quantlab.reporting.run_report import write_report as write_run_report
from quantlab.reporting.run_index import write_runs_index, build_runs_index
from quantlab.reporting.compare_runs import write_comparison
from quantlab.reporting.advanced_report import write_advanced_report
from quantlab.reporting.forward_report import write_forward_report
from quantlab.execution.forward_eval import (
    load_candidate_from_run,
    run_forward_evaluation,
    write_forward_eval_artifacts,
)
from quantlab.experiments import run_sweep


def _plot_equity(bt, out_path: str, ticker: str, strategy_name: str) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(bt.index, bt["equity"], label="Equity (net)")
    plt.title(f"Equity Curve — {ticker} — {strategy_name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def _plot_price_signals(df, signals, out_path: str, ticker: str, strategy_name: str) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["close"], label="Close")
    plt.plot(df.index, df["ma20"], label="MA20", linestyle="--")

    buy_idx = df.index[signals == 1]
    sell_idx = df.index[signals == -1]
    plt.scatter(buy_idx, df.loc[buy_idx, "close"], marker="^", s=100, label="BUY")
    plt.scatter(sell_idx, df.loc[sell_idx, "close"], marker="v", s=100, label="SELL")

    plt.title(f"Price + Signals — {ticker} — {strategy_name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def _generate_report(
    *,
    outdir: str,
    ticker: str,
    strategy_name: str,
    backtest_metrics: dict,
    trades_path: str,
) -> str:
    meta = {
        "ticker": ticker,
        "strategy_name": strategy_name,
        "backtest_metrics": backtest_metrics,
    }

    report_md = os.path.join(outdir, "report.md")
    report_json = os.path.join(outdir, "report.json")

    payload = write_trade_report(
        trades_csv_path=trades_path,
        out_md_path=report_md,
        out_json_path=report_json,
        meta=meta,
    )

    metrics = payload.get("metrics", {})
    print("\n=== TRADE-LEVEL METRICS ===")
    print(f"Total Trades:  {metrics.get('trades', 0)}")
    print(f"Win Rate:      {metrics.get('win_rate_trades', 0.0):.2%}")
    print(f"Profit Factor: {metrics.get('profit_factor', 0.0):.2f}")
    print(f"Expectancy:    {metrics.get('expectancy_net', 0.0):.4f}")

    return report_md


def _run_forward_mode(args) -> None:
    """
    Stage L: orchestrate a forward evaluation session from CLI args.

    Loads the best candidate from an existing run directory, fetches OHLC data
    for the forward period, runs the paper portfolio simulation, persists all
    artifacts, and generates a JSON + Markdown report.
    """
    import datetime as _dt
    from quantlab.execution.forward_eval import (
        load_candidate_from_run,
        run_forward_evaluation,
        write_forward_eval_artifacts,
        load_forward_session,
    )
    from quantlab.reporting.forward_report import write_forward_report
    from quantlab.data.sources import fetch_ohlc

    resume_dir = getattr(args, "resume_forward", None)
    run_dir = getattr(args, "forward_eval", None)

    if resume_dir:
        print(f"\n=== STAGE L.2: RESUMING FORWARD SESSION ===")
        print(f"  Session dir: {resume_dir}")
        try:
            session_data = load_forward_session(resume_dir)
        except ValueError as e:
            print(f"ERROR: {e}")
            return
        except Exception as e:
            print(f"ERROR: Could not load session: {e}")
            return

        candidate = session_data["candidate"]
        initial_state = session_data["portfolio_state"]
        out_dir = resume_dir
        initial_historical = {
            "historic_trades": session_data["historic_trades"],
            "historic_equity": session_data["historic_equity"],
        }
    else:
        print(f"\n=== STAGE L: FORWARD EVALUATION ===")
        print(f"  Source run : {run_dir}")
        candidate = None
        initial_state = None

        out_dir = args.forward_outdir
        if out_dir is None:
            session_tag = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            out_dir = os.path.join("outputs", "forward_runs", f"fwd_{session_tag}")
        initial_historical = None

    fwd_start = getattr(args, "forward_start", None)
    fwd_end = getattr(args, "forward_end", None)

    if not candidate:
        metric = getattr(args, "forward_metric", "sharpe_simple")
        print(f"\n[1/4] Loading candidate (metric={metric})...")
        candidate = load_candidate_from_run(run_dir, metric=metric)

    print(f"  Strategy  : {candidate.strategy_name}")
    print(f"  Source ID : {candidate.source_run_id}")
    print(f"  Params    : {candidate.params}")

    ticker = candidate.ticker or args.ticker
    interval = candidate.interval or args.interval

    today = _dt.date.today().isoformat()
    active_start = fwd_start or (initial_state.original_eval_start if initial_state else today)
    active_end = fwd_end or today

    fetch_start = active_start
    try:
        start_dt = _dt.datetime.strptime(active_start, "%Y-%m-%d")
        fetch_start = (start_dt - _dt.timedelta(days=400)).strftime("%Y-%m-%d")
    except Exception:
        pass

    print(f"\n[2/4] Fetching OHLC data ({ticker}, {fetch_start} → {active_end}, {interval})...")
    df = fetch_ohlc(ticker, fetch_start, active_end, interval=interval)
    print(f"  Bars fetched: {len(df)}")

    print(f"\n[3/4] Running forward paper evaluation...")
    try:
        result = run_forward_evaluation(
            candidate=candidate,
            df=df,
            initial_cash=args.initial_cash,
            eval_start=active_start,
            eval_end=active_end,
            initial_state=initial_state,
        )
    except Exception as e:
        print(f"ERROR: Forward evaluation failed: {e}")
        return

    ps = result["portfolio_state"]
    print(f"  Bars evaluated : {result['bars_evaluated']}")
    print(f"  Trades (segment): {len(result['trades'])}")
    print(f"  Ending equity  : {ps.current_equity:,.4f}")

    print(f"\n[4/4] Writing artifacts to {out_dir}...")
    os.makedirs(out_dir, exist_ok=True)
    written_files = write_forward_eval_artifacts(
        result,
        out_dir,
        initial_historical=initial_historical,
    )
    json_p, md_p = write_forward_report(out_dir)
    written_files += [json_p, md_p]

    for f in written_files:
        print(f"  → {f}")


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="QuantLab MVP: indicadores, señales, backtest + paper broker (logging)."
    )
    parser.add_argument("--ticker", default="ETH-USD")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2024-01-01")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--fee", type=float, default=0.002)

    # Estrategia (v2)
    parser.add_argument("--rsi_buy_max", type=float, default=60.0)
    parser.add_argument("--rsi_sell_min", type=float, default=75.0)
    parser.add_argument("--cooldown_days", type=int, default=0)

    # Output
    parser.add_argument("--outdir", default=None, help="Output directory (default: outputs)")
    parser.add_argument("--save_price_plot", action="store_true")

    # Paper broker
    parser.add_argument("--paper", action="store_true", help="Ejecuta paper broker + CSV de trades")
    parser.add_argument("--initial_cash", type=float, default=1000.0, help="Cash inicial para paper broker")

    # Slippage
    parser.add_argument("--slippage_bps", type=float, default=8.0, help="Slippage fijo en bps (10bps=0.10%%)")
    parser.add_argument("--slippage_mode", default="fixed", choices=["fixed", "atr"])
    parser.add_argument("--k_atr", type=float, default=0.05, help="Sensibilidad slippage ATR (si slippage_mode=atr)")

    # Reporting
    parser.add_argument("--report", nargs="?", const=True, help="Genera report para un run (pasa el path) o para la ejecución actual (sin path)")
    parser.add_argument("--trades_csv", default=None, help="Path a trades.csv si quieres regenerar report sin --paper")
    parser.add_argument("--sweep", help="Path a .yaml de configuración para grid search (ej: configs/experiments/eth_2023_grid.yaml)")
    parser.add_argument("--sweep_outdir", default=None, help="Manual override for sweep output directory")

    # Stage J: Run Registry & Comparison
    parser.add_argument("--list-runs", metavar="ROOT_DIR", default=None,
                        help="Scan ROOT_DIR for completed runs and write runs_index.{csv,json,md}")
    parser.add_argument("--best-from", metavar="ROOT_DIR", default=None,
                        help="Print the best run in ROOT_DIR by --metric")
    parser.add_argument("--metric", default="sharpe_simple",
                        help="Metric used by --best-from (default: sharpe_simple)")
    parser.add_argument("--compare", nargs="+", metavar="RUN_DIR",
                        help="Compare two or more run directories and write compare_report.{json,md}")

    # Stage K: Advanced Metrics & Charts
    parser.add_argument("--advanced-report", metavar="RUN_DIR", default=None,
                        help="Generate advanced_report.json + advanced_report.md + charts for a run directory")

    # Stage L: Forward Evaluation / Paper Portfolio
    parser.add_argument("--forward-eval", metavar="RUN_DIR", default=None,
                        help="Run forward paper evaluation using candidate from RUN_DIR")
    parser.add_argument("--forward-start", metavar="YYYY-MM-DD", default=None,
                        help="Forward evaluation period start date")
    parser.add_argument("--forward-end", metavar="YYYY-MM-DD", default=None,
                        help="Forward evaluation period end date")
    parser.add_argument("--forward-outdir", metavar="DIR", default=None,
                        help="Output directory for forward evaluation artifacts")
    parser.add_argument("--initial-cash", type=float, default=10_000.0,
                        help="Starting cash for forward paper portfolio (default: 10000)")
    parser.add_argument("--forward-metric", default="sharpe_simple",
                        help="Metric used to select the best candidate from run (default: sharpe_simple)")
    parser.add_argument("--resume-forward", metavar="SESSION_DIR", default=None,
                        help="Resume an existing forward evaluation session from its directory")

    parser.add_argument("--portfolio-report", metavar="ROOT_DIR", default=None,
                        help="Aggregate all forward sessions in ROOT_DIR into a portfolio report")
    parser.add_argument("--portfolio-mode", default="raw_capital", choices=["raw_capital", "equal_weight", "custom_weight"],
                        help="Allocation mode for portfolio aggregation (default: raw_capital)")
    parser.add_argument("--portfolio-weights", metavar="JSON_FILE", default=None,
                        help="Path to JSON file with custom weights for --portfolio-mode custom_weight")

    # Stage M.3: Portfolio Selection
    parser.add_argument("--portfolio-top-n", type=int, default=None,
                        help="Keep only the best N sessions after hygiene/dedup")
    parser.add_argument("--portfolio-rank-metric", default="total_return",
                        choices=["total_return", "ending_equity", "contribution_pct", "updated_at"],
                        help="Metric to rank sessions for Top-N selection (default: total_return)")
    parser.add_argument("--portfolio-min-return", type=float, default=None,
                        help="Exclude sessions with total_return below this threshold")
    parser.add_argument("--portfolio-max-drawdown", type=float, default=None,
                        help="Exclude sessions with max drawdown worse than this threshold (e.g. -0.20)")
    parser.add_argument("--portfolio-include-tickers", default=None,
                        help="Comma-separated list of tickers to include")
    parser.add_argument("--portfolio-exclude-tickers", default=None,
                        help="Comma-separated list of tickers to exclude")
    parser.add_argument("--portfolio-include-strategies", default=None,
                        help="Comma-separated list of strategies to include")
    parser.add_argument("--portfolio-exclude-strategies", default=None,
                        help="Comma-separated list of strategies to exclude")
    parser.add_argument("--portfolio-latest-per-source-run", action="store_true",
                        help="If set, only keep the latest session for each source_run_id")
    parser.add_argument("--portfolio-compare", metavar="ROOT_DIR", default=None,
                        help="Compare portfolio results across all allocation modes for eligible sessions in ROOT_DIR")

    args = parser.parse_args()

    # --- REPORT COMMANDS ---
    if handle_report_commands(
        args,
        write_run_report=write_run_report,
        write_advanced_report=write_advanced_report,
        write_runs_index=write_runs_index,
        build_runs_index=build_runs_index,
        write_comparison=write_comparison,
    ):
        return

    # --- FORWARD COMMANDS ---
    if handle_forward_commands(
        args,
        run_forward_mode=_run_forward_mode,
    ):
        return
    
    # --- PORTFOLIO COMMANDS ---
    if handle_portfolio_commands(
        args,
        write_portfolio_report=write_portfolio_report,
        write_mode_comparison_report=write_mode_comparison_report,
    ):
        return

    # --- SWEEP MODE (exits early) ---
    if args.sweep:
        out_dir = args.sweep_outdir or args.outdir
        run_sweep(args.sweep, out_dir=out_dir)
        return

    outdir = args.outdir or "outputs"
    os.makedirs(outdir, exist_ok=True)

    # 1) Datos
    df = fetch_ohlc(args.ticker, args.start, args.end, interval=args.interval)

    # 2) Indicadores
    df = add_indicators(df)

    # 3) Señales
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

    equity_path = os.path.join(outdir, "equity.png")
    _plot_equity(bt, equity_path, args.ticker, strat.name)
    print(f"\nSaved: {equity_path}")

    if args.save_price_plot:
        price_path = os.path.join(outdir, "price_signals.png")
        _plot_price_signals(df, signals, price_path, args.ticker, strat.name)
        print(f"Saved: {price_path}")

    # 5) Paper broker (opcional)
    trades_df = None
    trades_path = os.path.join(outdir, "trades.csv")

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
        save_trades_csv(trades_df, trades_path)

        print("\n=== PAPER BROKER ===")
        print(f"Initial cash: {args.initial_cash}")
        print(f"Trades logged: {len(trades_df)}")
        print(f"Saved: {trades_path}")

        if not trades_df.empty:
            print("\nLast trades (paper broker):")
            print(trades_df.tail(5))

    # 6) Report — classic trade-level report (legacy boolean mode)
    # Note: --report <run_dir> is handled early above and never reaches here.
    if args.report:
        csv_path = args.trades_csv or trades_path
        if trades_df is None:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(
                    f"No existe trades.csv para report. Esperado en: {csv_path}. "
                    f"Ejecuta primero con --paper o pasa --trades_csv."
                )
            trades_df = pd.read_csv(csv_path)

        if trades_df.empty:
            print("\n=== REPORT ===")
            print("No se genera report porque no hay trades en trades_df/trades.csv.")
            return

        report_path = _generate_report(
            outdir=outdir,
            ticker=args.ticker,
            strategy_name=strat.name,
            backtest_metrics=metrics,
            trades_path=trades_path,
        )
        print(f"\nSaved: {report_path}")


if __name__ == "__main__":
    main()