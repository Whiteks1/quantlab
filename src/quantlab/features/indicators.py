import pandas as pd
import ta

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    close = out["close"].squeeze()  # 👈 clave (garantiza 1D)
    out["close"] = close            # deja la columna normalizada

    out["rsi"] = ta.momentum.RSIIndicator(close=close, window=14).rsi()
    out["ma20"] = close.rolling(20).mean()
    out["ma100"] = close.rolling(100).mean()

    if "high" in out.columns and "low" in out.columns:
        high = out["high"].squeeze()
        low = out["low"].squeeze()
        out["high"] = high
        out["low"] = low

        out["atr"] = ta.volatility.AverageTrueRange(
            high=high,
            low=low,
            close=close,
            window=14
        ).average_true_range()
    else:
        out["atr"] = 0.0

    return out.dropna()