"""Tests for SPICE deck include rewriting."""

from pathlib import Path

from spicelab.deck import (
    rewrite_model_includes,
    scale_l1_widths,
    splice_control_block,
)


SAMPLE_DECK = """
.include /Users/tmarhguy/Downloads/22nm_HP.pm
Vclk CLK 0 PULSE(0 1.0 0.01n 0.002n 0.002n 0.48n 1.0n)
.control
tran 0.001n 5n
.endc
.END
"""


def test_rewrite_model_includes(monkeypatch, tmp_path: Path):
    model = tmp_path / "22nm_HP.pm"
    model.write_text("* dummy model")
    monkeypatch.setenv("SPICE_MODEL_PATH", str(model))

    out = rewrite_model_includes(SAMPLE_DECK)
    assert str(model) in out
    assert "/Users/tmarhguy/Downloads" not in out


def test_scale_l1_widths():
    text = "Mnmos@0 y a gnd gnd N L=1 W=2\nMpmos@0 y a vdd vdd P L=1 W=5"
    scaled = scale_l1_widths(text, 0.5)
    assert "L=1 W=1" in scaled
    assert "L=1 W=3" in scaled or "L=1 W=2" in scaled


def test_splice_control_block():
    new_ctrl = ".control\ntran 0.001n 2n\n.endc\n.END\n"
    out = splice_control_block(SAMPLE_DECK, new_ctrl)
    assert "tran 0.001n 2n" in out
    assert "tran 0.001n 5n" not in out
