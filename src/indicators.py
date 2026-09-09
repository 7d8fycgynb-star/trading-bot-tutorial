"""Technické indikátory pro začátečníky."""

from __future__ import annotations


def sma(values: list[float], period: int) -> list[float | None]:
    """Simple Moving Average.

    Pro prvních ``period - 1`` hodnot vrací ``None`` (ještě není dost dat).
    """
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
