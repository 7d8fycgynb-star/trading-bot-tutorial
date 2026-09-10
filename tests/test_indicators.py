from src.indicators import bollinger, ema, macd, rsi, sma


def test_sma_basic():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = sma(values, 3)
    assert result[:2] == [None, None]
    assert result[2] == 2.0
    assert result[3] == 3.0
    assert result[4] == 4.0


def test_ema_starts_after_period():
    values = [float(i) for i in range(1, 11)]
    result = ema(values, 5)
    assert result[:4] == [None, None, None, None]
    assert result[4] is not None
    assert result[-1] is not None


def test_rsi_bounds():
    # rostoucí řada → vysoké RSI
    up = [float(i) for i in range(1, 40)]
    r = rsi(up, 14)
    assert r[-1] is not None and r[-1] > 70


def test_macd_and_bollinger_lengths():
    values = [100 + (i % 7) - 3 for i in range(80)]
    m = macd(values)
    b = bollinger(values, 20, 2)
    assert len(m.macd) == len(values)
    assert len(b.upper) == len(values)
    assert any(x is not None for x in m.histogram)
    assert any(x is not None for x in b.lower)
