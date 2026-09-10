#!/usr/bin/env python3
"""CLI — paper + ostrý trading (s pojistkami).

Příklady:
  python bot.py backtest --strategy sma
  python bot.py compare
  python bot.py account
  python bot.py order --side BUY --quote 10
  python bot.py trade --iterations 3
  python bot.py trade --mode live --iterations 1   # jen s pojistkami
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config import settings
from src.engine import run_backtest
from src.exchange import (
    BinanceSpotClient,
    ExchangeError,
    SafetyLimits,
    TradingMode,
)
from src.live_paper import LivePaperConfig, run_live_paper
from src.live_trader import LiveTradeConfig, run_live_trader
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
    if getattr(args, "live_data", False):
        print(
            f"Stahuji {args.symbol} {args.interval} "
            f"({args.limit} svíček) z Binance..."
        )
        candles = fetch_binance_klines(args.symbol, args.interval, args.limit)
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
    p.add_argument("--position-fraction", type=float, default=settings.position_fraction)
    p.add_argument("--stop-loss", type=float, default=settings.stop_loss_pct)
    p.add_argument("--take-profit", type=float, default=settings.take_profit_pct)
    p.add_argument("--fast", type=int, default=settings.fast_period)
    p.add_argument("--slow", type=int, default=settings.slow_period)
    p.add_argument("-q", "--quiet", action="store_true")


def _resolve_mode(mode_str: str) -> TradingMode:
    mode = TradingMode(mode_str)
    if mode is TradingMode.LIVE:
        if not settings.enable_live_trading:
            raise ExchangeError(
                "Live zamčeno. V .env nastav ENABLE_LIVE_TRADING=true a "
                f"LIVE_CONFIRM={SafetyLimits().require_live_phrase}"
            )
    return mode


def _build_client(mode_str: str) -> BinanceSpotClient:
    mode = _resolve_mode(mode_str)
    safety = SafetyLimits(
        max_order_quote=settings.max_order_quote,
        max_daily_quote=settings.max_daily_quote,
        min_order_quote=settings.min_order_quote,
    )
    return BinanceSpotClient(
        api_key=settings.binance_api_key,
        api_secret=settings.binance_api_secret,
        mode=mode,
        base_url=settings.binance_base_url or None,
        safety=safety,
        live_confirm=settings.live_confirm,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crypto bot — paper backtest + ostrý trading s limity."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("strategies", help="Vypíše dostupné strategie")

    backtest = sub.add_parser("backtest", help="Paper backtest")
    source = backtest.add_mutually_exclusive_group()
    source.add_argument("--csv", type=str, default=str(settings.sample_csv))
    source.add_argument("--live", dest="live_data", action="store_true")
    backtest.add_argument("--strategy", default=settings.strategy, choices=sorted(STRATEGIES))
    backtest.add_argument("--export", type=str, default="")
    _add_common(backtest)

    compare = sub.add_parser("compare", help="Porovná strategie")
    source2 = compare.add_mutually_exclusive_group()
    source2.add_argument("--csv", type=str, default=str(settings.sample_csv))
    source2.add_argument("--live", dest="live_data", action="store_true")
    _add_common(compare)

    live = sub.add_parser("live", help="Paper live loop (bez exchange orderů)")
    live.add_argument("--strategy", default=settings.strategy, choices=sorted(STRATEGIES))
    live.add_argument("--poll", type=int, default=5)
    live.add_argument("--iterations", type=int, default=3)
    live.add_argument("--lookback", type=int, default=settings.limit)
    _add_common(live)

    account = sub.add_parser("account", help="Zůstatky (dry-run/testnet/live)")
    account.add_argument(
        "--mode",
        default=settings.trading_mode,
        choices=[m.value for m in TradingMode],
    )

    order = sub.add_parser("order", help="Manuální market order s limity")
    order.add_argument("--mode", default=settings.trading_mode, choices=[m.value for m in TradingMode])
    order.add_argument("--symbol", default=settings.symbol)
    order.add_argument("--side", required=True, choices=["BUY", "SELL"])
    order.add_argument("--quote", type=float, help="USDT částka pro BUY")
    order.add_argument("--quantity", type=float, help="Base qty pro SELL (např. BTC)")

    trade = sub.add_parser(
        "trade",
        help="Strategický live loop s exchange (default dry-run)",
    )
    trade.add_argument("--mode", default=settings.trading_mode, choices=[m.value for m in TradingMode])
    trade.add_argument("--strategy", default=settings.strategy, choices=sorted(STRATEGIES))
    trade.add_argument("--poll", type=int, default=5)
    trade.add_argument("--iterations", type=int, default=3)
    trade.add_argument("--lookback", type=int, default=settings.limit)
    trade.add_argument("--quote", type=float, default=settings.quote_per_buy)
    _add_common(trade)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "strategies":
        print("Dostupné strategie:")
        for name in sorted(STRATEGIES):
            print(f"  - {name}")
        print("\nOstrý trading: docs/LIVE_TRADING.md")
        return 0

    if getattr(args, "stop_loss", None) == 0:
        args.stop_loss = None
    if getattr(args, "take_profit", None) == 0:
        args.take_profit = None

    if args.command == "backtest":
        try:
            prices = _load_prices(args)
        except RuntimeError as exc:
            print(f"Chyba: {exc}", file=sys.stderr)
            return 1
        strategy = build_strategy(args.strategy, fast=args.fast, slow=args.slow)
        risk = _risk_from_args(args)
        print(
            f"Svíček: {len(prices)} | strategie={args.strategy} | "
            f"SL={args.stop_loss} TP={args.take_profit}"
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
            print(
                "Export:",
                export_trades_csv(result, out / "trades.csv"),
                export_report_json(result, out / "report.json"),
                export_equity_csv(result, out / "equity.csv"),
            )
        return 0

    if args.command == "compare":
        try:
            prices = _load_prices(args)
        except RuntimeError as exc:
            print(f"Chyba: {exc}", file=sys.stderr)
            return 1
        risk = _risk_from_args(args)
        results = [
            run_backtest(
                prices,
                build_strategy(name, fast=args.fast, slow=args.slow),
                starting_cash=args.cash,
                fee_rate=args.fee,
                risk=risk,
                verbose=False,
            )
            for name in sorted(STRATEGIES)
        ]
        print_comparison(results)
        return 0

    if args.command == "live":
        strategy = build_strategy(args.strategy, fast=args.fast, slow=args.slow)
        try:
            run_live_paper(
                strategy,
                starting_cash=args.cash,
                fee_rate=args.fee,
                risk=_risk_from_args(args),
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

    if args.command == "account":
        try:
            client = _build_client(args.mode)
            acc = client.account()
            print(f"mode={client.mode.value} base={client.base_url}")
            balances = [
                b for b in acc.get("balances", [])
                if float(b.get("free", 0)) > 0 or float(b.get("locked", 0)) > 0
            ]
            if not balances:
                balances = acc.get("balances", [])[:5]
            for b in balances:
                print(f"  {b['asset']}: free={b['free']} locked={b.get('locked', 0)}")
        except ExchangeError as exc:
            print(f"Chyba: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.command == "order":
        try:
            client = _build_client(args.mode)
            if args.side == "BUY":
                if not args.quote:
                    raise ExchangeError("BUY vyžaduje --quote (USDT)")
                result = client.market_buy_quote(args.symbol, args.quote)
            else:
                if not args.quantity:
                    raise ExchangeError("SELL vyžaduje --quantity (base asset)")
                result = client.market_sell_base(args.symbol, args.quantity)
            print(json.dumps({
                "mode": result.mode,
                "symbol": result.symbol,
                "side": result.side,
                "status": result.status,
                "quote_qty": result.quote_qty,
                "quantity": result.quantity,
                "dry_run": result.dry_run,
                "raw": result.raw,
            }, indent=2, ensure_ascii=False))
        except ExchangeError as exc:
            print(f"Chyba: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.command == "trade":
        try:
            client = _build_client(args.mode)
            strategy = build_strategy(args.strategy, fast=args.fast, slow=args.slow)
            run_live_trader(
                strategy,
                client,
                risk=_risk_from_args(args),
                config=LiveTradeConfig(
                    symbol=args.symbol,
                    interval=args.interval,
                    lookback=args.lookback,
                    poll_seconds=args.poll,
                    max_iterations=args.iterations,
                    quote_per_buy=args.quote,
                ),
            )
        except (ExchangeError, RuntimeError) as exc:
            print(f"Chyba: {exc}", file=sys.stderr)
            return 1
        return 0

    parser.error(f"Neznámý příkaz: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
