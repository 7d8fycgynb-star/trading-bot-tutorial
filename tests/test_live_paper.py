from src.live_paper import LivePaperConfig, run_live_paper
from src.market import Candle
from src.risk import RiskConfig
from src.strategy import SmaCrossoverStrategy, SmaConfig


def test_live_paper_iterations(monkeypatch):
    candles = [
        Candle(i, 100 + i, 101 + i, 99 + i, 100 + (i % 5), 1.0) for i in range(80)
    ]

    import src.live_paper as lp

    monkeypatch.setattr(lp, "fetch_binance_klines", fake_fetch := (lambda *a, **k: candles))
    slept = []
    trader = run_live_paper(
        SmaCrossoverStrategy(SmaConfig(5, 20)),
        risk=RiskConfig(stop_loss_pct=None, take_profit_pct=None),
        config=LivePaperConfig(poll_seconds=0, max_iterations=2, lookback=80),
        sleep_fn=lambda s: slept.append(s),
    )
    assert trader.starting_cash == 10_000
    assert len(slept) == 1


def test_live_paper_duration(monkeypatch, tmp_path):
    candles = [Candle(i, 100, 101, 99, 100.0 + i, 1.0) for i in range(80)]
    import src.live_paper as lp

    monkeypatch.setattr(lp, "fetch_binance_klines", lambda *a, **k: candles)
    times = iter([1000.0, 1000.5, 1001.0, 1002.0, 1100.0])
    log = tmp_path / "run.log"
    state = tmp_path / "state.json"
    run_live_paper(
        SmaCrossoverStrategy(SmaConfig(5, 20)),
        risk=RiskConfig(stop_loss_pct=None, take_profit_pct=None),
        config=LivePaperConfig(
            poll_seconds=0,
            max_iterations=None,
            duration_seconds=1.0,
            lookback=80,
            log_file=str(log),
            state_file=str(state),
        ),
        sleep_fn=lambda s: None,
        time_fn=lambda: next(times),
    )
    assert log.exists()
    assert "Live paper start" in log.read_text(encoding="utf-8")
    assert state.exists()
