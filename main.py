import argparse
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt

from quantlab.data.sources import fetch_ohlc
from quantlab.features.indicators import add_indicators
from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
from quantlab.backtest.engine import run_backtest
from quantlab.backtest.metrics import compute_metrics
from quantlab.execution.paper import run_paper_broker, save_trades_csv


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
    parser.add_argument("--outdir", default="outputs")
    parser.add_argument("--save_price_plot", action="store_true")

    # Paper broker
    parser.add_argument("--paper", action="store_true", help="Ejecuta paper broker + CSV de trades")
    parser.add_argument("--initial_cash", type=float, default=1000.0, help="Cash inicial para paper broker")

    args = parser.parse_args()

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
    signals = strat.generate_signals(df)

    buys = int((signals == 1).sum())
    sells = int((signals == -1).sum())
    print("\n=== SIGNALS ===")
    print(f"strategy: {strat.name}")
    print(f"BUY signals:  {buys}")
    print(f"SELL signals: {sells}")

    os.makedirs(args.outdir, exist_ok=True)

    # 4) Backtest (equity curve “vectorizada”)
    bt = run_backtest(df, signals, fee_rate=args.fee)
    metrics = compute_metrics(bt)

    print("\n=== BACKTEST METRICS ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    equity_path = os.path.join(args.outdir, "equity.png")
    plt.figure(figsize=(12, 6))
    plt.plot(bt.index, bt["equity"], label="Equity (net)")
    plt.title(f"Equity Curve — {args.ticker} — {strat.name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(equity_path)
    plt.close()
    print(f"\nSaved: {equity_path}")

    if args.save_price_plot:
        price_path = os.path.join(args.outdir, "price_signals.png")
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df["close"], label="Close")
        plt.plot(df.index, df["ma20"], label="MA20", linestyle="--")

        buy_idx = df.index[signals == 1]
        sell_idx = df.index[signals == -1]
        plt.scatter(buy_idx, df.loc[buy_idx, "close"], marker="^", s=100, label="BUY")
        plt.scatter(sell_idx, df.loc[sell_idx, "close"], marker="v", s=100, label="SELL")

        plt.title(f"Price + Signals — {args.ticker} — {strat.name}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(price_path)
        plt.close()
        print(f"Saved: {price_path}")

    # 5) Paper broker + logging (Etapa C temprana)
    if args.paper:
        trades_df = run_paper_broker(
            df=df,
            signals=signals,
            initial_cash=args.initial_cash,
            fee_rate=args.fee,
        )
        trades_path = os.path.join(args.outdir, "trades.csv")
        save_trades_csv(trades_df, trades_path)

        print("\n=== PAPER BROKER ===")
        print(f"Initial cash: {args.initial_cash}")
        print(f"Trades logged: {len(trades_df)}")
        print(f"Saved: {trades_path}")

        if not trades_df.empty:
            print("\nLast trades:")
            print(trades_df.tail(10))


if __name__ == "__main__":
    main()