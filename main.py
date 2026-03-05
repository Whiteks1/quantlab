import argparse
import os

import pandas as pd
from dotenv import load_dotenv
import matplotlib.pyplot as plt

from quantlab.data.sources import fetch_ohlc
from quantlab.features.indicators import add_indicators
from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
from quantlab.backtest.engine import run_backtest
from quantlab.backtest.metrics import compute_metrics
from quantlab.execution.paper import run_paper_broker, save_trades_csv
from quantlab.reporting.report import write_report as write_trade_report
from quantlab.reporting.run_report import write_report as write_run_report
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
        "backtest_metrics": backtest_metrics
    }
    
    report_md = os.path.join(outdir, "report.md")
    report_json = os.path.join(outdir, "report.json")
    
    payload = write_trade_report(
        trades_csv_path=trades_path,
        out_md_path=report_md,
        out_json_path=report_json,
        meta=meta
    )

    metrics = payload.get("metrics", {})
    print("\n=== TRADE-LEVEL METRICS ===")
    print(f"Total Trades:  {metrics.get('trades', 0)}")
    print(f"Win Rate:      {metrics.get('win_rate_trades', 0.0):.2%}")
    print(f"Profit Factor: {metrics.get('profit_factor', 0.0):.2f}")
    print(f"Expectancy:    {metrics.get('expectancy_net', 0.0):.4f}")

    return report_md


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

    args = parser.parse_args()

    # --- SWEEP MODE (exits early) ---
    if args.sweep:
        # If sweep_outdir is set, use it. Otherwise, if outdir is set, use it.
        # If both are None, run_sweep will create a unique dir in outputs/runs/
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

    # 6) Report (opcional)
    if args.report:
        # Si args.report es un string, es un path a un run_dir
        if isinstance(args.report, str):
            if os.path.isdir(args.report):
                write_run_report(args.report)
                print(f"\nStandardized run report generated for: {args.report}")
                return
            else:
                print(f"\nError: {args.report} is not a valid directory.")
                return

        # Comportamiento legacy: report de trade de la ejecución actual
        if trades_df is None:
            csv_path = args.trades_csv or trades_path
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
            trades_path=csv_path if trades_df is None else trades_path,
        )
        print(f"\nSaved: {report_path}")
    

if __name__ == "__main__":
    main()