"""Generic parallel grid sweep utilities."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable


def grid_sweep(
    values: list[float],
    evaluate: Callable[[float], dict[str, Any]],
    *,
    param_name: str = "value",
    max_workers: int = 2,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def job(v: float) -> dict[str, Any]:
        try:
            meta = evaluate(v)
            row = {param_name: v, "ok": True}
            row.update(meta)
            return row
        except Exception as exc:
            return {param_name: v, "ok": False, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(job, v) for v in values]
        for fut in as_completed(futures):
            rows.append(fut.result())

    rows.sort(key=lambda r: values.index(r[param_name]) if r[param_name] in values else 0)
    return rows
