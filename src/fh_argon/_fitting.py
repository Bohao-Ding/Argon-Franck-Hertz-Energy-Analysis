"""The adopted saved-H1 continuation, with explicit input and output paths.

Functions do no work until called. Optimizer equations, budgets, state names,
and recorded numerical diagnostics follow the preserved calculation.
"""
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from scipy.optimize import minimize
from .response import make_model, raw_values, load_parameters, set_coefficients, distribution
from ._compat import model
from ._compat.spectral_models import simplex
from ._compat.spectral_revision import revision_grid

def fit_initial(data_path: Path, starting_h1: Path, scales_path: Path, output: Path):
    torch.set_num_threads(1)
    HERE = output
    source = starting_h1
    receipt = json.loads((source / "fit.json").read_text())
    frame = model.read_excel_or_csv(data_path)
    cid, rcol, acol, icol = [model.pick_col(frame, names) for names in (
        ("curve_id", "curveID", "curve", "id"), ("Vr", "vr", "V_r", "Ur"),
        ("Va", "va", "V_a", "Ua"), ("IuA", "Ip", "I", "current"))]
    curves = [g.sort_values(acol) for _, g in frame.groupby(cid, sort=True)
              if float(g[rcol].iloc[0]) in (0, 4, 6, 8)]
    va, vr, y = [torch.tensor(np.stack([g[col].to_numpy(np.float32) for g in curves]),
                             dtype=torch.float64) for col in (acol, rcol, icol)]
    idx = torch.arange(4)
    manifest = json.loads(scales_path.read_text())
    scale = torch.tensor(manifest["training_current_ranges_uA"], dtype=torch.float64)[:, None]
    objective_scale = scale
    rows, predictions, per_curve, solvers = [], [], [], []


    def mse(net, weights=None):
        return ((net(va, vr, idx, "curve", weights)-y)/objective_scale).square().mean()


    def differences(before, after, names):
        return {name: float(np.abs(np.asarray(after[name])-np.asarray(before[name])).max(initial=0))
                for name in names}


    def save_stage(net, name, spec):
        directory = HERE / name
        directory.mkdir(exist_ok=True)
        with torch.no_grad():
            pred = net(va, vr, idx, "curve")
            residual = pred-y
            physical = {key: float(value) for key, value in net.phys_params().items()}
            row = dict(stage=name, normalized_mse=float((residual/scale).square().mean()),
                       raw_mse_uA2=float(residual.square().mean()), **distribution(net))
        rows.append(row)
        (directory / "fit.json").write_text(json.dumps(dict(spec=spec, metrics=row,
            raw_parameter_values=raw_values(net), physical_parameters=physical), indent=2), encoding="utf-8")
        torch.save(net.state_dict(), directory / "best.pt")
        for i in range(4):
            per_curve.append(dict(stage=name, Vr_V=float(vr[i, 0]),
                normalized_mse=float((residual[i]/scale[i]).square().mean()),
                raw_mse_uA2=float(residual[i].square().mean())))
            predictions.extend(dict(stage=name, Vr_V=float(vr[i,j]), Va_V=float(va[i,j]),
                observed_uA=float(y[i,j]), fitted_uA=float(pred[i,j]),
                scale_uA=float(scale[i,0])) for j in range(y.shape[1]))
        if net.family == "C":
            pd.DataFrame(dict(energy_eV=net.energy_grid.numpy(), density_per_eV=net.density().detach().numpy()
                             )).to_csv(directory / "density.csv", index=False, lineterminator="\n")
            pd.DataFrame(dict(coefficient=simplex(net.spectral_logits).detach().numpy())).to_csv(
                directory / "coefficients.csv", index=False, lineterminator="\n")
        pd.DataFrame(rows).to_csv(HERE / "summary.csv", index=False, lineterminator="\n")
        print("STAGE", json.dumps(row), flush=True)


    def framework_fit(net, name, names):
        started = time.monotonic()
        for key, parameter in net.named_parameters():
            parameter.requires_grad_(key in names)
        parameters = [p for key,p in net.named_parameters() if key in names]
        best_loss, best, calls = float(mse(net).detach()), raw_values(net), 0
        optimizer = torch.optim.LBFGS(parameters, lr=1, max_iter=1000,
            tolerance_grad=1e-9, tolerance_change=1e-14, line_search_fn="strong_wolfe")
        def closure():
            nonlocal best_loss, best, calls
            optimizer.zero_grad(set_to_none=True)
            loss = mse(net)
            loss.backward()
            calls += 1
            if float(loss.detach()) < best_loss:
                best_loss, best = float(loss.detach()), raw_values(net)
            return loss
        optimizer.step(closure)
        load_parameters(net, best)
        loss = mse(net)
        gradients = torch.autograd.grad(loss, parameters)
        result = dict(stage=name, optimizer="LBFGS strong_wolfe", calls=calls,
            iterations=int(optimizer.state[parameters[0]].get("n_iter", 0)), cap=1000,
            gradient_max=max(float(g.abs().max()) for g in gradients),
            optimized_mse=float(loss.detach()), trained_parameters=names,
            seconds=time.monotonic()-started)
        solvers.append(result)
        print("OPTIMIZER", json.dumps(result), flush=True)


    h1 = make_model(receipt["spec"])
    h1.load_state_dict(torch.load(source / "best.pt", map_location="cpu", weights_only=True))
    live_h1 = [name for name,p in h1.named_parameters() if p.requires_grad and p.numel()]
    external = [name for name in live_h1 if name != "spectral_mu"]
    save_stage(h1, "S0_saved_regularized_H1", receipt["spec"])
    framework_fit(h1, "S1_H1_pure_mse", live_h1)
    save_stage(h1, "S1_H1_pure_mse", receipt["spec"])

    spec = {**receipt["spec"], "family":"C"}
    continuous = make_model(spec)
    load_parameters(continuous, raw_values(h1))
    x, q, basis, _, _, _ = revision_grid((9.,16.), .1, .025)
    means = (x*q)@basis
    energy = distribution(h1)["mean_eV"]
    right = int(np.clip(np.searchsorted(means, energy), 1, len(means)-1))
    fraction = (energy-means[right-1])/(means[right]-means[right-1])
    initial = np.zeros(len(means))
    initial[right-1:right+1] = [1-fraction, fraction]
    set_coefficients(continuous, initial)
    save_stage(continuous, "S2_C_replacement", spec)
    before_density = raw_values(continuous)
    for parameter in continuous.parameters():
        parameter.requires_grad_(False)
    best_loss, best_weights = float(mse(continuous).detach()), simplex(continuous.spectral_logits).detach().numpy()
    started = time.monotonic()


    def density_objective(values):
        nonlocal best_loss, best_weights
        weights = torch.tensor(values, dtype=torch.float64, requires_grad=True)
        loss = mse(continuous, weights)
        gradient = torch.autograd.grad(loss, weights)[0]
        value = float(loss.detach())
        if values.min() >= 0 and abs(values.sum()-1) < 1e-7 and value < best_loss:
            best_loss, best_weights = value, values.copy()
        return 1000*value, 1000*gradient.detach().numpy()


    result = minimize(density_objective, best_weights, jac=True, method="SLSQP",
        bounds=[(0,1)]*len(best_weights),
        constraints=dict(type="eq", fun=lambda w:w.sum()-1, jac=lambda w:np.ones_like(w)),
        options=dict(maxiter=400, ftol=1e-11))
    set_coefficients(continuous, best_weights)
    solvers.append(dict(stage="S3_C_density_only", optimizer="SLSQP", iterations=int(result.nit),
        cap=400, success=bool(result.success), message=str(result.message),
        seconds=time.monotonic()-started))
    save_stage(continuous, "S3_C_density_only", spec)
    density_external_diff = differences(before_density, raw_values(continuous),
        [name for name in before_density if name != "spectral_logits"])
    before_framework = raw_values(continuous)
    frozen_density = continuous.density().detach().clone()
    framework_fit(continuous, "S4_C_framework_only", external)
    save_stage(continuous, "S4_C_framework_only", spec)
    freeze_checks = dict(external_differences_during_density=density_external_diff,
        coefficients_max_change_during_framework=differences(before_framework,
            raw_values(continuous), ["spectral_logits"])["spectral_logits"],
        density_max_change_during_framework=float((continuous.density()-frozen_density).abs().max()),
        external_changes_during_framework=differences(before_framework, raw_values(continuous), external))

    framework_fit(h1, "S5_H1_matched_continuation", external)
    save_stage(h1, "S5_H1_matched_continuation", receipt["spec"])
    pd.DataFrame(per_curve).to_csv(HERE / "per_curve.csv", index=False, lineterminator="\n")
    pd.DataFrame(predictions).to_csv(HERE / "predictions.csv", index=False, lineterminator="\n")
    (HERE / "solvers.json").write_text(json.dumps(solvers, indent=2), encoding="utf-8")
    (HERE / "freeze_checks.json").write_text(json.dumps(freeze_checks, indent=2), encoding="utf-8")

