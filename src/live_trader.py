"""Živý obchodní loop — strategie + exchange (dry-run/testnet/live)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .exchange import BinanceSpotClient, OrderResult
from .loop_utils import RunLogger, load_state, save_state
from .market import closes, fetch_binance_klines
from .risk import RiskConfig
from .strategy import Signal, Strategy


@dataclass
class LiveTradeConfig:
    symbol: str = "BTCUSDT"
    interval: str = "1h"
    lookback: int = 200
    poll_seconds: int = 300
    max_iterations: int | None = 3
    duration_seconds: float | None = None
    quote_per_buy: float = 15.0
    log_file: str | None = None
    state_file: str | None = None


@dataclass
class LiveTradeState:
    in_position: bool = False
    base_qty: float = 0.0
    entry_price: float | None = None
    orders: list[OrderResult] = field(default_factory=list)


def run_live_trader(
    strategy: Strategy,
    client: BinanceSpotClient,
    *,
    risk: RiskConfig | None = None,
    config: LiveTradeConfig | None = None,
    sleep_fn=time.sleep,
    time_fn=time.time,
) -> LiveTradeState:
    cfg = config or LiveTradeConfig()
    risk = risk or RiskConfig()
    logger = RunLogger(cfg.log_file)
    state = LiveTradeState()
    last_index = -1
    iteration = 0
    started = time_fn()

    if cfg.state_file:
        saved = load_state(cfg.state_file)
        if saved:
            state.in_position = bool(saved.get("in_position", False))
            state.base_qty = float(saved.get("base_qty", 0.0))
            entry = saved.get("entry_price")
            state.entry_price = float(entry) if entry is not None else None
            last_index = int(saved.get("last_index", -1))
            logger.log(f"Obnoven stav z {cfg.state_file}")

    logger.log(
        f"LIVE TRADER start | mode={client.mode.value} | {cfg.symbol} {cfg.interval} | "
        f"quote/buy={cfg.quote_per_buy} | strategie={getattr(strategy, 'name', '?')} | "
        f"duration={cfg.duration_seconds or 'iterations-only'}s"
    )
    if client.mode.value == "live":
        logger.log("!!! OSTRÝ REŽIM — reálné peníze !!!")
    elif client.mode.value == "dry-run":
        logger.log("Dry-run: příkazy se jen simulují.")

    while True:
        iteration += 1
        if cfg.max_iterations is not None and iteration > cfg.max_iterations:
            break
        if cfg.duration_seconds is not None and (time_fn() - started) >= cfg.duration_seconds:
            logger.log("Uplynul časový limit — končím.")
            break

        candles = fetch_binance_klines(cfg.symbol, cfg.interval, cfg.lookback)
        prices = closes(candles)
        snap = strategy.evaluate(prices)[-1]
        price = snap.price

        if state.in_position and state.entry_price is not None:
            stop = risk.stop_price(state.entry_price)
            take = risk.take_profit_price(state.entry_price)
            if stop is not None and price <= stop:
                order = client.market_sell_base(cfg.symbol, state.base_qty)
                state.orders.append(order)
                state.in_position = False
                state.base_qty = 0.0
                state.entry_price = None
                logger.log(f"[iter {iteration}] STOP-LOSS SELL status={order.status}")
            elif take is not None and price >= take:
                order = client.market_sell_base(cfg.symbol, state.base_qty)
                state.orders.append(order)
                state.in_position = False
                state.base_qty = 0.0
                state.entry_price = None
                logger.log(f"[iter {iteration}] TAKE-PROFIT SELL status={order.status}")

        if snap.index != last_index:
            if snap.signal is Signal.BUY and not state.in_position:
                quote = cfg.quote_per_buy * risk.position_fraction
                order = client.market_buy_quote(cfg.symbol, quote)
                state.orders.append(order)
                qty = order.quantity if order.quantity is not None else quote / price
                state.in_position = True
                state.base_qty = qty
                state.entry_price = price
                logger.log(
                    f"[iter {iteration}] BUY  @ ~{price:,.2f} quote={quote} "
                    f"status={order.status} ({snap.detail or 'signal'})"
                )
            elif snap.signal is Signal.SELL and state.in_position:
                order = client.market_sell_base(cfg.symbol, state.base_qty)
                state.orders.append(order)
                state.in_position = False
                state.base_qty = 0.0
                state.entry_price = None
                logger.log(
                    f"[iter {iteration}] SELL @ ~{price:,.2f} "
                    f"status={order.status} ({snap.detail or 'signal'})"
                )
            last_index = snap.index

        pos = "LONG" if state.in_position else "FLAT"
        logger.log(
            f"[iter {iteration}] price={price:,.2f} signal={snap.signal.value} "
            f"pos={pos} mode={client.mode.value}"
        )

        if cfg.state_file:
            save_state(
                cfg.state_file,
                {
                    "in_position": state.in_position,
                    "base_qty": state.base_qty,
                    "entry_price": state.entry_price,
                    "last_index": last_index,
                    "iteration": iteration,
                    "mode": client.mode.value,
                },
            )

        if cfg.max_iterations is not None and iteration >= cfg.max_iterations:
            break
        if cfg.duration_seconds is not None and (time_fn() - started) >= cfg.duration_seconds:
            break
        sleep_fn(cfg.poll_seconds)

    logger.log(f"Live trader hotovo. orders={len(state.orders)}")
    return state
