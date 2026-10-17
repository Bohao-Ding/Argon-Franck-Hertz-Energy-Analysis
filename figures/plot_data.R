#!/usr/bin/env Rscript
# Figure 1: conceptual collection physics beside all 805 measured points.
# R alone draws/exports the figures; no fitting or new observations are performed.
library(ggplot2)
library(patchwork)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Usage: Rscript plot_data.R SOURCE_TABLES OUTPUT")
source <- args[1]
output <- args[2]
dir.create(output, recursive = TRUE, showWarnings = FALSE)
read_table <- function(name) read.csv(file.path(source, name), check.names = FALSE)
theme_set(theme_classic(base_size = 9, base_family = "Arial") + theme(
  axis.line = element_line(linewidth = .3), axis.ticks = element_line(linewidth = .3),
  axis.text = element_text(size = 9), axis.title = element_text(size = 9),
  legend.title = element_blank(), legend.text = element_text(size = 9),
  plot.tag = element_text(face = "bold", size = 10), plot.title = element_text(size = 9)))
save_figure <- function(p, stem, height_mm, width_mm=183) {
  svglite::svglite(file.path(output, paste0(stem, ".svg")), width = width_mm/25.4, height = height_mm/25.4)
  print(p); dev.off()
  grDevices::cairo_pdf(file.path(output, paste0(stem, ".pdf")), width = width_mm/25.4, height = height_mm/25.4, family = "Arial")
  print(p); dev.off()
  ragg::agg_png(file.path(output, paste0(stem, ".png")), width = width_mm, height = height_mm, units = "mm", res = 600)
  print(p); dev.off()
  ragg::agg_tiff(file.path(output, paste0(stem, ".tiff")), width = width_mm, height = height_mm, units = "mm", res = 600, compression = "lzw")
  print(p); dev.off()
}
observed <- read_table("observed.csv")
observed$condition <- factor(observed$Vr)
p_raw <- ggplot(observed, aes(Va, observed_uA, colour = condition, linetype = condition)) +
  geom_line(linewidth = .4) +
  scale_colour_manual(values = c("#222222", "#246C85", "#B57A43", "#776C8E", "#8B9A62"),
                      labels = c("0 V", "4 V", "6 V", "8 V", "10 V")) +
  scale_linetype_manual(values = c("solid", "dashed", "dotdash", "longdash", "twodash"),
                        labels = c("0 V", "4 V", "6 V", "8 V", "10 V")) +
  scale_x_continuous(sec.axis = dup_axis(name = NULL, labels = NULL)) +
  scale_y_continuous(sec.axis = dup_axis(name = NULL, labels = NULL)) +
  labs(x = "Accelerating voltage (V)", y = "Current (\u03bcA)", title = "One archived dataset") +
  theme(panel.border = element_rect(fill = NA, linewidth = .3), axis.line = element_blank())
# Functional mechanism diagram: no claim about actual tube geometry.
mesh <- data.frame(y=seq(2.3,5.35,by=.38))
atoms <- data.frame(x=c(2.7,3.0,4.3,5.5),y=c(4.35,2.85,3.9,2.85),
                    label=c("Ar","Ar","Ar*","Ar"))
