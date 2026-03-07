import pytest
from quantlab.portfolio.portfolio import Portfolio

def test_portfolio_buy_flow():
    pf = Portfolio(cash=10000.0)
    pf.update_fill("BTC-USD", "BUY", 0.1, 50000.0, fee=10.0)
    
    # 50000 * 0.1 = 5000 + 10 fee = 5010 cost
    assert pf.cash == 4990.0
    assert "BTC-USD" in pf.positions
    assert pf.positions["BTC-USD"].quantity == 0.1
    assert pf.positions["BTC-USD"].avg_price == 50000.0

def test_portfolio_sell_flow():
    pf = Portfolio(cash=4990.0)
    pf.update_fill("BTC-USD", "BUY", 0.1, 50000.0) # re-init state in logic
    pf.cash = 4990.0 # override to be precise
    
    pf.update_fill("BTC-USD", "SELL", 0.1, 60000.0, fee=10.0)
    
    # Sell proceeds: 6000 - 10 = 5990
    # New cash: 4990 + 5990 = 10980
    assert pf.cash == 10980.0
    assert pf.positions["BTC-USD"].quantity == 0.0
    
    # Realized PnL: 0.1 * (60000 - 50000) = 1000
    assert pf.realized_pnl == 1000.0

def test_portfolio_ledger_tracking():
    pf = Portfolio(cash=10000.0)
    pf.update_fill("ETH-USD", "BUY", 1.0, 2000.0)
    
    assert len(pf.ledger.fills) == 1
    assert pf.ledger.fills[0]["symbol"] == "ETH-USD"
