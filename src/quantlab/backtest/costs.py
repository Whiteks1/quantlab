from __future__ import annotations
import pandas as pd


def slippage_fixed(slippage_bps: float) -> float:
    """
    Devuelve slippage como fracción.
    bps = basis points. 10 bps = 0.10%
    """
    return float(slippage_bps) / 10_000.0


def slippage_atr(
    df: pd.DataFrame,
    i: int,
    k_atr: float = 0.05,
    floor_bps: float = 2.0,
    cap_bps: float = 30.0,
) -> float:
    """
    Slippage dinámico aproximado:
      slip ≈ k_atr * (ATR / close) con límites [floor, cap]
    Requiere columnas 'atr' y 'close'.

    - k_atr: sensibilidad (0.03–0.10 suele ser razonable para empezar)
    - floor_bps: mínimo slippage
    - cap_bps: máximo slippage
    """
    close = float(df["close"].iat[i])
    atr = float(df["atr"].iat[i]) if "atr" in df.columns else 0.0

    if close <= 0:
        return slippage_fixed(floor_bps)

    raw = k_atr * (atr / close)  # fracción
    floor = slippage_fixed(floor_bps)
    cap = slippage_fixed(cap_bps)

    return max(floor, min(cap, raw))


def exec_price(close: float, side: str, slippage: float) -> float:
    """
    side: 'BUY' o 'SELL'
    """
    close = float(close)
    slippage = float(slippage)
    if side.upper() == "BUY":
        return close * (1.0 + slippage)
    if side.upper() == "SELL":
        return close * (1.0 - slippage)
    raise ValueError("side must be BUY or SELL")