def continue_distribution(stages: Path, arm: str):
    torch.set_num_threads(1)
    HERE = stages
    adamw_final = arm == "raw_from_normalized_adamw"
    source = HERE if arm == "normalized" else HERE / "raw_mse_objective"
    source_stage = "S4_C_framework_only"
    if arm in ("raw_from_normalized", "raw_from_normalized_adamw"):
        source = HERE / "extended_normalized"
        source_stage = "S3_C_density_refined"
    output = HERE / ("extended_"+arm)
    output.mkdir(exist_ok=True)
    # These are the archived measured observations, not model-generated targets.
    observed = pd.read_csv(source / "predictions.csv")
    observed = observed[observed.stage == source_stage].sort_values(["Vr_V", "Va_V"])
    va, vr, y, scale = [torch.tensor(observed[col].to_numpy().reshape(4,161), dtype=torch.float64)
                        for col in ("Va_V", "Vr_V", "observed_uA", "scale_uA")]
    idx = torch.arange(4)
    fit = json.loads((source / source_stage / "fit.json").read_text())
    net = make_model(fit["spec"])
    net.load_state_dict(torch.load(source / source_stage / "best.pt", weights_only=True))
    external = [name for name,p in net.named_parameters()
                if p.requires_grad and p.numel() and name != "spectral_logits"]
    summary, per_curve, predictions, history, solvers = [], [], [], [], []


    def errors(weights=None):
        residual = net(va, vr, idx, "curve", weights)-y
        normalized = (residual/scale).square().mean()
        raw = residual.square().mean()
        return (normalized if arm == "normalized" else raw), normalized, raw


    def save_stage(name):
        directory = output / name
        directory.mkdir(exist_ok=True)
        with torch.no_grad():
            loss, normalized, raw = errors()
            row = dict(stage=name, objective=float(loss), normalized_mse=float(normalized),
                       raw_mse_uA2=float(raw), **distribution(net))
            pred = net(va, vr, idx, "curve")
            physical = {key:float(value) for key,value in net.phys_params().items()}
        summary.append(row)
        (directory / "fit.json").write_text(json.dumps(dict(spec=fit["spec"], metrics=row,
            raw_parameter_values=raw_values(net), physical_parameters=physical), indent=2), encoding="utf-8")
        torch.save(net.state_dict(), directory / "best.pt")
        pd.DataFrame(dict(energy_eV=net.energy_grid.numpy(), density_per_eV=net.density().detach().numpy()
                         )).to_csv(directory / "density.csv", index=False, lineterminator="\n")
        pd.DataFrame(dict(coefficient=simplex(net.spectral_logits).detach().numpy())).to_csv(
            directory / "coefficients.csv", index=False, lineterminator="\n")
        for i in range(4):
            residual = pred[i]-y[i]
            per_curve.append(dict(stage=name, Vr_V=float(vr[i,0]),
                normalized_mse=float((residual/scale[i]).square().mean()),
                raw_mse_uA2=float(residual.square().mean())))
            predictions.extend(dict(stage=name, Vr_V=float(vr[i,j]), Va_V=float(va[i,j]),
                observed_uA=float(y[i,j]), fitted_uA=float(pred[i,j]), scale_uA=float(scale[i,j]))
                for j in range(161))
        for filename, records in (("summary.csv",summary), ("per_curve.csv",per_curve),
                                  ("predictions.csv",predictions), ("training_history.csv",history)):
            pd.DataFrame(records).to_csv(output / filename, index=False, lineterminator="\n")
        print(arm, "STAGE", json.dumps(row), flush=True)


    save_stage("S0_C_previous_framework")
    for name,p in net.named_parameters():
        p.requires_grad_(name in external)
    parameters = [p for name,p in net.named_parameters() if name in external]
    frozen_logits = net.spectral_logits.detach().clone()
    frozen_density = net.density().detach().clone()
    best_loss, best = float(errors()[0].detach()), raw_values(net)
    started = time.monotonic()


    def consider(stage, iteration, loss, normalized, raw):
        nonlocal best_loss, best
        value = float(loss.detach())
        if value < best_loss:
            best_loss, best = value, raw_values(net)
        history.append(dict(stage=stage, iteration=iteration, objective=value,
            normalized_mse=float(normalized.detach()), raw_mse_uA2=float(raw.detach())))


    optimizer = (torch.optim.AdamW(parameters, lr=.0002, eps=1e-10, weight_decay=0)
                 if adamw_final else torch.optim.Adam(parameters, lr=.0002, eps=1e-10))
    optimizer_name = "AdamW" if adamw_final else "Adam"
    for epoch in range(1,5001):
        optimizer.zero_grad(set_to_none=True)
        loss, normalized, raw = errors()
        consider("framework_"+optimizer_name, epoch, loss, normalized, raw)
        loss.backward()
        optimizer.step()
        if epoch % 1000 == 0:
            print(arm, "EPOCH", epoch, "best objective", best_loss, flush=True)
    loss, normalized, raw = errors()
    consider("framework_"+optimizer_name, 5001, loss, normalized, raw)
    load_parameters(net, best)
    solvers.append(dict(stage="framework_"+optimizer_name, epochs=5000, lr=.0002,
        weight_decay=0, eps=1e-10,
        best_objective=best_loss, seconds=time.monotonic()-started))
    save_stage("S1_C_extended_"+optimizer_name)
    started = time.monotonic()
    optimizer = torch.optim.LBFGS(parameters, lr=1, max_iter=1000,
        tolerance_grad=1e-9, tolerance_change=1e-14, line_search_fn="strong_wolfe")
    calls = 0


    def closure():
        nonlocal calls
        optimizer.zero_grad(set_to_none=True)
        loss, normalized, raw = errors()
        calls += 1
        consider("framework_LBFGS", calls, loss, normalized, raw)
        loss.backward()
        return loss


    if not adamw_final:
        optimizer.step(closure)
    load_parameters(net, best)
    gradients = torch.autograd.grad(errors()[0], parameters)
    solvers.append(dict(stage="framework_finish", optimizer="AdamW" if adamw_final else "LBFGS",
        calls=calls, iterations=int(optimizer.state[parameters[0]].get("n_iter",0)),
        cap=0 if adamw_final else 1000, gradient_max=max(float(g.abs().max()) for g in gradients),
        seconds=time.monotonic()-started))
    save_stage("S2_C_extended_framework")
    freeze = dict(logits_max_change_during_extended_framework=float((net.spectral_logits-frozen_logits).abs().max()),
        density_max_change_during_extended_framework=float((net.density()-frozen_density).abs().max()))
    before = raw_values(net)
    for p in net.parameters():
        p.requires_grad_(False)
    best_weights = simplex(net.spectral_logits).detach().numpy()
    best_loss = float(errors()[0].detach())
    calls = 0
    started = time.monotonic()


    def density_objective(values):
        nonlocal best_loss, best_weights, calls
        weights = torch.tensor(values, dtype=torch.float64, requires_grad=True)
        loss, normalized, raw = errors(weights)
        gradient = torch.autograd.grad(loss, weights)[0]
        calls += 1
        value = float(loss.detach())
        if values.min() >= 0 and abs(values.sum()-1) < 1e-7 and value < best_loss:
            best_loss, best_weights = value, values.copy()
        history.append(dict(stage="density_SLSQP", iteration=calls, objective=value,
            normalized_mse=float(normalized.detach()), raw_mse_uA2=float(raw.detach())))
        return 1000*value, 1000*gradient.detach().numpy()


    if adamw_final:
        weights = torch.nn.Parameter(torch.tensor(best_weights, dtype=torch.float64))
        optimizer = torch.optim.AdamW([weights], lr=.00002, eps=1e-10, weight_decay=0)
        for epoch in range(1,5001):
            optimizer.zero_grad(set_to_none=True)
            loss, normalized, raw = errors(weights)
            if float(loss.detach()) < best_loss:
                best_loss, best_weights = float(loss.detach()), weights.detach().numpy().copy()
            history.append(dict(stage="density_AdamW", iteration=epoch, objective=float(loss.detach()),
                normalized_mse=float(normalized.detach()), raw_mse_uA2=float(raw.detach())))
            loss.backward()
            optimizer.step()
            # Euclidean projection onto the nonnegative unit simplex.
            with torch.no_grad():
                ordered = weights.sort(descending=True).values
                cumulative = ordered.cumsum(0)-1
                rank = torch.arange(1,len(weights)+1,dtype=weights.dtype)
                count = int((ordered-cumulative/rank > 0).sum())
                weights.copy_((weights-cumulative[count-1]/count).clamp_min(0))
            if epoch % 1000 == 0:
                print(arm,"DENSITY EPOCH",epoch,"best objective",best_loss,flush=True)
        loss, normalized, raw = errors(weights)
        if float(loss.detach()) < best_loss:
            best_loss, best_weights = float(loss.detach()), weights.detach().numpy().copy()
        history.append(dict(stage="density_AdamW", iteration=5001, objective=float(loss.detach()),
            normalized_mse=float(normalized.detach()), raw_mse_uA2=float(raw.detach())))
        solvers.append(dict(stage="density_AdamW", epochs=5000, lr=.00002, eps=1e-10,
            weight_decay=0, constraint="Euclidean projection onto unit simplex after each step",
            seconds=time.monotonic()-started))
    else:
        result = minimize(density_objective, best_weights, jac=True, method="SLSQP",
            bounds=[(0,1)]*len(best_weights),
            constraints=dict(type="eq", fun=lambda w:w.sum()-1, jac=lambda w:np.ones_like(w)),
            options=dict(maxiter=400, ftol=1e-11))
        solvers.append(dict(stage="density_SLSQP", calls=calls, iterations=int(result.nit), cap=400,
            success=bool(result.success), message=str(result.message), seconds=time.monotonic()-started))
    set_coefficients(net, best_weights)
    after = raw_values(net)
    freeze["external_differences_during_density_refinement"] = {
        name:float(np.abs(np.asarray(after[name])-np.asarray(value)).max(initial=0))
        for name,value in before.items() if name != "spectral_logits"}
    save_stage("S3_C_density_refined")
    (output / "solvers.json").write_text(json.dumps(solvers, indent=2), encoding="utf-8")
    (output / "freeze_checks.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
