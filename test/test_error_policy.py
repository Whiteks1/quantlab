import json
import sys
import subprocess

import pytest

from quantlab.errors import ConfigError, DataError, StrategyError


def run_main(args):
    return subprocess.run(
        [sys.executable, "main.py"] + args,
        capture_output=True,
        text=True,
    )


def test_invalid_json_request_returns_exit_2():
    result = run_main(["--json-request", "{invalid_json}"])
    assert result.returncode == 2
    assert "ERROR:" in result.stderr


def test_unknown_json_command_returns_exit_2():
    req = json.dumps({
        "schema_version": "1.0",
        "command": "invalid_cmd",
        "params": {},
    })
    result = run_main(["--json-request", req])
    assert result.returncode == 2
    assert "Unknown command" in result.stderr