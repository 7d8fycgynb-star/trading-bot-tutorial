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


def _optional_float(name: str, default: float | None) -> float | None:
    raw = os.getenv(name)
    if raw is None:
        return default
    if raw.strip().lower() in {"", "none", "off", "false"}:
        return None
    return float(raw)


@dataclass(frozen=True)
class Settings:
    symbol: str = os.getenv("SYMBOL", "BTCUSDT")
    interval: str = os.getenv("INTERVAL", "1h")
    limit: int = _int("LIMIT", 200)
    strategy: str = os.getenv("STRATEGY", "sma")
    fast_period: int = _int("FAST_PERIOD", 10)
    slow_period: int = _int("SLOW_PERIOD", 30)
    starting_cash: float = _float("STARTING_CASH", 10_000.0)
    fee_rate: float = _float("FEE_RATE", 0.001)
    position_fraction: float = _float("POSITION_FRACTION", 1.0)
    stop_loss_pct: float | None = _optional_float("STOP_LOSS_PCT", 0.03)
    take_profit_pct: float | None = _optional_float("TAKE_PROFIT_PCT", 0.06)
    sample_csv: Path = ROOT / "data" / "sample_btc_usdt.csv"
    reports_dir: Path = ROOT / "reports"


settings = Settings()
