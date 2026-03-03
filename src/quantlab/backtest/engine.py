import pandas as pd

def run_backtest(df: pd.DataFrame, signals: pd.Series, fee_rate: float = 0.002) -> pd.DataFrame:
    """
    Backtest simplificado:
    - Posición: 1 cuando entra, 0 cuando sale.
    - Ejecuta al cierre del día (simplificación).
    - Aplica comisión al entrar y al salir.
    """
    out = df.copy()
    out["signal"] = signals
    out["position"] = 0

    pos = 0
    for i in range(len(out)):
        s = int(out["signal"].iloc[i])
        if s == 1 and pos == 0:
            pos = 1
            out.iloc[i, out.columns.get_loc("position")] = pos
        elif s == -1 and pos == 1:
            pos = 0
            out.iloc[i, out.columns.get_loc("position")] = pos
        else:
            out.iloc[i, out.columns.get_loc("position")] = pos

    # Returns
    out["ret"] = out["close"].pct_change().fillna(0.0)
    out["strategy_ret"] = out["ret"] * out["position"].shift(1).fillna(0)

    # Comisiones: cuando cambia position (entry/exit)
    out["trade"] = out["position"].diff().fillna(out["position"])
    out["fees"] = 0.0
    out.loc[out["trade"].abs() > 0, "fees"] = fee_rate

    out["strategy_ret_net"] = out["strategy_ret"] - out["fees"]
    out["equity"] = (1.0 + out["strategy_ret_net"]).cumprod()

    return out