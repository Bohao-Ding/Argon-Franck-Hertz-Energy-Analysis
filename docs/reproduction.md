# Reproduction

[Project](../README.md) · [Design](design.md) · [Discrete diagnostics](discrete_diagnostics.md)

Run modes **1 → 4 → 2** to replay the saved results and redraw the figures. The [AI-agent instructions](../README.md#reproduce-with-an-ai-agent) cover local environment setup.

## Python

Use a compatible environment with NumPy, pandas, SciPy, PyTorch, and openpyxl. [requirements.txt](../requirements.txt) records the replay versions; Python 3.13.7 was used. Numerical calculations run on CPU.

From the repository directory, launch `python run.py` with the selected interpreter. Input paths resolve relative to the repository.

## R

Mode 2 needs `ggplot2`, `patchwork`, `svglite`, `ragg`, and Cairo PDF support. The launcher finds `Rscript` through `PATH` or `R_HOME`; `R_LIBS_USER` can expose an existing R user library to that process.

Check the selected R environment with:

```text
Rscript --vanilla -e 'print(vapply(c("ggplot2", "patchwork", "svglite", "ragg"), requireNamespace, logical(1), quietly=TRUE)); print(capabilities("cairo"))'
```

Plots request Arial, with rendering determined by the system's available fonts. Project graphics export as PNG/SVG; saved-result figures export as PDF/SVG/PNG/TIFF. The menu reports missing dependencies before starting a selected mode.

## Modes and outputs

Each selection creates `outputs/<timestamp>_<mode>/`.

| Mode | Outputs and scope |
| --- | --- |
| 1: replay | `replayed_currents.csv`, `distribution_summaries.csv`, `replay_checks.json`; H1 and six continuous stages. |
| 2: figures | `figures/`; data, current, distribution, stage, and three project graphics. |
| 3: refit | `stages/` and `refit.log`; the adopted alternating fit from saved H1 starting parameters. |
| 4: diagnostics | `diagnostic_currents.csv`, `distribution_summaries.csv`, `probe_summaries.csv`, `probe_contrasts.csv`, `replay_checks.json`; 34 full-data models and controlled probes. |
| 5: affine comparison | Local current and feature scores for the five scans. |

Mode 3 runs the optimization sequence and takes longer than parameter replay. Mode 4 loads JSON parameters; fold, perturbation, and matched-budget results are supplied as summary tables.

## Local affine comparison

Run `python run.py affine` or choose mode 5. This mode uses only
`data/observed.csv` and the stored single-energy parameters. It runs on
a single CPU thread and requires no R or optimiser.

For the four spectroscopic positions, the effective energy is
`mean + shift + scale * (level - mean)`. The shift range is ±0.10 eV
and the spacing scale is 0.95–1.05. The grid also includes the exact shift
to the local fitted centre. The transform preserves spacing ratios. It
represents sensitivity to an effective energy-axis correction; assigning
its parameters to individual instruments would require independent calibration.

- `protocol.json` gives the ranges, input paths, and comparison rules.
- `current_scores.csv` compares whole-current residual sums of squares, including the stored H1 reference.
- `feature_scores.csv` reports amplitude and phase RSS reductions for peak-to-peak and valley-to-valley cycles at 1, 2 and 4 V smoothing. Positive values favour the alternative over its same-mean single-energy control.
- `summary.json` gives the shared setting chosen on 0/4/6 V, the sweep counts and the exploratory 8 V feature-selected counterexample.
- `anchor_predictions.csv` contains native-node currents at the absolute and fitted-mean reference settings. `run.json` gives counts and runtime.

The comparison should reproduce 242 energy settings and 1,452 whole-current
rows. At 8 V, the shared setting gives joint gains for valley-to-valley
features, and 132 of 242 settings give joint gains with all three smoothing
settings. The stored response had already used the 8 V curve. The 10 V
readout is evaluated both with transferred 8 V coefficients and with neutral
coefficients. The original 0 V scan provides current scores without supported
common harmonics.

## Checking results

Numerical calculations retain the original float32 workbook conversion before float64 evaluation. Replay reports current differences against saved predictions and changes in fixed parameters. Inspect these values alongside distribution summaries and exported figures.

The reported continuous peak uses the original 0.025 eV grid. R evaluates the same spline coefficients on a finer drawing grid. Stage summaries track initialization, density updates, and Gaussian response width.

To refresh the committed previews, review the three PNG/SVG exports from mode 2 and copy them to `docs/assets/`. See [asset provenance](assets/README.md) for their source tables.

## 中文说明

按 **1 → 4 → 2** 的顺序复算保存结果并重绘图件。[AI 智能体指令](../README.zh-CN.md#让-ai-智能体协助复现)用于逐步准备本地环境。

Python 依赖见 `requirements.txt`。R 需要四个绘图包和 Cairo；通过 `PATH` 或 `R_HOME` 查找 Rscript，通过会话级 `R_LIBS_USER` 暴露已有用户库。模式 3 接续优化；模式 4 重放 34 组全数据模型与受控探针。留出、扰动和匹配预算结果以汇总表提供。

模式 5 可通过 `python run.py affine` 直接运行，复算本地五条曲线的平移和缩放对照。

各模式写入独立输出目录。复核电流差异、固定参数、分布统计量和图件；报告峰位取自原有 0.025 eV 网格。
