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


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "ano"}


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

    # Exchange / real money
    trading_mode: str = os.getenv("TRADING_MODE", "dry-run")  # dry-run|testnet|live
    enable_live_trading: bool = _bool("ENABLE_LIVE_TRADING", False)
    live_confirm: str = os.getenv("LIVE_CONFIRM", "")
    binance_api_key: str = os.getenv("BINANCE_API_KEY", "")
    binance_api_secret: str = os.getenv("BINANCE_API_SECRET", "")
    binance_base_url: str = os.getenv("BINANCE_BASE_URL", "")
    max_order_quote: float = _float("MAX_ORDER_QUOTE", 25.0)
    max_daily_quote: float = _float("MAX_DAILY_QUOTE", 100.0)
    min_order_quote: float = _float("MIN_ORDER_QUOTE", 5.0)
    quote_per_buy: float = _float("QUOTE_PER_BUY", 15.0)


settings = Settings()
