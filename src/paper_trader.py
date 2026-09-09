"""Simulovaný obchodník (paper trading) — žádné reálné peníze."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Trade:
    side: str  # BUY | SELL
    price: float
    quantity: float
    fee: float
    timestamp_index: int


@dataclass
class PaperTrader:
    """Jednoduchý paper trader: drží buď cash, nebo pozici (ne obojí zároveň)."""

    starting_cash: float = 10_000.0
    fee_rate: float = 0.001  # 0.1 % jako na burze
    cash: float = field(init=False)
    position: float = field(init=False, default=0.0)
    entry_price: float | None = field(init=False, default=None)
    trades: list[Trade] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        if self.starting_cash <= 0:
            raise ValueError("starting_cash must be > 0")
        if self.fee_rate < 0:
            raise ValueError("fee_rate must be >= 0")
        self.cash = float(self.starting_cash)

    @property
    def in_position(self) -> bool:
        return self.position > 0

    def equity(self, price: float) -> float:
        return self.cash + self.position * price

    def buy(self, price: float, timestamp_index: int = 0) -> Trade | None:
        """Nakoupí za všechen dostupný cash (po poplatku)."""
        if self.in_position or self.cash <= 0 or price <= 0:
            return None

        spendable = self.cash / (1 + self.fee_rate)
        quantity = spendable / price
        fee = spendable * self.fee_rate
        total = spendable + fee

        self.cash -= total
        self.position = quantity
        self.entry_price = price

        trade = Trade("BUY", price, quantity, fee, timestamp_index)
        self.trades.append(trade)
        return trade

    def sell(self, price: float, timestamp_index: int = 0) -> Trade | None:
        """Prodá celou pozici."""
        if not self.in_position or price <= 0:
            return None

        gross = self.position * price
        fee = gross * self.fee_rate
        net = gross - fee
        quantity = self.position

        self.cash += net
        self.position = 0.0
        self.entry_price = None

        trade = Trade("SELL", price, quantity, fee, timestamp_index)
        self.trades.append(trade)
        return trade

    def summary(self, last_price: float) -> dict[str, float | int]:
        equity = self.equity(last_price)
        return {
            "starting_cash": self.starting_cash,
            "cash": round(self.cash, 2),
            "position": round(self.position, 8),
            "equity": round(equity, 2),
            "return_pct": round((equity / self.starting_cash - 1) * 100, 2),
            "trades": len(self.trades),
        }
