#!/usr/bin/env python3
"""CLI vstupní bod — paper-trading bot (tutoriál).

Příklady:
  python bot.py backtest --csv data/sample_btc_usdt.csv
  python bot.py backtest --live
"""

from __future__ import annotations

import argparse
import sys

from config import settings
from src.market import closes, fetch_binance_klines, load_candles_from_csv
from src.paper_trader import PaperTrader
from src.strategy import Signal, SmaCrossoverStrategy, StrategyConfig


def run_backtest(
    price_series: list[float],
    *,
    fast_period: int,
    slow_period: int,
    starting_cash: float,
    fee_rate: float,
    verbose: bool = True,
) -> dict:
    strategy = SmaCrossoverStrategy(
        StrategyConfig(fast_period=fast_period, slow_period=slow_period)
    )
    trader = PaperTrader(starting_cash=starting_cash, fee_rate=fee_rate)
    snapshots = strategy.evaluate(price_series)

    for snap in snapshots:
        if snap.signal is Signal.BUY:
            trade = trader.buy(snap.price, snap.index)
            if trade and verbose:
                print(
                    f"[{snap.index:4d}] BUY  @ {snap.price:,.2f}  "
                    f"qty={trade.quantity:.6f}  fee={trade.fee:.2f}"
                )
        elif snap.signal is Signal.SELL:
            trade = trader.sell(snap.price, snap.index)
            if trade and verbose:
                print(
                    f"[{snap.index:4d}] SELL @ {snap.price:,.2f}  "
                    f"qty={trade.quantity:.6f}  fee={trade.fee:.2f}"
                )

    last_price = price_series[-1]
    # Uzavři otevřenou pozici na konci backtestu kvůli férovém P&L
    if trader.in_position:
        trade = trader.sell(last_price, len(price_series) - 1)
        if trade and verbose:
            print(
                f"[END ] SELL @ {last_price:,.2f}  "
                f"(uzavření pozice na konci backtestu)"
            )

    summary = trader.summary(last_price)
    if verbose:
        print()
        print("=== Shrnutí paper backtestu ===")
        print(f"Startovní kapitál : {summary['starting_cash']:,.2f} USDT")
        print(f"Konečné equity    : {summary['equity']:,.2f} USDT")
        print(f"Výnos             : {summary['return_pct']}%")
        print(f"Počet obchodů     : {summary['trades']}")
        print()
        print(
            "POZOR: Toto je simulace. Nejde o investiční doporučení "
            "a minulé výsledky nezaručují budoucí výnosy."
        )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Jednoduchý crypto paper-trading bot (SMA crossover)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    backtest = sub.add_parser("backtest", help="Spustí paper backtest")
    source = backtest.add_mutually_exclusive_group()
    source.add_argument(
        "--csv",
        type=str,
        default=str(settings.sample_csv),
        help="Cesta k CSV se svíčkami (výchozí: sample data)",
    )
    source.add_argument(
        "--live",
        action="store_true",
        help="Stáhne aktuální data z Binance public API",
    )
    backtest.add_argument("--symbol", default=settings.symbol)
    backtest.add_argument("--interval", default=settings.interval)
    backtest.add_argument("--limit", type=int, default=settings.limit)
    backtest.add_argument("--fast", type=int, default=settings.fast_period)
    backtest.add_argument("--slow", type=int, default=settings.slow_period)
    backtest.add_argument("--cash", type=float, default=settings.starting_cash)
    backtest.add_argument("--fee", type=float, default=settings.fee_rate)
    backtest.add_argument("-q", "--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "backtest":
        if args.live:
            print(
                f"Stahuji {args.symbol} {args.interval} "
                f"({args.limit} svíček) z Binance..."
            )
            try:
                candles = fetch_binance_klines(
                    symbol=args.symbol, interval=args.interval, limit=args.limit
                )
            except RuntimeError as exc:
                print(f"Chyba: {exc}", file=sys.stderr)
                return 1
        else:
            print(f"Načítám CSV: {args.csv}")
            candles = load_candles_from_csv(args.csv)

        prices = closes(candles)
        print(
            f"Svíček: {len(prices)} | SMA {args.fast}/{args.slow} | "
            f"cash={args.cash:g} | fee={args.fee}"
        )
        print()
        run_backtest(
            prices,
            fast_period=args.fast,
            slow_period=args.slow,
            starting_cash=args.cash,
            fee_rate=args.fee,
            verbose=not args.quiet,
        )
        return 0

    parser.error(f"Neznámý příkaz: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
