"""
test_integration_deterministic.py — Automated validation of the Stepbit communication contract.
Focuses on stable, non-network-dependent failure cases (Issue #27).
"""
import subprocess
import sys
import json
import pytest

def run_main(args):
    """Helper to run main.py as a subprocess and return the result."""
    return subprocess.run(
        [sys.executable, "main.py"] + args,
        capture_output=True,
        text=True
    )

def test_config_error_malformed_json():
    """Verify exit code 2 and clean stderr for malformed JSON."""
    result = run_main(["--json-request", "{invalid_json}"])
    assert result.returncode == 2
    assert "ERROR: Invalid --json-request payload" in result.stderr
    assert "Traceback" not in result.stderr

def test_config_error_missing_command():
    """Verify exit code 2 and clean stderr for missing command."""
    req = json.dumps({"schema_version": "1.0", "params": {}})
    result = run_main(["--json-request", req])
    assert result.returncode == 2
    assert "ERROR: Missing 'command' in JSON request" in result.stderr
    assert "Traceback" not in result.stderr

def test_config_error_invalid_schema():
    """Verify exit code 2 and clean stderr for invalid schema_version."""
    req = json.dumps({"schema_version": "2.0", "command": "run", "params": {}})
    result = run_main(["--json-request", req])
    assert result.returncode == 2
    assert "ERROR: Unsupported or missing schema_version" in result.stderr
    assert "Traceback" not in result.stderr

def test_config_error_unknown_command():
    """Verify exit code 2 and clean stderr for unknown command."""
    req = json.dumps({"schema_version": "1.0", "command": "unknown_cmd", "params": {}})
    result = run_main(["--json-request", req])
    assert result.returncode == 2
    assert "ERROR: Unknown command" in result.stderr
    assert "Traceback" not in result.stderr
