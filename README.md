# trading-bot-tutorial

Kompletní **paper-trading** bot pro kryptoměny — tutoriál, který tě naučí prakticky všechno od indikátorů po risk management.

Bot **neodesílá reálné příkazy**. Minulé výsledky ≠ budoucí výnosy.

## Co umí

- Indikátory: **SMA, EMA, RSI, MACD, Bollinger**
- Strategie: `sma`, `ema`, `rsi`, `macd`, `bollinger`, `combo`
- Risk: **position sizing**, **stop-loss**, **take-profit**
- Metriky: výnos, max drawdown, win rate, profit factor, Sharpe-like
- Příkazy: `backtest`, `compare`, `live`, `strategies`
- Export: CSV/JSON reporty
- Data: offline CSV nebo Binance public API

## Rychlý start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python bot.py strategies
python bot.py backtest --strategy sma
python bot.py compare
python bot.py live --iterations 3 --poll 5
pytest -q
```

Live data:

```bash
python bot.py backtest --live --strategy macd --limit 200
```

Export:

```bash
python bot.py backtest --strategy combo --export reports/demo
```

## Tutoriál krok za krokem

→ **[docs/TUTORIAL.md](docs/TUTORIAL.md)** — od nuly po live paper loop.

## Struktura

```
bot.py
config.py
docs/TUTORIAL.md
src/   # indicators, strategy, risk, engine, metrics, …
data/sample_btc_usdt.csv
tests/
```

## Disclaimer

Vzdělávací projekt. Nejde o investiční, daňové ani obchodní poradenství.
