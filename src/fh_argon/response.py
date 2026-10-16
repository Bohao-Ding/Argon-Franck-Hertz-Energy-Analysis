"""IID effective excitation energies with one unit-area Gaussian convolution."""
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from ._compat.spectral_revision import RevisedSpectrum, quantiles
from ._compat.spectral_models import simplex


class RenewalSpectrum(RevisedSpectrum):
    def __init__(self, n_curves=4, family="H1", *, excitation=12.0, knot_step=.1, step=.025):
        super().__init__(n_curves, family, seed=0, excitation=excitation, step=step,
                         knot_step=knot_step, domain=(9., 16.), phase_response=True,
                         normalization_voltage=80., fixed_width=None)
        physical = super().phys_params()
        initial = float((physical["osc_amp"]*physical["width"]).detach())*np.sqrt(2*np.pi)
        self.raw_osc_strength = nn.Parameter(torch.tensor(np.log(np.expm1(initial)), dtype=torch.float64))
        self.raw_osc_amp.requires_grad_(False)
        self.loss_step = step
        self.fft_size = round(409.6/step)
        self.cycles = 16
        self.register_buffer("omega", 2*np.pi*torch.fft.rfftfreq(self.fft_size, d=step, dtype=torch.float64))

    def phys_params(self):
        physical = super().phys_params()
        strength = F.softplus(self.raw_osc_strength)
        physical["osc_amp"] = strength  # Compatibility with the unchanged modulation readout.
        physical["osc_strength_V"] = strength
        return physical

    def weighted_periodic_response(self, voltage, physical, levels):
        if self.family == "H1":
            transform = torch.exp(-1j*self.omega*levels["energies"][0])
        else:
            start = round(self.domain[0]/self.loss_step)
            masses = F.pad(levels["weights"], (start, self.fft_size-start-len(self.energy_grid)))
            transform = torch.fft.rfft(masses)
        power = transform
        total = transform
        for _ in range(2, self.cycles+1):
            power = power*transform
            total = total+power
        response = torch.fft.irfft(total*torch.exp(-.5*(physical["width"]*self.omega).square()),
                                    n=self.fft_size)/self.loss_step
        position = ((voltage.reshape(-1)+physical["phase"])/self.loss_step).remainder(self.fft_size)
        left = position.floor().long()
        fraction = position-left
        values = response[left]*(1-fraction)+response[(left+1)%self.fft_size]*fraction
        return values.reshape_as(voltage)


def make_model(spec):
    return RenewalSpectrum(family=spec["family"], excitation=spec["excitation"],
                           knot_step=spec["knot_step"], step=spec["step"])


def raw_values(net):
    return {name: parameter.detach().numpy().tolist() for name, parameter in net.named_parameters()}


def load_parameters(net, values):
    with torch.no_grad():
        for name, parameter in net.named_parameters():
            if name in values and list(parameter.shape) == list(np.asarray(values[name]).shape):
                parameter.copy_(torch.as_tensor(values[name], dtype=parameter.dtype))


def set_coefficients(net, weights):
    positive = np.maximum(np.asarray(weights), 1e-12)
    with torch.no_grad():
        net.spectral_logits.copy_(torch.tensor(np.log(positive[:-1]/positive[-1])))


def distribution(net):
    with torch.no_grad():
        levels = net.level_params()
        energy, mass = (levels[key].numpy() for key in ("energies", "weights"))
        mean = float(energy@mass)
        result = dict(mean_eV=mean, sd_eV=float(np.sqrt(mass@(energy-mean)**2)),
            response_sd_V=float(net.phys_params()["width"]), phase_V=float(net.phys_params()["phase"]),
            phase_beta=float(net.phys_params()["phase_beta"]), mode_eV=float(energy[np.argmax(mass)]))
        if net.family == "H1":
            return result
        density = net.density().numpy()
    peak = int(np.argmax(density)); left = right = peak; half = density[peak]/2
    while left>0 and density[left-1]>=half: left -= 1
    while right<len(energy)-1 and density[right+1]>=half: right += 1
    lo = energy[left] if left==0 else np.interp(half, density[left-1:left+1], energy[left-1:left+1])
    hi = energy[right] if right==len(energy)-1 else np.interp(half, density[right:right+2][::-1], energy[right:right+2][::-1])
    qs = quantiles(energy, mass, [.05, .5, .95], density)
    return {**result, "mode_eV": float(energy[peak]), "peak_fwhm_eV": float(hi-lo),
            "q05_eV": float(qs[0]), "median_eV": float(qs[1]), "q95_eV": float(qs[2])}
