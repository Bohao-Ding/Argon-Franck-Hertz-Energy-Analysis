"""Replay saved results or explicitly continue the adopted fitting sequence."""
from contextlib import redirect_stdout
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ._compat import model
from .response import distribution, make_model


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "reference"
STAGES = {
    "H1": "S1_H1_pure_mse",
    "Replacement": "S2_C_replacement",
    "Density fit": "S3_C_density_only",
    "Framework fit": "S4_C_framework_only",
    "Density continuation": "extended_normalized/S3_C_density_refined",
    "Framework AdamW": "extended_raw_from_normalized_adamw/S1_C_extended_AdamW",
    "Final density": "extended_raw_from_normalized_adamw/S3_C_density_refined",
}


def _output_directory(output: Path) -> Path:
    output = Path(output).resolve()
    if output == ROOT or any(output.is_relative_to(ROOT / name)
                             for name in ("reference", "data", "src")):
        raise ValueError("Choose an output directory outside the saved data, source, and reference directories.")
    output.mkdir(parents=True, exist_ok=True)
    return output


def _measured_arrays():
    frame = model.read_excel_or_csv(ROOT / "data/FHdata.xlsx")
    columns = [model.pick_col(frame, names) for names in (
        ("curve_id", "curveID", "curve", "id"), ("Vr", "vr", "V_r", "Ur"),
        ("Va", "va", "V_a", "Ua"), ("IuA", "Ip", "I", "current"))]
    cid, rcol, acol, icol = columns
    curves = [g.sort_values(acol) for _, g in frame.groupby(cid, sort=True)
              if float(g[rcol].iloc[0]) in (0, 4, 6, 8)]
    # Preserve the original spreadsheet conversion before float64 calculation.
    return [np.stack([g[col].to_numpy(np.float32) for g in curves]).astype(float)
            for col in (acol, rcol, icol)]


def _half_maximum(energy, density):
    peak = int(np.argmax(density))
    left = right = peak
    half = density[peak] / 2
    while left > 0 and density[left - 1] >= half:
        left -= 1
    while right < len(energy) - 1 and density[right + 1] >= half:
        right += 1
    lo = energy[left] if left == 0 else np.interp(
        half, density[left - 1:left + 1], energy[left - 1:left + 1])
    hi = energy[right] if right == len(energy) - 1 else np.interp(
        half, density[right:right + 2][::-1], energy[right:right + 2][::-1])
    return float(lo), float(hi)


def _interval_probability(energy, density, lo, hi):
    interior = energy[(energy > lo) & (energy < hi)]
    points = np.r_[lo, interior, hi]
    return float(np.trapezoid(np.interp(points, energy, density), points))


