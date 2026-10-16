#!/usr/bin/env Rscript
# Render full-data alternating-inference results and the spectroscopic reference.
library(ggplot2)
library(patchwork)
args <- commandArgs(trailingOnly = TRUE)
if (!length(args) %in% c(2, 3)) stop("Usage: Rscript plot_alternating_case.R SOURCE_TABLES OUTPUT [figure3]")
source <- args[1]
output <- args[2]
figure3_only <- identical(args[3], "figure3")
dir.create(output, recursive = TRUE, showWarnings = FALSE)
read_table <- function(name) read.csv(file.path(source, name), check.names = FALSE)
theme_set(theme_classic(base_size = 9, base_family = "Arial") + theme(
  axis.line = element_line(linewidth = .3), axis.ticks = element_line(linewidth = .3),
  axis.text = element_text(size = 9), axis.title = element_text(size = 9),
  panel.border = element_rect(fill = NA, linewidth = .3),
  legend.title = element_blank(), legend.text = element_text(size = 9),
  legend.key.width = grid::unit(10, "mm"),
  strip.background = element_blank(), strip.text = element_text(hjust = 0, size = 9),
  plot.tag = element_text(face = "bold", size = 10), plot.title = element_text(size = 9)))
save_figure <- function(p, stem, height_mm) {
  svglite::svglite(file.path(output, paste0(stem, ".svg")), width = 183/25.4, height = height_mm/25.4)
  print(p); dev.off()
  grDevices::cairo_pdf(file.path(output, paste0(stem, ".pdf")), width = 183/25.4, height = height_mm/25.4, family = "Arial")
  print(p); dev.off()
  ragg::agg_png(file.path(output, paste0(stem, ".png")), width = 183, height = height_mm, units = "mm", res = 600)
  print(p); dev.off()
  ragg::agg_tiff(file.path(output, paste0(stem, ".tiff")), width = 183, height = height_mm, units = "mm", res = 600, compression = "lzw")
  print(p); dev.off()
}
if (!figure3_only) {
fits <- read_table("current_fits.csv")
fits$model <- factor(fits$model, levels = c("H1", "C"),
                     labels = c("Single-energy reference", "Continuous distribution"))
fits$condition <- factor(fits$Vr_V, levels = c(0, 4, 6, 8),
                         labels = c("(a)  0 V", "(b)  4 V", "(c)  6 V", "(d)  8 V"))
fits$residual_uA <- fits$fitted_uA - fits$observed_uA
observed <- subset(fits, model == "Continuous distribution")
colours <- c("Single-energy reference" = "#888888", "Continuous distribution" = "#246C85")
styles <- c("Single-energy reference" = "longdash", "Continuous distribution" = "solid")
p_fit <- ggplot() +
  geom_point(data = observed, aes(Va_V, observed_uA), size = .55, colour = "#333333") +
  geom_line(data = fits, aes(Va_V, fitted_uA, colour = model, linetype = model), linewidth = .55) +
  facet_wrap(~condition, ncol = 2) +
  scale_colour_manual(values = colours) + scale_linetype_manual(values = styles) +
  scale_x_continuous(breaks = seq(0, 80, 20), expand = expansion(mult = c(.01, .02))) +
  labs(x = "Accelerating voltage (V)", y = "Current (\u03bcA)") +
  theme(legend.position = "bottom")
p_residual <- ggplot(subset(fits, Vr_V == 8), aes(Va_V, residual_uA, colour = model, linetype = model)) +
  geom_hline(yintercept = 0, linewidth = .3, colour = "#333333") +
  geom_line(linewidth = .5, show.legend = FALSE) +
  scale_colour_manual(values = colours) + scale_linetype_manual(values = styles) +
  scale_x_continuous(breaks = seq(0, 80, 10), expand = expansion(mult = c(.01, .02))) +
  labs(x = "Accelerating voltage (V)", y = "Residual (\u03bcA)", title = "(e)  8 V: fitted minus observed") +
  theme(legend.position = "none")
save_figure(p_fit / p_residual + plot_layout(heights = c(3.4, 1), guides = "collect") &
              theme(legend.position = "bottom"), "fig2_alternating_current", 132)
}

