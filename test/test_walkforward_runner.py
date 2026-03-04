import pytest
import pandas as pd

import quantlab.experiments.runner as runner


def test_walkforward_selection_and_constraints(monkeypatch, tmp_path):
    """
    - Aplica constraint min_trade_trades
    - Selecciona top_k en TRAIN
    - Evalúa exactamente top_k en TEST
    - No mete 'param_grid' como columna basura
    """

    def fake_run_one(cfg):
        # Determinístico y rápido: NO yfinance, NO red.
        rsi_buy = float(cfg.get("rsi_buy_max", 60.0))
        rsi_sell = float(cfg.get("rsi_sell_min", 75.0))
        cooldown = int(cfg.get("cooldown_days", 0))

        # Forzamos constraint: sell_min=70 => pocos trades (filtrable)
        trade_trades = 2 if rsi_sell == 70.0 else (3 if rsi_sell == 75.0 else 4)

        # Métrica TRAIN vs TEST diferenciada por ventana (start)
        is_test = str(cfg.get("start")) == "2023-07-01"
        if is_test:
            sharpe = 1.0 + (rsi_sell / 100.0) + (rsi_buy / 1000.0) - (cooldown * 0.01)
            total_return = 0.05 + (rsi_sell / 1000.0) - (cooldown * 0.002)
        else:
            sharpe = (rsi_sell / 100.0) + (rsi_buy / 1000.0) - (cooldown * 0.01)
            total_return = (rsi_sell / 1000.0) - (cooldown * 0.002)

        return {
            "ticker": cfg["ticker"],
            "start": cfg["start"],
            "end": cfg["end"],
            "interval": cfg["interval"],
            "fee": cfg.get("fee", 0.002),
            "slippage_mode": cfg.get("slippage_mode", "fixed"),
            "slippage_bps": cfg.get("slippage_bps", 8.0),
            "k_atr": cfg.get("k_atr", 0.05),
            "cooldown_days": cooldown,
            "rsi_buy_max": rsi_buy,
            "rsi_sell_min": rsi_sell,
            "total_return": total_return,
            "max_drawdown": -0.1,
            "sharpe_simple": sharpe,
            "trades": 10,
            "trade_trades": trade_trades,
            "win_rate_trades": 0.5,
            "profit_factor": 1.2,
            "expectancy_net": 1.0,
            "avg_holding_days": 5.0,
            "exposure": 0.5,
        }

    # Monkeypatch del run_one REAL
    monkeypatch.setattr(runner, "run_one", fake_run_one)

    config = {
        "ticker": "ETH-USD",
        "interval": "1d",
        "fee": 0.002,
        "slippage_mode": "fixed",
        "slippage_bps": 8.0,
        "k_atr": 0.05,
        "param_grid": {
            "rsi_buy_max": [55.0, 60.0],
            "rsi_sell_min": [70.0, 75.0, 80.0],
            "cooldown_days": [0],
        },
        "splits": [
            {
                "name": "H1_2023_train__H2_2023_test",
                "train": {"start": "2023-01-01", "end": "2023-07-01"},
                "test": {"start": "2023-07-01", "end": "2024-01-01"},
            }
        ],
        "selection": {
            "sort_by": ["sharpe_simple", "total_return"],
            "ascending": [False, False],
            "top_k": 2,
        },
        "constraints": {"min_trade_trades": 3},
    }

    out_csv = tmp_path / "walkforward.csv"
    summary_csv = tmp_path / "walkforward_summary.csv"

    df = runner.run_walkforward(config, out_csv=str(out_csv), summary_csv=str(summary_csv))

    # Sanity
    assert not df.empty
    assert "phase" in df.columns
    assert "selected" in df.columns

    # IMPORTANT: no queremos 'param_grid' como columna en resultados
    assert "param_grid" not in df.columns

    train = df[df["phase"] == "train"].copy()
    test = df[df["phase"] == "test"].copy()

    # Constraint: sell_min=70 => trade_trades=2 => fuera
    assert (train[train["rsi_sell_min"] == 70.0]["trade_trades"] < 3).all()
    # top_k=2 seleccionados en train (después del filtro)
    assert int(train["selected"].sum()) == 2
    # y exactamente 2 runs en test
    assert len(test) == 2

    # Los parámetros del test deben corresponder con los ranks seleccionados del train
    for rank in [1, 2]:
        tr = train[train["rank_in_train"] == rank].iloc[0]
        te = test[test["rank_in_train"] == rank].iloc[0]
        assert te["rsi_buy_max"] == tr["rsi_buy_max"]
        assert te["rsi_sell_min"] == tr["rsi_sell_min"]
        assert te["cooldown_days"] == tr["cooldown_days"]

    # Summary file existe y tiene n_selected=2, n_test_runs=2
    s = pd.read_csv(summary_csv)
    assert int(s.loc[0, "n_selected"]) == 2
    assert int(s.loc[0, "n_test_runs"]) == 2