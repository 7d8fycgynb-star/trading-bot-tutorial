"""Načítání OHLCV dat — CSV (offline) nebo Binance public API."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import requests

# api.binance.com bývá v některých regionech blokované (HTTP 451).
# data-api.binance.vision je veřejný mirror kline dat.
BINANCE_KLINES_URLS = (
    "https://data-api.binance.vision/api/v3/klines",
    "https://api.binance.com/api/v3/klines",
    "https://api.binance.us/api/v3/klines",
)


@dataclass(frozen=True)
class Candle:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_candles_from_csv(path: str | Path) -> list[Candle]:
    """Načte svíčky z CSV se sloupci: open_time,open,high,low,close,volume."""
    path = Path(path)
    candles: list[Candle] = []

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"open_time", "open", "high", "low", "close", "volume"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"CSV must contain columns: {sorted(required)}")

        for row in reader:
            candles.append(
                Candle(
                    open_time=int(row["open_time"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )

    if not candles:
        raise ValueError(f"No candles found in {path}")
    return candles


def fetch_binance_klines(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 200,
    timeout: float = 15.0,
) -> list[Candle]:
    """Stáhne veřejné kline data z Binance (bez API klíče)."""
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    errors: list[str] = []

    for url in BINANCE_KLINES_URLS:
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            raw = response.json()
            break
        except requests.RequestException as exc:
            errors.append(f"{url}: {exc}")
    else:
        detail = " | ".join(errors)
        raise RuntimeError(
            "Nepodařilo se stáhnout data z Binance public API. "
            f"Zkus --csv data/sample_btc_usdt.csv. Detaily: {detail}"
        )

    candles: list[Candle] = []
    for item in raw:
        candles.append(
            Candle(
                open_time=int(item[0]),
                open=float(item[1]),
                high=float(item[2]),
                low=float(item[3]),
                close=float(item[4]),
                volume=float(item[5]),
            )
        )
    return candles


def closes(candles: list[Candle]) -> list[float]:
    return [c.close for c in candles]
