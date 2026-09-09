from src.strategy import Signal, SmaCrossoverStrategy, StrategyConfig


def test_detects_golden_and_death_cross():
    # Flat, then sharp up (golden), then sharp down (death)
    closes = (
        [10.0] * 30
        + [10.0 + i for i in range(1, 21)]  # uptrend
        + [30.0 - i for i in range(1, 21)]  # downtrend
    )
    strategy = SmaCrossoverStrategy(StrategyConfig(fast_period=3, slow_period=10))
    snaps = strategy.evaluate(closes)
    signals = [s.signal for s in snaps]
    assert Signal.BUY in signals
    assert Signal.SELL in signals


def test_hold_when_not_enough_data():
    strategy = SmaCrossoverStrategy(StrategyConfig(fast_period=3, slow_period=5))
    snaps = strategy.evaluate([1.0, 2.0, 3.0])
    assert all(s.signal is Signal.HOLD for s in snaps)
