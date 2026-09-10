"""Technické indikátory — stavební kameny strategií."""

from __future__ import annotations

from dataclasses import dataclass


def sma(values: list[float], period: int) -> list[float | None]:
    """Simple Moving Average."""
    if period <= 0:
        raise ValueError("period must be > 0")
    if not values:
        return []

    result: list[float | None] = [None] * len(values)
    window_sum = 0.0
    for i, value in enumerate(values):
        window_sum += value
        if i >= period:
            window_sum -= values[i - period]
        if i >= period - 1:
            result[i] = window_sum / period
    return result


def ema(values: list[float], period: int) -> list[float | None]:
    """Exponential Moving Average."""
    if period <= 0:
        raise ValueError("period must be > 0")
    if not values:
        return []

    result: list[float | None] = [None] * len(values)
    multiplier = 2 / (period + 1)
    prev: float | None = None

    for i, value in enumerate(values):
        if i < period - 1:
            continue
        if prev is None:
            seed = sum(values[i - period + 1 : i + 1]) / period
            prev = seed
            result[i] = seed
        else:
            prev = (value - prev) * multiplier + prev
            result[i] = prev
    return result


def rsi(values: list[float], period: int = 14) -> list[float | None]:
    """Relative Strength Index (0–100)."""
    if period <= 0:
        raise ValueError("period must be > 0")
    n = len(values)
    result: list[float | None] = [None] * n
    if n <= period:
        return result

    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        change = values[i] - values[i - 1]
        if change >= 0:
            gains += change
        else:
            losses -= change

    avg_gain = gains / period
    avg_loss = losses / period
    result[period] = 100.0 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))

    for i in range(period + 1, n):
        change = values[i] - values[i - 1]
        gain = max(change, 0.0)
        loss = max(-change, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        result[i] = 100.0 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))
    return result


@dataclass(frozen=True)
class MacdSeries:
    macd: list[float | None]
    signal: list[float | None]
    histogram: list[float | None]


def macd(
    values: list[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> MacdSeries:
    """MACD = EMA(fast) − EMA(slow), signal = EMA(MACD)."""
    fast_line = ema(values, fast)
    slow_line = ema(values, slow)
    macd_line: list[float | None] = []
    for f, s in zip(fast_line, slow_line):
        macd_line.append(None if f is None or s is None else f - s)

    # EMA přes známé MACD hodnoty — pro výuku držíme indexovou délku
    compact = [v for v in macd_line if v is not None]
    signal_compact = ema(compact, signal_period)

    signal_line: list[float | None] = [None] * len(values)
    hist: list[float | None] = [None] * len(values)
    compact_i = 0
    for i, m in enumerate(macd_line):
        if m is None:
            continue
        sig = signal_compact[compact_i]
        compact_i += 1
        signal_line[i] = sig
        if sig is not None:
            hist[i] = m - sig

    return MacdSeries(macd=macd_line, signal=signal_line, histogram=hist)


@dataclass(frozen=True)
class BollingerSeries:
    mid: list[float | None]
    upper: list[float | None]
    lower: list[float | None]


def bollinger(
    values: list[float], period: int = 20, num_std: float = 2.0
) -> BollingerSeries:
    """Bollinger Bands: SMA ± k·směrodatná odchylka."""
    mid = sma(values, period)
    upper: list[float | None] = [None] * len(values)
    lower: list[float | None] = [None] * len(values)

    for i in range(len(values)):
        if mid[i] is None:
            continue
        window = values[i - period + 1 : i + 1]
        mean = mid[i]
        variance = sum((x - mean) ** 2 for x in window) / period
        std = variance**0.5
        upper[i] = mean + num_std * std
        lower[i] = mean - num_std * std

    return BollingerSeries(mid=mid, upper=upper, lower=lower)
