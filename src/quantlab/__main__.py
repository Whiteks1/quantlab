from pathlib import Path
import runpy
import sys


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    main_py = project_root / "main.py"

    if not main_py.exists():
        raise FileNotFoundError(f"No se encontró main.py en {main_py}")

    sys.path.insert(0, str(project_root))
    runpy.run_path(str(main_py), run_name="__main__")


if __name__ == "__main__":
    main()