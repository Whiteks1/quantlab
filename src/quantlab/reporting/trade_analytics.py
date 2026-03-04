from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

import numpy as np
import pandas as pd


REQUIRED_COLS = {
    "timestamp",
    "side",
    "close",
    "exec_price",
    "qty",
    "fee",
    "equity_after",
}


@dataclass(frozen=True)
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    side: str  # LONG only in this lab (BUY->SELL)
    qty: float
    entry_price: float
    exit_price: float
    entry_fee: float
    exit_fee: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    holding_days: int
    reason_entry: str = ""
    reason_exit: str = ""


def _ensure_timestamp(s: pd.Series) -> pd.Series:
    # trades.csv uses YYYY-MM-DD; be strict but robust
    ts = pd.to_datetime(s, errors="coerce", utc=False)
    if ts.isna().any():
        bad = s[ts.isna()].head(5).tolist()
        raise ValueError(f"Could not parse some timestamps (sample): {bad}")
    return ts


def load_trades_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"trades.csv missing columns: {sorted(missing)}")

    out = df.copy()
    out["timestamp"] = _ensure_timestamp(out["timestamp"])
    out["side"] = out["side"].astype(str).str.upper().str.strip()

    # numeric safety
    for c in ["close", "exec_price", "qty", "fee", "equity_after"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    if out[["exec_price", "fee", "equity_after"]].isna().any().any():
        raise ValueError("trades.csv has NaN in critical numeric columns (exec_price/fee/equity_after).")

    # optional columns
    if "reason" not in out.columns:
        out["reason"] = ""
    else:
        out["reason"] = out["reason"].fillna("").astype(str)

    if "slippage" in out.columns:
        out["slippage"] = pd.to_numeric(out["slippage"], errors="coerce")
    else:
        out["slippage"] = np.nan

    return out.sort_values("timestamp").reset_index(drop=True)


def compute_round_trips(trades: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw broker fills (BUY/SELL rows) into per-trade round trips.

    Notes:
    - Your current SELL rows have qty=0. We handle that by assuming SELL closes the full open position.
    - Assumes a single position at a time (flat -> long -> flat), which matches your strategy.
    """
    if trades.empty:
        return pd.DataFrame()

    cols = set(trades.columns)
    missing = REQUIRED_COLS - cols
    if missing:
        raise ValueError(f"trades missing columns: {sorted(missing)}")

    # state
    pos_qty = 0.0
    entry_time: Optional[pd.Timestamp] = None
    entry_price: Optional[float] = None
    entry_fee_acc = 0.0
    entry_reason = ""

    # weighted avg entry if multiple buys before sell (robust)
    entry_notional = 0.0  # sum(qty*price)

    records = []

    for _, r in trades.iterrows():
        side = str(r["side"]).upper().strip()
        ts = r["timestamp"]
        px = float(r["exec_price"])
        fee = float(r["fee"])
        qty = float(r["qty"]) if not pd.isna(r["qty"]) else 0.0
        reason = str(r.get("reason", ""))

        if side == "BUY":
            # open or add
            if pos_qty <= 0:
                entry_time = ts
                entry_reason = reason
                entry_fee_acc = 0.0
                entry_notional = 0.0
                entry_price = None

            # qty must be positive on BUY
            if qty <= 0:
                # if broker ever logs 0, ignore but keep consistent
                continue

            pos_qty += qty
            entry_notional += qty * px
            entry_fee_acc += fee
            entry_price = entry_notional / pos_qty

        elif side == "SELL":
            if pos_qty <= 0:
                # sell while flat -> ignore
                continue

            # many of your SELL rows log qty=0; interpret as "close all"
            sell_qty = qty if qty > 0 else pos_qty

            # clamp
            sell_qty = min(sell_qty, pos_qty)

            assert entry_time is not None
            assert entry_price is not None

            gross_pnl = sell_qty * (px - entry_price)
            exit_fee = fee

            # allocate entry fees proportionally if partial sell
            entry_fee_alloc = entry_fee_acc * (sell_qty / pos_qty) if pos_qty > 0 else 0.0
            net_pnl = gross_pnl - entry_fee_alloc - exit_fee

            invested = sell_qty * entry_price
            return_pct = (net_pnl / invested) if invested > 0 else 0.0

            holding_days = int((ts - entry_time).days)

            records.append(
                Trade(
                    entry_time=entry_time,
                    exit_time=ts,
                    side="LONG",
                    qty=float(sell_qty),
                    entry_price=float(entry_price),
                    exit_price=float(px),
                    entry_fee=float(entry_fee_alloc),
                    exit_fee=float(exit_fee),
                    gross_pnl=float(gross_pnl),
                    net_pnl=float(net_pnl),
                    return_pct=float(return_pct),
                    holding_days=holding_days,
                    reason_entry=entry_reason,
                    reason_exit=reason,
                ).__dict__
            )

            # reduce position
            pos_qty -= sell_qty
            # reduce entry fee / notional as well for partials
            entry_fee_acc -= entry_fee_alloc
            entry_notional = entry_price * pos_qty

            if pos_qty <= 1e-12:
                # flat
                pos_qty = 0.0
                entry_time = None
                entry_price = None
                entry_fee_acc = 0.0
                entry_notional = 0.0
                entry_reason = ""

        else:
            # unknown side -> ignore
            continue

    out = pd.DataFrame.from_records(records)
    if out.empty:
        return out

    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out["exit_time"] = pd.to_datetime(out["exit_time"])
    out["holding_days"] = out["holding_days"].astype(int)

    # convenience flags
    out["is_loss"] = out["net_pnl"] < 0
    out["pnl_pct"] = out["return_pct"]
    return out


def streaks(is_loss: pd.Series) -> Tuple[int, int]:
    """Return (max_consecutive_losses, max_consecutive_wins)."""
    max_losses = 0
    max_wins = 0
    cur_losses = 0
    cur_wins = 0
    for v in is_loss.fillna(False).astype(bool).tolist():
        if v:
            cur_losses += 1
            cur_wins = 0
        else:
            cur_wins += 1
            cur_losses = 0
        max_losses = max(max_losses, cur_losses)
        max_wins = max(max_wins, cur_wins)
    return max_losses, max_wins


def aggregate_trade_metrics(round_trips: pd.DataFrame) -> Dict[str, Any]:
    if round_trips is None or round_trips.empty:
        return {
            "trades": 0,
            "win_rate_trades": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": 0.0,
            "expectancy_net": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "avg_holding_days": 0.0,
            "max_consecutive_losses": 0,
            "max_consecutive_wins": 0,
            "exposure": 0.0,
        }

    rt = round_trips.copy()
    trades_n = int(len(rt))

    gross_profit = float(rt.loc[rt["net_pnl"] > 0, "net_pnl"].sum())
    gross_loss = float(rt.loc[rt["net_pnl"] < 0, "net_pnl"].sum())  # negative
    profit_factor = (gross_profit / abs(gross_loss)) if gross_loss < 0 else np.inf

    win_rate = float((rt["net_pnl"] > 0).mean())

    avg_win = float(rt.loc[rt["net_pnl"] > 0, "net_pnl"].mean()) if (rt["net_pnl"] > 0).any() else 0.0
    avg_loss = float(rt.loc[rt["net_pnl"] < 0, "net_pnl"].mean()) if (rt["net_pnl"] < 0).any() else 0.0

    expectancy = float(rt["net_pnl"].mean())

    avg_holding = float(rt["holding_days"].mean()) if "holding_days" in rt.columns else 0.0

    max_losses, max_wins = streaks(rt["net_pnl"] < 0)

    # exposure: fraction of days in-market between first entry and last exit
    first_entry = rt["entry_time"].min()
    last_exit = rt["exit_time"].max()
    total_days = max(int((last_exit - first_entry).days), 1)

    # approximate in-market days by sum holding_days (non-overlapping in your model)
    in_mkt_days = int(rt["holding_days"].clip(lower=0).sum())
    exposure = float(in_mkt_days / total_days)

    return {
        "trades": trades_n,
        "win_rate_trades": win_rate,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": float(profit_factor) if np.isfinite(profit_factor) else float("inf"),
        "expectancy_net": expectancy,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_holding_days": avg_holding,
        "max_consecutive_losses": int(max_losses),
        "max_consecutive_wins": int(max_wins),
        "exposure": exposure,
        "total_net_pnl": rt["net_pnl"].sum() if not rt.empty else 0.0
    }