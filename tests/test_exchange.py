import pytest

from src.exchange import BinanceSpotClient, ExchangeError, SafetyLimits, TradingMode


def test_live_requires_confirm_phrase():
    with pytest.raises(ExchangeError, match="Live režim zamčen"):
        BinanceSpotClient(
            api_key="k",
            api_secret="s",
            mode=TradingMode.LIVE,
            live_confirm="ne",
        )


def test_dry_run_buy_respects_max_order():
    client = BinanceSpotClient(mode=TradingMode.DRY_RUN, safety=SafetyLimits(max_order_quote=20, min_order_quote=5, max_daily_quote=100))
    with pytest.raises(ExchangeError, match="překračuje"):
        client.market_buy_quote("BTCUSDT", 50)


def test_dry_run_buy_ok(monkeypatch):
    client = BinanceSpotClient(mode=TradingMode.DRY_RUN, safety=SafetyLimits(max_order_quote=25, min_order_quote=5, max_daily_quote=100))

    monkeypatch.setattr(client, "price", lambda symbol: 100_000.0)
    result = client.market_buy_quote("BTCUSDT", 10)
    assert result.dry_run is True
    assert result.status == "DRY_RUN"
    assert result.side == "BUY"


def test_daily_limit():
    client = BinanceSpotClient(mode=TradingMode.DRY_RUN, safety=SafetyLimits(max_order_quote=25, min_order_quote=5, max_daily_quote=15))
    monkeypatch_price = lambda self, symbol: 100.0
    client.price = lambda symbol: 100.0  # type: ignore
    client.market_buy_quote("BTCUSDT", 10)
    with pytest.raises(ExchangeError, match="Denní limit"):
        client.market_buy_quote("BTCUSDT", 10)


def test_account_dry_run_without_keys():
    client = BinanceSpotClient(mode=TradingMode.DRY_RUN)
    acc = client.account()
    assert acc["accountType"] == "DRY_RUN"
