"""Simulovaný obchodník (paper trading) — žádné reálné peníze."""

from __future__ import annotations

from dataclasses import dataclass, field

from .risk import RiskConfig


@dataclass
class Trade:
    side: str  # BUY | SELL
    price: float
    quantity: float
    fee: float
    timestamp_index: int
    reason: str = ""
    pnl: float | None = None


@dataclass
class PaperTrader:
    """Paper trader s velikostí pozice a evidencí P&L."""

    starting_cash: float = 10_000.0
    fee_rate: float = 0.001
    risk: RiskConfig = field(default_factory=RiskConfig)
    cash: float = field(init=False)
    position: float = field(init=False, default=0.0)
    entry_price: float | None = field(init=False, default=None)
    stop_price: float | None = field(init=False, default=None)
    take_profit_price: float | None = field(init=False, default=None)
    trades: list[Trade] = field(init=False, default_factory=list)
    closed_pnls: list[float] = field(init=False, default_factory=list)

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

    def buy(
        self, price: float, timestamp_index: int = 0, reason: str = "signal"
    ) -> Trade | None:
        if self.in_position or self.cash <= 0 or price <= 0:
            return None

        budget = self.cash * self.risk.position_fraction
        spendable = budget / (1 + self.fee_rate)
        if spendable <= 0:
            return None
        quantity = spendable / price
        fee = spendable * self.fee_rate
        total = spendable + fee

        self.cash -= total
        self.position = quantity
        self.entry_price = price
        self.stop_price = self.risk.stop_price(price)
        self.take_profit_price = self.risk.take_profit_price(price)

        trade = Trade("BUY", price, quantity, fee, timestamp_index, reason)
        self.trades.append(trade)
        return trade

    def sell(
        self, price: float, timestamp_index: int = 0, reason: str = "signal"
    ) -> Trade | None:
        if not self.in_position or price <= 0 or self.entry_price is None:
            return None

        gross = self.position * price
        fee = gross * self.fee_rate
        net = gross - fee
        quantity = self.position
        # P&L po poplatcích oproti nákladům na nákup
        cost = self.entry_price * quantity * (1 + self.fee_rate)
        pnl = net - cost

        self.cash += net
        self.position = 0.0
        self.entry_price = None
        self.stop_price = None
        self.take_profit_price = None
        self.closed_pnls.append(pnl)

        trade = Trade("SELL", price, quantity, fee, timestamp_index, reason, pnl)
        self.trades.append(trade)
        return trade

    def check_exits(self, price: float, timestamp_index: int) -> Trade | None:
        """Zkontroluje stop-loss / take-profit na aktuální ceně."""
        if not self.in_position:
            return None
        if self.stop_price is not None and price <= self.stop_price:
            return self.sell(price, timestamp_index, reason="stop-loss")
        if self.take_profit_price is not None and price >= self.take_profit_price:
            return self.sell(price, timestamp_index, reason="take-profit")
        return None

    def summary(self, last_price: float) -> dict[str, float | int]:
        equity = self.equity(last_price)
        return {
            "starting_cash": self.starting_cash,
            "cash": round(self.cash, 2),
            "position": round(self.position, 8),
            "equity": round(equity, 2),
            "return_pct": round((equity / self.starting_cash - 1) * 100, 2),
            "trades": len(self.trades),
            "closed_trades": len(self.closed_pnls),
        }
