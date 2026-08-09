# Report artifacts

Committed JSON/CSV/Markdown outputs from the SPICE automation pipeline.

| File | Description |
|------|-------------|
| `sram_fmax_baseline.json` | Sustained f_max binary-search result (W/W/R/R, steady verify) |
| `sram_sweep_results.csv` | Width-scale parametric sweep (scout + final verification) |
| `sram_comparison.md` | Human-readable comparison summary |

**Regenerate locally** (requires NGSpice + PTM 22nm HP model):

```bash
export SPICE_MODEL_PATH=/path/to/22nm_HP.pm
pip install -e ".[dev]"
spice-automation fmax --json-out reports/sram_fmax_baseline.json
spice-automation sweep --csv-out reports/sram_sweep_results.csv
```

Or run `./scripts/run-sram-demo.sh` from the repo root.
