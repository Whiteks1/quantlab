import argparse
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt

from quantlab.data.sources import fetch_ohlc
from quantlab.features.indicators import add_indicators
from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
from quantlab.backtest.engine import run_backtest
from quantlab.backtest.metrics import compute_metrics

def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="ETH-USD")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2024-01-01")
    parser.add_argument("--fee", type=float, default=0.002)
    args = parser.parse_args()

    df = fetch_ohlc(args.ticker, args.start, args.end, interval="1d")
    df = add_indicators(df)

    strat = RsiMaAtrStrategy()
    signals = strat.generate_signals(df)

    bt = run_backtest(df, signals, fee_rate=args.fee)
    metrics = compute_metrics(bt)

    print("\n=== METRICS ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    os.makedirs("outputs", exist_ok=True)
    plt.figure(figsize=(12, 6))
    plt.plot(bt.index, bt["equity"], label="Equity (net)")
    plt.title(f"Equity Curve — {args.ticker} — {strat.name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("outputs/equity.png")
    print("\nSaved: outputs/equity.png")

if __name__ == "__main__":
    main()