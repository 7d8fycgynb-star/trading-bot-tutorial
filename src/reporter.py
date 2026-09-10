"""Výpisy a export výsledků (CSV / JSON)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .engine import BacktestResult
from .metrics import PerformanceReport


DISCLAIMER = (
    "POZOR: Toto je simulace. Nejde o investiční doporučení "
    "a minulé výsledky nezaručují budoucí výnosy."
)


def print_report(result: BacktestResult) -> None:
    r = result.report
    print()
    print(f"=== Shrnutí: {result.strategy_name} ===")
    print(f"Startovní kapitál : {r.starting_cash:,.2f} USDT")
    print(f"Konečné equity    : {r.ending_equity:,.2f} USDT")
    print(f"Výnos             : {r.return_pct:.2f}%")
    print(f"Max. drawdown     : {r.max_drawdown_pct:.2f}%")
    print(f"Win rate          : {r.win_rate_pct:.2f}%")
    print(f"Profit factor     : {r.profit_factor:.2f}")
    print(f"Obchody (closed)  : {r.closed_trades}  (celkem eventů: {r.total_trades})")
    print(f"Avg / best / worst: {r.avg_trade_pnl:.2f} / {r.best_trade:.2f} / {r.worst_trade:.2f}")
    print(f"Sharpe-like       : {r.sharpe_like:.2f}")
    print()
    print(DISCLAIMER)


def print_comparison(results: list[BacktestResult]) -> None:
    print()
    print(f"{'strategie':<12} {'výnos%':>8} {'DD%':>8} {'win%':>8} {'PF':>6} {'obchody':>8}")
    print("-" * 56)
    for res in sorted(results, key=lambda x: x.report.return_pct, reverse=True):
        r = res.report
        print(
            f"{res.strategy_name:<12} {r.return_pct:>8.2f} {r.max_drawdown_pct:>8.2f} "
            f"{r.win_rate_pct:>8.2f} {r.profit_factor:>6.2f} {r.closed_trades:>8}"
        )
    print()
    print(DISCLAIMER)


def export_trades_csv(result: BacktestResult, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["index", "side", "price", "quantity", "fee", "reason", "pnl"],
        )
        writer.writeheader()
        for t in result.trades:
            writer.writerow(
                {
                    "index": t.timestamp_index,
                    "side": t.side,
                    "price": t.price,
                    "quantity": t.quantity,
                    "fee": t.fee,
                    "reason": t.reason,
                    "pnl": "" if t.pnl is None else t.pnl,
                }
            )
    return path


def export_report_json(result: BacktestResult, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "strategy": result.strategy_name,
        "metrics": result.report.as_dict(),
        "trades": [
            {
                "index": t.timestamp_index,
                "side": t.side,
                "price": t.price,
                "quantity": t.quantity,
                "fee": t.fee,
                "reason": t.reason,
                "pnl": t.pnl,
            }
            for t in result.trades
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def export_equity_csv(result: BacktestResult, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["index", "equity"])
        for i, eq in enumerate(result.equity_curve):
            writer.writerow([i, eq])
    return path
