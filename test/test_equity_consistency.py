import pytest
from quantlab.portfolio.portfolio import Portfolio

def test_equity_identity_rule():
    """
    Portfolio identity rule must hold:
    cash + positions_value == equity
    """
    pf = Portfolio(cash=10000.0)
    pf.update_fill("BTC-USD", "BUY", 0.1, 50000.0, fee=10.0)
    pf.update_fill("ETH-USD", "BUY", 1.0, 2000.0, fee=5.0)
    
    # Cash: 10000 - 5010 - 2005 = 2985
    assert pf.cash == 2985.0
    
    price_map = {
        "BTC-USD": 60000.0, # Unrealized gain
        "ETH-USD": 1800.0   # Unrealized loss
    }
    
    # Position market values:
    # BTC: 0.1 * 60000 = 6000
    # ETH: 1.0 * 1800 = 1800
    # Total positions value = 7800
    pos_val = pf.positions_value(price_map)
    assert pos_val == 7800.0
    
    expected_equity = pf.cash + pos_val # 2985 + 7800 = 10785
    assert pf.equity(price_map) == expected_equity
    assert pf.equity(price_map) == 10785.0
    
    # Unrealized PnL Check:
    # BTC: 0.1 * (60000 - 50000) = 1000
    # ETH: 1.0 * (1800 - 2000) = -200
    # Total unrealized = 800
    assert pf.total_unrealized_pnl(price_map) == 800.0