sampled_density <- subset(read_table("density_stages.csv"), stage == "Final density")
coefficients <- read_table("final_coefficients.csv")$coefficient
# Evaluate the fitted cubic spline; retain its original quadrature normalization.
knots <- c(rep(9, 4), seq(9, 16, length.out = 71)[2:70], rep(16, 4))
basis <- splines::splineDesign(knots, sampled_density$energy_eV, ord = 4)
quadrature <- rep(diff(sampled_density$energy_eV)[1], nrow(sampled_density))
quadrature[c(1, length(quadrature))] <- quadrature[1]/2
normalized_coefficients <- coefficients / as.numeric(crossprod(quadrature, basis))
cat(sprintf("Figure 3 spline reproduction: maximum absolute difference %.3g.\n",
            max(abs(drop(basis %*% normalized_coefficients) - sampled_density$density_per_eV))))
density <- data.frame(energy_eV = seq(9, 16, by = .001))
density$density_per_eV <- drop(splines::splineDesign(knots, density$energy_eV, ord = 4) %*%
                               normalized_coefficients)
reference <- read_table("spectrum_reference.csv")
nist <- as.numeric(unlist(reference[1, paste0("E", 1:4, "_eV")]))
peak_height <- max(density$density_per_eV)
half_height <- max(sampled_density$density_per_eV)/2
ymax <- peak_height * 1.33
base_density <- ggplot(density, aes(energy_eV, density_per_eV)) +
  annotate("rect", xmin = min(nist), xmax = max(nist), ymin = 0, ymax = Inf, fill = "#ECEEEF") +
  geom_area(fill = "#246C85", alpha = .13) +
  geom_line(colour = "#246C85", linewidth = .75, lineend = "round", linejoin = "round") +
  scale_y_continuous(limits = c(0, ymax), expand = expansion(mult = c(0, 0))) +
  labs(x = "Excitation energy (eV)", y = "Probability density (eV\u207b\u00b9)") +
  theme(axis.line = element_blank(),
        panel.grid.major.y = element_line(colour = "#F0F0F0", linewidth = .25),
        plot.title = element_text(face = "bold", margin = margin(b = 7)),
        plot.margin = margin(6, 7, 5, 4))
p_full <- base_density + coord_cartesian(xlim = c(9, 16)) +
  annotate("rect", xmin = 11.35, xmax = 11.95, ymin = 0, ymax = peak_height * 1.03,
           fill = NA, colour = "#94A4AA", linewidth = .35, linetype = "dashed") +
  annotate("segment", x = 11.95, xend = 12.85, y = peak_height * .78,
           yend = peak_height * .78, linewidth = .35, colour = "#94A4AA") +
  annotate("text", x = 13.02, y = peak_height * .78, label = "Peak enlarged\nin (b)",
           hjust = 0, lineheight = 1.15, size = 9/ggplot2::.pt, family = "Arial", colour = "#505B60") +
  scale_x_continuous(breaks = 9:16, expand = expansion(mult = 0)) +
  labs(title = "(a)  Full energy range")
