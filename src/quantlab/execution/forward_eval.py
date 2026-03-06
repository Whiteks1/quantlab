"""
forward_eval.py – Stage L: forward evaluation and paper portfolio for QuantLab.

Provides a sequential, stateful paper-trading simulation over a selected
candidate strategy derived from an existing research run.

Key concepts
------------
CandidateConfig
    Immutable record of which strategy + params were selected for forward
    evaluation, and from which run they came.

PortfolioState
    Mutable portfolio snapshot persisted between (and within) sessions.
    Always JSON-safe.

Workflow
--------
1.  ``load_candidate_from_run(run_dir)``  →  ``CandidateConfig``
2.  ``build_strategy(candidate)``         →  ``Strategy`` instance
3.  ``run_forward_evaluation(candidate, df, ...)``  →  dict with trades,
    equity curve, final portfolio state.
4.  ``write_forward_eval_artifacts(result, out_dir)`` → list of file paths.
5.  (Optional) ``load_portfolio_state(path)`` for session resume.

Functions
---------
load_candidate_from_run(run_dir, metric)     -> CandidateConfig
build_strategy(candidate)                    -> Strategy
run_forward_evaluation(candidate, df, ...)   -> dict
update_portfolio_state(state, trades_df, equity_series, ...) -> PortfolioState
write_forward_eval_artifacts(result, out_dir) -> list[str]
load_portfolio_state(path)                   -> PortfolioState
"""

from __future__ import annotations

import json
import math
import secrets
import uuid
import warnings
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from quantlab.backtest.costs import slippage_fixed, slippage_atr, exec_price
from quantlab.features.indicators import add_indicators


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Strategy registry: maps strategy_name -> constructor callable.
#: Extend this dict to support additional strategies in future stages.
_STRATEGY_REGISTRY: Dict[str, Any] = {}


def _register_strategy(name: str):
    """Decorator to register a strategy class by name."""
    def _inner(cls):
        _STRATEGY_REGISTRY[name] = cls
        return cls
    return _inner


# Lazy-register known strategies at import time.
try:
    from quantlab.strategies.rsi_ma_atr import RsiMaAtrStrategy
    _STRATEGY_REGISTRY["rsi_ma_cross_v2"] = RsiMaAtrStrategy
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class CandidateConfig:
    """
    Immutable snapshot of the candidate selected for forward evaluation.

    Attributes
    ----------
    strategy_name:
        Name matching ``Strategy.name`` (e.g. ``"rsi_ma_cross_v2"``).
    params:
        Dict of strategy hyper-parameters (e.g. ``rsi_buy_max``, …).
    fee_rate:
        Transaction fee rate (e.g. 0.002 = 0.2 %).
    slippage_bps:
        Fixed slippage in basis points.
    slippage_mode:
        ``"fixed"`` or ``"atr"``.
    k_atr:
        ATR slippage sensitivity (used only when slippage_mode == "atr").
    source_run_id:
        ``run_id`` of the originating research run.
    source_run_dir:
        Absolute path to the source run directory.
    selection_metric:
        Which metric was used to pick this candidate (e.g. ``"sharpe_simple"``).
    selection_value:
        Value of the selection metric for this candidate.  May be ``None``.
    selected_at:
        ISO-8601 timestamp when the candidate was selected.
    ticker:
        Ticker symbol inferred from the source run (if available).
    interval:
        OHLC bar interval (e.g. ``"1d"``).
    """

    strategy_name: str
    params: Dict[str, Any]
    fee_rate: float = 0.002
    slippage_bps: float = 8.0
    slippage_mode: str = "fixed"
    k_atr: float = 0.05
    source_run_id: str = ""
    source_run_dir: str = ""
    selection_metric: str = "sharpe_simple"
    selection_value: Optional[float] = None
    selected_at: str = ""
    ticker: str = ""
    interval: str = "1d"
    initial_cash: float = 10_000.0


