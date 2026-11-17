# Testing excitation hypotheses with argon Franck–Hertz curves

This activity follows a conventional Franck–Hertz experiment in an upper-level
undergraduate laboratory. Students use the archived current curves and saved
comparisons. [Model design](design.md) explains the current response; convolution
and refitting can be used as extensions.

| Step | What students do | What students report |
| --- | --- | --- |
| 1. Establish a single-energy baseline | Mark successive extrema in the measured curves and compare the spacing estimate with the saved H1 fit. | The characteristic excitation scale is about 11.64 eV. |
| 2. Describe the continuous fit | Compare the initial and final densities and locate the final main peak at half height. | The fitted interval is about 11.538–11.735 eV under this representation. Much of the width was present at initialisation. |
| 3. Test a prescribed four-position pattern | Use the saved fixed-framework probes. Compare four points with a same-mean single point, then compare four points with two points at the same mean and variance. | Record which current differences are shared by the dispersed candidates and which depend on their shape. |
| 4. Assess resolution | Inspect the saved component-count scans and compare fits across the two allowed energy intervals. | Explain how merging components and changes with the allowed interval limit the inference of individual energies. Propose an additional measurement for one ambiguity. |

Steps 3 and 4 use the [public discrete diagnostics](discrete_diagnostics.md) on
the original archive. The four-point probes are prescribed comparison patterns;
their spacings are set by the probe design. The four tabulated argon reference
energies are available for a separate comparison with the fitted interval. All
core activities can use saved results. [Reproduction](reproduction.md) explains
replay and the optional fitting workflow.

## Supporting exercises

## 1. Predict a current signature

Use repeated excitation at a characteristic energy to predict recurring
current minima. Estimate valley spacings, follow changes with retarding
voltage, and explain how excitation changes the transmitted electron flux.
Distinguish atomic excitation energy from remaining longitudinal electron
kinetic energy.

## 2. Combine successive excitation energies

For two equally probable energies of 11 and 13 eV, two collisions give 22,
24, and 26 eV with probabilities 0.25, 0.50, and 0.25. Explain the two orders
that produce the middle term. Connect these combinations to convolution
powers, the broadened response, the current modulation, and collection.

## 3. Track the saved stages

Menu mode 1 replays H1 and the six adopted continuous-distribution stages.
Identify fixed and updated parameters. Separate inherited features from
quantities computed after fitting. Menu mode 2 redraws their current and
energy-distribution figures. Mode 4 adds the saved discrete-channel replay
and fixed-framework probes; see
[discrete diagnostics](discrete_diagnostics.md).

## 4. Calculate summaries and compare with spectroscopy

Integrate the initial and final distributions to calculate normalization,
mean, SD, peak energy, half-maximum interval, and probability in the 4s range.
Use the original calculation grid for the reported peak. Compare changes
with the saved physical summaries and the four discrete reference energies.
Explain which features were already introduced at initialization. Distinguish
interval probability, atomic population, and a parameter confidence interval.

## 5. Interpret the two widths

Express excitation losses as voltages. Derive n times the single-collision
variance plus the common Gaussian variance. Compare this with using the same random
excitation energy n times, which gives an n-squared dependence. Propose a
measurement that helps distinguish energy spread and current broadening.
Mode 3 continues the adopted fitting sequence.

For the historical four-energy example, see [H4s comparison](optional_h4s.md).
The final task is to link each interpretation to measured currents, model
assumptions, or external spectroscopic knowledge.
