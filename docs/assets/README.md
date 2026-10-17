# Preview assets and provenance

All three graphics are drawn by `figures/plot_project.R` using R/ggplot2 and patchwork. Run menu mode 2 to recreate them in a fresh output directory. PNG files have a white background and width 1920 pixels; SVG files retain editable text. The committed previews are copied from reviewed exports, not regenerated during ordinary replay.

| Graphic | Source tables under `reference/` | Visual claim and limits |
| --- | --- | --- |
| `project_overview` | `tables/current_fits.csv`, `density_stages.csv`, `final_coefficients.csv`, `spectrum_reference.csv` | Measured curves and saved continuous predictions beside a peak-region enlargement. The spline support remains 9–16 eV; the small high-energy tail is outside this view. Spectroscopic markers are a comparison after fitting. |
| `response_contrasts` | `discrete_diagnostics/probe_contrasts.csv` | The wide-domain discrete-scan H1 framework is frozen. Four prescribed points are compared with one point at equal mean, then with a uniform density at equal mean and SD. The two vertical scales differ by four orders of magnitude. |
| `broadening_tradeoff` | `discrete_diagnostics/profile_scores.csv` | Full-data fixed-SD candidates show internal/external width compensation. The shared zero-variance H1 reference is plotted for each family; infeasible candidates have no fitted point. These are computational settings, not experimental replicates. |

The overview evaluates the saved cubic spline on a finer drawing grid without refitting. Its reported mode remains defined on the original 0.025 eV calculation grid. Probe lines connect the original 0.5 V samples. No uncertainty bars, significance labels, or instrument-detection claims are introduced.

## 中文

三幅图均由同一 R 脚本读取保存的源表绘制，导出 PNG/SVG。概览图只放大分布峰区；响应差异图使用不同纵轴数量级；展宽补偿图表示计算设置之间的关系。图中没有新增测量、拟合或实验不确定度估计。
