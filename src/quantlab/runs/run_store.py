import os
from pathlib import Path
from typing import Any, Dict, Optional

from quantlab.runs.serializers import save_json

class RunStore:
    """
    Manage the directory structure and core artifacts for a specific run.
    """
    def __init__(self, run_id: str, base_dir: str = "outputs/runs"):
        self.run_id = run_id
        self.base_dir = Path(base_dir)
        self.run_path = self.base_dir / run_id
        
    def initialize(self) -> Path:
        """Create the run directory structure and return the Path object."""
        self.run_path.mkdir(parents=True, exist_ok=True)
        (self.run_path / "artifacts").mkdir(exist_ok=True)
        return self.run_path
        
    def write_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save metadata.json to the run directory."""
        metadata["run_id"] = self.run_id
        save_json(metadata, self.run_path / "metadata.json")
        
    def write_config(self, config: Dict[str, Any]) -> None:
        """Save config.json to the run directory."""
        save_json(config, self.run_path / "config.json")
        
    def write_metrics(self, metrics: Dict[str, Any]) -> None:
        """Save metrics.json to the run directory."""
        save_json(metrics, self.run_path / "metrics.json")
        
    def get_run_path(self) -> Path:
        """Return the absolute path to the run directory."""
        return self.run_path
