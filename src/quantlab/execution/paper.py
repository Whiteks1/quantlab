from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import pandas as pd


@dataclass
class Trade:
    timestamp: pd.Timestamp
    side: str              # "BUY" | "SELL"
    price: float
    qty: float
    fee: float
    equity_after: float
    reason: str = ""


def run_paper_broker(
    df: pd.DataFrame,
    signals: pd.Series,
    initial_cash: float = 1000.0,
    fee_rate: float = 0.002,
) -> pd.DataFrame:
    """
    Paper broker simple:
      - Estado: cash + position_qty
      - Compra: invierte TODO el cash en el activo (market al close) cuando signal==1
      - Venta: liquida TODA la posición cuando signal==-1
      - Fee: proporcional al notional de cada operación
      - Log: devuelve DataFrame de trades
    """
    if df.empty:
        raise ValueError("df está vacío")
    if "close" not in df.columns:
        raise ValueError("df debe tener columna 'close'")

    # Alinea señales al índice del df
    signals = signals.reindex(df.index).fillna(0).astype(int)

    cash = float(initial_cash)
    qty = 0.0
    trades: List[Trade] = []

    for ts, row in df.iterrows():
        price = float(row["close"])
        s = int(signals.loc[ts])

        # BUY (si estás fuera)
        if s == 1 and qty == 0.0 and cash > 0.0:
            notional = cash
            fee = notional * fee_rate
            spend = notional - fee
            buy_qty = spend / price

            qty = buy_qty
            cash = 0.0

            equity = cash + qty * price
            trades.append(Trade(ts, "BUY", price, qty, fee, equity, reason="signal=1"))

        # SELL (si estás dentro)
        elif s == -1 and qty > 0.0:
            notional = qty * price
            fee = notional * fee_rate
            proceeds = notional - fee

            cash = proceeds
            qty = 0.0

            equity = cash
            trades.append(Trade(ts, "SELL", price, 0.0, fee, equity, reason="signal=-1"))

    # Trade log a DataFrame
    trades_df = pd.DataFrame([t.__dict__ for t in trades])
    return trades_df


def save_trades_csv(trades_df: pd.DataFrame, path: str) -> None:
    if trades_df is None or trades_df.empty:
        # Crea CSV vacío con columnas estándar para que sea predecible
        cols = ["timestamp", "side", "price", "qty", "fee", "equity_after", "reason"]
        pd.DataFrame(columns=cols).to_csv(path, index=False)
        return
    trades_df.to_csv(path, index=False)