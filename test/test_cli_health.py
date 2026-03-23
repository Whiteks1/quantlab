from __future__ import annotations

import json
import subprocess
import sys


def run_main(args):
    return subprocess.run(
        [sys.executable, "main.py"] + args,
        capture_output=True,
        text=True,
    )


def test_version_prints_stable_project_version():
    result = run_main(["--version"])

    assert result.returncode == 0
    assert result.stdout.strip() == "0.1.0"
    assert result.stderr == ""


def test_check_prints_stable_health_report():
    result = run_main(["--check"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["version"] == "0.1.0"
    assert payload["quantlab_import"] is True
    assert payload["interpreter"] == sys.executable
    assert payload["project_root"].endswith("quant_lab")
    assert payload["main_path"].endswith("quant_lab\\main.py") or payload["main_path"].endswith("quant_lab/main.py")
