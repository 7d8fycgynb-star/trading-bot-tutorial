"""Živý paper loop — periodicky stáhne data a vyhodnotí strategii (bez reálných příkazů)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .loop_utils import RunLogger, load_state, save_state
from .market import closes, fetch_binance_klines
from .paper_trader import PaperTrader
from .risk import RiskConfig
from .strategy import Signal, Strategy


@dataclass
class LivePaperConfig:
    symbol: str = "BTCUSDT"
    interval: str = "1h"
    lookback: int = 200
    poll_seconds: int = 300  # 5 min — vhodné pro 1h svíčky
    max_iterations: int | None = 5
    duration_seconds: float | None = None
    log_file: str | None = None
    state_file: str | None = None


def run_live_paper(
    strategy: Strategy,
    *,
    starting_cash: float = 10_000.0,
    fee_rate: float = 0.001,
    risk: RiskConfig | None = None,
    config: LivePaperConfig | None = None,
    sleep_fn=time.sleep,
    time_fn=time.time,
) -> PaperTrader:
    cfg = config or LivePaperConfig()
    logger = RunLogger(cfg.log_file)
    risk = risk or RiskConfig()
    trader = PaperTrader(
        starting_cash=starting_cash, fee_rate=fee_rate, risk=risk
    )
    iteration = 0
    last_signal_index = -1
    started = time_fn()

    if cfg.state_file:
        saved = load_state(cfg.state_file)
        if saved:
            trader.cash = float(saved.get("cash", trader.cash))
            trader.position = float(saved.get("position", 0.0))
            trader.entry_price = saved.get("entry_price")
            if trader.entry_price is not None:
                trader.entry_price = float(trader.entry_price)
                trader.stop_price = risk.stop_price(trader.entry_price)
                trader.take_profit_price = risk.take_profit_price(trader.entry_price)
            last_signal_index = int(saved.get("last_signal_index", -1))
            logger.log(f"Obnoven stav z {cfg.state_file}")

    logger.log(
        f"Live paper start: {cfg.symbol} {cfg.interval} | poll={cfg.poll_seconds}s | "
        f"strategie={getattr(strategy, 'name', '?')} | "
        f"duration={cfg.duration_seconds or 'iterations-only'}s"
    )
    logger.log("Režim: SIMULACE — žádné reálné příkazy.")

    while True:
        iteration += 1
        if cfg.max_iterations is not None and iteration > cfg.max_iterations:
            break
        if cfg.duration_seconds is not None and (time_fn() - started) >= cfg.duration_seconds:
            logger.log("Uplynul časový limit — končím.")
            break

        candles = fetch_binance_klines(cfg.symbol, cfg.interval, cfg.lookback)
        prices = closes(candles)
        snaps = strategy.evaluate(prices)
        snap = snaps[-1]
        price = snap.price

        exit_trade = trader.check_exits(price, snap.index)
        if exit_trade:
            logger.log(
                f"[iter {iteration}] EXIT {exit_trade.reason} @ {price:,.2f} "
                f"pnl={exit_trade.pnl:+.2f}"
            )

        if snap.index != last_signal_index:
            if snap.signal is Signal.BUY and not trader.in_position:
                trade = trader.buy(price, snap.index, reason=snap.detail or "live-signal")
                if trade:
                    logger.log(f"[iter {iteration}] BUY  @ {price:,.2f} ({trade.reason})")
            elif snap.signal is Signal.SELL and trader.in_position:
                trade = trader.sell(price, snap.index, reason=snap.detail or "live-signal")
                if trade:
                    logger.log(
                        f"[iter {iteration}] SELL @ {price:,.2f} "
                        f"({trade.reason}) pnl={trade.pnl:+.2f}"
                    )
            last_signal_index = snap.index

        eq = trader.equity(price)
        pos = "LONG" if trader.in_position else "FLAT"
        logger.log(
            f"[iter {iteration}] price={price:,.2f} signal={snap.signal.value} "
            f"pos={pos} equity={eq:,.2f}"
        )

        if cfg.state_file:
            save_state(
                cfg.state_file,
                {
                    "cash": trader.cash,
                    "position": trader.position,
                    "entry_price": trader.entry_price,
                    "last_signal_index": last_signal_index,
                    "equity": eq,
                    "iteration": iteration,
                },
            )

        # ukonči před sleep, pokud další iterace už nemá smysl
        if cfg.max_iterations is not None and iteration >= cfg.max_iterations:
            break
        if cfg.duration_seconds is not None and (time_fn() - started) >= cfg.duration_seconds:
            break
        sleep_fn(cfg.poll_seconds)

    summary = trader.summary(price)
    logger.log(
        f"Hotovo. equity={summary['equity']} return={summary['return_pct']}% "
        f"trades={summary['trades']}"
    )
    return trader
