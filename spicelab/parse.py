"""Parse NGSpice measurement output."""

from __future__ import annotations

import json
import re
from pathlib import Path


def parse_measure(stdout: str, name: str, required: bool = True) -> float:
    m = re.search(rf"{re.escape(name)}\s*=\s*([+\-0-9.eE]+)", stdout)
    if not m:
        if required:
            raise RuntimeError(f"Missing measure: {name}")
        return float("nan")
    return float(m.group(1))


def extract_json_field(text: str, key: str) -> float | bool | None:
    """Extract a scalar from JSON embedded in stdout."""
    try:
        obj = json.loads(text)
        return obj.get(key)
    except json.JSONDecodeError:
        pat_d = re.compile(
            rf'"{re.escape(key)}"\s*:\s*([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)'
        )
        pat_b = re.compile(rf'"{re.escape(key)}"\s*:\s*(true|false)')
        m = pat_d.search(text)
        if m:
            return float(m.group(1))
        m = pat_b.search(text)
        if m:
            return m.group(1) == "true"
        return None


def display_path(path: Path, *, base: Path | None = None) -> str:
    anchor = (base or Path.cwd()).resolve()
    target = path.resolve()
    try:
        return str(target.relative_to(anchor))
    except ValueError:
        return str(target)
