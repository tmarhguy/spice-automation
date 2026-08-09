# Process model files

SPICE decks in `examples/` reference a **PTM 22 nm High-Performance** model card via `.include`.

The framework rewrites `.include` paths at runtime when `SPICE_MODEL_PATH` is set:

```bash
export SPICE_MODEL_PATH=/path/to/22nm_HP.pm
```

Obtain the model card from your ESE 3700 course materials or your local Electric VLSI export setup. **Do not commit** proprietary or course-restricted model files to this repository.

If `SPICE_MODEL_PATH` is unset, decks keep their shipped paths (which point to the author's machine and will fail elsewhere until you set the variable).
