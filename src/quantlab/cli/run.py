from __future__ import annotations

import os
from typing import Callable, Any


def run_classic_pipeline(
    args,
    *,
    fetch_ohlc: Callable[..., Any],
    add_indicators: Callable[..., Any],
    strategy_cls: Any,
    run_backtest: Callable[..., Any],
    compute_metrics: Callable[..., Any],
    run_paper_broker: Callable[..., Any],
    save_trades_csv: Callable[..., Any],
    write_trade_report: Callable[..., Any],
):
    """
    Execute the classic QuantLab pipeline.

    This function contains the original pipeline previously located
    in main.py.
    """

    outdir = args.outdir or "outputs"
    os.makedirs(outdir, exist_ok=True)

    print("\n=== QUANTLAB RUN ===")

    # --- DATA FETCH ---
    df = fetch_ohlc(
        ticker=args.ticker,
        start=args.start,
        end=args.end,
        interval=args.interval,
    )

    if df is None or len(df) == 0:
        raise RuntimeError("No OHLC data returned")

    # --- INDICATORS ---
    df = add_indicators(df)

    # --- STRATEGY ---
    strategy = strategy_cls(
        rsi_buy_max=args.rsi_buy_max,
        rsi_sell_min=args.rsi_sell_min,
        cooldown_days=args.cooldown_days,
    )

    signals = strategy.generate_signals(df)

    # --- BACKTEST ---
    backtest_result = run_backtest(
        df,
        signals,
        fee=args.fee,
    )

    metrics = compute_metrics(backtest_result)

    print("\n=== METRICS ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    # --- PAPER BROKER ---
    if args.paper:
        print("\n=== PAPER BROKER ===")

        trades = run_paper_broker(
            df,
            signals,
            initial_cash=args.initial_cash,
            fee=args.fee,
            slippage_bps=args.slippage_bps,
            slippage_mode=args.slippage_mode,
            k_atr=args.k_atr,
        )

        trades_path = save_trades_csv(trades, outdir)

        print(f"Trades saved to {trades_path}")

        write_trade_report(
            trades_path,
            outdir,
        )