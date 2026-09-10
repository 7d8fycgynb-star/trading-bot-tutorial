from src.live_paper import LivePaperConfig, run_live_paper
from src.market import Candle
from src.risk import RiskConfig
from src.strategy import SmaCrossoverStrategy, SmaConfig


def test_live_paper_iterations(monkeypatch):
    candles = [
        Candle(i, 100 + i, 101 + i, 99 + i, 100 + (i % 5), 1.0) for i in range(80)
    ]

    def fake_fetch(symbol, interval, limit, timeout=15.0):
        return candles

    slept = []

    import src.live_paper as lp

    monkeypatch.setattr(lp, "fetch_binance_klines", fake_fetch)
    trader = run_live_paper(
        SmaCrossoverStrategy(SmaConfig(5, 20)),
        risk=RiskConfig(stop_loss_pct=None, take_profit_pct=None),
        config=LivePaperConfig(poll_seconds=0, max_iterations=2, lookback=80),
        sleep_fn=lambda s: slept.append(s),
    )
    assert trader.starting_cash == 10_000
    assert len(slept) == 1  # sleep mezi iteracemi, ne po poslední? check implementation
