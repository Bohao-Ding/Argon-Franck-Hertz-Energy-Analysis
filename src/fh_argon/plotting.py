"""Render saved-result and project figures using R sources and tables."""
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[2]
R_PACKAGES = ("ggplot2", "patchwork", "svglite", "ragg")


class PlottingError(RuntimeError):
    """A dependency or plotting problem with a portable user-facing message."""


def _rscript() -> str:
    executable = shutil.which("Rscript")
    if executable:
        return executable
    if os.environ.get("R_HOME"):
        r_home = Path(os.environ["R_HOME"])
        for relative in ("bin/Rscript.exe", "bin/x64/Rscript.exe", "bin/Rscript"):
            candidate = r_home / relative
            if candidate.is_file():
                return str(candidate)
    raise PlottingError("Rscript was not found. Reuse an existing R installation through PATH or R_HOME.")


def _run(arguments: list[str]):
    try:
        return subprocess.run(arguments, cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
    except OSError:
        raise PlottingError("Rscript could not start. Check the existing R installation.") from None


def render(output: Path):
    """Export saved-result and web figures without changing source tables."""
    executable = _rscript()
    package_names = ",".join(f'"{name}"' for name in R_PACKAGES)
    expression = (
        f"required <- c({package_names}); "
        "missing <- required[!vapply(required, requireNamespace, logical(1), quietly=TRUE)]; "
        "if(length(missing)) { cat(paste(missing, collapse='\\n')); quit(status=2) }; "
        "if(!capabilities('cairo')) quit(status=3)"
    )
    check = _run([executable, "--vanilla", "-e", expression])
    if check.returncode == 2:
        missing = [name for name in R_PACKAGES if name in check.stdout.split()]
        detail = ", ".join(missing) if missing else ", ".join(R_PACKAGES)
        raise PlottingError("R packages unavailable to Rscript: " + detail +
                            ". Make an existing compatible R library visible; nothing was installed.")
    if check.returncode == 3:
        raise PlottingError("The existing R installation lacks Cairo PDF support.")
    if check.returncode:
        raise PlottingError("The R dependency check did not finish. Check the existing R environment.")

    tables = ROOT / "reference/tables"
    required = [ROOT / "data/observed.csv"] + [tables / name for name in (
        "current_fits.csv", "density_stages.csv", "final_coefficients.csv",
        "spectrum_reference.csv", "physical_summaries.csv")]
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise PlottingError("Missing figure source tables: " + ", ".join(missing))
    figures = Path(output) / "figures"
    (figures / "assets").mkdir(parents=True, exist_ok=True)
    for script, source in (
        ("plot_data.R", ROOT / "data"),
        ("plot_results.R", tables),
        ("plot_project.R", ROOT),
    ):
        result = _run([executable, "--vanilla", str(ROOT / "figures" / script),
                       str(source), str(figures)])
        if result.returncode:
            raise PlottingError(f"Figure export did not finish ({script}). "
                                "Check the source tables and R package versions.")
    print("Exported Figures 1, 2, 3, and S1 as PDF, SVG, PNG, and TIFF.")
    print("Exported project overview, response contrasts, and broadening tradeoff as PNG and SVG.")
    return {"figures_directory": "figures"}
