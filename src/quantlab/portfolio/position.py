"""
position.py – Core position model for QuantLab Portfolio Engine.
"""

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Position:
    """
    Represents a single symbol position.
    
    Uses weighted average price for cost basis and realized PnL calculation.
    """
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0

    def update_on_buy(self, qty: float, price: float) -> None:
        """
        Update position on a BUY fill. Adjusts weighted average price.
        """
        if qty <= 0:
            return
            
        total_cost = (self.quantity * self.avg_price) + (qty * price)
        self.quantity += qty
        self.avg_price = total_cost / self.quantity if self.quantity > 0 else 0.0

    def update_on_sell(self, qty: float, price: float) -> float:
        """
        Update position on a SELL fill. Reduces quantity and calculates realized PnL.
        
        Returns:
            realized_pnl from this specific fill.
        """
        if qty <= 0 or self.quantity <= 0:
            return 0.0
            
        close_qty = min(qty, self.quantity)
        
        # PnL = qty * (exit_price - entry_price)
        fill_pnl = close_qty * (price - self.avg_price)
        self.realized_pnl += fill_pnl
        self.quantity -= close_qty
        
        # If position is closed, we don't necessarily reset avg_price 
        # but for a clean model we could. Keeping it for now as "last cost basis".
        if self.quantity == 0:
             # reset avg price if desired, but weighted avg logic naturally holds it
             pass
             
        return fill_pnl

    def market_value(self, current_price: float) -> float:
        """Return the current market value of the position."""
        return self.quantity * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        """Return the current unrealized PnL based on market price."""
        return self.quantity * (current_price - self.avg_price)
