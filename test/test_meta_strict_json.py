import pytest
import json
import math
from pathlib import Path
from quantlab.experiments.runner import _save_reproducibility_pack

def test_meta_strict_json_handling(tmp_path):
    """
    Verify that _save_reproducibility_pack:
    1. Replaces NaN/Inf with None (null in JSON).
    2. Writes valid, strict JSON (no NaN/Infinity tokens).
    """
    out_dir = tmp_path / "run_metadata_test"
    out_dir.mkdir()
    
    config = {"ticker": "TEST"}
    
    # Force some naughty floats
    metrics_summary = [
        {
            "sharpe_simple": float('nan'),
            "total_return": float('inf'),
            "max_drawdown": float('-inf'),
            "label": "naughty_metrics"
        }
    ]
    
    _save_reproducibility_pack(
        out_dir=out_dir,
        config=config,
        mode="grid",
        metrics_summary=metrics_summary,
        config_path="unknown"
    )
    
    meta_json_path = out_dir / "metadata.json"
    assert meta_json_path.exists()
    
    # 1. Native JSON load should work (it wouldn't if Infinity/NaN were present and allow_nan=False was used in dump)
    with open(meta_json_path, "r", encoding="utf-8") as f:
        content = f.read()
        
        # 2. Strict check: ensure NO unquoted Infinity, -Infinity or NaN
        # json.dump(allow_nan=False) would have raised if we didn't sanitize.
        assert "Infinity" not in content
        assert "NaN" not in content
        
        # 3. Check values are null
        data = json.loads(content)
        item = data["top10"][0]
        assert item["sharpe_simple"] is None
        assert item["total_return"] is None
        assert item["max_drawdown"] is None
