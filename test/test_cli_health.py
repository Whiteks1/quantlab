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
    assert payload["venv_active"] is True
    assert Path(payload["project_root"]).name in {"quant_lab", "quantlab"}