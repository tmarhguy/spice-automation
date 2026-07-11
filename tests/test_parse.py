"""Tests for NGSpice output parsing."""

from spicelab.parse import parse_measure


FIXTURE = """
t_clk_to_dout = 1.1065e-10
pavg_mw = 0.021367
b0a0 = 1.0
b0a1 = 0.0
"""


def test_parse_measure():
    assert parse_measure(FIXTURE, "t_clk_to_dout") == 1.1065e-10
    assert parse_measure(FIXTURE, "b0a0") == 1.0


def test_parse_measure_missing_optional():
    import math

    val = parse_measure(FIXTURE, "missing", required=False)
    assert math.isnan(val)
