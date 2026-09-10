"""Obchodní strategie — signály BUY / SELL / HOLD."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .indicators import bollinger, ema, macd, rsi, sma


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class StrategySnapshot:
    index: int
    price: float
    signal: Signal
    detail: str = ""


class Strategy(Protocol):
    name: str

    def evaluate(self, closes: list[float]) -> list[StrategySnapshot]: ...


@dataclass(frozen=True)
class SmaConfig:
    fast_period: int = 10
    slow_period: int = 30

    def __post_init__(self) -> None:
        if self.fast_period >= self.slow_period:
            raise ValueError("fast_period must be < slow_period")


class SmaCrossoverStrategy:
    """Golden / death cross na SMA."""

    name = "sma"

    def __init__(self, config: SmaConfig | None = None) -> None:
        self.config = config or SmaConfig()

    def evaluate(self, closes: list[float]) -> list[StrategySnapshot]:
        fast = sma(closes, self.config.fast_period)
        slow = sma(closes, self.config.slow_period)
        out: list[StrategySnapshot] = []
        prev: float | None = None
        for i, price in enumerate(closes):
            signal = Signal.HOLD
            detail = ""
            f, s = fast[i], slow[i]
            if f is not None and s is not None:
                diff = f - s
                if prev is not None:
                    if prev <= 0 < diff:
                        signal = Signal.BUY
                        detail = "golden cross SMA"
                    elif prev >= 0 > diff:
                        signal = Signal.SELL
                        detail = "death cross SMA"
                prev = diff
            out.append(StrategySnapshot(i, price, signal, detail))
        return out


@dataclass(frozen=True)
class EmaConfig:
    fast_period: int = 12
    slow_period: int = 26


class EmaCrossoverStrategy:
    """Křížení EMA — rychlejší než SMA."""

    name = "ema"

    def __init__(self, config: EmaConfig | None = None) -> None:
        self.config = config or EmaConfig()
        if self.config.fast_period >= self.config.slow_period:
            raise ValueError("fast_period must be < slow_period")

    def evaluate(self, closes: list[float]) -> list[StrategySnapshot]:
        fast = ema(closes, self.config.fast_period)
        slow = ema(closes, self.config.slow_period)
        out: list[StrategySnapshot] = []
        prev: float | None = None
        for i, price in enumerate(closes):
            signal = Signal.HOLD
            detail = ""
            f, s = fast[i], slow[i]
            if f is not None and s is not None:
                diff = f - s
                if prev is not None:
                    if prev <= 0 < diff:
                        signal, detail = Signal.BUY, "golden cross EMA"
                    elif prev >= 0 > diff:
                        signal, detail = Signal.SELL, "death cross EMA"
                prev = diff
            out.append(StrategySnapshot(i, price, signal, detail))
        return out


@dataclass(frozen=True)
class RsiConfig:
    period: int = 14
    oversold: float = 30.0
    overbought: float = 70.0


class RsiStrategy:
    """RSI: nákup z přeprodanosti, prodej z překoupenosti."""

    name = "rsi"

    def __init__(self, config: RsiConfig | None = None) -> None:
        self.config = config or RsiConfig()

    def evaluate(self, closes: list[float]) -> list[StrategySnapshot]:
        values = rsi(closes, self.config.period)
        out: list[StrategySnapshot] = []
        prev: float | None = None
        for i, price in enumerate(closes):
            signal = Signal.HOLD
            detail = ""
            r = values[i]
            if r is not None and prev is not None:
                if prev < self.config.oversold <= r:
                    signal, detail = Signal.BUY, f"RSI opouští oversold ({r:.1f})"
                elif prev > self.config.overbought >= r:
                    signal, detail = Signal.SELL, f"RSI opouští overbought ({r:.1f})"
            if r is not None:
                prev = r
            out.append(StrategySnapshot(i, price, signal, detail))
        return out


@dataclass(frozen=True)
class MacdConfig:
    fast: int = 12
    slow: int = 26
    signal_period: int = 9


class MacdStrategy:
    """MACD line kříží signal line."""

    name = "macd"

    def __init__(self, config: MacdConfig | None = None) -> None:
        self.config = config or MacdConfig()

    def evaluate(self, closes: list[float]) -> list[StrategySnapshot]:
        series = macd(
            closes, self.config.fast, self.config.slow, self.config.signal_period
        )
        out: list[StrategySnapshot] = []
        prev: float | None = None
        for i, price in enumerate(closes):
            signal = Signal.HOLD
            detail = ""
            m, s = series.macd[i], series.signal[i]
            if m is not None and s is not None:
                diff = m - s
                if prev is not None:
                    if prev <= 0 < diff:
                        signal, detail = Signal.BUY, "MACD bullish cross"
                    elif prev >= 0 > diff:
                        signal, detail = Signal.SELL, "MACD bearish cross"
                prev = diff
            out.append(StrategySnapshot(i, price, signal, detail))
        return out


@dataclass(frozen=True)
class BollingerConfig:
    period: int = 20
    num_std: float = 2.0


class BollingerStrategy:
    """Mean reversion: nákup u dolní, prodej u horní bandy."""

    name = "bollinger"

    def __init__(self, config: BollingerConfig | None = None) -> None:
        self.config = config or BollingerConfig()

    def evaluate(self, closes: list[float]) -> list[StrategySnapshot]:
        bands = bollinger(closes, self.config.period, self.config.num_std)
        out: list[StrategySnapshot] = []
        prev_below = False
        prev_above = False
        for i, price in enumerate(closes):
            signal = Signal.HOLD
            detail = ""
            lo, hi = bands.lower[i], bands.upper[i]
            if lo is not None and hi is not None:
                below = price < lo
                above = price > hi
                # vstup při návratu dovnitř pásma
                if prev_below and not below and price <= bands.mid[i]:
                    signal, detail = Signal.BUY, "návrat z dolní Bollinger bandy"
                elif prev_above and not above and price >= bands.mid[i]:
                    signal, detail = Signal.SELL, "návrat z horní Bollinger bandy"
                prev_below, prev_above = below, above
            out.append(StrategySnapshot(i, price, signal, detail))
        return out


@dataclass(frozen=True)
class ComboConfig:
    rsi_period: int = 14
    rsi_oversold: float = 35.0
    rsi_overbought: float = 65.0
    ema_fast: int = 12
    ema_slow: int = 26


class ComboStrategy:
    """Kombinace: trend (EMA) + momentum (RSI) — méně falešných signálů.

    BUY  = golden cross EMA, nebo RSI opouští oversold v uptrendu
    SELL = death cross EMA, nebo RSI opouští overbought
    """

    name = "combo"

    def __init__(self, config: ComboConfig | None = None) -> None:
        self.config = config or ComboConfig()

    def evaluate(self, closes: list[float]) -> list[StrategySnapshot]:
        fast = ema(closes, self.config.ema_fast)
        slow = ema(closes, self.config.ema_slow)
        r = rsi(closes, self.config.rsi_period)
        out: list[StrategySnapshot] = []
        prev_trend: float | None = None
        prev_rsi: float | None = None
        for i, price in enumerate(closes):
            signal = Signal.HOLD
            detail = ""
            f, s, rsi_v = fast[i], slow[i], r[i]
            if f is not None and s is not None and rsi_v is not None:
                trend = f - s
                uptrend = trend > 0
                if prev_trend is not None and prev_rsi is not None:
                    golden = prev_trend <= 0 < trend
                    death = prev_trend >= 0 > trend
                    rsi_buy = prev_rsi < self.config.rsi_oversold <= rsi_v and uptrend
                    rsi_sell = prev_rsi > self.config.rsi_overbought >= rsi_v
                    if golden or rsi_buy:
                        signal = Signal.BUY
                        detail = "combo BUY (EMA/RSI)"
                    elif death or rsi_sell:
                        signal = Signal.SELL
                        detail = "combo SELL (EMA/RSI)"
                prev_trend = trend
                prev_rsi = rsi_v
            out.append(StrategySnapshot(i, price, signal, detail))
        return out


STRATEGIES = {
    "sma": SmaCrossoverStrategy,
    "ema": EmaCrossoverStrategy,
    "rsi": RsiStrategy,
    "macd": MacdStrategy,
    "bollinger": BollingerStrategy,
    "combo": ComboStrategy,
}


def build_strategy(name: str, **kwargs):
    key = name.lower()
    if key not in STRATEGIES:
        raise ValueError(f"Neznámá strategie: {name}. Dostupné: {list(STRATEGIES)}")
    cls = STRATEGIES[key]
    # předáme jen relevantní kwargs přes jednoduché config objekty
    if key == "sma":
        return cls(SmaConfig(kwargs.get("fast", 10), kwargs.get("slow", 30)))
    if key == "ema":
        return cls(EmaConfig(kwargs.get("fast", 12), kwargs.get("slow", 26)))
    if key == "rsi":
        return cls(
            RsiConfig(
                kwargs.get("rsi_period", 14),
                kwargs.get("oversold", 30.0),
                kwargs.get("overbought", 70.0),
            )
        )
    if key == "macd":
        return cls(MacdConfig(kwargs.get("fast", 12), kwargs.get("slow", 26), 9))
    if key == "bollinger":
        return cls(BollingerConfig(kwargs.get("bb_period", 20), 2.0))
    if key == "combo":
        return cls(ComboConfig())
    return cls()