@dataclass
class PortfolioState:
    """
    Persistent paper portfolio state for a forward evaluation session.

    All fields are JSON-safe.  Persist with ``json.dump(asdict(state), ...)``
    and reload with ``load_portfolio_state(path)``.

    Attributes
    ----------
    session_id:   Unique ID for this forward-eval session.
    mode:         Always ``"forward_paper"`` in Stage L.
    eval_start:   ISO date string for forward period start.
    eval_end:     ISO date string for forward period end.
    cash:         Current cash balance.
    qty:          Current asset quantity held.
    current_equity: Mark-to-market portfolio value at last bar.
    total_fees:   Cumulative fees paid.
    total_slippage: Cumulative slippage incurred.
    last_timestamp: ISO timestamp of the last processed bar (or ``None``).
    n_trades:     Total number of executed trade legs (BUY + SELL).
    candidate:    Serialised ``CandidateConfig`` dict.
    created_at:   When this state was first created.
    updated_at:   When this state was last written.
    """

    session_id: str
    mode: str = "forward_paper"
    eval_start: str = ""
    eval_end: str = ""
    cash: float = 0.0
    qty: float = 0.0
    current_equity: float = 0.0
    total_fees: float = 0.0
    total_slippage: float = 0.0
    last_timestamp: Optional[str] = None
    n_trades: int = 0
    candidate: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    # Stage L.1: Transparency fields
    starting_cash: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    has_open_position: bool = False
    open_position_qty: float = 0.0
    open_position_entry_price: Optional[float] = None
    open_position_mark_price: Optional[float] = None
    open_position_market_value: float = 0.0
    bars_fetched: int = 0
    warmup_bars: int = 0
    
    # Stage L.2: Resume / Continuity fields
    original_eval_start: str = ""
    resume_count: int = 0
    total_bars_evaluated: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe dict representation."""
        return _sanitize(asdict(self))


# ---------------------------------------------------------------------------
# JSON sanitisation
# ---------------------------------------------------------------------------

def _sanitize(obj: Any) -> Any:
    """Recursively make a nested structure strictly JSON-safe."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


# ---------------------------------------------------------------------------
# Candidate loading
# ---------------------------------------------------------------------------

def _pick_best_row(df: pd.DataFrame, metric: str) -> Optional[Dict[str, Any]]:
    """Pick the row with the highest numeric value of *metric*."""
    if df.empty or metric not in df.columns:
        return None
    valid = df[pd.to_numeric(df[metric], errors="coerce").notna()].copy()
    if valid.empty:
        return None
    valid["_sort"] = pd.to_numeric(valid[metric], errors="coerce")
    return valid.sort_values("_sort", ascending=False).iloc[0].drop("_sort").to_dict()


