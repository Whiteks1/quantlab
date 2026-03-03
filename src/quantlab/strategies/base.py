from dataclasses import dataclass
import pandas as pd

@dataclass
class SignalResult:
    # 1 = long/buy, -1 = exit/sell, 0 = hold
    signal: int
    reason: str

class Strategy:
    name: str = "base"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Devuelve una serie de señales (1,0,-1) indexada igual que df."""
        raise NotImplementedError