# Formalizing the SPICE Automation Framework

*July 11, 2026*

---

## Where this started

When I first worked on the [16×4 full-custom 6T SRAM](https://github.com/tmarhguy/64b-sram) macro and the [8-bit ripple-carry adder](https://github.com/tmarhguy/full-adder) months ago (Spring 2026), I relied on a lot of customized C++ and Python tooling to verify the speed and PPA metrics. The course [ESE 3700](https://www.engineering.upenn.edu/~ese3700/) required a minimum speed of **500 MHz**. After deep optimization—and verifying functional readbacks in NGSpice—I hit a **9× margin**, pushing the macro to a **4.571 GHz** max speed. But extracting and reading those metrics relied on some heavily hardcoded C++ and Python scripting I had thrown together just to get through the iterations.

### SRAM results (proof circuit)

| Metric                 | Value                | Notes                                         |
| ---------------------- | -------------------- | --------------------------------------------- |
| Sustained **fmax**     | **4.571 GHz**        | Binary search on CLK period, W/W/R/R pattern  |
| Spec margin            | **9.14×** vs 500 MHz | `fmax / 0.5 GHz`                              |
| Min CLK period         | **218.75 ps**        | At sustained closure                          |
| CLK → DOUT delay       | **110.65 ps**        | `@0.5 V` functional readback                  |
| Avg power              | **21.37 µW**         | Over 0.984 ns measurement window              |
| **FOM** (access sweep) | **≈ 1.26×10⁻²²**     | `60 × Area × Power × Delay²`                  |
| Steady-state verify    | **PASS**             | 32 macros, 128 CLK cycles, 64 readback checks |

Pattern: **W/W/R/R** with `addr0=0x5`, `addr1=0xA` @ **0.5 V** VDD. Width-scale sweeps (0.50–1.00) all reproduced the same ~4.57 GHz closure—the limiter is the shared cycle envelope, not a single cell tweak.

---

## Why I'm building this

In a quest to organize my workflow for the obvious future where I will work with SPICE in advanced courses, research, my career, and personal explorations, I am building this automation framework to quickly verify my SPICE tooling metrics.

I decided to pull the old optimization loop out of the specific project repo and formalize it into a clean, reusable Python package. On the technical side, the framework is built to **decouple the generic runner from the specific circuit recipes**:

- **Dynamic Deck Rewriting** — Instead of hardcoding predictive 22 nm HP model paths into every SPICE deck, the framework intercepts the deck and dynamically rewrites the `.include` lines at runtime via environment variables. This keeps the original circuit files perfectly clean for version control and automated CI/CD runs.

- **Automated NGSpice Runner** — A Python pipeline natively drives NGSpice subprocesses to automatically run binary searches for sustained **F_max** and execute concurrent parametric width-scale sweeps.

- **PPA Reporting** — The framework parses the `.meas` extractions, calculates custom Figure of Merit (FOM) formulas (like $60 \times \text{Area} \times \text{Power} \times \text{Delay}^2$), and automatically spits out comparative results directly into **JSON**, **CSV**, and **Markdown** reports.

---

## What this is

This is a project that I am organizing in my repository. As I continue to iterate on custom silicon, having the data structured and handed to me automatically is absolutely essential. Perhaps it'll be found useful to someone else out there building from the transistor up.

**Proof circuit:** [`examples/64b-sram`](examples/64b-sram) (ESE 3700 Proj2) · **Artifacts:** [`reports/sram_fmax_baseline.json`](../reports/sram_fmax_baseline.json), [`reports/sram_sweep_results.csv`](../reports/sram_sweep_results.csv)
