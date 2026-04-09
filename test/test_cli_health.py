from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_main(args):
    return subprocess.run(
        [sys.executable, "main.py"] + args,
        capture_output=True,
        text=True,
    )


def run_module(args):
    return subprocess.run(
        [sys.executable, "-m", "quantlab"] + args,
        capture_output=True,
        text=True,
    )


def test_version():
    result = run_main(["--version"])
    assert result.returncode == 0
    assert result.stdout.strip() == "0.1.0"


def test_check():
    result = run_main(["--check"])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["quantlab_import"] is True
    assert isinstance(payload["venv_active"], bool)
    project_root = Path(payload["project_root"])
    main_path = Path(payload["main_path"])
    src_root = Path(payload["src_root"])

    assert project_root.exists()
    assert main_path == project_root / "main.py"
    assert src_root == project_root / "src"
    assert main_path.exists()
    assert src_root.exists()


def test_module_entrypoint_version():
    result = run_module(["--version"])
    assert result.returncode == 0
    assert result.stdout.strip() == "0.1.0"
