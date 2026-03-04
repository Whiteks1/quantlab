import pandas as pd
from .base import Strategy


class RsiMaAtrStrategy(Strategy):
    """
    Estrategia v2 (más "tradeable" que la v1):

    Entrada (BUY = 1):
      - Cruce alcista del precio por encima de MA20 (close cruza de abajo hacia arriba)
      - RSI no demasiado alto (evita entrar tarde en sobrecompra)
        -> rsi < 60 (ajustable)

    Salida (SELL = -1):
      - Cruce bajista del precio por debajo de MA20
      O
      - RSI muy alto (toma de beneficio / sobrecompra)
        -> rsi > 75 (ajustable)

    Extras:
      - Cooldown en días tras una operación (opcional)
        para evitar entrar/salir demasiado seguido.
    """

    name = "rsi_ma_cross_v2"

    def __init__(self, rsi_buy_max: float = 60.0, rsi_sell_min: float = 75.0, cooldown_days: int = 0):
        self.rsi_buy_max = float(rsi_buy_max)
        self.rsi_sell_min = float(rsi_sell_min)
        self.cooldown_days = int(cooldown_days)

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df.empty:
            return pd.Series(dtype=int)

        required = {"close", "ma20", "rsi"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Faltan columnas requeridas para la estrategia: {sorted(missing)}")

        close = df["close"]
        ma20 = df["ma20"]
        rsi = df["rsi"]

        # Cruces
        cross_up = (close > ma20) & (close.shift(1) <= ma20.shift(1))
        cross_down = (close < ma20) & (close.shift(1) >= ma20.shift(1))

        # Condiciones base
        buy_cond = cross_up & (rsi < self.rsi_buy_max)
        sell_cond = cross_down | (rsi > self.rsi_sell_min)

        # Señales resultantes (1, 0, -1) con "estado" para evitar BUY repetidos estando dentro
        signals = pd.Series(0, index=df.index, dtype=int)

        in_position = False
        cooldown = 0

        for i in range(len(df)):
            if cooldown > 0:
                cooldown -= 1
                signals.iloc[i] = 0
                continue

            if not in_position:
                if bool(buy_cond.iloc[i]):
                    signals.iloc[i] = 1
                    in_position = True
                    cooldown = self.cooldown_days
            else:
                if bool(sell_cond.iloc[i]):
                    signals.iloc[i] = -1
                    in_position = False
                    cooldown = self.cooldown_days

        return signals