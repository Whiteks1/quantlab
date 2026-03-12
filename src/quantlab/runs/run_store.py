from pathlib import Path
from typing import Any, Dict

from quantlab.runs.serializers import save_json


class RunStore:
    """
    Manage the directory structure and core artifacts for a specific run.

    Responsibilities:
    - create the run directory structure
    - persist core artifacts (metadata, config, metrics)
    - expose the run path
    """

    def __init__(self, run_id: str, base_dir: str = "outputs/runs"):
        self.run_id = run_id
        self.base_dir = Path(base_dir)
        self.run_path = self.base_dir / run_id

    def initialize(self) -> Path:
        """
        Create the run directory structure and return the run path.

        Structure:
        outputs/runs/<run_id>/
            metadata.json
            config.json
            metrics.json
            artifacts/
        """
        self.run_path.mkdir(parents=True, exist_ok=True)
        (self.run_path / "artifacts").mkdir(exist_ok=True)
        return self.run_path

    def _ensure_initialized(self) -> None:
        """
        Ensure the run directory exists before writing artifacts.
        """
        self.run_path.mkdir(parents=True, exist_ok=True)

    def write_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Save metadata.json to the run directory.

        The run_id is injected without mutating the original metadata object.
        """
        self._ensure_initialized()

        data = dict(metadata)
        data["run_id"] = self.run_id

        save_json(data, self.run_path / "metadata.json")

    def write_config(self, config: Dict[str, Any]) -> None:
        """
        Save config.json to the run directory.
        """
        self._ensure_initialized()
        save_json(config, self.run_path / "config.json")

    def write_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Save metrics.json to the run directory.
        """
        self._ensure_initialized()
        save_json(metrics, self.run_path / "metrics.json")

    def get_run_path(self) -> Path:
        """
        Return the absolute path to the run directory.
        """
        return self.run_path.resolve()