def load_candidate_from_run(
    run_dir: str | Path,
    metric: str = "sharpe_simple",
) -> CandidateConfig:
    """
    Derive a ``CandidateConfig`` from an existing research run directory.

    Resolution order for strategy params:
    1. ``leaderboard.csv``       (grid run — best row by *metric*)
    2. ``oos_leaderboard.csv``   (walkforward run — best OOS row)
    3. ``meta.json``             (fallback: use config defaults if present)

    Parameters
    ----------
    run_dir:
        Path to a completed QuantLab run directory.
    metric:
        Metric used to rank and select the best candidate row.

    Returns
    -------
    CandidateConfig

    Raises
    ------
    FileNotFoundError:
        If *run_dir* does not exist.
    ValueError:
        If no usable candidate can be derived from the artifacts present.
    """
    run_path = Path(run_dir)
    if not run_path.exists():
        raise FileNotFoundError(f"Run directory not found: {run_path}")

    # Load meta.json for provenance
    meta: Dict[str, Any] = {}
    meta_path = run_path / "meta.json"
    if meta_path.exists():
        try:
            with open(meta_path, encoding="utf-8") as fh:
                meta = json.load(fh)
        except Exception as exc:
            warnings.warn(f"[forward_eval] Could not read meta.json: {exc}")

    # Also try run_report.json for header info
    rr_path = run_path / "run_report.json"
    run_report: Dict[str, Any] = {}
    if rr_path.exists():
        try:
            with open(rr_path, encoding="utf-8") as fh:
                run_report = json.load(fh)
        except Exception:
            pass

    run_id: str = meta.get("run_id") or run_report.get("header", {}).get("run_id") or run_path.name

    # ------------------------------------------------------------------ #
    # Attempt 1: grid leaderboard
    # ------------------------------------------------------------------ #
    best_row: Optional[Dict[str, Any]] = None
    for lb_name in ("leaderboard.csv", "experiments.csv"):
        lb_path = run_path / lb_name
        if lb_path.exists():
            try:
                df_lb = pd.read_csv(lb_path)
                best_row = _pick_best_row(df_lb, metric)
                if best_row:
                    break
            except Exception as exc:
                warnings.warn(f"[forward_eval] Could not read {lb_name}: {exc}")

    # ------------------------------------------------------------------ #
    # Attempt 2: walkforward OOS leaderboard
    # ------------------------------------------------------------------ #
    if best_row is None:
        oos_path = run_path / "oos_leaderboard.csv"
        if oos_path.exists():
            try:
                df_oos = pd.read_csv(oos_path)
                best_row = _pick_best_row(df_oos, metric)
            except Exception as exc:
                warnings.warn(f"[forward_eval] Could not read oos_leaderboard.csv: {exc}")

    # ------------------------------------------------------------------ #
    # Attempt 3: run_report.json results / oos_leaderboard key
    # ------------------------------------------------------------------ #
    if best_row is None:
        for key in ("results", "oos_leaderboard"):
            rows = run_report.get(key, [])
            if rows:
                best_row = rows[0]  # already sorted by run_report writer
                break

    if best_row is None:
        raise ValueError(
            f"Could not derive a candidate from run directory: {run_path}\n"
            f"Expected at least one of: leaderboard.csv, oos_leaderboard.csv, "
            f"or results in run_report.json."
        )

    # ------------------------------------------------------------------ #
    # Extract strategy params from best row
    # ------------------------------------------------------------------ #
    # Param columns: any column that is NOT a known metric column.
    _METRIC_COLS = {
        "sharpe_simple", "total_return", "win_rate", "profit_factor",
        "expectancy", "max_drawdown", "n_trades", "split", "rank",
        "train_sharpe", "oos_sharpe", "config_hash", "run_id",
    }
    params = {
        k: v for k, v in best_row.items()
        if k not in _METRIC_COLS and not k.startswith("_") and v is not None
    }

    # Extract cost params if present
    fee_rate = float(best_row.get("fee_rate", meta.get("fee_rate", 0.002)))
    slippage_bps = float(best_row.get("slippage_bps", meta.get("slippage_bps", 8.0)))
    slippage_mode = str(best_row.get("slippage_mode", meta.get("slippage_mode", "fixed")))
    k_atr = float(best_row.get("k_atr", meta.get("k_atr", 0.05)))

    selection_value: Optional[float] = None
    raw_sv = best_row.get(metric)
    if raw_sv is not None:
        try:
            selection_value = float(raw_sv)
        except (TypeError, ValueError):
            pass

    strategy_name = str(best_row.get("strategy_name", "rsi_ma_cross_v2"))

    return CandidateConfig(
        strategy_name=strategy_name,
        params=params,
        fee_rate=fee_rate,
        slippage_bps=slippage_bps,
        slippage_mode=slippage_mode,
        k_atr=k_atr,
        source_run_id=run_id,
        source_run_dir=str(run_path.resolve()),
        selection_metric=metric,
        selection_value=selection_value,
        selected_at=datetime.now(timezone.utc).isoformat(),
        ticker=str(meta.get("ticker", best_row.get("ticker", params.get("ticker", "")))),
        interval=str(meta.get("interval", "1d")),
        initial_cash=float(meta.get("initial_cash", 10_000.0)),
    )


# ---------------------------------------------------------------------------
# Strategy construction
# ---------------------------------------------------------------------------

