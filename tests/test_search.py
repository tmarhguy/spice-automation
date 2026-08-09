"""Tests for generic binary search."""

from spice_automation.search import binary_search


def test_binary_search_bracket():
    # Closure: ok when value >= 10
    def evaluate(v: float) -> tuple[bool, dict]:
        return v >= 10.0, {"v": v}

    result = binary_search(evaluate, lo=0.0, hi=20.0, tol=0.5)
    assert result.best_value >= 10.0
    assert result.best_value < 10.5
    assert result.best_meta["v"] == result.best_value


def test_binary_search_already_at_lo():
    def evaluate(v: float) -> tuple[bool, dict]:
        return True, {"v": v}

    result = binary_search(evaluate, lo=5.0, hi=20.0, tol=0.1)
    assert result.best_value == 5.0
