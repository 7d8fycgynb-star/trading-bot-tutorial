"""Konfigurace bota — hodnoty lze přepsat přes .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    symbol: str = os.getenv("SYMBOL", "BTCUSDT")
    interval: str = os.getenv("INTERVAL", "1h")
    limit: int = _int("LIMIT", 200)
    fast_period: int = _int("FAST_PERIOD", 10)
    slow_period: int = _int("SLOW_PERIOD", 30)
    starting_cash: float = _float("STARTING_CASH", 10_000.0)
    fee_rate: float = _float("FEE_RATE", 0.001)
    sample_csv: Path = ROOT / "data" / "sample_btc_usdt.csv"


settings = Settings()
