from pathlib import Path
from typing import Any, Dict

from quantlab.runs.serializers import save_json
from quantlab.runs.artifacts import (
    PAPER_SESSION_METADATA_FILENAME,
    PAPER_SESSION_STATUS_FILENAME,
)


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


class PaperSessionStore:
    """
    Manage the directory structure and core artifacts for a paper session.

    Paper sessions are distinct from research runs and live under
    ``outputs/paper_sessions/<session_id>/``.
    """

    def __init__(self, session_id: str, base_dir: str = "outputs/paper_sessions"):
        self.session_id = session_id
        self.base_dir = Path(base_dir)
        self.session_path = self.base_dir / session_id

    def initialize(self) -> Path:
        self.session_path.mkdir(parents=True, exist_ok=True)
        (self.session_path / "artifacts").mkdir(exist_ok=True)
        return self.session_path

    def _ensure_initialized(self) -> None:
        self.session_path.mkdir(parents=True, exist_ok=True)

    def write_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Persist both the generic metadata.json used by report builders and the
        paper-specific session_metadata.json for operator-facing lifecycle work.
        """
        self._ensure_initialized()

        data = dict(metadata)
        data["session_id"] = self.session_id
        data["run_id"] = data.get("run_id", self.session_id)

        save_json(data, self.session_path / "metadata.json")
        save_json(data, self.session_path / PAPER_SESSION_METADATA_FILENAME)

    def write_config(self, config: Dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(config, self.session_path / "config.json")

    def write_metrics(self, metrics: Dict[str, Any]) -> None:
        self._ensure_initialized()
        save_json(metrics, self.session_path / "metrics.json")

    def write_status(self, status: Dict[str, Any]) -> None:
        self._ensure_initialized()

        data = dict(status)
        data["session_id"] = self.session_id
        save_json(data, self.session_path / PAPER_SESSION_STATUS_FILENAME)

    def get_session_path(self) -> Path:
        return self.session_path.resolve()
