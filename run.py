"""Choose a manuscript reproduction task without command-line arguments."""
from datetime import datetime
from importlib.util import find_spec
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
PYTHON_PACKAGES = ("numpy", "pandas", "scipy", "torch", "openpyxl")


def main() -> int:
    print("Argon Franck-Hertz Energy Analysis")
    print("1. Replay saved parameters and calculate distribution summaries")
    print("2. Render manuscript figures with R/ggplot2")
    print("3. Continue the adopted fitting sequence from the saved H1 starting parameters")
    print("0. Exit")
    while True:
        try:
            choice = input("Choose a mode [0-3]: ").strip()
        except EOFError:
            return 0
        if choice in ("0", "1", "2", "3"):
            break
        print("Enter 0, 1, 2, or 3.")
    if choice == "0":
        return 0

    if choice in ("1", "3"):
        missing = [name for name in PYTHON_PACKAGES if find_spec(name) is None]
        if missing:
            print("Missing Python packages: " + ", ".join(missing))
            print("Use an existing compatible environment; see the README environment checklist.")
            return 1
        for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
            os.environ[name] = "1"
        from fh_argon.workflows import replay, refit
        action = replay if choice == "1" else refit
    else:
        from fh_argon.plotting import PlottingError, render
        action = render

    mode = {"1": "replay", "2": "figures", "3": "refit"}[choice]
    output = ROOT / "outputs" / f"{datetime.now():%Y%m%d_%H%M%S_%f}_{mode}"
    print("Output: " + output.relative_to(ROOT).as_posix())
    if choice == "2":
        try:
            action(output)
        except PlottingError as error:
            print(str(error))
            return 1
    else:
        action(output)
    print("Completed. Saved input and reference files were not overwritten.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped by the user; any partial output is retained.")
        raise SystemExit(130)
    except ModuleNotFoundError as error:
        print(f"A required Python module is unavailable: {error.name}.")
        print("Check the selected environment against the README dependency list.")
        raise SystemExit(1)
    except Exception as error:
        print(f"The selected task could not finish ({type(error).__name__}).")
        print("Check the input/reference files and dependency versions; partial output is retained.")
        raise SystemExit(1)
