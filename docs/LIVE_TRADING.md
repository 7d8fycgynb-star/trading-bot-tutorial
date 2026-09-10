# Ostrý trading (reálné peníze)

Toto je **nebezpečná** část tutoriálu. Můžeš přijít o peníze. Bot není investiční doporučení.

## Bezpečnostní pojistky (povinné)

1. **Výchozí režim = `dry-run`** — příkazy se neodesílají  
2. **Limity**: `MAX_ORDER_QUOTE` (default 25 USDT), `MAX_DAILY_QUOTE` (100 USDT)  
3. **Live zámek**: `ENABLE_LIVE_TRADING=true` **a**  
   `LIVE_CONFIRM=ANO_CHCI_REALNE_PENIZE`  
4. API klíč jen s právem **Spot Trade**, **bez Withdraw**  
5. Nejdřív paper (`backtest` / `live`), pak `dry-run`, pak `testnet`, teprve nakonec `live`

## 1) Dry-run (bezpečné, doporučeno teď hned)

```bash
cp .env.example .env
# TRADING_MODE=dry-run

python bot.py account --mode dry-run
python bot.py order --mode dry-run --side BUY --quote 10
python bot.py trade --mode dry-run --strategy sma --iterations 3 --quote 10
```

## 2) Binance Testnet (fiktivní peníze, ale skutečné API)

1. Vytvoř klíče na [Binance Spot Testnet](https://testnet.binance.vision/)  
2. Do `.env`:

```env
TRADING_MODE=testnet
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
BINANCE_BASE_URL=https://testnet.binance.vision
```

```bash
python bot.py account --mode testnet
python bot.py order --mode testnet --side BUY --quote 10
```

## 3) Live (reálné peníze)

```env
TRADING_MODE=live
ENABLE_LIVE_TRADING=true
LIVE_CONFIRM=ANO_CHCI_REALNE_PENIZE
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
MAX_ORDER_QUOTE=15
MAX_DAILY_QUOTE=50
QUOTE_PER_BUY=10
```

```bash
python bot.py account --mode live
python bot.py order --mode live --side BUY --quote 10
python bot.py trade --mode live --strategy rsi --iterations 1 --quote 10 --poll 60
```

## Checklist před live

- [ ] Umíš vysvětlit každou metriku z backtestu  
- [ ] Máš stop-loss nastavený  
- [ ] Order size je částka, kterou jsi ochoten ztratit  
- [ ] Klíč nemá withdraw  
- [ ] Nejdřív jsi ověřil dry-run i testnet  
- [ ] Nejsi v zemi/síti, kde Binance API blokuje (HTTP 451) — případně `BINANCE_BASE_URL`

## Co bot NĚDĚLÁ

- Nevybírá peníze z burzy  
- Neumí futures / páku (schválně — spot only)  
- Negarantuje zisk  
- Neobchází KYC ani omezení burzy  

## Regionální blokace

Z některých sítí vrací Binance HTTP 451. Pak:
- použij VPN/povolenou síť, nebo
- nastav `BINANCE_BASE_URL` na dostupný endpoint (např. Binance.US, pokud ho používáš),
- případně zůstaň u paper/dry-run.


## 2denní test

Bez Binance účtu (paper simulace):

```bash
./scripts/run_2day_test.sh
# nebo:
python bot.py live --days 2 --poll 300 --strategy sma --log logs/2day_paper.log
tail -f logs/2day_paper.log
```

S dry-run exchange (pořád bez reálných peněz):

```bash
MODE=dry-run ./scripts/run_2day_test.sh
```

Stav se ukládá do `logs/*_state.json` — po restartu můžeš pokračovat.
