# Tutoriál: od nuly k paper-trading botovi

Tento dokument tě provede **vším**, co bot umí. Pořád platí: **jen simulace**, žádné reálné peníze.

## 1. Co je trading bot?

Program, který:
1. načte tržní data (ceny),
2. spočítá indikátory,
3. podle pravidel (strategie) vydá signál BUY / SELL / HOLD,
4. provede obchod — u nás **fiktivně** (paper trading),
5. změří výsledek (výnos, drawdown, win rate…).

## 2. Instalace

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ověření:

```bash
pytest -q
python bot.py strategies
```

## 3. Data: CSV vs live

### Offline CSV (doporučeno na začátek)

```bash
python bot.py backtest --csv data/sample_btc_usdt.csv --strategy sma
```

CSV má sloupce: `open_time,open,high,low,close,volume`.

### Live data z Binance (public API, bez klíče)

```bash
python bot.py backtest --live --symbol BTCUSDT --interval 1h --limit 200 --strategy macd
```

Bot zkouší více veřejných endpointů (kvůli regionálním blokacím).

## 4. Indikátory (`src/indicators.py`)

| Indikátor | Co říká | Typické použití |
|-----------|---------|-----------------|
| **SMA** | průměr cen za N svíček | trend, crossover |
| **EMA** | průměr s větším vážením nedávných cen | rychlejší trend |
| **RSI** | momentum 0–100 | oversold / overbought |
| **MACD** | rozdíl dvou EMA + signal line | momentum + crossover |
| **Bollinger** | SMA ± směrodatná odchylka | volatilita, mean reversion |

## 5. Strategie (`src/strategy.py`)

```bash
python bot.py strategies
```

- **sma** — golden/death cross SMA  
- **ema** — totéž na EMA  
- **rsi** — nákup při odchodu z oversold, prodej z overbought  
- **macd** — křížení MACD a signal line  
- **bollinger** — návrat z krajních pásem  
- **combo** — EMA trend + RSI filtr (méně falešných signálů)

## 6. Risk management (`src/risk.py`)

Bez řízení rizika bot „all-in“ umí rychle ztratit fictivní kapitál.

```bash
python bot.py backtest --strategy combo \
  --position-fraction 0.5 \
  --stop-loss 0.03 \
  --take-profit 0.06
```

- **position-fraction** — kolik % cashu jde do jednoho nákupu  
- **stop-loss** — automatický prodej při poklesu (0.03 = −3 %)  
- **take-profit** — automatický prodej při zisku (0.06 = +6 %)  
- vypnutí: `--stop-loss 0 --take-profit 0`

## 7. Metriky (`src/metrics.py`)

Po backtestu uvidíš:

- **výnos %** — celkový paper P&L  
- **max. drawdown %** — největší propad od vrcholu  
- **win rate** — podíl ziskových uzavřených obchodů  
- **profit factor** — součet zisků / součet ztrát  
- **Sharpe-like** — výnos vs. volatilita equity křivky (zjednodušeně)

## 8. Porovnání strategií

```bash
python bot.py compare --csv data/sample_btc_usdt.csv
python bot.py compare --live --limit 300
```

Stejná data → různé strategie → tabulka výnos / DD / win rate.

## 9. Export reportu

```bash
python bot.py backtest --strategy sma --export reports/sma_run
```

Vznikne:
- `trades.csv` — všechny nákupy/prodeje  
- `report.json` — metriky  
- `equity.csv` — křivka kapitálu

## 10. Živý paper loop

```bash
python bot.py live --strategy ema --iterations 3 --poll 5
```

Bot periodicky stáhne data, vyhodnotí signál a **simuluje** obchody.  
Žádné API klíče, žádné reálné ordery.

## 11. Konfigurace přes `.env`

Zkopíruj `.env.example` → `.env` a uprav SYMBOL, STRATEGY, SL/TP…

## 12. Mapa kódu

```
bot.py                 CLI
config.py              nastavení
src/indicators.py      SMA/EMA/RSI/MACD/Bollinger
src/strategy.py        strategie
src/risk.py            SL/TP/sizing
src/paper_trader.py    simulované portfolio
src/engine.py          backtest smyčka
src/metrics.py         výkonnost
src/reporter.py        výpis + export
src/live_paper.py      živý paper loop
src/market.py          CSV + Binance
```

## 13. Jak si bot „naučit“ dál (domácí úkoly)

1. Přidej strategii na základě objemu (volume spike).  
2. Loguj equity do grafu (matplotlib).  
3. Optimalizuj parametry SMA (grid search) — pozor na overfitting.  
4. Až rozumíš rizikům: Binance **testnet** (stále bez reálných peněz).  
5. Live trading s reálnými penězi nedělej, dokud neumíš vysvětlit každou metriku výše.

## Disclaimer

Vzdělávací projekt. Nejde o investiční doporučení. Krypto je rizikové.


## 14. Ostrý trading (reálné peníze)

Až pochopíš paper metriky, pokračuj v **[LIVE_TRADING.md](LIVE_TRADING.md)**.

Shrnutí příkazů:

```bash
python bot.py account --mode dry-run
python bot.py order --mode dry-run --side BUY --quote 10
python bot.py trade --mode dry-run --strategy sma --iterations 3
```

Live je záměrně zamčené frází `ANO_CHCI_REALNE_PENIZE`.
