"""Strategie křížení klouzavých průměrů (SMA crossover)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .indicators import sma


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class StrategyConfig:
    fast_period: int = 10
    slow_period: int = 30

    def __post_init__(self) -> None:
        if self.fast_period <= 0 or self.slow_period <= 0:
            raise ValueError("periods must be > 0")
        if self.fast_period >= self.slow_period:
            raise ValueError("fast_period must be < slow_period")


@dataclass(frozen=True)
class StrategySnapshot:
    index: int
    price: float
    fast_sma: float | None
    slow_sma: float | None
    signal: Signal


class SmaCrossoverStrategy:
    """Nákup při golden cross (rychlá SMA nad pomalou), prodej při death cross."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()

    def evaluate(self, closes: list[float]) -> list[StrategySnapshot]:
        fast = sma(closes, self.config.fast_period)
        slow = sma(closes, self.config.slow_period)
        snapshots: list[StrategySnapshot] = []

        prev_diff: float | None = None
        for i, price in enumerate(closes):
            f, s = fast[i], slow[i]
            signal = Signal.HOLD

            if f is not None and s is not None:
                diff = f - s
                if prev_diff is not None:
                    if prev_diff <= 0 < diff:
                        signal = Signal.BUY
                    elif prev_diff >= 0 > diff:
                        signal = Signal.SELL
                prev_diff = diff

            snapshots.append(
                StrategySnapshot(
                    index=i,
                    price=price,
                    fast_sma=f,
                    slow_sma=s,
                    signal=signal,
                )
            )

        return snapshots
