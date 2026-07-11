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
python3 -m spicelab.cli fmax \
  --json-out reports/sram_fmax_baseline.json \
  --format pretty

echo ""
echo "==> Width-scale parametric sweep + comparison report"
python3 -m spicelab.cli sweep \
  --csv-out reports/sram_sweep_results.csv \
  --md-out reports/sram_comparison.md \
  --workers 2

echo ""
echo "Done. Artifacts in reports/"