def build_strategy(candidate: CandidateConfig):
    """
    Reconstruct a ``Strategy`` instance from a ``CandidateConfig``.

    Parameters
    ----------
    candidate:
        Candidate config produced by :func:`load_candidate_from_run`.

    Returns
    -------
    Strategy

    Raises
    ------
    KeyError:
        If ``candidate.strategy_name`` is not in the registry.
    """
    cls = _STRATEGY_REGISTRY.get(candidate.strategy_name)
    if cls is None:
        raise KeyError(
            f"Unknown strategy '{candidate.strategy_name}'. "
            f"Registered: {sorted(_STRATEGY_REGISTRY)}"
        )
    # Filter params to only those accepted by the strategy constructor
    import inspect
    sig = inspect.signature(cls.__init__)
    valid_params = {
        k: v for k, v in candidate.params.items()
        if k in sig.parameters and k != "self"
    }
    return cls(**valid_params)


# ---------------------------------------------------------------------------
# Forward evaluation engine
# ---------------------------------------------------------------------------

def run_forward_evaluation(
    candidate: CandidateConfig,
    df: pd.DataFrame,
    initial_cash: float = 10_000.0,
    eval_start: Optional[str] = None,
    eval_end: Optional[str] = None,
    session_id: Optional[str] = None,
    initial_state: Optional[PortfolioState] = None,
) -> Dict[str, Any]:
    """
    Run a sequential paper evaluation of *candidate* over *df*.
    
    If *initial_state* is provided, the evaluation resumes from that point.

    Data is processed chronologically bar-by-bar using ``run_paper_broker``
    semantics.  This is NOT a re-labelled backtest: the result is explicitly
    framed as a forward paper evaluation with candidate provenance metadata.

    Parameters
    ----------
    candidate:
        Strategy config to evaluate.
    df:
        OHLC DataFrame covering the forward period.  Must have a DatetimeIndex
        and at least a ``close`` column.  Indicators will be added internally.
    initial_cash:
        Starting paper cash.
    eval_start:
        ISO date string — informational, stored in portfolio state.
    eval_end:
        ISO date string — informational, stored in portfolio state.
    session_id:
        Unique session identifier.  Auto-generated if ``None``.

    Returns
    -------
    dict with keys:
        - ``candidate``        : :class:`CandidateConfig`
        - ``trades``           : ``pd.DataFrame`` — trade log
        - ``equity_curve``     : ``pd.Series`` — normalised equity
        - ``portfolio_state``  : :class:`PortfolioState`
        - ``bars_evaluated``   : int
    """
    if df is None or df.empty:
        raise ValueError("Forward evaluation requires a non-empty OHLC DataFrame.")
    if "close" not in df.columns:
        raise ValueError("OHLC DataFrame must contain a 'close' column.")

    # Truncate to eval_end if provided
    if eval_end:
        df = df[df.index <= pd.Timestamp(eval_end)].copy()
        if df.empty:
             raise ValueError(f"No data found before eval_end ({eval_end}).")

    # 1. Prepare data (indicators)
    df_ind = add_indicators(df.copy())
    if df_ind.empty:
        raise ValueError(
            f"Indicator computation produced an empty DataFrame (fetched {len(df)} bars). "
            "Ensure the forward period has enough bars (at least 100 recommended)."
        )

    sid = session_id or (initial_state.session_id if initial_state else str(secrets.token_hex(4))[:8])
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # 2. Prepare state and simulation parameters
    if initial_state:
        state = deepcopy(initial_state)
        state.updated_at = now_iso
        state.resume_count += 1
        state.bars_fetched += len(df)
        state.warmup_bars += (len(df) - len(df_ind))
        
        current_cash = state.cash
        current_qty = state.qty
        start_ts = state.last_timestamp
        skip_inclusive = True
    else:
        state = PortfolioState(
            session_id=sid,
            eval_start=eval_start or "",
            eval_end=eval_end or "",
            cash=initial_cash,
            qty=0.0,
            current_equity=initial_cash,
            candidate=_sanitize(asdict(candidate)),
            created_at=now_iso,
            updated_at=now_iso,
            starting_cash=initial_cash,
            bars_fetched=len(df),
            warmup_bars=len(df) - len(df_ind),
            original_eval_start=eval_start or "",
        )
        current_cash = initial_cash
        current_qty = 0.0
        # For fresh run with lookback, we only start trading at or after eval_start
        start_ts = eval_start
        skip_inclusive = False

    # Generate signals
    strategy = build_strategy(candidate)
    signals = strategy.generate_signals(df_ind)

    # Run paper broker
    trades_df_new = _run_paper_broker_fwd(
        df=df_ind,
        signals=signals,
        initial_cash=current_cash,
        initial_qty=current_qty,
        fee_rate=candidate.fee_rate,
        slippage_bps=candidate.slippage_bps,
        slippage_mode=candidate.slippage_mode,
        k_atr=candidate.k_atr,
        start_ts=start_ts,
        skip_inclusive=skip_inclusive,
    )

    # Build equity curve for THIS segment
    # It will start at 1.0 (relative to segment start)
    equity_curve_abs = _build_equity_curve_abs(
        df_ind=df_ind,
        trades_df=trades_df_new,
        initial_cash=current_cash,
        initial_qty=current_qty,
        start_ts=start_ts,
        skip_inclusive=skip_inclusive,
    )

    # Normalize for the returned result (Stage L requirement: starts at 1.0)
    # We normalize to the starting cash of this segment
    session_starting_cash = state.starting_cash or initial_cash
    equity_curve_norm = equity_curve_abs / session_starting_cash

    # Update state
    last_ts_val = df_ind.index[-1]
    state.eval_end = eval_end or (str(last_ts_val.date()) if hasattr(last_ts_val, "date") else str(last_ts_val))
    state.last_timestamp = state.eval_end
    state.total_bars_evaluated += len(equity_curve_norm)
    
    portfolio_state = update_portfolio_state(
        state,
        trades_df=trades_df_new,
        equity_series=equity_curve_norm,
        initial_cash=session_starting_cash,
    )

    return {
        "candidate": candidate,
        "trades": trades_df_new,
        "equity_curve": equity_curve_norm,
        "portfolio_state": portfolio_state,
        "bars_evaluated": len(equity_curve_norm),
    }

