# Example circuits

Git submodules — clone with `git clone --recurse-submodules`.

| Submodule | GitHub | Framework recipe |
|-----------|--------|------------------|
| [64b-sram/](64b-sram/) | [tmarhguy/64b-sram](https://github.com/tmarhguy/64b-sram) | **SRAM** — `spice-automation fmax` / `sweep` |
| [full-adder/](full-adder/) | [tmarhguy/full-adder](https://github.com/tmarhguy/full-adder) | Planned — six-metric characterization |

Default deck for SRAM recipe: `examples/64b-sram/spice/top.spi` (see `recipes/sram/config.yaml`).

Update submodules:

```bash
git submodule update --remote examples/64b-sram
```
