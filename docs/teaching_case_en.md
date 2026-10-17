# From excitation hypotheses to an effective excitation energy distribution

The core activity uses atomic excitation, retarding fields, probability
densities, and numerical integration. Convolutions and refitting are advanced
extensions. See [model design](design.md) for the shared response and assumptions.

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
