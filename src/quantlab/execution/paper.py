from __future__ import annotations

from dataclasses import dataclass
from typing import List
import pandas as pd

from quantlab.backtest.costs import slippage_fixed, slippage_atr, exec_price


@dataclass
class Trade:
    timestamp: pd.Timestamp
    side: str              # "BUY" | "SELL"
    close: float
    exec_price: float
    qty: float
    fee: float
    equity_after: float
    slippage: float
    reason: str = ""


def run_paper_broker(
    df: pd.DataFrame,
    signals: pd.Series,
    initial_cash: float = 1000.0,
    fee_rate: float = 0.002,
    slippage_bps: float = 8.0,
    slippage_mode: str = "fixed",   # "fixed" | "atr"
    k_atr: float = 0.05,
) -> pd.DataFrame:
    if df.empty:
        raise ValueError("df está vacío")
    if "close" not in df.columns:
        raise ValueError("df debe tener columna 'close'")

    signals = signals.reindex(df.index).fillna(0).astype(int)

    cash = float(initial_cash)
    qty = 0.0
    trades: List[Trade] = []

    for i, (ts, row) in enumerate(df.iterrows()):
        close = float(row["close"])
        s = int(signals.loc[ts])

        if slippage_mode == "atr":
            slip = slippage_atr(df, i, k_atr=k_atr)
        else:
            slip = slippage_fixed(slippage_bps)

        # BUY
        if s == 1 and qty == 0.0 and cash > 0.0:
            px = exec_price(close, "BUY", slip)
            notional = cash
            fee = notional * fee_rate
            spend = notional - fee
            buy_qty = spend / px

            qty = buy_qty
            cash = 0.0
            equity = cash + qty * close  # mark-to-market al close

            trades.append(Trade(ts, "BUY", close, px, qty, fee, equity, slip, reason="signal=1"))

        # SELL
        elif s == -1 and qty > 0.0:
            px = exec_price(close, "SELL", slip)
            notional = qty * px
            fee = notional * fee_rate
            proceeds = notional - fee

            cash = proceeds
            qty = 0.0
            equity = cash

            trades.append(Trade(ts, "SELL", close, px, 0.0, fee, equity, slip, reason="signal=-1"))

    return pd.DataFrame([t.__dict__ for t in trades])


def save_trades_csv(trades_df: pd.DataFrame, path: str) -> None:
    cols = ["timestamp", "side", "close", "exec_price", "qty", "fee", "equity_after", "slippage", "reason"]
    if trades_df is None or trades_df.empty:
        pd.DataFrame(columns=cols).to_csv(path, index=False)
        return
    trades_df.to_csv(path, index=False)