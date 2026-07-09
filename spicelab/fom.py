"""Figure-of-merit and PPA metric helpers."""

from __future__ import annotations


def sram_fom_access(area_wmin: float, power_w: float, delay_s: float) -> float:
    """FOM = 60 * Area * Power * Delay^2 (access-time delay term)."""
    return 60.0 * area_wmin * power_w * (delay_s ** 2)


def sram_fom_cycle(area_wmin: float, power_w: float, period_s: float) -> float:
    """FOM using CLK period as delay term."""
    return 60.0 * area_wmin * power_w * (period_s ** 2)


def power_w_from_pavg_mw(pavg_mw: float) -> float:
    return pavg_mw * 1e-3
