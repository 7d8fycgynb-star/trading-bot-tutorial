"""Backtest engine — propojí strategii, risk a paper trader."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics import PerformanceReport, build_report
from .paper_trader import PaperTrader, Trade
from .risk import RiskConfig
from .strategy import Signal, Strategy


@dataclass
class BacktestResult:
    strategy_name: str
    report: PerformanceReport
    trades: list[Trade]
    equity_curve: list[float]


def run_backtest(
    closes: list[float],
    strategy: Strategy,
    *,
    starting_cash: float = 10_000.0,
    fee_rate: float = 0.001,
    risk: RiskConfig | None = None,
    close_open_at_end: bool = True,
    verbose: bool = False,
) -> BacktestResult:
    trader = PaperTrader(
        starting_cash=starting_cash,
        fee_rate=fee_rate,
        risk=risk or RiskConfig(),
    )
    snapshots = strategy.evaluate(closes)
    equity_curve: list[float] = []

    for snap in snapshots:
        # Nejdřív risk exits (SL/TP), pak signál strategie
        exit_trade = trader.check_exits(snap.price, snap.index)
        if exit_trade and verbose:
            _print_trade(exit_trade)

        if snap.signal is Signal.BUY and not trader.in_position:
            trade = trader.buy(snap.price, snap.index, reason=snap.detail or "signal")
            if trade and verbose:
                _print_trade(trade)
        elif snap.signal is Signal.SELL and trader.in_position:
            trade = trader.sell(snap.price, snap.index, reason=snap.detail or "signal")
            if trade and verbose:
                _print_trade(trade)

        equity_curve.append(trader.equity(snap.price))

    last_price = closes[-1]
    if close_open_at_end and trader.in_position:
        trade = trader.sell(last_price, len(closes) - 1, reason="end-of-backtest")
        if trade:
            equity_curve[-1] = trader.equity(last_price)
            if verbose:
                _print_trade(trade)

    report = build_report(
        starting_cash=starting_cash,
        ending_equity=trader.equity(last_price),
        equity_curve=equity_curve,
        closed_pnls=trader.closed_pnls,
        total_trades=len(trader.trades),
    )
    return BacktestResult(
        strategy_name=getattr(strategy, "name", strategy.__class__.__name__),
        report=report,
        trades=trader.trades,
        equity_curve=equity_curve,
    )


def _print_trade(trade: Trade) -> None:
    pnl = "" if trade.pnl is None else f"  pnl={trade.pnl:+.2f}"
    print(
        f"[{trade.timestamp_index:4d}] {trade.side:4s} @ {trade.price:,.2f}  "
        f"qty={trade.quantity:.6f}  fee={trade.fee:.2f}  ({trade.reason}){pnl}"
    )
