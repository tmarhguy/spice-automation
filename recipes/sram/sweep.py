"""SRAM width-scale parametric sweep (generalizes opt_fmax.cpp)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from recipes.sram.evaluate import SramConfig, find_fmax_sram
from spicelab.report import write_sweep_csv as _write_sweep_csv

SRAM_SWEEP_FIELDS = [
    "phase",
    "scale",
    "fmax_ghz",
    "tmin_ns",
    "steady",
    "ok",
    "fom_access_sweep_sci",
    "fom_cycle_tmin_sweep_sci",
    "margin_vs_spec_x",
]


def run_width_sweep(
    deck_path: Path,
    cfg: SramConfig,
    *,
    scales: list[float] | None = None,
    scout_verify_macros: int | None = None,
    scout_tol_ns: float | None = None,
    final_verify_macros: int | None = None,
    final_tol_ns: float | None = None,
    max_finalists: int | None = None,
    max_workers: int = 2,
) -> list[dict[str, Any]]:
    sweep_cfg = cfg.sweep
    scout_scales = scales or [float(s) for s in sweep_cfg.get("scout_scales", [])]
    scout_verify = scout_verify_macros or int(sweep_cfg.get("scout_verify_macros", 2))
    scout_tol = scout_tol_ns or float(sweep_cfg.get("scout_tol_ns", 0.02))
    final_verify = final_verify_macros or int(sweep_cfg.get("final_verify_macros", 32))
    final_tol = final_tol_ns or float(sweep_cfg.get("final_tol_ns", 0.005))
    finalists_n = max_finalists or int(sweep_cfg.get("max_finalists", 4))

    scout_rows: list[dict[str, Any]] = []

    def eval_scale(scale: float, verify: int, tol: float, phase: str, idx: int) -> dict[str, Any]:
        try:
            result = find_fmax_sram(
                deck_path,
                cfg,
                min_period_ns=cfg.min_period_ns,
                max_period_ns=cfg.max_period_ns,
                tol_ns=tol,
                verify_macro_cycles=verify,
                width_scale=scale,
            )
            return {
                "phase": phase,
                "scale": scale,
                "fmax_ghz": result.get("sustained_fmax_ghz"),
                "tmin_ns": result.get("t_min_clk_ns"),
                "steady": result.get("steady_state_verify_pass"),
                "ok": True,
                "fom_access_sweep_sci": result.get("fom_access_sweep_sci", ""),
                "fom_cycle_tmin_sweep_sci": result.get("fom_cycle_tmin_sweep_sci", ""),
                "margin_vs_spec_x": result.get("margin_vs_spec_x"),
            }
        except Exception as exc:
            return {
                "phase": phase,
                "scale": scale,
                "fmax_ghz": "",
                "tmin_ns": "",
                "steady": False,
                "ok": False,
                "fom_access_sweep_sci": "",
                "fom_cycle_tmin_sweep_sci": "",
                "margin_vs_spec_x": "",
                "error": str(exc),
            }

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(eval_scale, s, scout_verify, scout_tol, "scout", i): s
            for i, s in enumerate(scout_scales)
        }
        for fut in as_completed(futures):
            scout_rows.append(fut.result())

    scout_rows.sort(key=lambda r: scout_scales.index(r["scale"]) if r["scale"] in scout_scales else 0)

    valid = [r for r in scout_rows if r.get("ok") and r.get("steady")]
    valid.sort(key=lambda r: float(r.get("fmax_ghz", 0) or 0), reverse=True)
    finalists = valid[:finalists_n]

    final_rows: list[dict[str, Any]] = []
    for i, row in enumerate(finalists):
        scale = float(row["scale"])
        final_rows.append(
            eval_scale(scale, final_verify, final_tol, "final", 100 + i)
        )

    return scout_rows + final_rows


def write_sweep_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    _write_sweep_csv(path, rows, SRAM_SWEEP_FIELDS)
