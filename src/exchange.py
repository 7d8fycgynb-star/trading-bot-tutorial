"""Binance Spot klient — dry-run / testnet / live.

Bezpečnostní zásady:
- API klíče jen z prostředí (.env), nikdy do gitu
- výchozí režim je dry-run (nic se neodesílá)
- live vyžaduje explicitní potvrzení
- doporučení: klíč jen Spot Trade, BEZ výběru (withdraw)
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import urlencode

import requests


class TradingMode(str, Enum):
    DRY_RUN = "dry-run"
    TESTNET = "testnet"
    LIVE = "live"


MODE_BASE_URLS = {
    TradingMode.TESTNET: "https://testnet.binance.vision",
    TradingMode.LIVE: "https://api.binance.com",
}


@dataclass(frozen=True)
class SafetyLimits:
    """Tvrdé limity proti nehodě."""

    max_order_quote: float = 25.0  # max USDT na jeden market order
    max_daily_quote: float = 100.0  # soft limit na sumu quote za běh procesu
    min_order_quote: float = 5.0
    require_live_phrase: str = "ANO_CHCI_REALNE_PENIZE"


@dataclass
class OrderResult:
    mode: str
    symbol: str
    side: str
    quote_qty: float | None
    quantity: float | None
    status: str
    raw: dict[str, Any]
    dry_run: bool = False


class ExchangeError(RuntimeError):
    pass


class BinanceSpotClient:
    def __init__(
        self,
        *,
        api_key: str = "",
        api_secret: str = "",
        mode: TradingMode = TradingMode.DRY_RUN,
        base_url: str | None = None,
        safety: SafetyLimits | None = None,
        live_confirm: str = "",
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.mode = mode
        self.safety = safety or SafetyLimits()
        self.session = session or requests.Session()
        self._spent_quote_today = 0.0

        if base_url:
            self.base_url = base_url.rstrip("/")
        elif mode is TradingMode.DRY_RUN:
            # dry-run defaultně cílí na live URL jen pro veřejné info; order se nepošle
            self.base_url = MODE_BASE_URLS[TradingMode.LIVE]
        else:
            self.base_url = MODE_BASE_URLS[mode]

        if mode is TradingMode.LIVE:
            if live_confirm != self.safety.require_live_phrase:
                raise ExchangeError(
                    "Live režim zamčen. Nastav LIVE_CONFIRM="
                    f"{self.safety.require_live_phrase} a ENABLE_LIVE_TRADING=true."
                )
            if not self.api_key or not self.api_secret:
                raise ExchangeError("Live režim vyžaduje BINANCE_API_KEY a BINANCE_API_SECRET.")

        if mode is TradingMode.TESTNET and (not self.api_key or not self.api_secret):
            raise ExchangeError("Testnet vyžaduje TESTNET API klíč a secret.")

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        return headers

    def _sign(self, params: dict[str, Any]) -> str:
        query = urlencode(params, doseq=True)
        return hmac.new(
            self.api_secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        signed: bool = False,
        timeout: float = 20.0,
    ) -> Any:
        params = dict(params or {})
        if signed:
            if not self.api_secret:
                raise ExchangeError("Chybí API secret pro podepsaný request.")
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 5000
            params["signature"] = self._sign(params)

        url = f"{self.base_url}{path}"
        response = self.session.request(
            method, url, params=params, headers=self._headers(), timeout=timeout
        )
        if response.status_code >= 400:
            raise ExchangeError(
                f"Binance HTTP {response.status_code}: {response.text[:300]}"
            )
        return response.json()

    def ping(self) -> dict[str, Any]:
        return self._request("GET", "/api/v3/ping")

    def price(self, symbol: str) -> float:
        symbol = symbol.upper()
        errors: list[str] = []
        bases = [self.base_url]
        for mirror in (
            "https://data-api.binance.vision",
            "https://api.binance.com",
            "https://api.binance.us",
        ):
            if mirror not in bases:
                bases.append(mirror)
        for base in bases:
            try:
                url = f"{base}/api/v3/ticker/price"
                response = self.session.get(
                    url, params={"symbol": symbol}, headers=self._headers(), timeout=15
                )
                response.raise_for_status()
                return float(response.json()["price"])
            except Exception as exc:  # noqa: BLE001 - zkusíme další mirror
                errors.append(f"{base}: {exc}")
        raise ExchangeError("Nepodařilo se získat cenu. " + " | ".join(errors))

    def account(self) -> dict[str, Any]:
        if self.mode is TradingMode.DRY_RUN and not (self.api_key and self.api_secret):
            return {
                "accountType": "DRY_RUN",
                "balances": [
                    {"asset": "USDT", "free": "10000", "locked": "0"},
                    {"asset": "BTC", "free": "0", "locked": "0"},
                ],
            }
        return self._request("GET", "/api/v3/account", signed=True)

    def free_balance(self, asset: str) -> float:
        acc = self.account()
        asset = asset.upper()
        for bal in acc.get("balances", []):
            if bal.get("asset") == asset:
                return float(bal.get("free", 0))
        return 0.0

    def _check_quote_limits(self, quote_qty: float) -> None:
        if quote_qty < self.safety.min_order_quote:
            raise ExchangeError(
                f"Order {quote_qty} USDT je pod minimem {self.safety.min_order_quote}."
            )
        if quote_qty > self.safety.max_order_quote:
            raise ExchangeError(
                f"Order {quote_qty} USDT překračuje MAX_ORDER_QUOTE="
                f"{self.safety.max_order_quote}. Zvyš limit jen vědomě."
            )
        if self._spent_quote_today + quote_qty > self.safety.max_daily_quote:
            raise ExchangeError(
                f"Denní limit {self.safety.max_daily_quote} USDT by byl překročen "
                f"(už {self._spent_quote_today:.2f})."
            )

    def market_buy_quote(self, symbol: str, quote_qty: float) -> OrderResult:
        """Market BUY za quote množství (např. 10 USDT)."""
        symbol = symbol.upper()
        quote_qty = float(quote_qty)
        self._check_quote_limits(quote_qty)

        if self.mode is TradingMode.DRY_RUN:
            px = None
            try:
                px = self.price(symbol)
            except Exception:
                px = None
            raw = {
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quoteOrderQty": quote_qty,
                "simulated_price": px,
                "note": "DRY-RUN — příkaz NEBYL odeslán",
            }
            self._spent_quote_today += quote_qty
            return OrderResult(
                mode=self.mode.value,
                symbol=symbol,
                side="BUY",
                quote_qty=quote_qty,
                quantity=None,
                status="DRY_RUN",
                raw=raw,
                dry_run=True,
            )

        raw = self._request(
            "POST",
            "/api/v3/order",
            {
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quoteOrderQty": f"{quote_qty:.8f}".rstrip("0").rstrip("."),
            },
            signed=True,
        )
        self._spent_quote_today += quote_qty
        return OrderResult(
            mode=self.mode.value,
            symbol=symbol,
            side="BUY",
            quote_qty=quote_qty,
            quantity=float(raw.get("executedQty") or 0) or None,
            status=str(raw.get("status", "UNKNOWN")),
            raw=raw,
        )

    def market_sell_base(self, symbol: str, quantity: float) -> OrderResult:
        """Market SELL za base množství (např. 0.001 BTC)."""
        symbol = symbol.upper()
        quantity = float(quantity)
        if quantity <= 0:
            raise ExchangeError("quantity must be > 0")

        # odhad quote pro denní limit
        try:
            est_quote = self.price(symbol) * quantity
        except Exception:
            est_quote = 0.0
        if est_quote:
            self._check_quote_limits(est_quote)

        if self.mode is TradingMode.DRY_RUN:
            raw = {
                "symbol": symbol,
                "side": "SELL",
                "type": "MARKET",
                "quantity": quantity,
                "estimated_quote": est_quote,
                "note": "DRY-RUN — příkaz NEBYL odeslán",
            }
            if est_quote:
                self._spent_quote_today += est_quote
            return OrderResult(
                mode=self.mode.value,
                symbol=symbol,
                side="SELL",
                quote_qty=est_quote or None,
                quantity=quantity,
                status="DRY_RUN",
                raw=raw,
                dry_run=True,
            )

        # Binance vyžaduje správný stepSize — tutoriál používá zaokrouhlení na 6 míst
        qty = f"{quantity:.6f}".rstrip("0").rstrip(".")
        raw = self._request(
            "POST",
            "/api/v3/order",
            {
                "symbol": symbol,
                "side": "SELL",
                "type": "MARKET",
                "quantity": qty,
            },
            signed=True,
        )
        if est_quote:
            self._spent_quote_today += est_quote
        return OrderResult(
            mode=self.mode.value,
            symbol=symbol,
            side="SELL",
            quote_qty=est_quote or None,
            quantity=float(raw.get("executedQty") or quantity),
            status=str(raw.get("status", "UNKNOWN")),
            raw=raw,
        )
