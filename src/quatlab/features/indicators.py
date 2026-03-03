import pandas as pd
import ta

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    close = out["close"]

    out["rsi"] = ta.momentum.RSIIndicator(close=close, window=14).rsi()
    out["ma20"] = close.rolling(20).mean()
    out["ma100"] = close.rolling(100).mean()

    # ATR necesita high/low/close reales. Si faltan, fallará.
    if "high" in out.columns and "low" in out.columns:
        out["atr"] = ta.volatility.AverageTrueRange(
            high=out["high"],
            low=out["low"],
            close=close,
            window=14
        ).average_true_range()
    else:
        out["atr"] = 0.0

    return out.dropna()