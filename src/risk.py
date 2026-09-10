"""Risk management — velikost pozice, stop-loss, take-profit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    """Pravidla řízení rizika pro paper trading."""

    position_fraction: float = 1.0  # podíl cashu na nákup (0–1)
    stop_loss_pct: float | None = 0.03  # 3 % pod vstupem
    take_profit_pct: float | None = 0.06  # 6 % nad vstupem
    max_open_trades: int = 1

    def __post_init__(self) -> None:
        if not 0 < self.position_fraction <= 1:
            raise ValueError("position_fraction must be in (0, 1]")
        if self.stop_loss_pct is not None and self.stop_loss_pct <= 0:
            raise ValueError("stop_loss_pct must be > 0")
        if self.take_profit_pct is not None and self.take_profit_pct <= 0:
            raise ValueError("take_profit_pct must be > 0")
        if self.max_open_trades < 1:
            raise ValueError("max_open_trades must be >= 1")

    def stop_price(self, entry: float) -> float | None:
        if self.stop_loss_pct is None:
            return None
        return entry * (1 - self.stop_loss_pct)

    def take_profit_price(self, entry: float) -> float | None:
        if self.take_profit_pct is None:
            return None
        return entry * (1 + self.take_profit_pct)
