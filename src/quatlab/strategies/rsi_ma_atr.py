import pandas as pd
from .base import Strategy

class RsiMaAtrStrategy(Strategy):
    name = "rsi_ma_atr_v1"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        sig = pd.Series(0, index=df.index, dtype=int)

        buy = (df["rsi"] < 30) & (df["close"] > df["ma20"])
        sell = (df["rsi"] > 70) | (df["close"] < df["ma20"] * 0.98)

        sig.loc[buy] = 1
        sig.loc[sell] = -1
        return sig