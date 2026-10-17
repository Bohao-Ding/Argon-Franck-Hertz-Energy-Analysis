# Discrete structure and identifiability

[Project](../README.md) · [Design](design.md) · [Reproduce](reproduction.md) · [Saved manifest](../reference/discrete_diagnostics/manifest.json)

These diagnostics ask which excitation hypotheses the same 644 measured points can distinguish within the shared collision-response framework. They retain alternatives that explain apparent gains without requiring resolved discrete structure.

## Evidence chain

| Question | Comparison | What the saved results support |
| --- | --- | --- |
| Does a larger nominal K help? | K=1–8, broad/narrow domains, voltage-block holdouts and residual perturbations. | Fitted components coincide; no stable predictive advantage identifies K. |
| Does extra optimization explain the change? | Ten H1 continuations with the same additional update budget. | The main training/holdout changes are reproduced by single-energy controls. |
| Is nonzero variance needed? | Fixed-SD H1/H2/H4/uniform profiles; selection uses training data only. | Both full-data selections return zero variance; the narrow-domain folds do likewise. |
| Is discrete shape needed after matching moments? | Frozen external parameters, equal mean and variance; compare four points with two points or a uniform density. | Residual shape differences are small and do not obtain stable predictive support. |

The wide domain is 9–16 eV. The narrow domain, 11.4–12.0 eV, is a **strong support prior**. A prescribed positive SD or a prior boundary is not evidence that the data identified a split.

## Why response width matters

![Response variance decreases as the prescribed internal energy variance increases, for two-point, four-point and uniform candidates in both energy domains.](assets/broadening_tradeoff.png)

The plotted points are full-data fitted settings, not experimental replicates. Internal energy variance can be traded against external Gaussian response variance. Separately refitted curves therefore do not isolate internal structure. The [collapse decomposition](../reference/discrete_diagnostics/collapse_decomposition.csv) retains a same-mean point under each candidate's own external framework: representative apparent holdout gains do not require the candidate's variance.

Nominal K is exactly nonunique when coincident energies or zero weights are permitted. Narrow continuous densities can also approach point-spectrum responses. These facts limit the inverse problem; they do not prove that real, separated atomic levels are absent or universally unobservable.

## What is included

All files below are under `reference/discrete_diagnostics/`.

| Saved material | Files / coverage |
| --- | --- |
| Full-data replay | `parameters/`: four original H1/H4 fits across two domains, plus thirty fixed-variance candidates; `saved_currents.csv`: their 34 × 644 predictions. |
| K scan | `scan_scores.csv`, `scan_cv.csv`, `scan_levels.csv`, `scan_path_status.csv`. |
| Conditional perturbations | `noise_summary.csv`, `noise_window_stability.csv`; 40 residual-perturbation refits per domain from the original run. |
| Matched-budget H1 | `matched_control_scores.csv`, `matched_control_cv.csv`; ten additional controls. |
| Fixed variance | `profile_scores.csv`, `profile_selected.csv`, `profile_cv.csv`, `profile_path_status.csv`, `profile_candidates.csv`. |
| Controlled inference | `probe_contrasts.csv`, `probe_summary.csv`, `probe_settings.json`; original 0.5 V coordinates and the prescribed distributions. |
| Interpretation records | `broadening_tradeoff.csv`, `collapse_decomposition.csv`, `shape_oof_summary.csv`, `profile_protocol.json`, `decision.json`. |

The original K-scan batch comprises 540 optimization paths; the matched controls add ten. The variance scan completed 150 feasible paths, with ten additional candidates infeasible under the narrow prior. Fixed budgets ended while training objectives were still improving. The status records preserve “尚未稳定” (not yet stable), historical interruption information, and infeasible candidates. Conditional simulation retraining was not started.

Path strings in status tables identify original runs. They are identifiers, not links to bundled iteration histories. Those histories, all fold/perturbation checkpoints, process logs, and orchestration scripts are not part of the curated forward-replay package.

## Running the supplement

Choose **mode 4** in `python run.py`. The forward-only channels reuse the shared response and load the original JSON parameter values. There is no optimizer or simulation in this mode.

Each of the 34 full-data predictions is compared with its saved current. The probes then compare learned H4, the same-mean point, prescribed H2/H4 with SD 0.10 eV, and an equal-mean/equal-variance uniform density under both original H1 and H4 frameworks, in both domains. The external parameters stay fixed within each comparison.

Output differences use `alternative_uA - reference_uA`. Each condition retains 161 voltage samples. Probe distributions are defined inputs, not inferred atom populations. The current differences in the homepage panels have different scales and cannot establish an instrument resolution or noise threshold.

Mode 4 does not rerun the K scan, matched controls, fixed-variance optimization, holdouts, or perturbation refits. Their tables are retained computational records. Folds, starts, and residual perturbations are not new independent measurements or calibrated experimental confidence intervals.

## 中文说明

本补充沿用 0/4/6/8 V、644 点的同一档案，按“名义 K → 匹配优化预算 → 非零方差 → 同均值同方差谱形”的顺序排查替代解释。宽域为 9–16 eV，11.4–12.0 eV 窄域明确属于强先验。

两域全数据方差扫描都选择零方差；窄域各折亦选择零方差。宽域只有一折选择 0.06 eV，二点、四点和均匀谱表现近似，未形成稳定的多能量预测优势。展宽补偿图是拟合设置之间的关系，不是实验重复的回归。

可运行部分为 34 组全数据参数和固定框架前向探针；留出、扰动及匹配预算训练的汇总结果保留为计算记录。原扫描 540 条路径、追加 10 条 H1 对照，以及方差扫描 150 条可行路径均保留预算末仍未稳定的事实；另 10 条是先验不可行候选。没有继续条件模拟重训。

这里的“未分辨”限于当前档案、模型和协议。它不等于真实体系只有一个能级，也不意味着彼此分离的原子能级永远不能分辨。