transmitted <- data.frame(x=c(6.45,6.9,9.08),y=c(3.9,4.32,4.32))
p_selection <- ggplot() +
  annotate("rect",xmin=.7,xmax=6.5,ymin=2.1,ymax=5.7,fill="#F1F6F8",colour=NA) +
  annotate("rect",xmin=6.5,xmax=9.7,ymin=2.1,ymax=5.7,fill="#F7F3ED",colour=NA) +
  annotate("rect",xmin=.7,xmax=9.7,ymin=2.1,ymax=5.7,fill=NA,colour="#A4A9AC",linewidth=.3) +
  annotate("segment",x=1.4,xend=1.4,y=2.55,yend=5.3,colour="#434A4F",linewidth=.75,lineend="round") +
  geom_segment(data=mesh,aes(x=6.5,xend=6.5,y=y,yend=y+.19),colour="#434A4F",linewidth=.5) +
  annotate("segment",x=9.2,xend=9.2,y=2.55,yend=5.3,colour="#434A4F",linewidth=.75,lineend="round") +
  geom_point(data=atoms,aes(x,y),size=4.2,shape=21,fill="#EEE5D9",colour="#AD8251",stroke=.35) +
  geom_text(data=atoms,aes(x,y,label=label),size=3,family="Arial",colour="#55432E") +
  annotate("text",x=1.4,y=6.35,label="C\nHeated cathode",size=3,family="Arial",lineheight=.95) +
  annotate("text",x=6.5,y=6.35,label="G\nAccelerating grid",size=3,family="Arial",lineheight=.95) +
  annotate("text",x=9.2,y=6.35,label="A\nCollector",size=3,family="Arial",lineheight=.95) +
  annotate("segment",x=1.55,xend=3.94,y=3.9,yend=3.9,colour="#246C85",linewidth=.5,
           arrow=grid::arrow(length=grid::unit(1.5,"mm"),type="closed")) +
  annotate("segment",x=4.66,xend=6.42,y=3.9,yend=3.9,colour="#246C85",linewidth=.5,
           arrow=grid::arrow(length=grid::unit(1.5,"mm"),type="closed")) +
  geom_path(data=transmitted,aes(x,y),colour="#246C85",linewidth=.5,linejoin="round",
            arrow=grid::arrow(length=grid::unit(1.5,"mm"),type="closed")) +
  annotate("text",x=2.75,y=3.45,label="Electron motion",size=3,family="Arial",colour="#246C85") +
  annotate("text",x=4.3,y=5.4,label="Inelastic collision",size=3,family="Arial") +
  annotate("text",x=4.3,y=4.95,label="Excitation energy E",size=3,family="Arial",colour="#6B6259") +
  annotate("text",x=7.85,y=5.12,label="epsilon['||'] > e*V[r]",parse=TRUE,size=3.2) +
  annotate("curve",x=6.85,xend=6.57,y=3.72,yend=2.92,curvature=-.7,colour="#AD8251",linewidth=.5,
           arrow=grid::arrow(length=grid::unit(1.4,"mm"),type="closed")) +
  annotate("text",x=8.05,y=3.16,label="Rejected",size=3,family="Arial",colour="#8A653E") +
  annotate("text",x=3.95,y=2.35,label="Acceleration + excitation",size=2.9,family="Arial",colour="#4A6471") +
  annotate("text",x=8.0,y=2.35,label="Retarding field",size=2.9,family="Arial",colour="#77634D") +
  annotate("segment",x=9.2,xend=9.2,y=2.55,yend=1.4,colour="#434A4F",linewidth=.35) +
  annotate("segment",x=9.2,xend=8.55,y=1.4,yend=1.4,colour="#434A4F",linewidth=.35) +
  annotate("point",x=8.3,y=1.4,shape=21,size=5,fill="white",colour="#434A4F",stroke=.35) +
  annotate("text",x=8.3,y=1.4,label="I",size=3,family="Arial") +
  annotate("text",x=8.4,y=.9,label="Collector current",size=3,family="Arial") +
  annotate("segment",x=1.4,xend=6.38,y=7.2,yend=7.2,colour="#68757C",linewidth=.3,
           arrow=grid::arrow(ends="both",length=grid::unit(1.2,"mm"))) +
  annotate("text",x=3.95,y=7.82,label="V[a] == V[G] - V[C]",parse=TRUE,size=3.2) +
  annotate("segment",x=6.62,xend=9.2,y=7.2,yend=7.2,colour="#68757C",linewidth=.3,
           arrow=grid::arrow(ends="both",length=grid::unit(1.2,"mm"))) +
  annotate("text",x=7.85,y=7.82,label="V[r] == V[G] - V[A]",parse=TRUE,size=3.2) +
  coord_cartesian(xlim=c(0,10.6),ylim=c(0,8.5),expand=FALSE) +
  labs(title="Acceleration, excitation and collection") +
  theme_void(base_family="Arial",base_size=9) +
  theme(plot.title=element_text(size=9),plot.tag=element_text(face="bold",size=10))
save_figure(p_selection,"assets/fig1a_mechanism",82,width_mm=105)
save_figure(p_selection + p_raw + plot_layout(widths=c(1.25,1)) +
              plot_annotation(tag_levels="a"),"fig1_data_prediction",82)
