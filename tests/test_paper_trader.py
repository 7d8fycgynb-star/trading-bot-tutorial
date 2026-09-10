from src.paper_trader import PaperTrader
from src.risk import RiskConfig


def test_buy_and_sell_roundtrip():
    trader = PaperTrader(starting_cash=10_000, fee_rate=0.001, risk=RiskConfig(position_fraction=1.0, stop_loss_pct=None, take_profit_pct=None))
    buy = trader.buy(100.0, 0)
    assert buy is not None
    assert trader.in_position
    sell = trader.sell(110.0, 1)
    assert sell is not None
    assert sell.pnl is not None and sell.pnl > 0
    assert len(trader.closed_pnls) == 1


def test_stop_loss_triggers():
    trader = PaperTrader(
        starting_cash=1000,
        fee_rate=0,
        risk=RiskConfig(position_fraction=1.0, stop_loss_pct=0.05, take_profit_pct=None),
    )
    trader.buy(100.0, 0)
    trade = trader.check_exits(94.0, 1)
    assert trade is not None
    assert trade.reason == "stop-loss"


def test_take_profit_triggers():
    trader = PaperTrader(
        starting_cash=1000,
        fee_rate=0,
        risk=RiskConfig(position_fraction=1.0, stop_loss_pct=None, take_profit_pct=0.1),
    )
    trader.buy(100.0, 0)
    trade = trader.check_exits(111.0, 1)
    assert trade is not None
    assert trade.reason == "take-profit"


def test_position_fraction():
    trader = PaperTrader(
        starting_cash=1000,
        fee_rate=0,
        risk=RiskConfig(position_fraction=0.5, stop_loss_pct=None, take_profit_pct=None),
    )
    trader.buy(100.0, 0)
    assert abs(trader.cash - 500) < 1e-6
    assert abs(trader.position - 5) < 1e-6
