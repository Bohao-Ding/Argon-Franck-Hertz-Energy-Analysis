# Argon Franck–Hertz Energy Analysis

A reproducible model of collector-current response in the argon Franck–Hertz experiment. Python implements the collision response and excitation hypotheses; R draws the saved results and controlled comparisons.

[中文](README.zh-CN.md) · [Model design](docs/design.md) · [Reproduce](docs/reproduction.md) · [Discrete diagnostics](docs/discrete_diagnostics.md)

## Results at a glance

![Four measured current curves and their saved continuous-distribution predictions, beside the fitted effective-energy peak and four spectroscopic reference markers.](docs/assets/project_overview.png)

The current fit uses **644 archived points at retarding voltages 0, 4, 6, and 8 V**. The density panel enlarges the peak region of a distribution supported on 9–16 eV. Its mean is about 11.640 eV. This is a model-conditional effective contribution to current response, not a measured atomic spectrum or state population.

## Quick start

Use an existing Python environment containing the packages in [requirements.txt](requirements.txt). Run:

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

Start with mode 1, then explore mode 4. Every selection writes a fresh `outputs/<timestamp>_<mode>/` directory. Inputs and saved references stay intact. Numerical modes use one CPU thread and float64; CUDA is not required. The menu does not install packages or download data.

For R discovery, package checks, output filenames, and fitting details, see [Reproduction](docs/reproduction.md).

## Reproduce with an AI agent

Open this repository in a local AI coding agent and copy the instruction below. It guides the agent through inspecting your machine, preparing a compatible environment, and checking the saved results.

```text
Help me reproduce this repository locally, adapting each step to this machine.

1. Read README.md, docs/reproduction.md, and requirements.txt. Inspect the OS,
   available Python interpreters/environments, and installed package versions.
   Check Rscript, its visible R libraries, Cairo, and fonts separately.
2. Report the available environment and the minimal configuration needed.
   Reuse a compatible environment first. If a new environment is necessary,
   use an isolated project-local environment and leave global dependencies
   intact. Prepare only missing dependencies within the current authorization;
   do not replace an existing environment or install CUDA for this CPU workflow.
3. Use the selected Python interpreter to run run.py and choose mode 1.
   Inspect replay_checks.json and the distribution summaries. Compare the
   recalculated currents with the saved values and explain any discrepancy.
4. Choose mode 4 to replay the 34 full-data models and fixed-framework probes.
   Inspect current/probe differences and unchanged parameters. Fold and
   perturbation tables are saved records; this mode does not rerun their fits.
5. Prepare R for mode 2, reusing an existing installation first. Add missing
   R components or packages within the current authorization. Make Rscript
   and its packages visible to the same process, using session configuration
   where appropriate. Redraw and inspect the figures. If setup is blocked,
   report the blocker and retain the completed Python replay results.
6. Keep measured data, saved references, and source files unchanged. Use fresh
   output directories. Run mode 3 only if I explicitly request a new fit and
   we have agreed on its computational budget.
7. Report interpreter/package versions, configuration changes, modes actually
   run, output locations, and replay differences. Distinguish parameter replay,
   figure redrawing, and fitting; none supplies new independent measurements.
```

## Model design

The same current-response framework accepts a single effective energy, weighted discrete energies, or a normalized continuous density. Independent successive collisions are combined through convolution powers, followed by one unit-area Gaussian response and the common current readout.

[Design and data flow](docs/design.md) explains what is shared, what changes between representations, and how energy variance can compensate for response broadening. The [classroom activities](docs/teaching_case_en.md) connect these choices to excitation, collection, and convolution.

## What can the curves distinguish?

![Fixed-framework current differences: four prescribed energies versus one energy at equal mean, and four energies versus a uniform density at equal mean and variance. The vertical scales differ by four orders of magnitude.](docs/assets/response_contrasts.png)

These are prescribed probes under the same frozen response, not recovered atomic levels. Adding energy spread changes the predicted current more than changing shape at the same mean and variance. The two panels use different scales; neither defines an instrument detection threshold.

The curated [discrete diagnostics](docs/discrete_diagnostics.md) include K=1–8 scans, matched-budget H1 controls, fixed-variance profiles, and the recorded optimization statuses. The current archive and protocol provide **no stable predictive support for resolving a discrete-level count**. Narrow support is a strong prior, and paths still improving at their budget remain labelled not yet stable.

## Repository map

| Location | Contents |
| --- | --- |
| `src/fh_argon/` | Shared current response, replay/fitting workflows, and forward-only discrete channels. |
| `data/` | Original workbook and the five-curve, 805-point overview table; the four-curve fits use 644 points. |
| `reference/` | Saved continuous stages, starting parameters, plotting tables, and the curated discrete diagnostics. |
| `figures/` | R sources for saved-result figures and web graphics. |
| `docs/` | Design, reproduction, interpretation, classroom tasks, and committed preview assets. |

The [historical specified-four-energy comparison](docs/optional_h4s.md) belongs to an earlier five-curve periodic model and is kept separate from the present convolution analysis.

## Interpretation and license

Internal holdouts, optimizer starts, and residual perturbations reuse one experimental archive. They are not independent experiments or calibrated confidence intervals. A fitted effective distribution does not measure atomic populations; lack of resolved components does not establish that real atomic levels are absent.

Source code is distributed under the [MIT license](LICENSE). This repository contains implementation, data, design explanations, and computational records.
