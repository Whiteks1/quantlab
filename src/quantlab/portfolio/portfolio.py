"""
portfolio.py – Core portfolio model for QuantLab Portfolio Engine.
"""

from __future__ import annotations
from typing import Dict

from quantlab.portfolio.position import Position
from quantlab.portfolio.ledger import Ledger

class Portfolio:
    """
    Manages cash, positions, and equity using an explicit state model.
    """
    def __init__(self, cash: float = 10_000.0):
        self.cash = cash
        self.positions: Dict[str, Position] = {}
        self.realized_pnl = 0.0
        self.ledger = Ledger()

    def update_fill(self, symbol: str, side: str, qty: float, price: float, fee: float = 0.0) -> None:
        """
        Processes a trade fill, updating cash, positions, and ledger.
        """
        side = side.upper()
        if side == "BUY":
            cost = (qty * price) + fee
            self.cash -= cost
            
            if symbol not in self.positions:
                self.positions[symbol] = Position(symbol=symbol)
            
            self.positions[symbol].update_on_buy(qty, price)
            self.ledger.record_fill(symbol, side, qty, price, fee)
            if fee > 0:
                self.ledger.record_cash_change(-fee, f"Fee on {side} {symbol}")
                
        elif side == "SELL":
            proceeds = (qty * price) - fee
            self.cash += proceeds
            
            if symbol in self.positions:
                fill_pnl = self.positions[symbol].update_on_sell(qty, price)
                self.realized_pnl += fill_pnl
                self.ledger.record_realized_pnl(symbol, fill_pnl)
                
            self.ledger.record_fill(symbol, side, qty, price, fee)
            if fee > 0:
                self.ledger.record_cash_change(-fee, f"Fee on {side} {symbol}")
        else:
            raise ValueError(f"Unsupported side: {side}")

    def positions_value(self, price_map: Dict[str, float]) -> float:
        """
        Calculates the total market value of all open positions.
        """
        val = 0.0
        for symbol, pos in self.positions.items():
            price = price_map.get(symbol, pos.avg_price) # Fallback to cost if no price
            val += pos.market_value(price)
        return val

    def equity(self, price_map: Dict[str, float]) -> float:
        """
        Calculates the total portfolio equity: cash + positions_value.
        """
        return self.cash + self.positions_value(price_map)

    def total_unrealized_pnl(self, price_map: Dict[str, float]) -> float:
        """
        Calculates the total unrealized PnL across all positions.
        """
        pnl = 0.0
        for symbol, pos in self.positions.items():
            price = price_map.get(symbol, pos.avg_price)
            pnl += pos.unrealized_pnl(price)
        return pnl
