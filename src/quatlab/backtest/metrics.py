import pandas as pd
import numpy as np

def compute_metrics(bt: pd.DataFrame) -> dict:
    equity = bt["equity"]
    total_return = float(equity.iloc[-1] - 1.0)

    # Drawdown
    peak = equity.cummax()
    dd = (equity / peak) - 1.0
    max_dd = float(dd.min())

    # Winrate (por días positivos con posición)
    active = bt["position"].shift(1).fillna(0) == 1
    wins = (bt.loc[active, "strategy_ret_net"] > 0).sum()
    total = active.sum()
    winrate = float(wins / total) if total > 0 else 0.0

    # Sharpe simple (diario) - sin tasa libre
    r = bt["strategy_ret_net"]
    sharpe = float(np.sqrt(252) * (r.mean() / (r.std() + 1e-12)))

    return {
        "total_return": total_return,
        "max_drawdown": max_dd,
        "winrate_active_days": winrate,
        "sharpe_simple": sharpe,
        "days": int(len(bt)),
        "trades": int((bt["trade"].abs() > 0).sum())
    }