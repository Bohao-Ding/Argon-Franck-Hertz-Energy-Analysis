"""Replay the local affine excitation comparison on CPU, without refitting."""
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path
import time

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.signal import find_peaks, savgol_filter
import torch

from .channels import DiscreteChannel
from .response import RenewalSpectrum, load_parameters

PROJECT = Path(__file__).resolve().parents[2]
LEVELS = np.array([11.54835442, 11.62359272, 11.72316039, 11.82807116])
MU, SD = float(LEVELS.mean()), float(LEVELS.std())


def write(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def save(path, record):
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def cycle_features(x, y, kind, width, boundaries=None):
    if boundaries is None:
        step = max(.25, float(np.median(np.diff(x))))
        grid = np.linspace(x[0], x[-1], int(np.ceil(np.ptp(x) / step)) + 1)
        step = float(grid[1] - grid[0])
        window = max(3, int(np.ceil(width / step)) | 1)
        smoothed = savgol_filter(PchipInterpolator(x, y)(grid), window, 2)
        if kind == "valley":
            smoothed = -smoothed
        peaks, _ = find_peaks(smoothed, prominence=.03 * np.ptp(y), distance=max(1, int(7 / step)))
        edges = grid[peaks]
    else:
        edges = np.asarray(boundaries)

    features = {}
    for cycle, (left, right) in enumerate(zip(edges[:-1], edges[1:])):
        inside = (x >= left) & (x < right)
        voltage, current = x[inside], y[inside]
        if len(voltage) < 2:
            continue
        period = right - left
        max_gap = max(np.diff(np.r_[left, voltage, right]))
        harmonics = min(3, (len(voltage) - 6) // 2, int(np.ceil(period / (2 * max_gap)) - 1))
        if harmonics < 1:
            continue
        position = (voltage - left) / period
        columns = [np.ones(len(position)), position - .5]
        for harmonic in range(1, harmonics + 1):
            angle = 2 * np.pi * harmonic * position
            columns.extend([np.cos(angle), np.sin(angle)])
        spacing = np.diff(voltage)
        weights = np.r_[spacing[0] / 2, (spacing[:-1] + spacing[1:]) / 2, spacing[-1] / 2]
        root_weight = np.sqrt(weights)
        coefficients = np.linalg.lstsq(np.column_stack(columns) * root_weight[:, None],
                                       current * root_weight, rcond=None)[0]
        values = coefficients[2::2] - 1j * coefficients[3::2]
        amplitude, phase = np.abs(values), np.angle(values)
        for harmonic in range(2, harmonics + 1):
            index = harmonic - 1
            if min(amplitude[0], amplitude[index]) <= np.finfo(float).eps * max(np.ptp(current), 1.):
                continue
            features[cycle, harmonic] = (
                float(np.log(amplitude[index] / amplitude[0])),
                float(wrap(phase[index] - harmonic * phase[0])),
            )
    return features, edges.tolist()


def rss(error):
    return float(error @ error)


def wrap(x):
    return np.angle(np.exp(1j*x))


def replay_affine(output):
    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    began, cpu = time.monotonic(), time.process_time()
    input_path = PROJECT / "data/observed.csv"
    data = np.loadtxt(input_path, delimiter=",", skiprows=1)
    fit_path = PROJECT / "reference/stages/S1_H1_pure_mse/fit.json"
    fit = json.loads(fit_path.read_text(encoding="utf-8"))
    parameters = fit["raw_parameter_values"]
    fitted = RenewalSpectrum(n_curves=4, family="H1", excitation=12.)
    load_parameters(fitted, parameters)
    fitted_center = float(fitted.level_params()["energies"][0].detach())
    offsets = {"S": np.array([0.]), "F": LEVELS - MU, "B2": np.array([-SD, SD])}
    models = {label: DiscreteChannel(count, (9., 16.), fitted_center)
              for label, count in (("S", 1), ("F", 4), ("B2", 2))}
    for model in models.values():
        load_parameters(model, parameters)

    anchors = {"absolute": (0., 1.), "centered": (fitted_center - MU, 1.)}
    shifts = sorted(set(np.linspace(-.10,.10,21).tolist() + [anchors["centered"][0]]))
    stretches = np.linspace(.95,1.05,11)
    settings = list(itertools.product(("peak","valley"),(1.,2.,4.)))
    config = dict(model="archived H1 response; fixed external parameters", input=str(input_path.relative_to(PROJECT)),
                  fit=str(fit_path.relative_to(PROJECT)), cpu_threads=torch.get_num_threads(), device="cpu", base_levels_eV=LEVELS.tolist(),
                  base_mean_eV=MU, fitted_center_eV=fitted_center, energy_transform="mean + shift + stretch*(level-mean)",
                  shifts_eV=shifts, stretches=stretches.tolist(), anchors=anchors,
                  selection_current="minimize mean F current RSS divided by archived H1 RSS on 0/4/6 V",
                  selection_8V_exploratory="maximize the worse 8 V valley-to-valley F gain at 1 V smoothing",
                  transfer="8 V (seen in archived H1 response fit), 10 V (8 V nuisance or neutral extrapolation)",
                  feature_settings=settings)
    save(output/"protocol.json",config)
    current_rows, feature_rows, predictions = [], [], []
    for vr, mode in [(0,"curve"),(4,"curve"),(6,"curve"),(8,"curve"),(10,"curve"),(10,"neutral")]:
        sel = data[:,0]==vr
        x,y = data[sel,1],data[sel,2]
        assert len(x)==161 and np.allclose(np.diff(x),.5)
        va=torch.tensor(x,dtype=torch.float64)
        retard=torch.full_like(va,vr)
        idx=torch.tensor((0,4,6,8).index(vr) if vr!=10 else 3,dtype=torch.int64)
        observed = {setting: cycle_features(x,y,*setting) for setting in settings}
        def predict(center,stretch,label):
            model = models[label]
            model.energies.copy_(torch.as_tensor(center + stretch*offsets[label]))
            return model(va, retard, idx, mode).numpy()
        with torch.inference_mode():
            archived = fitted(va, retard, idx, mode).numpy()
            reference = predict(fitted_center, 1., "S")
            np.testing.assert_allclose(reference, archived, rtol=0, atol=1e-10)
            for shift in shifts:
                center=MU+shift
                single=predict(center,1.,"S")
                single_features={k: cycle_features(x,single,*k,observed[k][1])[0] for k in settings if observed[k][0]}
                for stretch in stretches:
                    f=predict(center,stretch,"F")
                    b=predict(center,stretch,"B2")
                    meta=dict(vr_V=vr,readout=mode,shift_eV=shift,stretch=stretch,mean_eV=center,sd_eV=SD*stretch)
                    if (shift,stretch) in anchors.values():
                        for k in range(len(x)):
                            predictions.append(dict(meta, x_V=x[k],observed_uA=y[k],S=single[k],F=f[k],B2=b[k]))
                    s_error,f_error,b_error=rss(y-single),rss(y-f),rss(y-b)
                    current_rows.append(dict(meta,S_rss=s_error,F_rss=f_error,B2_rss=b_error,H1_rss=rss(y-archived),
                                            F_gain_pct=100*(1-f_error/s_error),B2_gain_pct=100*(1-b_error/s_error),
                                            F_minus_S_rms_uA=np.linalg.norm(f-single)/np.sqrt(len(x)),
                                            F_B2_over_FS_pct=100*np.linalg.norm(f-b)/np.linalg.norm(f-single)))
                    for kind,width in settings:
                        obs,edges=observed[kind,width]
                        setting=dict(meta,kind=kind,smoothing_V=width)
                        if not obs:
                            feature_rows.append(dict(setting,components=0,status="no_supported_features"))
                            continue
                        values=[obs,single_features[kind,width],cycle_features(x,f,kind,width,edges)[0],
                                cycle_features(x,b,kind,width,edges)[0]]
                        keys=sorted(obs)
                        assert all(value.keys()==obs.keys() for value in values)
                        o,s,ff,bb=[np.array([v[k] for k in keys]) for v in values]
                        err=[o-v for v in (s,ff,bb)]
                        amp=[rss(e[:,0]) for e in err]
                        phase=[rss(wrap(e[:,1])) for e in err]
                        feature_rows.append(dict(setting,components=len(keys),status="estimated",
                                                 F_amp_pct=100*(1-amp[1]/amp[0]),B2_amp_pct=100*(1-amp[2]/amp[0]),
                                                 F_phase_pct=100*(1-phase[1]/phase[0]),B2_phase_pct=100*(1-phase[2]/phase[0])))
        print(f"Finished {vr} V {mode}",flush=True)
    write(output/"current_scores.csv",current_rows)
    write(output/"feature_scores.csv",feature_rows)
    write(output/"anchor_predictions.csv",predictions)
    summary = summarize(current_rows, feature_rows)
    save(output/"summary.json", summary)
    print("Shared setting: shift %.2f eV, spacing scale %.2f" %
          (summary["shared_shift_eV"], summary["shared_stretch"]))
    save(output/"run.json",dict(grid_pairs=len(shifts)*len(stretches),current_rows=len(current_rows),
                             feature_rows=len(feature_rows), estimated_features=sum(r["status"]=="estimated" for r in feature_rows),
                             cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-began))


def summarize(current_rows, feature_rows):
    """Select the affine setting on current errors at 0/4/6 V."""
    calibration = defaultdict(float)
    for row in current_rows:
        if row["vr_V"] in (0, 4, 6):
            pair = row["shift_eV"], row["stretch"]
            calibration[pair] += row["F_rss"] / row["H1_rss"]
    shift, stretch = min(calibration, key=calibration.get)
    shared = {"shift_eV": shift, "stretch": stretch}
    def matches(row):
        return all(row[key] == value for key, value in shared.items())
    selected = [row for row in feature_rows if matches(row) and row["smoothing_V"] == 1.]
    joint_counts = {}
    for vr, readout in dict.fromkeys((row["vr_V"], row["readout"]) for row in feature_rows):
        for kind in ("peak", "valley"):
            subsets = defaultdict(list)
            for row in feature_rows:
                if (row["vr_V"], row["readout"], row["kind"]) == (vr, readout, kind) and row["status"] == "estimated":
                    subsets[row["shift_eV"], row["stretch"]].append(row)
            joint_counts[f"{vr}V_{readout}_{kind}"] = {
                "estimable_pairs": len(subsets),
                "joint_gain_all_three_smoothing_settings": sum(
                    len(rows) == 3 and all(r["F_amp_pct"] > 0 and r["F_phase_pct"] > 0 for r in rows)
                    for rows in subsets.values()
                ),
            }
    explored = max(
        (row for row in feature_rows if row["vr_V"] == 8 and row["kind"] == "valley"
         and row["smoothing_V"] == 1. and row["status"] == "estimated"),
        key=lambda row: min(row["F_amp_pct"], row["F_phase_pct"]),
    )
    explored_current = next(
        row for row in current_rows if row["vr_V"] == 8
        and all(row[k] == explored[k] for k in ("shift_eV", "stretch"))
    )
    shape_gap = {metric: max(abs(row[f"F_{metric}_pct"] - row[f"B2_{metric}_pct"])
                             for row in feature_rows if row["status"] == "estimated")
                 for metric in ("amp", "phase")}
    return dict(shared_shift_eV=shift, shared_stretch=stretch, features_1V=selected,
                exploratory_8V_feature=explored, exploratory_8V_current=explored_current,
                max_absolute_F_B2_gain_gap_pct_points=shape_gap,
                shared_current=[row for row in current_rows if matches(row)],
                joint_gain_counts=joint_counts)