def _build_equity_curve_abs(
    df_ind: pd.DataFrame,
    trades_df: pd.DataFrame,
    initial_cash: float,
    initial_qty: float = 0.0,
    start_ts: Optional[str] = None,
    skip_inclusive: bool = True,
) -> pd.Series:
    """
    Build an absolute equity curve (in currency terms) for a segment.
    """
    eq_vals = []
    last_qty = float(initial_qty)
    last_cash = float(initial_cash)

    trade_idx = 0
    sorted_trades = trades_df.reset_index(drop=True)

    for ts, row in df_ind.iterrows():
        ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        if start_ts:
            if skip_inclusive and ts_str <= start_ts:
                continue
            if not skip_inclusive and ts_str < start_ts:
                continue

        # Process any trades at this timestamp
        while trade_idx < len(sorted_trades):
            t_ts = pd.Timestamp(sorted_trades.loc[trade_idx, "timestamp"])
            if t_ts == ts:
                side = sorted_trades.loc[trade_idx, "side"]
                qty_t = float(sorted_trades.loc[trade_idx, "qty"])
                equity_t = float(sorted_trades.loc[trade_idx, "equity_after"])
                if side == "BUY":
                    last_qty = qty_t
                    last_cash = 0.0
                else:
                    last_qty = 0.0
                    last_cash = equity_t
                trade_idx += 1
            else:
                break

        # Mark-to-market at current close
        close = float(row["close"])
        current_eq = last_cash + last_qty * close
        eq_vals.append(current_eq)

    if not eq_vals:
        return pd.Series(dtype=float)
        
    # We want to return a series indexed by timestamps after start_ts
    mask = [True] * len(df_ind)
    if start_ts:
        mask = [ (ts.isoformat() if hasattr(ts, "isoformat") else str(ts)) > start_ts for ts in df_ind.index ]
        
    return pd.Series(eq_vals, index=df_ind.index[mask])


