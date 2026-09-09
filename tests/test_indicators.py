from src.indicators import sma


def test_sma_basic():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = sma(values, 3)
    assert result[:2] == [None, None]
    assert result[2] == 2.0
    assert result[3] == 3.0
    assert result[4] == 4.0


def test_sma_period_one():
    values = [10.0, 20.0]
    assert sma(values, 1) == [10.0, 20.0]


def test_sma_empty():
    assert sma([], 5) == []
