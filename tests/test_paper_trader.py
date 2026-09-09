from src.paper_trader import PaperTrader


def test_buy_and_sell_roundtrip():
    trader = PaperTrader(starting_cash=10_000, fee_rate=0.001)
    buy = trader.buy(100.0, 0)
    assert buy is not None
    assert trader.in_position
    assert trader.cash == 0.0 or abs(trader.cash) < 1e-6

    sell = trader.sell(110.0, 1)
    assert sell is not None
    assert not trader.in_position
    summary = trader.summary(110.0)
    assert summary["trades"] == 2
    assert summary["equity"] > 10_000 * 0.99  # roughly profitable after fees


def test_cannot_double_buy():
    trader = PaperTrader(starting_cash=1000, fee_rate=0)
    assert trader.buy(50) is not None
    assert trader.buy(50) is None


def test_cannot_sell_without_position():
    trader = PaperTrader(starting_cash=1000, fee_rate=0)
    assert trader.sell(50) is None
