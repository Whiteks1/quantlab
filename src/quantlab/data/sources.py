import yfinance as yf
import pandas as pd

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Si vienen columnas MultiIndex, aplánalas: ('Close','ETH-USD') -> 'close'
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    return df

def fetch_ohlc(ticker: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
    df = yf.download(
        ticker,
        start=start,
        end=end,
        interval=interval,
        progress=False,
        auto_adjust=True,
        group_by="column",
    )

    if df is None or df.empty:
        raise ValueError(f"No se pudieron descargar datos para {ticker}")

    df = _flatten_columns(df)
    df = df.rename(columns=str.lower)

    # Asegura que estas columnas sean Series 1D
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = df[col].squeeze()

    # Nos quedamos con OHLCV estándar si existe
    keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    return df[keep].dropna()