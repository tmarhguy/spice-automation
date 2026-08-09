"""Command-line interface for spice-automation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from recipes.sram.evaluate import find_fmax_sram, load_config
from spice_automation.report import (
    comparison_markdown,
    write_comparison_markdown,
    write_json,
)
from spice_automation.sweep import run_sram_width_sweep, write_sram_sweep_csv


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def cmd_fmax(args: argparse.Namespace) -> int:
    cfg = load_config()
    deck = Path(args.deck or cfg.deck)
    if not deck.is_absolute():
        deck = _repo_root() / deck

    result = find_fmax_sram(
        deck,
        cfg,
        min_period_ns=args.min_period_ns,
        max_period_ns=args.max_period_ns,
        tol_ns=args.tol_ns,
        verify_macro_cycles=args.verify_macro_cycles,
    )

    if args.json_out:
        out_path = Path(args.json_out)
        if not out_path.is_absolute():
            out_path = _repo_root() / out_path
        write_json(out_path, result)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    elif args.format == "pretty":
        print("==============================================")
        print("SRAM W/W/R/R Sustained f_max Summary")
        print("==============================================")
        print(f"Deck                    : {result['deck_path']}")
        print(f"Sustained f_max         : {result['sustained_fmax_ghz']:.6f} GHz")
        print(f"T_min                   : {result['t_min_clk_ps']:.4f} ps")
        print(f"Margin vs spec          : {result['margin_vs_spec_x']:.4f}x")
        if result.get("steady_state_verify_pass") is not None:
            print(
                f"Steady-state verify     : "
                f"{'PASS' if result['steady_state_verify_pass'] else 'FAIL'}"
            )
        if "t_clk_to_dout_ps" in result:
            print(f"t_CLK->Dout             : {result['t_clk_to_dout_ps']:.4f} ps")
        if "fom_access_sweep_sci" in result:
            print(f"FOM (access, sweep)     : {result['fom_access_sweep_sci']}")
    else:
        parts = [
            f"T_min_ns={result['t_min_clk_ns']}",
            f"f_max_GHz={result['sustained_fmax_ghz']}",
            f"vs_{result['spec_fmin_ghz']}GHz={result['margin_vs_spec_x']}x",
        ]
        if result.get("steady_state_verify_pass") is not None:
            parts.append(f"steady_pass={result['steady_state_verify_pass']}")
        print(" ".join(parts))
    return 0


def cmd_sweep(args: argparse.Namespace) -> int:
    cfg = load_config()
    deck = Path(args.deck or cfg.deck)
    if not deck.is_absolute():
        deck = _repo_root() / deck

    scales = None
    if args.grid:
        scales = [float(x.strip()) for x in args.grid.split(",")]

    rows = run_sram_width_sweep(
        deck,
        cfg,
        scales=scales,
        max_workers=args.workers,
    )

    csv_path = Path(args.csv_out or "reports/sram_sweep_results.csv")
    if not csv_path.is_absolute():
        csv_path = _repo_root() / csv_path
    write_sram_sweep_csv(csv_path, rows)

    md_path = csv_path.with_suffix(".md")
    if args.md_out:
        md_path = Path(args.md_out)
        if not md_path.is_absolute():
            md_path = _repo_root() / md_path
    write_comparison_markdown(md_path, comparison_markdown(rows))

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    return 0


def cmd_report_compare(args: argparse.Namespace) -> int:
    import csv

    csv_path = Path(args.csv)
    if not csv_path.is_absolute():
        csv_path = _repo_root() / csv_path

    with csv_path.open() as f:
        rows = list(csv.DictReader(f))

    out_path = Path(args.out or "reports/sram_comparison.md")
    if not out_path.is_absolute():
        out_path = _repo_root() / out_path

    write_comparison_markdown(out_path, comparison_markdown(rows))
    print(f"Wrote {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spice-automation",
        description="NGSpice parametric optimization and PPA reporting",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fmax = sub.add_parser("fmax", help="Binary-search sustained f_max (SRAM recipe)")
    fmax.add_argument("--recipe", default="sram", choices=["sram"])
    fmax.add_argument("--deck", default=None, help="SPICE deck path")
    fmax.add_argument("--min-period-ns", type=float, default=None)
    fmax.add_argument("--max-period-ns", type=float, default=None)
    fmax.add_argument("--tol-ns", type=float, default=None)
    fmax.add_argument("--verify-macro-cycles", type=int, default=None)
    fmax.add_argument(
        "--json-out",
        default=None,
        help="Write JSON results to path",
    )
    fmax.add_argument(
        "--format",
        choices=["line", "pretty", "json"],
        default="pretty",
    )
    fmax.set_defaults(func=cmd_fmax)

    sweep = sub.add_parser("sweep", help="Parametric width-scale sweep (SRAM)")
    sweep.add_argument("--recipe", default="sram", choices=["sram"])
    sweep.add_argument("--deck", default=None)
    sweep.add_argument(
        "--param",
        default="width_scale",
        choices=["width_scale"],
    )
    sweep.add_argument(
        "--grid",
        default=None,
        help="Comma-separated scale values (overrides config scout_scales)",
    )
    sweep.add_argument("--csv-out", default=None)
    sweep.add_argument("--md-out", default=None)
    sweep.add_argument("--workers", type=int, default=2)
    sweep.set_defaults(func=cmd_sweep)

    report = sub.add_parser("report", help="Report utilities")
    report_sub = report.add_subparsers(dest="report_cmd", required=True)
    compare = report_sub.add_parser("compare", help="Build comparison markdown from CSV")
    compare.add_argument("--csv", required=True)
    compare.add_argument("--out", default=None)
    compare.set_defaults(func=cmd_report_compare)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
