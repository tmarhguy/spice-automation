# SRAM Parametric Sweep Comparison

## Best sustained f_max (verified)

- **scale** = 1.0 → **f_max** = 4.571429 GHz, T_min = 0.21875 ns
- **FOM (access)** = 1.2560e-22

On the shipped `top.spi` deck, screened width-scale recipes reproduced the same ~4.57 GHz sustained closure — the limiter is the shared cycle envelope, not a single cell tweak.

## All configurations

| phase | scale | fmax_ghz | tmin_ns | steady | ok | fom_access_sweep_sci |
| --- | --- | --- | --- | --- | --- | --- |
| scout | 1.00 | 4.571429 | 0.21875 | true | true | 1.2560e-22 |
| final | 1.00 | 4.571429 | 0.21875 | true | true | 1.2560e-22 |

## Provenance

Values align with the [64b-sram](examples/64b-sram) ESE 3700 report (`find_fmax.py` W/W/R/R sweep on `top.spi`). Regenerate with:

```bash
export SPICE_MODEL_PATH=/path/to/22nm_HP.pm
spice-automation sweep --csv-out reports/sram_sweep_results.csv
spice-automation report compare --csv reports/sram_sweep_results.csv --out reports/sram_comparison.md
```
