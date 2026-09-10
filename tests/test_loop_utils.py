from src.loop_utils import resolve_duration_seconds


def test_resolve_duration():
    assert resolve_duration_seconds(days=2) == 2 * 86400
    assert resolve_duration_seconds(hours=1, minutes=30) == 5400
    assert resolve_duration_seconds() is None
