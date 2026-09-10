from pathlib import Path

from src.engine import run_backtest
from src.market import closes, load_candles_from_csv
from src.risk import RiskConfig
from src.strategy import STRATEGIES, build_strategy


def test_sample_backtest_runs():
    csv_path = Path(__file__).resolve().parents[1] / "data" / "sample_btc_usdt.csv"
    prices = closes(load_candles_from_csv(csv_path))
    result = run_backtest(
        prices,
        build_strategy("sma", fast=10, slow=30),
        starting_cash=10_000,
        fee_rate=0.001,
        risk=RiskConfig(stop_loss_pct=0.05, take_profit_pct=0.1),
        verbose=False,
    )
    assert result.report.total_trades >= 2
    assert result.report.ending_equity > 0
    assert len(result.equity_curve) == len(prices)


def test_compare_all_strategies():
    csv_path = Path(__file__).resolve().parents[1] / "data" / "sample_btc_usdt.csv"
    prices = closes(load_candles_from_csv(csv_path))
    for name in STRATEGIES:
        result = run_backtest(prices, build_strategy(name), verbose=False)
        assert result.report.ending_equity > 0
