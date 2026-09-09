from pathlib import Path

from bot import run_backtest
from src.market import closes, load_candles_from_csv


def test_sample_backtest_runs():
    csv_path = Path(__file__).resolve().parents[1] / "data" / "sample_btc_usdt.csv"
    prices = closes(load_candles_from_csv(csv_path))
    summary = run_backtest(
        prices,
        fast_period=10,
        slow_period=30,
        starting_cash=10_000,
        fee_rate=0.001,
        verbose=False,
    )
    assert summary["trades"] >= 2
    assert summary["equity"] > 0
    assert summary["starting_cash"] == 10_000
