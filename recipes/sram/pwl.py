"""SRAM W/W/R/R PWL stimulus and control-block generation."""

from __future__ import annotations

import re

from spice_automation.deck import splice_control_block


def _format_pwl_line(
    prefix: str,
    points: list[tuple[float, float]],
    tail_t: float,
    tail_v: float,
) -> str:
    by_t: dict[float, float] = {}
    for t, v in points:
        by_t[t] = v
    by_t[tail_t] = tail_v
    ordered = sorted(by_t.items())
    parts = [prefix + "("]
    for i, (t, v) in enumerate(ordered):
        sep = "" if i == 0 else " "
        parts.append(f"{sep}{t:.6f}n {v:.6f}")
    parts.append(")")
    return "".join(parts)


def build_pwl_sources(
    period_ns: float,
    macro_cycles: int,
    vdd: float = 1.0,
) -> dict[str, str]:
    p = period_ns
    dt = max(0.01 * period_ns, 0.002)
    k = macro_cycles
    t_start = max(0.02 * period_ns, 0.005)
    t_edge = max(0.01 * period_ns, 0.002)
    t_pw = max(0.48 * period_ns, 0.005)
    we_fall = 1.8 * p

    vclk = (
        f"Vclk CLK 0 PULSE(0 {vdd:.1f} {t_start:.6f}n {t_edge:.6f}n {t_edge:.6f}n "
        f"{t_pw:.6f}n {period_ns:.6f}n)"
    )

    va3 = "Va3 A_3 0 PWL(0 0  1000n 0)"
    va2 = "Va2 A_2 0 PWL(0 0  1000n 0)"
    va1 = "Va1 A_1 0 PWL(0 0  1000n 0)"

    def rel_va0(chain_to_next: bool) -> list[tuple[float, float]]:
        pts = [
            (0.0, 0.0),
            (p, 0.0),
            (p + dt, 1.0),
            (2 * p, 1.0),
            (2 * p + dt, 0.0),
            (3 * p, 0.0),
            (3 * p + dt, 1.0),
        ]
        if chain_to_next:
            pts.append((4 * p, 0.0))
        else:
            pts.extend([(4 * p, 1.0), (4 * p + dt, 0.0)])
        return pts

    def rel_vd3(chain: bool) -> list[tuple[float, float]]:
        pts = [(0.0, 0.0), (p, 0.0), (p + dt, 1.0)]
        if chain:
            pts.append((4 * p, 0.0))
        else:
            pts.extend([(4 * p, 1.0), (4 * p + dt, 1.0)])
        return pts

    def rel_vd2(chain: bool) -> list[tuple[float, float]]:
        pts = [(0.0, 1.0), (p, 1.0), (p + dt, 0.0)]
        if chain:
            pts.append((4 * p, 1.0))
        else:
            pts.extend([(4 * p, 0.0), (4 * p + dt, 1.0)])
        return pts

    def rel_vd1(chain: bool) -> list[tuple[float, float]]:
        pts = [(0.0, 0.0), (p, 0.0), (p + dt, 1.0)]
        if chain:
            pts.append((4 * p, 0.0))
        else:
            pts.extend([(4 * p, 1.0), (4 * p + dt, 1.0)])
        return pts

    def rel_vd0(chain: bool) -> list[tuple[float, float]]:
        pts = [(0.0, 1.0), (p, 1.0), (p + dt, 0.0)]
        if chain:
            pts.append((4 * p, 1.0))
        else:
            pts.extend([(4 * p, 0.0), (4 * p + dt, 1.0)])
        return pts

    abs_a0: list[tuple[float, float]] = []
    abs_d3: list[tuple[float, float]] = []
    abs_d2: list[tuple[float, float]] = []
    abs_d1: list[tuple[float, float]] = []
    abs_d0: list[tuple[float, float]] = []
    for r in range(k):
        t_off = r * 4 * p
        chain = r < k - 1
        abs_a0.extend((t_off + tr, vr) for tr, vr in rel_va0(chain))
        abs_d3.extend((t_off + tr, vr) for tr, vr in rel_vd3(chain))
        abs_d2.extend((t_off + tr, vr) for tr, vr in rel_vd2(chain))
        abs_d1.extend((t_off + tr, vr) for tr, vr in rel_vd1(chain))
        abs_d0.extend((t_off + tr, vr) for tr, vr in rel_vd0(chain))

    va0 = _format_pwl_line("Va0 A_0 0 PWL", abs_a0, 1000.0, 0.0)
    vd3 = _format_pwl_line("Vd3 Din_3 0 PWL", abs_d3, 1000.0, 1.0)
    vd2 = _format_pwl_line("Vd2 Din_2 0 PWL", abs_d2, 1000.0, 1.0)
    vd1 = _format_pwl_line("Vd1 Din_1 0 PWL", abs_d1, 1000.0, 1.0)
    vd0 = _format_pwl_line("Vd0 Din_0 0 PWL", abs_d0, 1000.0, 1.0)

    parts_we = ["Vwe WE 0 PWL("]
    for r in range(k):
        t0 = r * 4 * p
        if r == 0:
            parts_we.append("0 1")
        parts_we.append(
            f" {t0 + we_fall:.6f}n 1  {(t0 + we_fall + dt):.6f}n 0"
        )
        if r < k - 1:
            parts_we.append(f"  {(t0 + 4 * p):.6f}n 1")
        else:
            parts_we.append(
                f" {t0 + 4 * p:.6f}n 0  {(t0 + 4 * p + dt):.6f}n 1  1000n 1"
            )
    parts_we.append(")")
    vwe = "".join(parts_we)

    return {
        "vclk": vclk,
        "va3": va3,
        "va2": va2,
        "va1": va1,
        "va0": va0,
        "vd3": vd3,
        "vd2": vd2,
        "vd1": vd1,
        "vd0": vd0,
        "vwe": vwe,
    }


