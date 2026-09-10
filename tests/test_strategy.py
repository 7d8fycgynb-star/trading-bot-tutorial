from src.strategy import STRATEGIES, Signal, SmaCrossoverStrategy, SmaConfig, build_strategy


def test_detects_golden_and_death_cross():
    closes = (
        [10.0] * 30
        + [10.0 + i for i in range(1, 21)]
        + [30.0 - i for i in range(1, 21)]
    )
    strategy = SmaCrossoverStrategy(SmaConfig(fast_period=3, slow_period=10))
    snaps = strategy.evaluate(closes)
    signals = [s.signal for s in snaps]
    assert Signal.BUY in signals
    assert Signal.SELL in signals


def test_all_strategies_run():
    closes = [100 + ((i * 7) % 13) - 5 + i * 0.05 for i in range(120)]
    for name in STRATEGIES:
        strategy = build_strategy(name)
        snaps = strategy.evaluate(closes)
        assert len(snaps) == len(closes)
        assert all(isinstance(s.signal, Signal) for s in snaps)
