"""SRAM f_max evaluation and search orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from spice_automation.deck import read_deck, rewrite_model_includes, scale_l1_widths
from spice_automation.fom import power_w_from_pavg_mw, sram_fom_access, sram_fom_cycle
from spice_automation.ngspice import ngspice_version_line, run_batch
from spice_automation.parse import display_path, parse_measure
from spice_automation.search import binary_search
from recipes.sram.pwl import make_deck


@dataclass
class SramConfig:
    deck: str
    spec_fmin_ghz: float = 0.5
    vdd_v: float = 1.0
    bitcell_area_wmin: float = 8.0
    min_period_ns: float = 0.10
    max_period_ns: float = 2.00
    tol_ns: float = 0.005
    verify_macro_cycles: int = 32
    read0_nibble: tuple[int, int, int, int] = (1, 0, 1, 0)
    read1_nibble: tuple[int, int, int, int] = (0, 1, 0, 1)
    pattern: str = "W/W/R/R addr0=0x5 addr1=0xA functional readback @0.5V"
    sweep: dict[str, Any] = field(default_factory=dict)


def load_config(config_path: Path | None = None) -> SramConfig:
    path = config_path or Path(__file__).resolve().parent / "config.yaml"
    raw = yaml.safe_load(path.read_text())
    read0 = tuple(raw.get("read0_nibble", [1, 0, 1, 0]))
    read1 = tuple(raw.get("read1_nibble", [0, 1, 0, 1]))
    return SramConfig(
        deck=raw["deck"],
        spec_fmin_ghz=float(raw.get("spec_fmin_ghz", 0.5)),
        vdd_v=float(raw.get("vdd_v", 1.0)),
        bitcell_area_wmin=float(raw.get("bitcell_area_wmin", 8.0)),
        min_period_ns=float(raw.get("min_period_ns", 0.10)),
        max_period_ns=float(raw.get("max_period_ns", 2.00)),
        tol_ns=float(raw.get("tol_ns", 0.005)),
        verify_macro_cycles=int(raw.get("verify_macro_cycles", 32)),
        read0_nibble=tuple(read0),
        read1_nibble=tuple(read1),
        pattern=str(raw.get("pattern", "")),
        sweep=dict(raw.get("sweep", {})),
    )


def _bits_from_block(
    out: str,
    r: int,
    phase: str,
    macro_cycles: int,
) -> tuple[int, int, int, int]:
    suffix = "a" if phase == "a" else "b"
    return tuple(
        int(parse_measure(out, f"b{r}{suffix}{j}") > 0.5) for j in range(4)
    )


def evaluate_macro_pattern(
    out: str,
    macro_cycles: int,
    proc_rc: int,
    read0: tuple[int, ...],
    read1: tuple[int, ...],
) -> tuple[bool, dict]:
    failed_blocks: list[int] = []
    for r in range(macro_cycles):
        ba = _bits_from_block(out, r, "a", macro_cycles)
        bb = _bits_from_block(out, r, "b", macro_cycles)
        if ba != read0 or bb != read1:
            failed_blocks.append(r)
    meta = {
        "failed_block_indices": failed_blocks,
        "pass_all": len(failed_blocks) == 0 and proc_rc == 0,
    }
    return meta["pass_all"], meta


def run_case(
    base_text: str,
    work_dir: Path,
    period_ns: float,
    macro_cycles: int,
    cfg: SramConfig,
    tmp_name: str = "top_fmax_tmp.spi",
) -> tuple[bool, dict]:
    deck = make_deck(base_text, period_ns, macro_cycles, vdd=cfg.vdd_v)
    deck = rewrite_model_includes(deck)
    tmp = work_dir / tmp_name
    tmp.write_text(deck)
    try:
        result = run_batch(tmp, cwd=work_dir)
        out = result.combined
        vals: dict[str, Any] = {"returncode": result.returncode}

        if result.returncode != 0:
            vals["pass_all"] = False
            vals["failed_block_indices"] = list(range(macro_cycles))
            vals["pass_r0"] = False
            vals["pass_r1"] = False
            return False, vals

        for r in range(macro_cycles):
            for j in range(4):
                vals[f"b{r}a{j}"] = parse_measure(out, f"b{r}a{j}", required=True)
                vals[f"b{r}b{j}"] = parse_measure(out, f"b{r}b{j}", required=True)

        if macro_cycles == 1:
            vals["t_clk_to_dout"] = parse_measure(out, "t_clk_to_dout", required=False)
            vals["iavg_vdd"] = parse_measure(out, "iavg_vdd", required=False)
            vals["pavg_mw"] = parse_measure(out, "pavg_mw", required=False)

        ok_pattern, meta = evaluate_macro_pattern(
            out,
            macro_cycles,
            result.returncode,
            cfg.read0_nibble,
            cfg.read1_nibble,
        )
        vals.update(meta)
        if macro_cycles >= 1:
            ba = _bits_from_block(out, 0, "a", macro_cycles)
            bb = _bits_from_block(out, 0, "b", macro_cycles)
            vals["pass_r0"] = ba == cfg.read0_nibble
            vals["pass_r1"] = bb == cfg.read1_nibble
        return ok_pattern, vals
    finally:
        if tmp.exists():
            tmp.unlink()


def find_fmax_sram(
    deck_path: Path,
    cfg: SramConfig,
    *,
    min_period_ns: float | None = None,
    max_period_ns: float | None = None,
    tol_ns: float | None = None,
    verify_macro_cycles: int | None = None,
    width_scale: float = 1.0,
) -> dict[str, Any]:
    deck_path = deck_path.resolve()
    if not deck_path.is_file():
        raise FileNotFoundError(f"Deck not found: {deck_path}")

    base_text = read_deck(deck_path)
    if width_scale != 1.0:
        base_text = scale_l1_widths(base_text, width_scale)

    work_dir = deck_path.parent
    lo = min_period_ns if min_period_ns is not None else cfg.min_period_ns
    hi = max_period_ns if max_period_ns is not None else cfg.max_period_ns
    tol = tol_ns if tol_ns is not None else cfg.tol_ns
    verify = (
        verify_macro_cycles
        if verify_macro_cycles is not None
        else cfg.verify_macro_cycles
    )

    def evaluate(period: float) -> tuple[bool, dict]:
        return run_case(base_text, work_dir, period, macro_cycles=1, cfg=cfg)

    search = binary_search(evaluate, lo, hi, tol)
    best_period = search.best_value
    best_vals = search.best_meta

    freq_ghz = 1.0 / best_period
    margin = freq_ghz / cfg.spec_fmin_ghz

    steady_ok: bool | None = None
    if verify > 1:
        steady_ok, _ = run_case(
            base_text, work_dir, best_period, macro_cycles=verify, cfg=cfg
        )
    elif verify == 1:
        steady_ok = bool(best_vals.get("pass_all", True))
    else:
        steady_ok = None

    deck_mtime_utc = datetime.utcfromtimestamp(
        deck_path.stat().st_mtime
    ).isoformat() + "Z"

    result: dict[str, Any] = {
        "sustained_fmax_ghz": round(freq_ghz, 6),
        "t_min_clk_ps": round(best_period * 1e3, 4),
        "t_min_clk_ns": round(best_period, 6),
        "deck_path": display_path(deck_path),
        "deck_path_abs": str(deck_path),
        "deck_mtime_utc": deck_mtime_utc,
        "spec_fmin_ghz": cfg.spec_fmin_ghz,
        "margin_vs_spec_x": round(margin, 4),
        "vdd_v": cfg.vdd_v,
        "search_tol_ps": round(tol * 1e3, 4),
        "verify_macro_cycles": verify,
        "steady_state_clk_cycles": verify * 4 if verify > 1 else 0,
        "steady_state_readback_checks": 2 * verify if verify > 1 else 2,
        "steady_state_verify_pass": steady_ok,
        "ngspice": ngspice_version_line(),
        "pattern": cfg.pattern,
        "width_scale": width_scale,
    }

    tcd = best_vals.get("t_clk_to_dout")
    if tcd is not None and tcd == tcd:
        tcd_f = float(tcd)
        result["t_clk_to_dout_s"] = tcd_f
        result["t_clk_to_dout_ps"] = round(tcd_f * 1e12, 4)

    pavg_mw = best_vals.get("pavg_mw")
    if pavg_mw is not None and pavg_mw == pavg_mw:
        p_mw_f = float(pavg_mw)
        result["pavg_mw"] = p_mw_f
        result["pavg_uw"] = round(p_mw_f * 1e3, 4)
        result["pavg_window_ns"] = round(4.5 * best_period, 6)
        result["fom_bitcell_area_wmin"] = cfg.bitcell_area_wmin
        if tcd is not None and tcd == tcd:
            p_w = power_w_from_pavg_mw(p_mw_f)
            fom = sram_fom_access(cfg.bitcell_area_wmin, p_w, float(tcd))
            fom_cycle = sram_fom_cycle(
                cfg.bitcell_area_wmin, p_w, best_period * 1e-9
            )
            result["fom_access_sweep"] = fom
            result["fom_access_sweep_sci"] = f"{fom:.4e}"
            result["fom_cycle_tmin_sweep"] = fom_cycle
            result["fom_cycle_tmin_sweep_sci"] = f"{fom_cycle:.4e}"

    return result