def build_control_block(
    period_ns: float,
    macro_cycles: int,
    *,
    include_clk_to_dout: bool,
    vdd: float = 1.0,
) -> str:
    p = period_ns
    k = macro_cycles
    t_stop = k * 4 * p + 0.5 * p
    t_step = max(period_ns / 200.0, 0.0005)
    lines = [
        ".control",
        f"tran {t_step:.6f}n {t_stop:.6f}n",
    ]

    print_names: list[str] = []
    for r in range(k):
        t_read0 = r * 4 * p + 2.5 * p
        t_read1 = r * 4 * p + 3.5 * p
        for j in range(4):
            name = f"b{r}a{j}"
            lines.append(f"meas tran {name} find v(Dout_{j}) at={t_read0:.6f}n")
            print_names.append(name)
        for j in range(4):
            name = f"b{r}b{j}"
            lines.append(f"meas tran {name} find v(Dout_{j}) at={t_read1:.6f}n")
            print_names.append(name)

    td_meas = 2.0 * period_ns
    if include_clk_to_dout:
        lines.append(
            "meas tran t_clk_to_dout trig v(CLK) val=0.5 rise=3 "
            f"targ v(Dout_0) val=0.5 cross=1 td={td_meas:.6f}n"
        )
        lines.append(f"meas tran iavg_vdd avg i(Vdd) from=0n to={t_stop:.6f}n")
        lines.append(f"let pavg_mw = -iavg_vdd * {vdd:.6f} * 1e3")
        print_names.append("t_clk_to_dout")
        print_names.append("iavg_vdd")
        print_names.append("pavg_mw")

    lines.append("print " + " ".join(print_names))
    lines.extend([".endc", ".END", ""])
    return "\n".join(lines)


def make_deck(
    template: str,
    period_ns: float,
    macro_cycles: int = 1,
    vdd: float = 1.0,
) -> str:
    src = build_pwl_sources(period_ns, macro_cycles, vdd=vdd)
    out = template
    replacements = {
        r"^Vclk CLK 0 PULSE\([^\n]+\)$": src["vclk"],
        r"^Va3 A_3 0 PWL\([^\n]+\)$": src["va3"],
        r"^Va2 A_2 0 PWL\([^\n]+\)$": src["va2"],
        r"^Va1 A_1 0 PWL\([^\n]+\)$": src["va1"],
        r"^Va0 A_0 0 PWL\([^\n]+\)$": src["va0"],
        r"^Vd3 Din_3 0 PWL\([^\n]+\)$": src["vd3"],
        r"^Vd2 Din_2 0 PWL\([^\n]+\)$": src["vd2"],
        r"^Vd1 Din_1 0 PWL\([^\n]+\)$": src["vd1"],
        r"^Vd0 Din_0 0 PWL\([^\n]+\)$": src["vd0"],
        r"^Vwe WE 0 PWL\([^\n]+\)$": src["vwe"],
    }
    for pat, repl in replacements.items():
        n = 0
        out, n = re.subn(pat, repl, out, flags=re.M)
        if n != 1:
            raise RuntimeError(f"Expected one match for pattern: {pat}")

    ctrl = build_control_block(
        period_ns,
        macro_cycles,
        include_clk_to_dout=(macro_cycles == 1),
        vdd=vdd,
    )
    return splice_control_block(out, ctrl)