def _run_paper_broker_fwd(
    df: pd.DataFrame,
    signals: pd.Series,
    initial_cash: float,
    fee_rate: float,
    slippage_bps: float,
    slippage_mode: str,
    k_atr: float,
    initial_qty: float = 0.0,
    start_ts: Optional[str] = None,
    skip_inclusive: bool = True,
) -> pd.DataFrame:
    """
    Execute a paper broker loop over *df* using *signals*.
    
    If *start_ts* is provided, bars on or before this timestamp are skipped.
    """
    from quantlab.execution.paper import Trade

    signals = signals.reindex(df.index).fillna(0).astype(int)
    cash = float(initial_cash)
    qty = float(initial_qty)
    trades: List[Trade] = []

    for i, (ts, row) in enumerate(df.iterrows()):
        ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        if start_ts:
            if skip_inclusive and ts_str <= start_ts:
                continue
            if not skip_inclusive and ts_str < start_ts:
                continue
            
        close = float(row["close"])
        s = int(signals.loc[ts])

        if slippage_mode == "atr":
            slip = slippage_atr(df, i, k_atr=k_atr)
        else:
            slip = slippage_fixed(slippage_bps)

        if s == 1 and qty == 0.0 and cash > 0.0:
            px = exec_price(close, "BUY", slip)
            notional = cash
            fee = notional * fee_rate
            spend = notional - fee
            buy_qty = spend / px

            qty = buy_qty
            cash = 0.0
            equity = cash + qty * close

            trades.append(Trade(ts, "BUY", close, px, qty, fee, equity, slip, reason="signal=1"))

        elif s == -1 and qty > 0.0:
            px = exec_price(close, "SELL", slip)
            notional = qty * px
            fee = notional * fee_rate
            proceeds = notional - fee

            cash = proceeds
            qty = 0.0
            equity = cash

            trades.append(Trade(ts, "SELL", close, px, 0.0, fee, equity, slip, reason="signal=-1"))

    if not trades:
        cols = ["timestamp", "side", "close", "exec_price", "qty", "fee", "equity_after", "slippage", "reason"]
        return pd.DataFrame(columns=cols)
    return pd.DataFrame([t.__dict__ for t in trades])


def _build_equity_curve(
    df_ind: pd.DataFrame,
    trades_df: pd.DataFrame,
    initial_cash: float,
) -> pd.Series:
    """
    Build a normalised bar-by-bar equity curve from the trades log and OHLC data.

    The curve starts at 1.0 and follows portfolio value relative to initial_cash.
    Between trades, equity is inferred from the last known position.
    """
    if trades_df.empty:
        # No trades: equity stays at 1.0
        return pd.Series(1.0, index=df_ind.index)

    trade_ts = set(pd.to_datetime(trades_df["timestamp"]))
    equity_map: Dict[Any, float] = {}

    for _, row in trades_df.iterrows():
        equity_map[pd.Timestamp(row["timestamp"])] = float(row["equity_after"])

    # Forward-fill equity through all bars
    eq_vals = []
    last_equity = initial_cash
    last_qty = 0.0
    last_cash = initial_cash

    # Build a simple position-tracking loop
    trade_idx = 0
    sorted_trades = trades_df.reset_index(drop=True)

    for ts, row in df_ind.iterrows():
        # Process any trades at this timestamp
        while trade_idx < len(sorted_trades):
            t_ts = pd.Timestamp(sorted_trades.loc[trade_idx, "timestamp"])
            if t_ts == ts:
                side = sorted_trades.loc[trade_idx, "side"]
                qty_t = float(sorted_trades.loc[trade_idx, "qty"])
                equity_t = float(sorted_trades.loc[trade_idx, "equity_after"])
                if side == "BUY":
                    last_qty = qty_t
                    last_cash = 0.0
                else:
                    last_qty = 0.0
                    last_cash = equity_t
                last_equity = equity_t
                trade_idx += 1
            else:
                break

        # Mark-to-market at current close
        close = float(row["close"])
        current_eq = last_cash + last_qty * close
        eq_vals.append(current_eq)

    eq_series = pd.Series(eq_vals, index=df_ind.index)
    # Normalise to 1.0 at start
    first_val = eq_series.iloc[0] if eq_series.iloc[0] > 0 else initial_cash
    return eq_series / first_val


