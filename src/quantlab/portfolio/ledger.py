"""
ledger.py – Simple event tracker for QuantLab Portfolio Engine.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class Ledger:
    """
    A minimal record of portfolio events.
    """
    def __init__(self):
        self.fills: List[Dict[str, Any]] = []
        self.cash_changes: List[Dict[str, Any]] = []
        self.pnl_events: List[Dict[str, Any]] = []

    def record_fill(
        self, 
        symbol: str, 
        side: str, 
        qty: float, 
        price: float, 
        fee: float,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record a trade fill event."""
        event = {
            "type": "fill",
            "symbol": symbol,
            "side": side.upper(),
            "qty": qty,
            "price": price,
            "fee": fee,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat()
        }
        self.fills.append(event)

    def record_cash_change(self, amount: float, reason: str, timestamp: Optional[datetime] = None) -> None:
        """Record a cash change (deposit, withdrawal, fee, etc)."""
        event = {
            "type": "cash_change",
            "amount": amount,
            "reason": reason,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat()
        }
        self.cash_changes.append(event)

    def record_realized_pnl(self, symbol: str, amount: float, timestamp: Optional[datetime] = None) -> None:
        """Record a realized PnL event."""
        event = {
            "type": "realized_pnl",
            "symbol": symbol,
            "amount": amount,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat()
        }
        self.pnl_events.append(event)
