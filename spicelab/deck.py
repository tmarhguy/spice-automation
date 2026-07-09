"""SPICE deck reading, model-path rewrite, and width scaling."""

from __future__ import annotations

import re
from pathlib import Path

from spicelab.ngspice import resolve_model_path

INCLUDE_PM_PATTERN = re.compile(
    r"^(\.include\s+)([^\n]*22nm[^\n]*\.pm)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
WIDTH_L1_PATTERN = re.compile(r"L=1 W=([0-9]+(?:\.[0-9]+)?)")


def rewrite_model_includes(text: str, model_path: Path | None = None) -> str:
    """Replace hardcoded 22nm model .include paths with SPICE_MODEL_PATH."""
    path = model_path or resolve_model_path()
    if path is None:
        return text

    def repl(m: re.Match[str]) -> str:
        return f"{m.group(1)}{path}"

    return INCLUDE_PM_PATTERN.sub(repl, text)


def scale_l1_widths(text: str, scale: float, min_w: float = 1.0) -> str:
    """Scale all L=1 W=N transistor widths (matches opt_fmax.cpp)."""

    def repl(m: re.Match[str]) -> str:
        w = float(m.group(1))
        nw = max(min_w, w * scale)
        nw = round(nw)
        return f"L=1 W={nw:.3f}"

    return WIDTH_L1_PATTERN.sub(repl, text)


def splice_control_block(text: str, control_block: str) -> str:
    """Replace everything from .control through .END with new control block."""
    if ".control" not in text:
        raise RuntimeError("Template missing .control block")
    prefix = text.split(".control", 1)[0]
    return prefix + control_block


def read_deck(path: Path, *, rewrite_model: bool = True) -> str:
    text = path.read_text()
    if rewrite_model:
        text = rewrite_model_includes(text)
    return text


def write_temp_deck(
    work_dir: Path,
    name: str,
    text: str,
    *,
    rewrite_model: bool = True,
) -> Path:
    if rewrite_model:
        text = rewrite_model_includes(text)
    tmp = work_dir / name
    tmp.write_text(text)
    return tmp
