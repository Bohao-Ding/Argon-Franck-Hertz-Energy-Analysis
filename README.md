# Argon Franck–Hertz Energy Analysis

A reproducible model of collector-current response in the argon Franck–Hertz experiment. Python implements the collision response and excitation hypotheses; R draws the saved results and controlled comparisons.

[中文](README.zh-CN.md) · [Model design](docs/design.md) · [Reproduce](docs/reproduction.md) · [Discrete diagnostics](docs/discrete_diagnostics.md)

## Results at a glance

![Four measured current curves and their saved continuous-distribution predictions, beside the fitted effective-energy peak and four spectroscopic reference markers.](docs/assets/project_overview.png)

The current fit uses **644 archived points at retarding voltages 0, 4, 6, and 8 V**. The density panel enlarges the peak region of a distribution supported on 9–16 eV. Its mean is about 11.640 eV. The fitted density describes effective excitation contributions in the current-response model.

## Quick start

Use a Python environment with the packages in [requirements.txt](requirements.txt), then run:

```text
python run.py
```

| Mode | What it does | Runs an optimizer? |
| --- | --- | --- |
| **1** | Replay H1 and six saved continuous-distribution stages; calculate currents and distribution summaries. | No |
| **2** | Redraw saved-result figures and the three project graphics with R/ggplot2. | No |
| **3** | Continue the adopted alternating fit from the saved H1 starting parameters. | **Yes** |
| **4** | Replay 34 discrete/fixed-variance full-data models and fixed-framework response probes. | No |
| **0** | Exit. | No |

Run modes 1, 4, and 2 to replay the results and redraw the figures. Each selection writes to `outputs/<timestamp>_<mode>/`. Numerical modes use one CPU thread and float64.

For R discovery, package checks, output filenames, and fitting details, see [Reproduction](docs/reproduction.md).

## Reproduce with an AI agent

Open this repository in a local AI coding agent and copy this instruction:

```text
Reproduce this repository on this machine.

1. Read README.md, docs/reproduction.md, and requirements.txt. Report the OS,
   Python/R installations, available environments, and package versions.
2. Reuse a compatible environment or prepare an isolated project environment.
   Add the required Python packages and R plotting tools. Configure Rscript,
   R libraries, Cairo, and fonts for the process that will run the figures.
3. Use the selected Python interpreter to run run.py: modes 1, 4, then 2.
   For a requested refit, agree on its computational budget and use mode 3.
4. Inspect replay_checks.json, current/probe differences, distribution summaries,
   and exported figures. Report completed steps and any environment blockers.
5. Treat data/ and reference/ as inputs and write results under outputs/.
   Summarize environment changes, versions, executed modes, and output paths.
```

## Model design

The same current-response framework accepts a single effective energy, weighted discrete energies, or a normalized continuous density. Independent successive collisions are combined through convolution powers, followed by one unit-area Gaussian response and the common current readout.

[Design and data flow](docs/design.md) explains what is shared, what changes between representations, and how energy variance can compensate for response broadening. The [classroom activities](docs/teaching_case_en.md) connect these choices to excitation, collection, and convolution.

## What can the curves distinguish?

![Fixed-framework current differences: four prescribed energies versus one energy at equal mean, and four energies versus a uniform density at equal mean and variance. The vertical scales differ by four orders of magnitude.](docs/assets/response_contrasts.png)

The left comparison adds energy spread at a common mean; the right changes distribution shape at a common mean and variance. Both use the same frozen external response. The vertical scales differ by four orders of magnitude.

Alongside the saved spline-fit path, the [discrete diagnostics](docs/discrete_diagnostics.md) compare K=1–8, matched-budget H1 controls, and prescribed variances. The fixed-variance scan selects zero variance in both full datasets. **The discrete-level count remains unresolved** in this dataset and response model. Path statuses and support domains accompany the results.

## Repository map

| Location | Contents |
| --- | --- |
| `src/fh_argon/` | Shared current response, replay/fitting workflows, and forward-only discrete channels. |
| `data/` | Original workbook and the five-curve, 805-point overview table; the four-curve fits use 644 points. |
| `reference/` | Saved continuous stages, starting parameters, plotting tables, and the curated discrete diagnostics. |
| `figures/` | R sources for saved-result figures and web graphics. |
| `docs/` | Design, reproduction, interpretation, classroom tasks, and committed preview assets. |

The [historical specified-four-energy comparison](docs/optional_h4s.md) belongs to an earlier five-curve periodic model and is kept separate from the present convolution analysis.

## License

Source code is distributed under the [MIT license](LICENSE).
