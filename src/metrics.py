"""Metriky výkonnosti backtestu."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceReport:
    starting_cash: float
    ending_equity: float
    return_pct: float
    total_trades: int
    closed_trades: int
    win_rate_pct: float
    profit_factor: float
    max_drawdown_pct: float
    avg_trade_pnl: float
    best_trade: float
    worst_trade: float
    sharpe_like: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "starting_cash": round(self.starting_cash, 2),
            "ending_equity": round(self.ending_equity, 2),
            "return_pct": round(self.return_pct, 2),
            "total_trades": self.total_trades,
            "closed_trades": self.closed_trades,
            "win_rate_pct": round(self.win_rate_pct, 2),
            "profit_factor": round(self.profit_factor, 2),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "avg_trade_pnl": round(self.avg_trade_pnl, 2),
            "best_trade": round(self.best_trade, 2),
            "worst_trade": round(self.worst_trade, 2),
            "sharpe_like": round(self.sharpe_like, 2),
        }


def max_drawdown_pct(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)
    return max_dd * 100


def sharpe_like(returns: list[float]) -> float:
    """Jednoduchá Sharpe-like metrika (bez risk-free rate, roční normalizace neřešíme)."""
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = var**0.5
    if std == 0:
        return 0.0
    return mean / std


def build_report(
    *,
    starting_cash: float,
    ending_equity: float,
    equity_curve: list[float],
    closed_pnls: list[float],
    total_trades: int,
) -> PerformanceReport:
    wins = [p for p in closed_pnls if p > 0]
    losses = [p for p in closed_pnls if p <= 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = (
        gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
    )
    # denní/bar výnosy z equity křivky
    bar_returns = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]
        if prev:
            bar_returns.append((equity_curve[i] - prev) / prev)

    return PerformanceReport(
        starting_cash=starting_cash,
        ending_equity=ending_equity,
        return_pct=(ending_equity / starting_cash - 1) * 100 if starting_cash else 0.0,
        total_trades=total_trades,
        closed_trades=len(closed_pnls),
        win_rate_pct=(len(wins) / len(closed_pnls) * 100) if closed_pnls else 0.0,
        profit_factor=profit_factor if profit_factor != float("inf") else 999.0,
        max_drawdown_pct=max_drawdown_pct(equity_curve),
        avg_trade_pnl=(sum(closed_pnls) / len(closed_pnls)) if closed_pnls else 0.0,
        best_trade=max(closed_pnls) if closed_pnls else 0.0,
        worst_trade=min(closed_pnls) if closed_pnls else 0.0,
        sharpe_like=sharpe_like(bar_returns),
    )