def replay(output: Path):
    """Recalculate H1 and six continuous stages without running an optimizer."""
    output = _output_directory(output)
    torch.set_num_threads(1)
    _, _, measured = _measured_arrays()
    reference = pd.read_csv(REFERENCE / "tables/spectrum_reference.csv").iloc[0]
    lower, upper = reference.E1_eV, reference.E4_eV
    currents, summaries, checks, states = [], [], [], {}
    for label, relative in STAGES.items():
        directory = REFERENCE / "stages" / relative
        fit = json.loads((directory / "fit.json").read_text(encoding="utf-8"))
        net = make_model(fit["spec"])
        net.load_state_dict(torch.load(directory / "best.pt", map_location="cpu", weights_only=True))
        points = pd.read_csv(directory.parent / "predictions.csv")
        points = points[points.stage == directory.name].sort_values(["Vr_V", "Va_V"])
        va, vr, observed, saved = [points[name].to_numpy().reshape(4, 161)
                                  for name in ("Va_V", "Vr_V", "observed_uA", "fitted_uA")]
        with torch.no_grad():
            current = net(torch.tensor(va), torch.tensor(vr), torch.arange(4), "curve").numpy()
            summary = distribution(net)
        parameters = {name: value.detach().numpy().copy() for name, value in net.named_parameters()}
        states[label] = parameters
        check = {
            "stage": label,
            "points": int(observed.size),
            "checkpoint_vs_saved_current_max_uA": float(np.abs(current - saved).max()),
            "observed_vs_workbook_max_uA": float(np.abs(observed - measured).max()),
            "checkpoint_vs_parameter_json_max": max(
                float(np.abs(value - np.asarray(fit["raw_parameter_values"][name])).max(initial=0))
                for name, value in parameters.items()),
            "mean_eV": summary["mean_eV"],
        }
        checks.append(check)
        currents.append(pd.DataFrame({
            "stage": label, "Vr_V": vr.ravel(), "Va_V": va.ravel(),
            "observed_uA": observed.ravel(), "fitted_uA": current.ravel(),
            "saved_fitted_uA": saved.ravel(),
        }))
        if net.family == "C":
            with torch.no_grad():
                energy = net.energy_grid.numpy()
                density = net.density().numpy()
            lo, hi = _half_maximum(energy, density)
            summaries.append({
                "stage": label, **summary,
                "density_integral": float(density @ net.quadrature.numpy()),
                "density_min_per_eV": float(density.min()),
                "fwhm_lower_eV": lo, "fwhm_upper_eV": hi,
                "mass_in_4s_interval": _interval_probability(energy, density, lower, upper),
            })
    freezes = {}
    for left, right, spectrum in (
        ("Replacement", "Density fit", False),
        ("Density fit", "Framework fit", True),
        ("Density continuation", "Framework AdamW", True),
        ("Framework AdamW", "Final density", False),
    ):
        freezes[f"{left} -> {right}"] = max(
            float(np.abs(value - states[right][name]).max(initial=0))
            for name, value in states[left].items()
            if (name == "spectral_logits") == spectrum)
    result = {
        "current_points": sum(check["points"] for check in checks),
        "continuous_stages": len(summaries),
        "max_saved_current_difference_uA": max(
            check["checkpoint_vs_saved_current_max_uA"] for check in checks),
        "max_observed_workbook_difference_uA": max(
            check["observed_vs_workbook_max_uA"] for check in checks),
        "frozen_parameter_max_changes": freezes,
        "stage_checks": checks,
        "final_distribution": summaries[-1],
        "files": ["replayed_currents.csv", "distribution_summaries.csv", "replay_checks.json"],
        "interpretation": "Numerical replay of saved fits; not independent measurements or confidence intervals.",
    }
    pd.concat(currents, ignore_index=True).to_csv(output / "replayed_currents.csv", index=False)
    pd.DataFrame(summaries).to_csv(output / "distribution_summaries.csv", index=False)
    (output / "replay_checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Replayed H1 and six continuous stages: {result['current_points']} current values.")
    print(f"Maximum difference from saved currents: {result['max_saved_current_difference_uA']:.3g} microampere.")
    final = summaries[-1]
    print(f"Final distribution: mean {final['mean_eV']:.8f} eV; peak {final['mode_eV']:.3f} eV; "
          f"SD {final['sd_eV']:.8f} eV; FWHM {final['peak_fwhm_eV']:.8f} eV.")
    print(f"Half-maximum interval: {final['fwhm_lower_eV']:.8f}--{final['fwhm_upper_eV']:.8f} eV; "
          f"probability between first and fourth 4s references: {final['mass_in_4s_interval']:.8f}.")
    return result


def refit(output: Path):
    """Continue the three adopted blocks from the saved H1, leaving references intact."""
    from ._fitting import continue_distribution, fit_initial

    output = _output_directory(output)
    stages = output / "stages"
    stages.mkdir(exist_ok=False)
    print("Continuing from the saved H1 starting parameters; optimization records go to refit.log.")
    with (output / "refit.log").open("w", encoding="utf-8") as log, redirect_stdout(log):
        fit_initial(ROOT / "data/FHdata.xlsx", REFERENCE / "starting_h1",
                    REFERENCE / "current_scales.json", stages)
        continue_distribution(stages, "normalized")
        continue_distribution(stages, "raw_from_normalized_adamw")
    result = {"stages_directory": "stages", "log": "refit.log"}
    print("The adopted fitting sequence has finished; saved reference results were not overwritten.")
    return result
