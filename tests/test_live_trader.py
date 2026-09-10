from src.exchange import BinanceSpotClient, SafetyLimits, TradingMode
from src.live_trader import LiveTradeConfig, run_live_trader
from src.market import Candle
from src.risk import RiskConfig
from src.strategy import SmaCrossoverStrategy, SmaConfig


def test_live_trader_dry_run_loop(monkeypatch):
    candles = [
        Candle(i, 100 + i, 101 + i, 99 + i, 100 + (i % 5), 1.0) for i in range(80)
    ]

    import src.live_trader as lt

    monkeypatch.setattr(lt, "fetch_binance_klines", lambda *a, **k: candles)
    client = BinanceSpotClient(
        mode=TradingMode.DRY_RUN,
        safety=SafetyLimits(max_order_quote=50, min_order_quote=5, max_daily_quote=200),
    )
    monkeypatch.setattr(client, "price", lambda symbol: 100.0)

    state = run_live_trader(
        SmaCrossoverStrategy(SmaConfig(5, 20)),
        client,
        risk=RiskConfig(stop_loss_pct=None, take_profit_pct=None),
        config=LiveTradeConfig(poll_seconds=0, max_iterations=2, lookback=80, quote_per_buy=10),
        sleep_fn=lambda s: None,
    )
    assert state.orders is not None
