import os
import pandas as pd

from quantlab.data.sources import fetch_ohlc
from quantlab.features.indicators import add_indicators
from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
from quantlab.backtest.engine import run_backtest
from quantlab.backtest.metrics import compute_metrics
from quantlab.execution.paper import run_paper_broker, save_trades_csv
from quantlab.reporting.charts import plot_basic_equity, plot_price_signals
from quantlab.cli.report import generate_legacy_report


def handle_run_command(args) -> bool:
    """
    Execute the standard single-run backtest simulation.

    Returns True because this is the fallback executable run mode.
    """

    outdir = args.outdir or "outputs"
    os.makedirs(outdir, exist_ok=True)

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

    equity_path = os.path.join(outdir, "equity.png")
    plot_basic_equity(bt, equity_path, args.ticker, strat.name)
    print(f"\nSaved: {equity_path}")

    if args.save_price_plot:
        price_path = os.path.join(outdir, "price_signals.png")
        plot_price_signals(df, signals, price_path, args.ticker, strat.name)
        print(f"Saved: {price_path}")

    # 5) Paper broker (optional)
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

    # 6) Legacy report mode
    if args.report:
        csv_path = args.trades_csv or trades_path
        if trades_df is None:
            if not os.path.exists(csv_path):
                print(f"ERROR: No existe trades.csv para report. Esperado en: {csv_path}")
                return None
            trades_df = pd.read_csv(csv_path)

        if trades_df.empty:
            print("\n=== REPORT ===")
            print("No se genera report porque no hay trades.")
        else:
            report_path = generate_legacy_report(
                outdir=outdir,
                ticker=args.ticker,
                strategy_name=strat.name,
                backtest_metrics=metrics,
                trades_path=csv_path,
            )
            print(f"\nSaved: {report_path}")

    return {
        "run_id": None,
        "artifacts_path": outdir,
        "report_path": os.path.join(outdir, "report.json") if os.path.exists(os.path.join(outdir, "report.json")) else None
    }


# Backward-compatible alias for older refactor paths / tests
run_classic_pipeline = handle_run_command
