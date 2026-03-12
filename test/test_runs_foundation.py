import os
import json
import math
import datetime
import shutil
from pathlib import Path
import pytest

from quantlab.runs.serializers import to_json, save_json
from quantlab.runs.run_id import generate_run_id
from quantlab.runs.run_store import RunStore
from quantlab.runs.registry import RunRegistry

# --- Testing Serializers ---

def test_json_serialization_nan_inf():
    data = {"nan": math.nan, "inf": math.inf, "neg_inf": -math.inf, "val": 10.5}
    res_str = to_json(data)
    res = json.loads(res_str)
    
    assert res["nan"] is None
    assert res["inf"] is None
    assert res["neg_inf"] is None
    assert res["val"] == 10.5

def test_json_serialization_datetime():
    dt = datetime.datetime(2026, 3, 10, 12, 0, 0)
    data = {"timestamp": dt}
    res_str = to_json(data)
    res = json.loads(res_str)
    
    assert res["timestamp"] == "2026-03-10T12:00:00"

def test_json_serialization_deterministic_keys():
    data = {"z": 1, "a": 2, "m": 3}
    res_str = to_json(data)
    # Check if 'a' comes before 'm' and 'm' before 'z' in the string
    assert res_str.find('"a"') < res_str.find('"m"') < res_str.find('"z"')

# --- Testing Run ID ---

def test_generate_run_id_format():
    rid = generate_run_id("testmode")
    parts = rid.split("_")
    # YYYYMMDD, HHMMSS, mode, hash
    assert len(parts) == 4
    assert parts[2] == "testmode"
    assert len(parts[3]) == 7

def test_generate_run_id_with_underscore_mode():
    rid = generate_run_id("test_mode")
    assert "test_mode" in rid
    assert rid.endswith(rid.split("_")[-1])
    assert len(rid.split("_")[-1]) == 7

def test_generate_run_id_deterministic():
    config = {"ticker": "BTC", "params": [1, 2, 3]}
    rid1 = generate_run_id("grid", config)
    rid2 = generate_run_id("grid", config)
    
    # Timestamps might differ if the call is slow, but the hash part should be identical
    assert rid1.split("_")[-1] == rid2.split("_")[-1]

# --- Testing Run Store ---

@pytest.fixture
def temp_outputs(tmp_path):
    base = tmp_path / "outputs"
    base.mkdir()
    return base

def test_run_store_initialization(temp_outputs):
    run_id = "20260310_120000_test_abc123"
    store = RunStore(run_id, base_dir=str(temp_outputs))
    path = store.initialize()
    
    assert path.exists()
    assert (path / "artifacts").exists()
    assert path.name == run_id

def test_run_store_writing_artifacts(temp_outputs):
    run_id = "test_run"
    store = RunStore(run_id, base_dir=str(temp_outputs))
    store.initialize()
    
    meta = {"mode": "test"}
    config = {"param": 1}
    metrics = {"return": 0.5}
    
    store.write_metadata(meta)
    store.write_config(config)
    store.write_metrics(metrics)
    
    assert (store.run_path / "metadata.json").exists()
    assert (store.run_path / "config.json").exists()
    assert (store.run_path / "metrics.json").exists()
    
    with open(store.run_path / "metadata.json", "r") as f:
        saved_meta = json.load(f)
        assert saved_meta["run_id"] == "test_run"
        assert saved_meta["mode"] == "test"

# --- Testing Registry ---

def test_run_registry_append(temp_outputs):
    reg_path = temp_outputs / "registry.csv"
    registry = RunRegistry(str(reg_path))
    
    summary1 = {"run_id": "run1", "total_return": 0.1, "mode": "grid"}
    summary2 = {"run_id": "run2", "total_return": 0.2, "mode": "grid"}
    
    registry.append_run(summary1)
    registry.append_run(summary2)
    
    all_runs = registry.get_all_runs()
    assert len(all_runs) == 2
    assert all_runs[0]["run_id"] == "run1"
    assert all_runs[1]["run_id"] == "run2"
    # Ensure floats are strings in CSV reading
    assert all_runs[0]["total_return"] == "0.1"
