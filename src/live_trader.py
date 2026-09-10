"""Živý obchodní loop — strategie + exchange (dry-run/testnet/live)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .exchange import BinanceSpotClient, OrderResult
from .market import closes, fetch_binance_klines
from .risk import RiskConfig
from .strategy import Signal, Strategy


@dataclass
class LiveTradeConfig:
    symbol: str = "BTCUSDT"
    interval: str = "1h"
    lookback: int = 200
    poll_seconds: int = 60
    max_iterations: int | None = 3
    quote_per_buy: float = 15.0  # kolik USDT na jeden nákup


@dataclass
class LiveTradeState:
    in_position: bool = False
    base_qty: float = 0.0
    entry_price: float | None = None
    orders: list[OrderResult] | None = None

    def __post_init__(self) -> None:
        if self.orders is None:
            self.orders = []


def run_live_trader(
    strategy: Strategy,
    client: BinanceSpotClient,
    *,
    risk: RiskConfig | None = None,
    config: LiveTradeConfig | None = None,
    sleep_fn=time.sleep,
) -> LiveTradeState:
    """Spustí trading loop.

    Důležité: i v LIVE režimu platí SafetyLimits z klienta (max order / denní limit).
    """
    cfg = config or LiveTradeConfig()
    risk = risk or RiskConfig()
    state = LiveTradeState()
    last_index = -1
    iteration = 0

    print(
        f"LIVE TRADER start | mode={client.mode.value} | {cfg.symbol} {cfg.interval} | "
        f"quote/buy={cfg.quote_per_buy} | strategie={getattr(strategy, 'name', '?')}"
    )
    if client.mode.value == "live":
        print("!!! OSTRÝ REŽIM — reálné peníze !!!")
    elif client.mode.value == "dry-run":
        print("Dry-run: příkazy se jen simulují.")
    print()

    while cfg.max_iterations is None or iteration < cfg.max_iterations:
        iteration += 1
        candles = fetch_binance_klines(cfg.symbol, cfg.interval, cfg.lookback)
        prices = closes(candles)
        snap = strategy.evaluate(prices)[-1]
        price = snap.price

        # Stop-loss / take-profit proti entry
        if state.in_position and state.entry_price is not None:
            stop = risk.stop_price(state.entry_price)
            take = risk.take_profit_price(state.entry_price)
            if stop is not None and price <= stop:
                order = client.market_sell_base(cfg.symbol, state.base_qty)
                state.orders.append(order)
                state.in_position = False
                state.base_qty = 0.0
                state.entry_price = None
                print(f"[iter {iteration}] STOP-LOSS SELL status={order.status}")
            elif take is not None and price >= take:
                order = client.market_sell_base(cfg.symbol, state.base_qty)
                state.orders.append(order)
                state.in_position = False
                state.base_qty = 0.0
                state.entry_price = None
                print(f"[iter {iteration}] TAKE-PROFIT SELL status={order.status}")

        if snap.index != last_index:
            if snap.signal is Signal.BUY and not state.in_position:
                quote = cfg.quote_per_buy * risk.position_fraction
                order = client.market_buy_quote(cfg.symbol, quote)
                state.orders.append(order)
                # odhad qty
                qty = order.quantity
                if qty is None:
                    qty = quote / price
                state.in_position = True
                state.base_qty = qty
                state.entry_price = price
                print(
                    f"[iter {iteration}] BUY  @ ~{price:,.2f} quote={quote} "
                    f"status={order.status} ({snap.detail or 'signal'})"
                )
            elif snap.signal is Signal.SELL and state.in_position:
                order = client.market_sell_base(cfg.symbol, state.base_qty)
                state.orders.append(order)
                state.in_position = False
                state.base_qty = 0.0
                state.entry_price = None
                print(
                    f"[iter {iteration}] SELL @ ~{price:,.2f} "
                    f"status={order.status} ({snap.detail or 'signal'})"
                )
            last_index = snap.index

        pos = "LONG" if state.in_position else "FLAT"
        print(
            f"[iter {iteration}] price={price:,.2f} signal={snap.signal.value} "
            f"pos={pos} mode={client.mode.value}"
        )

        if cfg.max_iterations is None or iteration < cfg.max_iterations:
            sleep_fn(cfg.poll_seconds)

    print("\nLive trader hotovo.")
    return state
