# Argon Franck–Hertz Energy Analysis

Reproduction sources for *Modeling effective excitation energy distributions in the argon Franck–Hertz experiment*.

This source tree accompanies a teaching case that connects measured collector currents, a single effective excitation energy, a continuous effective excitation energy distribution, and the four discrete spectroscopic Ar 4s reference energies. The smooth fitted distribution represents effective excitation contributions; it does not turn the atomic reference levels into a continuum.

[中文说明](README.zh-CN.md)

## Start and choose a mode

On Windows, open `start.cmd`. It uses an existing `.venv` first, or the Python already available in the active environment. Alternatively, run `python run.py` from the repository. The menu takes a number; no analysis parameters are required.

| Mode | Task | Dependencies |
| --- | --- | --- |
| 1 | Recalculate H1 and six continuous stages from saved parameters; write fitted currents, distribution summaries, and replay checks. No optimizer runs. | Python packages below |
| 2 | Redraw Figures 1, 2, 3, and S1 from the saved source tables using the current R/ggplot2 figure settings. | R and the four R packages below |
| 3 | Continue the adopted fitting sequence from the saved H1 starting parameters, including the distribution initialization and alternating parameter updates. | Python packages below |
| 0 | Exit. | Python standard library only |

Mode 3 can take substantially longer than replay. It continues the recorded starting point and optimization sequence; it is not a new independent experimental run or a restart from arbitrary initial conditions. Its optimization records are saved in `refit.log`.

Each selection writes to a fresh `outputs/<timestamp>_<mode>/` directory. Inputs and saved reference results are not overwritten. The program resolves paths relative to its own location, so the repository can be moved. It does not install packages, download data, or require CUDA. Numerical calculations use a single CPU thread and float64, retaining the original data-conversion convention.

## Files and outputs

- `data/`: the original measured workbook and the 805-point CSV used for the data overview. Fits use the recorded 644 points at retarding voltages 0, 4, 6, and 8 V.
- `reference/starting_h1/`: saved starting parameters for mode 3; `reference/stages/`: the saved H1 and continuous-stage fits for mode 1.
- `reference/tables/`: the manuscript source tables for mode 2. The four spectroscopic energies enter the comparison after fitting.
- `src/fh_argon/`: the current response model, reproduction workflows, and retained implementation dependencies in `_compat/`.
- `docs/`: English and Chinese classroom tasks and the optional historical H4s comparison.
- `figures/`: R figure sources. Mode 2 exports PDF, SVG, PNG, and TIFF to its own output directory, including the separate Figure 1a schematic.

Mode 1 produces `replayed_currents.csv`, `distribution_summaries.csv`, and `replay_checks.json`. Mode 3 writes fitted stages under `stages/`.

The reported peak energy is measured on the original 0.025 eV calculation grid. The finer Figure 3 plotting grid only evaluates the fitted spline smoothly and does not redefine that reported energy. The stage tables retain the finite width introduced at initialization, alongside later changes in the distribution and Gaussian current broadening.

## Existing environment and dependencies

Python numerical modes need `numpy`, `pandas`, `scipy`, `torch`, and `openpyxl`. `requirements.txt` records the versions used for local replay; Python 3.13.7 was used for that check. PyTorch is listed without a CUDA build suffix because the calculation uses CPU.

Figure export needs `Rscript` on `PATH`, or an existing R installation identified by `R_HOME`, plus `ggplot2`, `patchwork`, `svglite`, and `ragg`. The R user library must be visible to the actual `Rscript` process. Cairo PDF support is also required. The plots retain the manuscript's Arial font selection; font availability is determined by the existing system.

The menu checks dependencies only for the chosen mode. A missing dependency is reported without starting an installation. Reuse a compatible environment before requesting any environment changes.

## Reproduction with an AI agent

1. Read this file and identify an existing Python environment. Check its Python version and the five packages against `requirements.txt`; do not create or replace an environment automatically.
2. Reuse that environment by activating it before running `python run.py`, or use the existing repository `.venv` through `start.cmd`. No personal machine path is needed in source files.
3. For figures, check `Rscript` visibility and whether the four R packages are visible in that same process. An existing user library can be exposed through the current session environment; do not record personal library paths in the repository.
4. Start with mode 1 to inspect replayed currents and distribution summaries. Use mode 2 for figures. Run mode 3 only when a new optimization is explicitly wanted, preserving both its outputs and the saved reference results.
5. Report what was actually run and where its relative output directory is. Replay, redrawing, and fitting are separate activities; none adds independent measurements or a confidence interval.

The source is distributed under the retained MIT license in `LICENSE`.