p_peak <- base_density +
  annotate("segment", x = nist, xend = nist, y = peak_height * 1.08, yend = peak_height * 1.16,
           linewidth = .5, colour = "#50575B") +
  annotate("text", x = nist, y = peak_height * 1.24, label = paste0("E[", 1:4, "]"),
           parse = TRUE, size = 9/ggplot2::.pt, family = "Arial", colour = "#343D41") +
  annotate("segment", x = reference$final_mean_eV, xend = reference$final_mean_eV,
           y = 0, yend = peak_height * 1.03, linewidth = .4, linetype = "dashed", colour = "#246C85") +
  annotate("segment", x = reference$final_mean_eV + .012, xend = 11.81,
           y = peak_height * .95, yend = peak_height * .88, linewidth = .35, colour = "#246C85") +
  annotate("text", x = 11.927, y = peak_height * .88, label = "Mean\n11.640 eV",
           size = 9/ggplot2::.pt, family = "Arial", lineheight = 1.15, hjust = 1, colour = "#246C85") +
  annotate("segment", x = reference$fwhm_lower_eV, xend = reference$fwhm_upper_eV,
           y = half_height, yend = half_height, linewidth = .6, colour = "#AD713C") +
  annotate("segment", x = c(reference$fwhm_lower_eV, reference$fwhm_upper_eV),
           xend = c(reference$fwhm_lower_eV, reference$fwhm_upper_eV),
           y = half_height - peak_height * .035, yend = half_height + peak_height * .035,
           linewidth = .55, colour = "#AD713C") +
  annotate("segment", x = reference$fwhm_upper_eV + .01, xend = 11.81,
           y = half_height, yend = peak_height * .40, linewidth = .35, colour = "#AD713C") +
  annotate("text", x = 11.927, y = peak_height * .40, label = "FWHM\n0.197 eV",
           size = 9/ggplot2::.pt, family = "Arial", lineheight = 1.15, hjust = 1, colour = "#8E5E34") +
  coord_cartesian(xlim = c(11.35, 11.95)) +
  scale_x_continuous(breaks = c(11.4, 11.5, 11.6, 11.7, 11.8, 11.9), expand = expansion(mult = 0)) +
  labs(title = "(b)  Main peak and Ar 4s energies", y = NULL)
save_figure(p_full + p_peak + plot_layout(widths = c(.85, 1.35)), "fig3_alternating_density", 82)
if (!figure3_only) {
stages <- read_table("physical_summaries.csv")
stages$step <- seq_len(nrow(stages))
profiles <- subset(read_table("density_stages.csv"),
                   stage %in% c("Replacement", "Density continuation", "Final density"))
profiles$stage <- factor(profiles$stage,
                         levels = c("Replacement", "Density continuation", "Final density"),
                         labels = c("Initial distribution", "Further distribution fit", "Final distribution"))
p_profiles <- ggplot(profiles, aes(energy_eV, density_per_eV, colour = stage, linetype = stage)) +
  geom_line(linewidth = .55) +
  scale_colour_manual(values = c("#888888", "#AD713C", "#246C85")) +
  scale_linetype_manual(values = c("longdash", "dotdash", "solid")) +
  coord_cartesian(xlim = c(11.35, 11.95)) +
  scale_x_continuous(breaks = c(11.4, 11.6, 11.8)) +
  labs(x = "Excitation energy (eV)", y = "Probability density (eV\u207b\u00b9)",
       title = "(a) Excitation energy distributions")
p_loss_width <- ggplot(stages, aes(step, sd_eV)) +
  geom_line(linewidth = .5, colour = "#246C85") +
  geom_point(size = 1.5, colour = "#246C85") +
  scale_x_continuous(breaks = 1:6) +
  scale_y_continuous(limits = c(0, .11), breaks = c(0, .05, .1)) +
  labs(x = "Stage", y = "Excitation energy SD (eV)", title = "(b) Spread of excitation energies")
p_response_width <- ggplot(stages, aes(step, response_sd_V)) +
  geom_line(linewidth = .5, colour = "#AD713C") +
  geom_point(size = 1.5, colour = "#AD713C") +
  scale_x_continuous(breaks = 1:6) +
  scale_y_continuous(limits = c(2.12, 2.20), breaks = c(2.12, 2.16, 2.20)) +
  labs(x = "Stage", y = "Gaussian SD (V)", title = "(c) Current broadening")
save_figure(p_profiles + p_loss_width + p_response_width +
              plot_layout(widths = c(1.3, 1, 1), guides = "collect") &
              theme(legend.position = "bottom"), "figS1_alternating_stages", 84)
}
cat(if (figure3_only) "Exported Figure 3.\n" else "Exported full-data current description and continuous-density figures.\n")
