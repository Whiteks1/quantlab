from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from quantlab import __version__

MIN_PYTHON = (3, 10)


def is_venv_active() -> bool:
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    real_prefix = getattr(sys, "real_prefix", sys.prefix)
    return sys.prefix != base_prefix or sys.prefix != real_prefix


def build_health_report(
    *,
    project_root: Path,
    main_path: Path,
    src_root: Path,
    interpreter: str | None = None,
) -> dict[str, Any]:
    interpreter = interpreter or sys.executable
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    errors: list[str] = []
    quantlab_import = False
    imported_version: str | None = None

    if sys.version_info < MIN_PYTHON:
        errors.append(
            f"Python >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]} is required; "
            f"found {python_version}."
        )

    if not main_path.exists():
        errors.append(f"main.py not found at {main_path}")

    if not src_root.exists():
        errors.append(f"src root not found at {src_root}")

    try:
        import quantlab as quantlab_pkg

        quantlab_import = True
        imported_version = getattr(quantlab_pkg, "__version__", __version__)
    except Exception as exc:  # pragma: no cover - defensive path
        errors.append(f"Failed to import quantlab: {exc}")

    report = {
        "status": "ok" if not errors else "error",
        "project_root": str(project_root),
        "main_path": str(main_path),
        "src_root": str(src_root),
        "interpreter": interpreter,
        "venv_active": is_venv_active(),
        "quantlab_import": quantlab_import,
        "python_version": python_version,
        "version": imported_version or __version__,
    }
    if errors:
        report["errors"] = errors
    return report
