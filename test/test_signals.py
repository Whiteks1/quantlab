import json
import subprocess
import sys


def run_main(args):
    proc = subprocess.run(
        [sys.executable, "main.py"] + args,
        capture_output=True,
        text=True,
    )
    if proc.stdout:
        print(f"\n--- STDOUT ---\n{proc.stdout}")
    if proc.stderr:
        print(f"\n--- STDERR ---\n{proc.stderr}")
    return proc


def test_signals_success_path(tmp_path):
    signal_file = tmp_path / "signals.jsonl"

    # Use a longer date range so indicator lookbacks do not exhaust the dataset.
    req = json.dumps(
        {
            "schema_version": "1.0",
            "command": "run",
            "params": {
                "ticker": "ETH-USD",
                "start": "2022-01-01",
                "end": "2023-12-31",
                "paper": True,
            },
        }
    )

    result = run_main(["--json-request", req, "--signal-file", str(signal_file)])

    assert result.returncode == 0, f"Process failed with exit code {result.returncode}"
    assert signal_file.exists()

    with open(signal_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) >= 2, f"Expected at least 2 signals, got {len(lines)}"

    started = json.loads(lines[0])
    assert started["event"] == "SESSION_STARTED"
    assert started["status"] == "running"
    assert started["mode"] == "run"

    completed = json.loads(lines[-1])
    assert completed["event"] == "SESSION_COMPLETED"
    assert completed["status"] == "success"
    assert "artifacts_path" in completed
    assert "report_path" in completed


def test_signals_failure_path(tmp_path):
    signal_file = tmp_path / "signals.jsonl"

    # Run a command destined to fail validation (missing schema version)
    req = json.dumps(
        {
            "command": "run",
            "params": {"ticker": "INVALID"},
        }
    )

    result = run_main(["--json-request", req, "--signal-file", str(signal_file)])

    assert result.returncode == 2  # INVALID_CONFIG
    assert signal_file.exists()

    with open(signal_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    failure = json.loads(lines[-1])
    assert failure["event"] == "SESSION_FAILED"
    assert failure["status"] == "error"
    assert failure["exit_code"] == 2
    assert failure["error_type"] == "ConfigError"
    assert "Unsupported or missing schema_version" in failure["message"]


def test_signals_request_id_propagation(tmp_path):
    signal_file = tmp_path / "signals.jsonl"
    request_id = "test_req_999"

    req = json.dumps(
        {
            "schema_version": "1.0",
            "request_id": request_id,
            "command": "run",
            "params": {
                "ticker": "ETH-USD",
                "start": "2022-01-01",
                "end": "2023-12-31",
            },
        }
    )

    run_main(["--json-request", req, "--signal-file", str(signal_file)])

    with open(signal_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            assert data["request_id"] == request_id