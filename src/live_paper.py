"""Živý paper loop — periodicky stáhne data a vyhodnotí strategii (bez reálných příkazů)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .market import closes, fetch_binance_klines
from .paper_trader import PaperTrader
from .risk import RiskConfig
from .strategy import Signal, Strategy


@dataclass
class LivePaperConfig:
    symbol: str = "BTCUSDT"
    interval: str = "1h"
    lookback: int = 200
    poll_seconds: int = 60
    max_iterations: int | None = 5  # None = nekonečno (pro tutoriál defaultně omezeno)


def run_live_paper(
    strategy: Strategy,
    *,
    starting_cash: float = 10_000.0,
    fee_rate: float = 0.001,
    risk: RiskConfig | None = None,
    config: LivePaperConfig | None = None,
    sleep_fn=time.sleep,
) -> PaperTrader:
    cfg = config or LivePaperConfig()
    trader = PaperTrader(
        starting_cash=starting_cash, fee_rate=fee_rate, risk=risk or RiskConfig()
    )
    iteration = 0
    last_signal_index = -1

    print(
        f"Live paper start: {cfg.symbol} {cfg.interval} | "
        f"poll={cfg.poll_seconds}s | strategie={getattr(strategy, 'name', '?')}"
    )
    print("Režim: SIMULACE — žádné reálné příkazy.\n")

    while cfg.max_iterations is None or iteration < cfg.max_iterations:
        iteration += 1
        candles = fetch_binance_klines(cfg.symbol, cfg.interval, cfg.lookback)
        prices = closes(candles)
        snaps = strategy.evaluate(prices)
        snap = snaps[-1]
        price = snap.price

        exit_trade = trader.check_exits(price, snap.index)
        if exit_trade:
            print(
                f"[iter {iteration}] EXIT {exit_trade.reason} @ {price:,.2f} "
                f"pnl={exit_trade.pnl:+.2f}"
            )

        # Obchoduj jen když je nový bar / nový signál index
        if snap.index != last_signal_index:
            if snap.signal is Signal.BUY and not trader.in_position:
                trade = trader.buy(price, snap.index, reason=snap.detail or "live-signal")
                if trade:
                    print(f"[iter {iteration}] BUY  @ {price:,.2f} ({trade.reason})")
            elif snap.signal is Signal.SELL and trader.in_position:
                trade = trader.sell(price, snap.index, reason=snap.detail or "live-signal")
                if trade:
                    print(
                        f"[iter {iteration}] SELL @ {price:,.2f} "
                        f"({trade.reason}) pnl={trade.pnl:+.2f}"
                    )
            last_signal_index = snap.index

        eq = trader.equity(price)
        pos = "LONG" if trader.in_position else "FLAT"
        print(
            f"[iter {iteration}] price={price:,.2f} signal={snap.signal.value} "
            f"pos={pos} equity={eq:,.2f}"
        )

        if cfg.max_iterations is None or iteration < cfg.max_iterations:
            sleep_fn(cfg.poll_seconds)

    print("\nLive paper hotovo.")
    return trader
