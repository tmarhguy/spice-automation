#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${SPICE_MODEL_PATH:-}" ]]; then
  echo "Set SPICE_MODEL_PATH to your 22nm_HP.pm model card." >&2
  echo "See models/README.md" >&2
  exit 1
fi

if ! command -v ngspice >/dev/null 2>&1; then
  echo "ngspice not found. Install via: brew install ngspice" >&2
  exit 1
fi

python3 -m pip install -e ".[dev]" -q

echo "==> f_max binary search (SRAM top.spi)"
python3 -m spice_automation.cli fmax \
  --json-out reports/sram_fmax_baseline.json \
  --format pretty

echo ""
echo "==> Width-scale parametric sweep"
python3 -m spice_automation.cli sweep \
  --csv-out reports/sram_sweep_results.csv \
  --workers 2

echo ""
echo "==> Comparison report"
python3 -m spice_automation.cli report compare \
  --csv reports/sram_sweep_results.csv \
  --out reports/sram_comparison.md

echo ""
echo "Done. Artifacts in reports/"