def load_forward_session(session_dir: str | Path) -> Dict[str, Any]:
    """
    Load an existing forward session and its artifacts.

    Returns
    -------
    dict with keys:
        - "portfolio_state"
        - "historic_trades"
        - "historic_equity"
        - "candidate"
    """
    p = Path(session_dir)
    state_path = p / "portfolio_state.json"
    if not state_path.exists():
        raise ValueError(f"Invalid session directory: portfolio_state.json not found in {session_dir}")

    state = load_portfolio_state(state_path)
    
    trades_path = p / "forward_trades.csv"
    trades = pd.read_csv(trades_path) if trades_path.exists() else pd.DataFrame()
    
    equity_path = p / "forward_equity_curve.csv"
    equity = pd.read_csv(equity_path) if equity_path.exists() else pd.DataFrame()
    
    candidate = None
    if state.candidate:
        candidate = CandidateConfig(**state.candidate)
        
    return {
        "portfolio_state": state,
        "historic_trades": trades,
        "historic_equity": equity,
        "candidate": candidate
    }


# ---------------------------------------------------------------------------
# Portfolio state management
# ---------------------------------------------------------------------------

def update_portfolio_state(
    state: PortfolioState,
    trades_df: pd.DataFrame,
    equity_series: pd.Series,
    initial_cash: float = 10_000.0,
) -> PortfolioState:
    """
    Update *state* from the completed evaluation result.

    Parameters
    ----------
    state:
        Existing portfolio state to update in-place.
    trades_df:
        Trade log from :func:`run_forward_evaluation`.
    equity_series:
        Normalised equity curve from :func:`run_forward_evaluation`.
    initial_cash:
        Starting cash (used to compute final equity in currency terms).

    Returns
    -------
    PortfolioState  (the same object, mutated)
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    state.updated_at = now_iso

    if not trades_df.empty:
        last_trade = trades_df.iloc[-1]
        state.n_trades = len(trades_df)

        last_ts = pd.Timestamp(last_trade["timestamp"])
        state.last_timestamp = last_ts.isoformat() if not pd.isna(last_ts) else None

        # Determine current position
        last_side = str(last_trade["side"])
        if last_side == "BUY":
            state.qty = float(last_trade["qty"])
            state.cash = 0.0
        else:
            state.qty = 0.0
            state.cash = float(last_trade["equity_after"])

        # Cumulative costs
        state.total_fees = float(trades_df["fee"].sum())
        state.total_slippage = float(trades_df["slippage"].sum())

    # Current equity in absolute terms
    if not equity_series.empty:
        state.current_equity = float(equity_series.iloc[-1]) * initial_cash
        # Always update last_timestamp to the end of the processed series
        last_ts = equity_series.index[-1]
        state.last_timestamp = last_ts.isoformat() if hasattr(last_ts, "isoformat") else str(last_ts)

    # Stage L.1: Detail PnL and open position
    if not trades_df.empty:
        # Calculate realized PnL from closed round-trips
        pnl_list = []
        open_val = None
        for _, row in trades_df.iterrows():
            if row["side"] == "BUY":
                open_val = float(row["equity_after"])
            elif row["side"] == "SELL" and open_val is not None:
                pnl_list.append(float(row["equity_after"]) - open_val)
                open_val = None
        state.realized_pnl = sum(pnl_list)

        # Handle open position
        last_trade = trades_df.iloc[-1]
        if last_trade["side"] == "BUY":
            state.has_open_position = True
            state.open_position_qty = float(last_trade["qty"])
            state.open_position_entry_price = float(last_trade["exec_price"])
            # Mark price is the last close in df_ind (or initial df if empty)
            # We don't have df_ind here, but we have equity_series which covers df_ind
            mark_price = state.current_equity / state.open_position_qty if state.open_position_qty > 0 else 0.0
            state.open_position_mark_price = mark_price
            state.open_position_market_value = state.open_position_qty * mark_price
            state.unrealized_pnl = state.current_equity - float(last_trade["equity_after"])
        else:
            state.has_open_position = False
            state.unrealized_pnl = 0.0

    return state


def load_portfolio_state(path: str | Path) -> PortfolioState:
    """
    Load a persisted ``PortfolioState`` from a JSON file.

    Parameters
    ----------
    path:
        Path to ``portfolio_state.json``.

    Returns
    -------
    PortfolioState

    Raises
    ------
    FileNotFoundError, ValueError
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"portfolio_state.json not found: {p}")
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    # Re-hydrate known fields; ignore unknown keys gracefully
    known_fields = PortfolioState.__dataclass_fields__.keys()
    filtered = {k: v for k, v in data.items() if k in known_fields}
    return PortfolioState(**filtered)


