#!/usr/bin/env python3
"""CLI — kompletní paper-trading tutoriálový bot.

Příklady:
  python bot.py strategies
  python bot.py backtest --strategy sma
  python bot.py backtest --strategy rsi --live
  python bot.py compare
  python bot.py live --iterations 3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config import settings
from src.engine import run_backtest
from src.live_paper import LivePaperConfig, run_live_paper
from src.market import closes, fetch_binance_klines, load_candles_from_csv
from src.reporter import (
    export_equity_csv,
    export_report_json,
    export_trades_csv,
    print_comparison,
    print_report,
)
from src.risk import RiskConfig
from src.strategy import STRATEGIES, build_strategy


def _load_prices(args) -> list[float]:
    if getattr(args, "live_data", False) or getattr(args, "live", False):
        # backtest --live stahuje data; subcommand live má vlastní cestu
        print(
            f"Stahuji {args.symbol} {args.interval} "
            f"({args.limit} svíček) z Binance..."
        )
        try:
            candles = fetch_binance_klines(args.symbol, args.interval, args.limit)
        except RuntimeError as exc:
            print(f"Chyba: {exc}", file=sys.stderr)
            raise
    else:
        csv_path = getattr(args, "csv", str(settings.sample_csv))
        print(f"Načítám CSV: {csv_path}")
        candles = load_candles_from_csv(csv_path)
    return closes(candles)


def _risk_from_args(args) -> RiskConfig:
    return RiskConfig(
        position_fraction=args.position_fraction,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
    )


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--symbol", default=settings.symbol)
    p.add_argument("--interval", default=settings.interval)
    p.add_argument("--limit", type=int, default=settings.limit)
    p.add_argument("--cash", type=float, default=settings.starting_cash)
    p.add_argument("--fee", type=float, default=settings.fee_rate)
    p.add_argument(
        "--position-fraction",
        type=float,
        default=settings.position_fraction,
        help="Podíl cashu na jeden nákup (0–1)",
    )
    p.add_argument(
        "--stop-loss",
        type=float,
        nargs="?",
        const=settings.stop_loss_pct,
        default=settings.stop_loss_pct,
        help="Stop-loss jako desetinné číslo (0.03 = 3 %). Pro vypnutí: --stop-loss 0 a uprav kód, nebo nastav v .env na none",
    )
    p.add_argument(
        "--take-profit",
        type=float,
        nargs="?",
        const=settings.take_profit_pct,
        default=settings.take_profit_pct,
        help="Take-profit (0.06 = 6 %)",
    )
    p.add_argument("--fast", type=int, default=settings.fast_period)
    p.add_argument("--slow", type=int, default=settings.slow_period)
    p.add_argument("-q", "--quiet", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crypto paper-trading bot — tutoriál (SMA/EMA/RSI/MACD/Bollinger/Combo)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("strategies", help="Vypíše dostupné strategie")

    backtest = sub.add_parser("backtest", help="Paper backtest jedné strategie")
    source = backtest.add_mutually_exclusive_group()
    source.add_argument("--csv", type=str, default=str(settings.sample_csv))
    source.add_argument(
        "--live",
        dest="live_data",
        action="store_true",
        help="Stáhne aktuální data z Binance public API",
    )
    backtest.add_argument(
        "--strategy", default=settings.strategy, choices=sorted(STRATEGIES)
    )
    backtest.add_argument(
        "--export",
        type=str,
        default="",
        help="Složka pro export trades.csv / report.json / equity.csv",
    )
    _add_common(backtest)

    compare = sub.add_parser("compare", help="Porovná všechny strategie na stejných datech")
    source2 = compare.add_mutually_exclusive_group()
    source2.add_argument("--csv", type=str, default=str(settings.sample_csv))
    source2.add_argument("--live", dest="live_data", action="store_true")
    _add_common(compare)

    live = sub.add_parser("live", help="Živý paper loop (simulace, bez reálných příkazů)")
    live.add_argument("--strategy", default=settings.strategy, choices=sorted(STRATEGIES))
    live.add_argument("--poll", type=int, default=5, help="Sekundy mezi iteracemi")
    live.add_argument("--iterations", type=int, default=3, help="Počet iterací")
    live.add_argument("--lookback", type=int, default=settings.limit)
    _add_common(live)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "strategies":
        print("Dostupné strategie:")
        for name in sorted(STRATEGIES):
            print(f"  - {name}")
        print("\nDetail najdeš v docs/TUTORIAL.md")
        return 0

    # Normalizace SL/TP: 0 znamená vypnuto
    if getattr(args, "stop_loss", None) == 0:
        args.stop_loss = None
    if getattr(args, "take_profit", None) == 0:
        args.take_profit = None

    risk = _risk_from_args(args)

    if args.command == "backtest":
        try:
            prices = _load_prices(args)
        except RuntimeError:
            return 1
        strategy = build_strategy(args.strategy, fast=args.fast, slow=args.slow)
        print(
            f"Svíček: {len(prices)} | strategie={args.strategy} | "
            f"SL={args.stop_loss} TP={args.take_profit} | "
            f"fraction={args.position_fraction} | fee={args.fee}"
        )
        print()
        result = run_backtest(
            prices,
            strategy,
            starting_cash=args.cash,
            fee_rate=args.fee,
            risk=risk,
            verbose=not args.quiet,
        )
        if not args.quiet:
            print_report(result)
        if args.export:
            out = Path(args.export)
            t = export_trades_csv(result, out / "trades.csv")
            j = export_report_json(result, out / "report.json")
            e = export_equity_csv(result, out / "equity.csv")
            print(f"Export: {t}, {j}, {e}")
        return 0

    if args.command == "compare":
        try:
            prices = _load_prices(args)
        except RuntimeError:
            return 1
        print(f"Svíček: {len(prices)} | porovnání strategií\n")
        results = []
        for name in sorted(STRATEGIES):
            strategy = build_strategy(name, fast=args.fast, slow=args.slow)
            results.append(
                run_backtest(
                    prices,
                    strategy,
                    starting_cash=args.cash,
                    fee_rate=args.fee,
                    risk=risk,
                    verbose=False,
                )
            )
        print_comparison(results)
        return 0

    if args.command == "live":
        strategy = build_strategy(args.strategy, fast=args.fast, slow=args.slow)
        try:
            run_live_paper(
                strategy,
                starting_cash=args.cash,
                fee_rate=args.fee,
                risk=risk,
                config=LivePaperConfig(
                    symbol=args.symbol,
                    interval=args.interval,
                    lookback=args.lookback,
                    poll_seconds=args.poll,
                    max_iterations=args.iterations,
                ),
            )
        except RuntimeError as exc:
            print(f"Chyba: {exc}", file=sys.stderr)
            return 1
        return 0

    parser.error(f"Neznámý příkaz: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
