# Preview assets and provenance

`figures/plot_project.R` draws the three graphics with R/ggplot2 and patchwork. Mode 2 exports them to a fresh output directory as 1920-pixel-wide PNG and editable-text SVG files.

| Graphic | Sources under `reference/` | Content |
| --- | --- | --- |
| `project_overview` | `tables/`: `current_fits.csv`, `density_stages.csv`, `final_coefficients.csv`, `spectrum_reference.csv` | Four measured curves and saved continuous predictions, beside a peak-region view. The density support is 9–16 eV; dashed markers show spectroscopic references. |
| `response_contrasts` | `discrete_diagnostics/probe_contrasts.csv` | Frozen wide-domain H1 framework. Four points versus one point share the mean; four points versus uniform share mean and variance. The current scales differ by four orders of magnitude. |
| `broadening_tradeoff` | `discrete_diagnostics/profile_scores.csv` | Full-data fixed-SD fits, with the shared zero-variance reference plotted for each family. Response variance decreases as prescribed energy variance increases. |

The overview evaluates the saved spline on a finer drawing grid. Reported peak energy uses the original 0.025 eV grid; probe lines connect the original 0.5 V samples. The committed previews are reviewed copies of these exports.

## 中文

三幅图由同一 R 脚本读取保存的源表生成。概览图放大分布峰区；响应差异图分别比较展宽和谱形；展宽补偿图展示全数据固定方差拟合。PNG/SVG 预览图由复核后的导出文件更新。
