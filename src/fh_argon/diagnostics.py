"""Replay the curated full-data fits and prescribed fixed-framework probes."""
import json

import numpy as np
import pandas as pd
import torch

from .channels import DiscreteChannel, FixedVarianceChannel, copy_external
from .workflows import REFERENCE, _measured_arrays, _output_directory


SAVED = REFERENCE / "discrete_diagnostics"


def _load(entry):
    fit = json.loads((SAVED / entry["parameters"]).read_text(encoding="utf-8"))
    mean = fit["metrics"]["mean_eV"]
    if entry["kind"] == "profile":
        net = FixedVarianceChannel(fit["metrics"]["channel"], fit["metrics"]["sd_eV"], fit["bounds"], mean)
    else:
        net = DiscreteChannel(fit["k"], fit["bounds"], mean)
    with torch.no_grad():
        for name, p in net.named_parameters():
            p.copy_(torch.as_tensor(fit["raw_parameter_values"][name], dtype=p.dtype))
    return net


def _summary(net):
    levels = net.level_params()
    energy, weight = (levels[key].detach().numpy() for key in ("energies", "weights"))
    mean = float(energy @ weight)
    sd = float(net.sigma) if getattr(net, "channel", None) == "uniform" else float(np.sqrt(weight @ (energy-mean)**2))
    return dict(mean_eV=mean, sd_eV=sd, response_sd_V=float(net.phys_params()["width"]))


def replay_diagnostics(output):
    output = _output_directory(output)
    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float64)
    va, vr, observed = _measured_arrays()
    x, r = torch.tensor(va), torch.tensor(vr)
    saved = pd.read_csv(SAVED / "saved_currents.csv")
    manifest = json.loads((SAVED / "manifest.json").read_text(encoding="utf-8"))
    currents, summaries, checks, nets = [], [], [], {}
    max_parameter_change = max_external_change = 0.
    with torch.no_grad():
        for entry in manifest["models"]:
            net = _load(entry)
            model_id = entry["model_id"]
            nets[model_id] = net
            before = {name: p.clone() for name, p in net.named_parameters()}
            current = net(x, r, torch.arange(4), "curve").numpy()
            expected = saved[saved.model_id == model_id].sort_values(["Vr_V", "Va_V"])
            checks.append(dict(model_id=model_id, max_saved_current_difference_uA=float(
                np.abs(current.ravel()-expected.fitted_uA.to_numpy()).max())))
            currents.append(pd.DataFrame(dict(model_id=model_id, Vr_V=vr.ravel(), Va_V=va.ravel(),
                observed_uA=observed.ravel(), fitted_uA=current.ravel())))
            summaries.append(dict(model_id=model_id, kind=entry["kind"], domain=entry["domain"], **_summary(net)))
            max_parameter_change = max(max_parameter_change, max(
                float((p-before[name]).abs().max()) for name, p in net.named_parameters() if p.numel()))

        contrasts, probe_summaries = [], []
        for domain in ("wide", "narrow"):
            h1, h4 = (nets[f"scan_{domain}_H{k}"] for k in (1, 4))
            for label, framework in (("H1", h1), ("H4", h4)):
                mean = _summary(framework)["mean_eV"]
                probes = {name: FixedVarianceChannel(channel, sd, framework.bounds, mean)
                    for name, channel, sd in (("point", "H1", 0.), ("H2_probe", "H2", .1),
                        ("H4_probe", "H4", .1), ("uniform_probe", "uniform", .1))}
                probes["learned_H4"] = DiscreteChannel(4, framework.bounds, mean)
                probes["learned_H4"].energies.copy_(h4.energies)
                probes["learned_H4"].weights.copy_(h4.weights)
                probes["learned_H4_mean"] = DiscreteChannel(1, framework.bounds, _summary(h4)["mean_eV"])
                probes["learned_H1"] = DiscreteChannel(1, framework.bounds, _summary(h1)["mean_eV"])
                predictions = {}
                for name, probe in probes.items():
                    copy_external(framework, probe)
                    parameters = dict(framework.named_parameters())
                    max_external_change = max(max_external_change, max(float((p-parameters[n]).abs().max())
                        for n, p in probe.named_parameters() if n in probe.external_names))
                    predictions[name] = probe(x, r, torch.arange(4), "curve").numpy()
                    probe_summaries.append(dict(domain=domain, framework=label, channel=name, **_summary(probe)))
                for name, a, b in (
                    ("trained_internal_shape", "learned_H4", "learned_H4_mean"),
                    ("trained_energy_swap", "learned_H4", "learned_H1"),
                    ("spread_H4_vs_point", "H4_probe", "point"),
                    ("same_variance_H4_vs_H2", "H4_probe", "H2_probe"),
                    ("same_variance_H4_vs_uniform", "H4_probe", "uniform_probe")):
                    contrasts.append(pd.DataFrame(dict(domain=domain, framework=label, comparison=name,
                        Vr_V=vr.ravel(), Va_V=va.ravel(), reference_uA=predictions[b].ravel(),
                        alternative_uA=predictions[a].ravel(), delta_uA=(predictions[a]-predictions[b]).ravel())))

    contrasts = pd.concat(contrasts, ignore_index=True)
    expected = pd.read_csv(SAVED / "probe_contrasts.csv")
    joined = contrasts.merge(expected, on=["domain", "framework", "comparison", "Vr_V", "Va_V"],
                             suffixes=("", "_saved"), validate="one_to_one")
    result = dict(models=len(checks), points_per_model=observed.size, optimization_steps=0,
        max_saved_current_difference_uA=max(row["max_saved_current_difference_uA"] for row in checks),
        probe_rows_replayed=len(joined), max_saved_probe_difference_uA=float(
            (joined.delta_uA-joined.delta_uA_saved).abs().max()),
        max_parameter_change=max_parameter_change, max_external_parameter_change=max_external_change,
        model_checks=checks, interpretation="Full-data numerical replay and prescribed probes; no new measurements or confidence intervals.")
    pd.concat(currents, ignore_index=True).to_csv(output / "diagnostic_currents.csv", index=False)
    pd.DataFrame(summaries).to_csv(output / "distribution_summaries.csv", index=False)
    pd.DataFrame(probe_summaries).to_csv(output / "probe_summaries.csv", index=False)
    contrasts.to_csv(output / "probe_contrasts.csv", index=False)
    (output / "replay_checks.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(f"Replayed {len(checks)} full-data models and {len(joined)} probe differences; no optimization.")
    print(f"Maximum saved-current difference: {result['max_saved_current_difference_uA']:.3g} microampere.")
    print(f"Maximum saved-probe difference: {result['max_saved_probe_difference_uA']:.3g} microampere.")
    return result
