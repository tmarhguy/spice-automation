"""JSON, CSV, and Markdown report writers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def write_sweep_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def comparison_markdown(
    rows: list[dict[str, Any]],
    *,
    title: str = "SRAM Parametric Sweep Comparison",
) -> str:
    lines = [f"# {title}", ""]
    if not rows:
        lines.append("No results.")
        return "\n".join(lines)

    ok_rows = [r for r in rows if r.get("ok") and r.get("steady")]
    if ok_rows:
        best_fmax = max(ok_rows, key=lambda r: float(r.get("fmax_ghz", 0)))
        lines.append("## Best sustained f_max (verified)")
        lines.append("")
        lines.append(
            f"- **scale** = {best_fmax.get('scale')} → "
            f"**f_max** = {best_fmax.get('fmax_ghz')} GHz, "
            f"T_min = {best_fmax.get('tmin_ns')} ns"
        )
        if best_fmax.get("fom_access_sweep_sci"):
            lines.append(f"- **FOM (access)** = {best_fmax.get('fom_access_sweep_sci')}")
        lines.append("")

    lines.append("## All configurations")
    lines.append("")
    headers = [
        "phase",
        "scale",
        "fmax_ghz",
        "tmin_ns",
        "steady",
        "ok",
        "fom_access_sweep_sci",
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        cells = [str(r.get(h, "")) for h in headers]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def write_comparison_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
