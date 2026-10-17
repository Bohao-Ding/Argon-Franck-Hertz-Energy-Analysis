#!/usr/bin/env Rscript
# Web figures from saved tables; no fitting, simulation or new observations.
# Quantitative panels: current/distribution overview, moment-matched probes,
# and compensation between fitted widths. PNG/SVG, 12-inch web layout.
library(ggplot2)
library(patchwork)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Usage: Rscript plot_project.R REPOSITORY OUTPUT")
root <- args[1]
output <- args[2]
dir.create(output, recursive = TRUE, showWarnings = FALSE)
read_table <- function(folder, name) read.csv(file.path(root, "reference", folder, name), check.names = FALSE)
theme_set(theme_minimal(base_size = 12, base_family = "Arial") + theme(
  panel.grid.minor = element_blank(), panel.grid.major = element_line(colour = "#E6EAED", linewidth = .25),
  axis.title = element_text(colour = "#26343D"), axis.text = element_text(colour = "#45535D"),
  plot.title = element_text(face = "bold", colour = "#183544", size = 14),
  plot.subtitle = element_text(colour = "#52626D", size = 10.5),
  plot.caption = element_text(colour = "#52626D", hjust = 0, size = 10),
  legend.position = "bottom", legend.title = element_blank(),
  plot.margin = margin(12, 14, 10, 10)))
save_web <- function(p, stem, height) {
  svglite::svglite(file.path(output, paste0(stem, ".svg")), width = 12, height = height, bg = "white")
  print(p); dev.off()
  ragg::agg_png(file.path(output, paste0(stem, ".png")), width = 12, height = height,
                units = "in", res = 160, background = "white")
  print(p); dev.off()
}
curve_colours <- c("0 V" = "#306B8B", "4 V" = "#419085", "6 V" = "#B67D43", "8 V" = "#8471A1")
condition <- function(x) factor(paste(x, "V"), levels = names(curve_colours))

fits <- subset(read_table("tables", "current_fits.csv"), model == "C")
fits$condition <- condition(fits$Vr_V)
p_current <- ggplot(fits, aes(Va_V, colour = condition)) +
  geom_point(aes(y = observed_uA), size = .8, alpha = .6) +
  geom_line(aes(y = fitted_uA), linewidth = .65) +
  scale_colour_manual(values = curve_colours) +
  scale_x_continuous(breaks = seq(0, 80, 20)) +
  labs(x = "Accelerating voltage (V)", y = "Collector current (\u03bcA)",
       title = "Measured currents and saved predictions",
       subtitle = "Points: measurements   |   Lines: continuous-distribution model")
density <- subset(read_table("tables", "density_stages.csv"), stage == "Final density")
coefficients <- read_table("tables", "final_coefficients.csv")$coefficient
knots <- c(rep(9, 4), seq(9, 16, length.out = 71)[2:70], rep(16, 4))
basis <- splines::splineDesign(knots, density$energy_eV, ord = 4)
quadrature <- rep(diff(density$energy_eV)[1], nrow(density))
quadrature[c(1, length(quadrature))] <- quadrature[1]/2
coefficient_mass <- as.numeric(crossprod(quadrature, basis))
fine_energy <- seq(9, 16, by = .0025)
fine_density <- data.frame(energy_eV = fine_energy, density_per_eV = drop(
  splines::splineDesign(knots, fine_energy, ord = 4) %*% (coefficients/coefficient_mass)))
reference <- read_table("tables", "spectrum_reference.csv")
energies <- unlist(reference[1, c("E1_eV", "E2_eV", "E3_eV", "E4_eV")], use.names = FALSE)
p_density <- ggplot(fine_density, aes(energy_eV, density_per_eV)) +
  geom_area(fill = "#D8E8EE") + geom_line(colour = "#306B8B", linewidth = .8) +
  geom_vline(xintercept = energies, colour = "#AB7F4F", linewidth = .45, linetype = "dashed") +
  coord_cartesian(xlim = c(11.35, 11.95)) +
  scale_x_continuous(breaks = c(11.4, 11.6, 11.8)) +
  labs(x = "Effective excitation energy (eV)", y = expression(Density~(eV^{-1})),
       title = "Effective distribution: peak region",
       subtitle = "Dashed: Ar 4s reference energies; full support 9\u201316 eV") +
  theme(legend.position = "none")
