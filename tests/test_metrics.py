from src.metrics import build_report, max_drawdown_pct


def test_max_drawdown():
    assert max_drawdown_pct([100, 120, 90, 95]) == 25.0


def test_build_report_win_rate():
    report = build_report(
        starting_cash=1000,
        ending_equity=1100,
        equity_curve=[1000, 1050, 1100],
        closed_pnls=[50, -20, 30],
        total_trades=6,
    )
    assert report.win_rate_pct == round(2 / 3 * 100, 2) or abs(report.win_rate_pct - 66.66) < 0.1
    assert abs(report.return_pct - 10.0) < 1e-9
