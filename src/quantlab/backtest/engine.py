import numpy as np
import pandas as pd

try:
    from numba import njit
except ImportError:  # pragma: no cover - optional dependency
    njit = None


def _slippage_fixed_fraction(slippage_bps: float) -> float:
    return float(slippage_bps) / 10_000.0


def _slippage_atr_fraction(
    close_value: float,
    atr_value: float,
    *,
    k_atr: float,
    floor_bps: float = 2.0,
    cap_bps: float = 30.0,
) -> float:
    if close_value <= 0.0:
        return _slippage_fixed_fraction(floor_bps)

    raw = k_atr * (atr_value / close_value)
    floor = _slippage_fixed_fraction(floor_bps)
    cap = _slippage_fixed_fraction(cap_bps)
    return max(floor, min(cap, raw))


def _run_backtest_kernel_python(
    sig: np.ndarray,
    close: np.ndarray,
    atr: np.ndarray,
    *,
    fee_rate: float,
    slippage_bps: float,
    slippage_mode: str,
    k_atr: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = len(sig)
    positions = np.zeros(n, dtype=np.int64)

    pos = 0
    for i in range(n):
        s = int(sig[i])
        if s == 1 and pos == 0:
            pos = 1
        elif s == -1 and pos == 1:
            pos = 0
        positions[i] = pos

    prev_positions = np.concatenate((np.array([0], dtype=np.int64), positions[:-1]))
    trade = positions - prev_positions

    fees = np.zeros(n, dtype=np.float64)
    slip_cost = np.zeros(n, dtype=np.float64)

    for i in range(n):
        if trade[i] == 0:
            continue

        fees[i] = float(fee_rate)
        if slippage_mode == "atr":
            slip_cost[i] = _slippage_atr_fraction(
                float(close[i]),
                float(atr[i]),
                k_atr=k_atr,
            )
        else:
            slip_cost[i] = _slippage_fixed_fraction(slippage_bps)

    return positions, trade, fees, slip_cost


if njit is not None:  # pragma: no branch

    @njit(cache=True)
    def _run_backtest_kernel_numba(  # pragma: no cover - covered via integration-style test
        sig: np.ndarray,
        close: np.ndarray,
        atr: np.ndarray,
        fee_rate: float,
        slippage_bps: float,
        slippage_mode_code: int,
        k_atr: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        n = len(sig)
        positions = np.zeros(n, dtype=np.int64)

        pos = 0
        for i in range(n):
            s = int(sig[i])
            if s == 1 and pos == 0:
                pos = 1
            elif s == -1 and pos == 1:
                pos = 0
            positions[i] = pos

        trade = np.zeros(n, dtype=np.int64)
        prev = 0
        for i in range(n):
            trade[i] = positions[i] - prev
            prev = positions[i]

        fees = np.zeros(n, dtype=np.float64)
        slip_cost = np.zeros(n, dtype=np.float64)

        fixed_slippage = slippage_bps / 10_000.0
        floor = 2.0 / 10_000.0
        cap = 30.0 / 10_000.0

        for i in range(n):
            if trade[i] == 0:
                continue

            fees[i] = fee_rate
            if slippage_mode_code == 1:
                close_value = close[i]
                atr_value = atr[i]
                if close_value <= 0.0:
                    slip_cost[i] = floor
                else:
                    raw = k_atr * (atr_value / close_value)
                    if raw < floor:
                        slip_cost[i] = floor
                    elif raw > cap:
                        slip_cost[i] = cap
                    else:
                        slip_cost[i] = raw
            else:
                slip_cost[i] = fixed_slippage

        return positions, trade, fees, slip_cost


def available_backtest_backends() -> tuple[str, ...]:
    backends = ["python"]
    if njit is not None:
        backends.append("numba")
    return tuple(backends)


def run_backtest(
    df: pd.DataFrame,
    signals: pd.Series,
    fee_rate: float = 0.002,
    slippage_bps: float = 8.0,
    slippage_mode: str = "fixed",  # "fixed" | "atr"
    k_atr: float = 0.05,
    backend: str = "python",
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

    # Señales alineadas
    sig = signals.reindex(out.index).fillna(0).astype(int).to_numpy()
    out["signal"] = sig

    close = out["close"].to_numpy(dtype=float)
    atr = out["atr"].to_numpy(dtype=float) if "atr" in out.columns else np.zeros(len(out), dtype=float)

    if backend == "python":
        positions, trade, fees, slip_cost = _run_backtest_kernel_python(
            sig,
            close,
            atr,
            fee_rate=fee_rate,
            slippage_bps=slippage_bps,
            slippage_mode=slippage_mode,
            k_atr=k_atr,
        )
    elif backend == "numba":
        if njit is None:
            raise RuntimeError("Numba backend requested but numba is not installed.")
        slippage_mode_code = 1 if slippage_mode == "atr" else 0
        positions, trade, fees, slip_cost = _run_backtest_kernel_numba(
            sig.astype(np.int64),
            close,
            atr,
            float(fee_rate),
            float(slippage_bps),
            slippage_mode_code,
            float(k_atr),
        )
    else:
        raise ValueError(f"Unsupported backtest backend: {backend}")

    out["position"] = positions

    # Returns close-to-close
    out["ret"] = out["close"].pct_change().fillna(0.0)

    # Retorno estrategia usa position(t-1)
    pos_shift = pd.Series(positions, index=out.index).shift(1).fillna(0).to_numpy()
    out["strategy_ret"] = out["ret"].to_numpy() * pos_shift

    out["trade"] = trade

    out["fees"] = fees
    out["slip_cost"] = slip_cost

    out["strategy_ret_net"] = out["strategy_ret"] - out["fees"] - out["slip_cost"]
    out["equity"] = (1.0 + out["strategy_ret_net"]).cumprod()

    return out