overview <- p_current + p_density + plot_layout(widths = c(1.45, 1)) + plot_annotation(
  title = "From measured current to an effective excitation distribution",
  subtitle = "Four retarding conditions \u00b7 644 archived points \u00b7 one shared collision-response framework",
  caption = "The fitted density describes effective current-response contributions. It is not a measured atomic spectrum.")
save_web(overview, "project_overview", 5.5)

probes <- subset(read_table("discrete_diagnostics", "probe_contrasts.csv"), domain == "wide" & framework == "H1")
probes$condition <- condition(probes$Vr_V)
probe_plot <- function(comparison_name, divisor, title, subtitle, y_label) {
  frame <- subset(probes, comparison == comparison_name)
  ggplot(frame, aes(Va_V, delta_uA/divisor, colour = condition)) +
    geom_hline(yintercept = 0, colour = "#849098", linewidth = .3) +
    geom_line(linewidth = .65) + scale_colour_manual(values = curve_colours) +
    scale_x_continuous(breaks = seq(0, 80, 20)) +
    labs(x = "Accelerating voltage (V)", y = y_label, title = title, subtitle = subtitle)
}
p_spread <- probe_plot("spread_H4_vs_point", 1e-3,
  "Adding energy spread", "Four points minus one point; common mean",
  expression(Delta*I~(10^{-3}~mu*A)))
p_shape <- probe_plot("same_variance_H4_vs_uniform", 1e-7,
  "Changing shape at fixed moments", "Four points minus uniform; common mean and SD",
  expression(Delta*I~(10^{-7}~mu*A)))
contrasts <- p_spread + p_shape + plot_layout(guides = "collect") + plot_annotation(
  title = "Energy spread and discrete structure leave different response scales",
  subtitle = "Prescribed SD = 0.10 eV \u00b7 external parameters frozen to the discrete-scan H1 fit",
  caption = "The four points are diagnostic inputs. The two vertical scales differ; neither is an instrument detection threshold.") &
  theme(legend.position = "bottom")
save_web(contrasts, "response_contrasts", 5.4)

scores <- subset(read_table("discrete_diagnostics", "profile_scores.csv"), fold == "full")
baseline <- subset(scores, channel == "H1")
expanded <- subset(scores, channel != "H1")
for (channel in c("H2", "H4", "uniform")) {
  zero <- baseline
  zero$channel <- channel
  expanded <- rbind(expanded, zero)
}
expanded$family <- factor(expanded$channel, levels = c("H2", "H4", "uniform"),
                          labels = c("Two points", "Four points", "Uniform density"))
expanded$domain <- factor(expanded$domain, levels = c("wide", "narrow"),
  labels = c("Wide support: 9\u201316 eV", "Narrow support: 11.4\u201312.0 eV"))
tradeoff <- ggplot(expanded, aes(sd_eV^2, response_sd_V^2, colour = family, linetype = family)) +
  geom_line(linewidth = .8) + geom_point(size = 1.8) + facet_wrap(~domain) +
  scale_colour_manual(values = c("#306B8B", "#B67D43", "#419085")) +
  scale_linetype_manual(values = c("solid", "dashed", "dotdash")) +
  scale_x_continuous(breaks = c(0, .02, .04, .06)) +
  labs(x = expression(Internal~energy~variance~(eV^2)), y = expression(Response~variance~(V^2)),
       title = "Internal energy spread can trade against response broadening",
       subtitle = "Full-data fixed-SD settings; the narrow support is a strong prior",
       caption = "Points are fitted settings, not independent measurements. All paths retain their fixed-budget, not-yet-stable status.") +
  theme(strip.text = element_text(face = "bold", colour = "#26343D", size = 12))
save_web(tradeoff, "broadening_tradeoff", 5.2)
cat("Exported three project figures as PNG and SVG.\n")
