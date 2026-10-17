"""Forward-only excitation channels on the shared collision response."""
import numpy as np
import torch
from torch import nn

from .response import RenewalSpectrum


class DiscreteChannel(RenewalSpectrum):
    def __init__(self, k, bounds, excitation):
        super().__init__(family="H1", excitation=excitation)
        self.bounds = tuple(bounds)
        del self.spectral_mu
        self.energies = nn.Parameter(torch.full((k,), float(excitation), dtype=torch.float64))
        self.weights = nn.Parameter(torch.full((k,), 1.0 / k, dtype=torch.float64))
        self.external_names = {name for name, p in self.named_parameters()
                               if p.requires_grad and p.numel() and name not in {"energies", "weights"}}

    def level_params(self, spectrum_weights=None):
        return dict(energies=self.energies, weights=self.weights,
                    gaps=self.energies.new_empty(0))

    def characteristic(self, levels):
        return (levels["weights"][:, None] * torch.exp(
            -1j * levels["energies"][:, None] * self.omega[None, :])).sum(0)

    def weighted_periodic_response(self, voltage, physical, levels):
        transform = self.characteristic(levels)
        power, total = transform, transform
        for _ in range(2, self.cycles + 1):
            power = power * transform
            total = total + power
        response = torch.fft.irfft(total * torch.exp(
            -.5 * (physical["width"] * self.omega).square()), n=self.fft_size) / self.loss_step
        position = ((voltage.reshape(-1) + physical["phase"]) / self.loss_step).remainder(self.fft_size)
        left = position.floor().long()
        fraction = position - left
        return (response[left] * (1-fraction) + response[(left+1) % self.fft_size] * fraction).reshape_as(voltage)


OFFSETS = {"H1": [0.], "H2": [-1., 1.],
           "H4": (np.array([-1.5, -.5, .5, 1.5]) / np.sqrt(1.25)).tolist(),
           "uniform": [-np.sqrt(3), np.sqrt(3)]}


class FixedVarianceChannel(DiscreteChannel):
    def __init__(self, channel, sd, bounds, mean):
        super().__init__(1, bounds, mean)
        self.channel = channel
        self.sigma = nn.Parameter(torch.tensor(float(sd), dtype=torch.float64), requires_grad=False)
        self.register_buffer("profile_offsets", torch.tensor(OFFSETS[channel], dtype=torch.float64))
        self.register_buffer("profile_weights", torch.full(
            (len(OFFSETS[channel]),), 1.0 / len(OFFSETS[channel]), dtype=torch.float64))

    def level_params(self, spectrum_weights=None):
        if self.channel == "uniform":
            return super().level_params()
        return dict(energies=self.energies[0] + self.sigma * self.profile_offsets,
                    weights=self.profile_weights, gaps=self.energies.new_empty(0))

    def characteristic(self, levels):
        if self.channel == "uniform":
            return torch.exp(-1j * self.omega * self.energies[0]) * torch.sinc(
                np.sqrt(3) * self.sigma * self.omega / np.pi)
        return super().characteristic(levels)


def copy_external(source, target):
    with torch.no_grad():
        for name, p in target.named_parameters():
            if name in target.external_names:
                p.copy_(dict(source.named_parameters())[name])
