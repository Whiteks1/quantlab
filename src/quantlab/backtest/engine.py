import numpy as np
import pandas as pd

from quantlab.backtest.costs import slippage_fixed, slippage_atr


def run_backtest(
    df: pd.DataFrame,
    signals: pd.Series,
    fee_rate: float = 0.002,
    slippage_bps: float = 8.0,
    slippage_mode: str = "fixed",  # "fixed" | "atr"
    k_atr: float = 0.05,
) -> pd.DataFrame:
    """
    Backtest simplificado (CoW-safe para pandas 3.x):
      - position se construye en un array y luego se asigna 1 vez
      - fees/slippage se aplican el día del trade como penalización
    """
    out = df.copy()
    if out.empty:
        # Return empty df with expected columns
        for col in ["signal", "position", "ret", "strategy_ret", "trade", "fees", "slip_cost", "strategy_ret_net", "equity"]:
            out[col] = pd.Series(dtype=float)
        return out

    if out.empty:
        raise ValueError(
            "run_backtest received an empty DataFrame. Check data loading, date range, and preprocessing."
        )

    # Señales alineadas
    sig = signals.reindex(out.index).fillna(0).astype(int).to_numpy()
    out["signal"] = sig

    n = len(out)
    positions = np.zeros(n, dtype=int)

    # Construir posición (estado)
    pos = 0
    for i in range(n):
        s = int(sig[i])
        if s == 1 and pos == 0:
            pos = 1
        elif s == -1 and pos == 1:
            pos = 0
        positions[i] = pos

    out["position"] = positions

    # Returns close-to-close
    out["ret"] = out["close"].pct_change().fillna(0.0)

    # Retorno estrategia usa position(t-1)
    pos_shift = pd.Series(positions, index=out.index).shift(1).fillna(0).to_numpy()
    out["strategy_ret"] = out["ret"].to_numpy() * pos_shift

    # Trades: entry/exit
    trade = np.diff(positions, prepend=positions[0])
    out["trade"] = trade

    # Costes
    fees = np.zeros(n, dtype=float)
    slip_cost = np.zeros(n, dtype=float)

    for i in range(n):
        if trade[i] == 0:
            continue

        # comisión (aprox) como penalización fija en el día del trade
        fees[i] = float(fee_rate)

        # slippage (fixed o atr) como penalización adicional en el día del trade
        if slippage_mode == "atr":
            slip = slippage_atr(out, i, k_atr=k_atr)
        else:
            slip = slippage_fixed(slippage_bps)

        slip_cost[i] = slip

    out["fees"] = fees
    out["slip_cost"] = slip_cost

    out["strategy_ret_net"] = out["strategy_ret"] - out["fees"] - out["slip_cost"]
    out["equity"] = (1.0 + out["strategy_ret_net"]).cumprod()

    return out