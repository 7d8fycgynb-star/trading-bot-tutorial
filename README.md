# trading-bot-tutorial

Jednoduchý **paper-trading** bot pro kryptoměny — tutoriál pro začátečníky.

Bot používá strategii **křížení klouzavých průměrů (SMA crossover)** a obchoduje jen v simulaci.
**Neposílá reálné příkazy na burzu.** Minulé výsledky nezaručují budoucí výnosy.

## Co se naučíš

1. Načíst historická OHLCV data (CSV nebo Binance public API)
2. Spočítat simple moving average (SMA)
3. Generovat signály BUY / SELL při golden / death cross
4. Simulovat obchody včetně poplatků (paper trading)
5. Spustit backtest z příkazové řádky

## Požadavky

- Python 3.10+
- internet jen pokud chceš `--live` data z Binance (jinak stačí přiložené CSV)

## Rychlý start

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Offline backtest na ukázkových datech
python bot.py backtest --csv data/sample_btc_usdt.csv

# Volitelně: stáhnout aktuální svíčky z Binance (bez API klíče)
python bot.py backtest --live --symbol BTCUSDT --interval 1h --limit 200
```

Live režim zkouší veřejné endpointy (`data-api.binance.vision`, případně `api.binance.com` / `api.binance.us`).
Když je burza v regionu nedostupná, použij offline CSV.

Konfiguraci můžeš přepsat přes `.env` (viz `.env.example`).

## Jak strategie funguje

- **Rychlá SMA** (výchozí 10) sleduje kratší trend
- **Pomalá SMA** (výchozí 30) sleduje delší trend
- **Golden cross** (rychlá překříží pomalou směrem nahoru) → `BUY`
- **Death cross** (rychlá překříží pomalou směrem dolů) → `SELL`

Paper trader nakoupí za celý cash a při prodeji uzavře celou pozici. Počítej s poplatkem (`FEE_RATE`, výchozí 0.1 %).

## Struktura projektu

```
bot.py                 # CLI vstupní bod
config.py              # nastavení z prostředí / .env
src/
  indicators.py        # SMA
  strategy.py          # SMA crossover signály
  paper_trader.py      # simulované portfolio
  market.py            # CSV + Binance public API
data/
  sample_btc_usdt.csv  # ukázková data pro offline běh
tests/                 # unit testy
```

## Testy

```bash
pip install -r requirements.txt
pytest -q
```

## Další krohy (nápady)

- Přidat RSI nebo stop-loss
- Logovat obchody do CSV
- Napojit paper účet přes burzovní testnet (stále bez reálných peněz)
- Až budeš rozumět rizikům: teprve potom uvažuj o live tradingu s API klíči

## Disclaimer

Tento projekt je **vzdělávací**. Nejde o investiční, daňové ani obchodní poradenství.
Obchodování kryptoměn je rizikové — můžeš přijít o peníze.
