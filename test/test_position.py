import pytest
from quantlab.portfolio.position import Position

def test_position_buy():
    pos = Position(symbol="BTC-USD")
    pos.update_on_buy(1.0, 50000.0)
    assert pos.quantity == 1.0
    assert pos.avg_price == 50000.0
    
    pos.update_on_buy(1.0, 60000.0)
    assert pos.quantity == 2.0
    assert pos.avg_price == 55000.0

def test_position_sell_partial():
    pos = Position(symbol="BTC-USD", quantity=2.0, avg_price=55000.0)
    realized = pos.update_on_sell(1.0, 60000.0)
    
    assert pos.quantity == 1.0
    assert realized == 5000.0
    assert pos.realized_pnl == 5000.0

def test_position_sell_full():
    pos = Position(symbol="BTC-USD", quantity=1.0, avg_price=55000.0)
    realized = pos.update_on_sell(2.0, 60000.0) # sell more than owned
    
    assert pos.quantity == 0.0
    assert realized == 5000.0
    assert pos.realized_pnl == 5000.0

def test_position_pnl_calc():
    pos = Position(symbol="ETH-USD", quantity=10.0, avg_price=2000.0)
    assert pos.market_value(2500.0) == 25000.0
    assert pos.unrealized_pnl(2500.0) == 5000.0