# ---------------------------------------------------------------------------
# Artifact persistence
# ---------------------------------------------------------------------------

def write_forward_eval_artifacts(
    result: Dict[str, Any],
    out_dir: str | Path,
    initial_historical: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Persist all forward evaluation artifacts to *out_dir*.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    written: List[str] = []

    ps: PortfolioState = result["portfolio_state"]
    trades_df: pd.DataFrame = result["trades"]
    equity_norm: pd.Series = result["equity_curve"] # Segment normalized equity (starts at 1.0)

    # Handle merges
    if initial_historical:
        # Merge trades
        old_trades = initial_historical.get("historic_trades")
        if old_trades is not None and not old_trades.empty:
            trades_df = pd.concat([old_trades, trades_df], ignore_index=True)
            trades_df = trades_df.drop_duplicates(subset=["timestamp", "side", "qty", "exec_price"])
            
        old_equity_df = initial_historical.get("historic_equity")
        if old_equity_df is not None and not old_equity_df.empty:
            new_eq_df = pd.DataFrame({
                "timestamp": equity_norm.index.astype(str), 
                "equity": equity_norm.values
            })
            combined_eq = pd.concat([old_equity_df, new_eq_df], ignore_index=True)
            combined_eq = combined_eq.drop_duplicates(subset=["timestamp"], keep="last")
            combined_eq = combined_eq.sort_values("timestamp")
            
            equity_curve_to_save = combined_eq
            # Update result for report builder
            result["equity_curve"] = pd.Series(combined_eq["equity"].values, index=pd.to_datetime(combined_eq["timestamp"]))
            result["trades"] = trades_df
        else:
            equity_curve_to_save = pd.DataFrame({
                "timestamp": equity_norm.index.astype(str),
                "equity": equity_norm.values
            })
            result["equity_curve"] = equity_norm
    else:
        equity_curve_to_save = pd.DataFrame({
            "timestamp": equity_norm.index.astype(str),
            "equity": equity_norm.values
        })
        result["equity_curve"] = equity_norm

    # Save CSVs
    trades_path = out_path / "forward_trades.csv"
    trades_df.to_csv(trades_path, index=False)
    written.append(str(trades_path))

    equity_path = out_path / "forward_equity_curve.csv"
    equity_curve_to_save.to_csv(equity_path, index=False)
    written.append(str(equity_path))

    state_path = out_path / "portfolio_state.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(ps.to_dict(), f, indent=2, ensure_ascii=False, allow_nan=False)
    written.append(str(state_path))

    # forward_returns_series.csv
    if not result["equity_curve"].empty:
        rets_path = out_path / "forward_returns_series.csv"
        returns = result["equity_curve"].pct_change().fillna(0.0)
        ret_df = returns.reset_index()
        ret_df.columns = ["timestamp", "daily_return"]
        ret_df.to_csv(rets_path, index=False)
        written.append(str(rets_path))

    return written
