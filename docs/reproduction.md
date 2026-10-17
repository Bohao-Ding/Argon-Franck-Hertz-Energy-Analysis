# Reproduction

[Project](../README.md) · [Design](design.md) · [Discrete diagnostics](discrete_diagnostics.md)

Use a compatible Python environment. The menu does not install dependencies, create an environment, download inputs, or require CUDA. For step-by-step environment preparation with a local AI agent, see the [README instructions](../README.md#reproduce-with-an-ai-agent).

## Python

The numerical modes need NumPy, pandas, SciPy, PyTorch, and openpyxl. [requirements.txt](../requirements.txt) records the versions used for replay. Python 3.13.7 was used; the computation runs on CPU, so a PyTorch CUDA build suffix is not required.

From the repository directory, run `python run.py` with the selected environment's interpreter. The repository can be moved: input paths resolve relative to its own location.

## R

Mode 2 needs R, Cairo PDF support, and `ggplot2`, `patchwork`, `svglite`, and `ragg`. The Python launcher finds `Rscript` through `PATH`, or through an existing installation identified by `R_HOME`. An R user library must be visible to that same process, for example through the current session's `R_LIBS_USER`.

Check the selected R environment with:

```text
Rscript --vanilla -e 'print(vapply(c("ggplot2", "patchwork", "svglite", "ragg"), requireNamespace, logical(1), quietly=TRUE)); print(capabilities("cairo"))'
```

Plots use Arial, with system font availability determining rendering. The project graphics are exported as PNG/SVG; the original saved-result figure scripts retain PDF/SVG/PNG/TIFF export. No font or package is installed automatically.

## Modes and output files

Every selection writes to a fresh `outputs/<timestamp>_<mode>/` directory, which Git ignores.

| Mode | Outputs and scope |
| --- | --- |
| 1: replay | `replayed_currents.csv`, `distribution_summaries.csv`, `replay_checks.json`; H1 plus six continuous stages. |
| 2: figures | `figures/`; the original data/current/distribution/stage figures plus `project_overview`, `response_contrasts`, and `broadening_tradeoff`. |
| 3: refit | `stages/` and `refit.log`; continues the adopted fitting sequence from saved H1 parameters. |
| 4: diagnostics | `diagnostic_currents.csv`, `distribution_summaries.csv`, `probe_summaries.csv`, `probe_contrasts.csv`, `replay_checks.json`; 34 full-data models and the fixed-framework probes. |

Mode 3 takes substantially longer. It continues a recorded starting point and update sequence; it is not a restart from arbitrary initial conditions or an independent experiment. This project-display update did not execute that optimization.

Mode 4 reads JSON parameters, so its curated supplement does not need binary checkpoints. Holdout and perturbation tables are saved records: their complete checkpoint histories are outside the curated package and cannot be rerun through mode 4.

## Numerical conventions and checking results

Calculations use one CPU thread and float64 after the retained workbook conversion. Compare replayed currents to the saved values and inspect the reported differences and unchanged parameters. Small floating-point differences can depend on the environment; a replay is a software consistency check, not a test of the physical model against a new experiment.

The reported continuous peak uses the original 0.025 eV calculation grid. The finer R plotting grid evaluates the same spline coefficients and does not redefine that reported peak. The main-workflow summaries retain the finite width introduced at initialization, later distribution changes, and Gaussian response width.

If dependencies are missing, the selected mode stops with a message. Reuse an existing compatible installation first; prepare missing dependencies or an isolated project-local environment as needed within the current authorization. Partial outputs are retained if execution is interrupted.

## Recreating committed preview assets

Mode 2 produces the three previews inside its fresh output directory. A maintainer can copy the reviewed PNG/SVG files to `docs/assets/`; ordinary runs do not change those committed files. Their inputs and interpretation are listed in [asset provenance](assets/README.md).

## 中文说明

使用选定环境的 Python 解释器运行 `python run.py`。数值依赖和复算版本见 `requirements.txt`。绘图需要实际 Rscript 进程可见的四个 R 包、Cairo 和可用字体，可通过当前会话的 `R_HOME`、`R_LIBS_USER` 指向已有安装，不将个人路径写入源码。逐步检查和准备本地环境的 AI 智能体指令见[中文 README](../README.zh-CN.md#让-ai-智能体协助复现)。

先运行模式 1 查看主流程复算，再用模式 4 查看补充模型及受控探针。模式 2 从保存的源表重绘图件，所有输出均在新目录中。模式 3 才会接续优化，本次项目整理未执行模式 3。

模式 4 可重放 34 组全数据模型及固定外部框架探针；留出和扰动表仅为已保存记录。复算误差用于检查实现一致性，不是新实验、物理真实性检验或置信区间。图像的细网格也不提高实验分辨率。
