"""Error types for run_analysis input validation."""

from pathlib import Path


class RunAnalysisError(Exception):
    """Base exception for run_analysis package failures."""


class RunAnalysisValidationError(RunAnalysisError):
    """Raised when run_analysis input validation fails."""


class InvalidRunIdError(RunAnalysisValidationError):
    """Raised when a run_id does not match the accepted format."""

    def __init__(self, run_id: str) -> None:
        super().__init__(f"Invalid run_id: {run_id!r}")


class RunPathNotFoundError(RunAnalysisValidationError):
    """Raised when outputs/runs/<run_id> does not exist."""

    def __init__(self, run_path: Path) -> None:
        super().__init__(f"Run path does not exist: {run_path}")


class RunPathNotDirectoryError(RunAnalysisValidationError):
    """Raised when outputs/runs/<run_id> exists but is not a directory."""

    def __init__(self, run_path: Path) -> None:
        super().__init__(f"Run path is not a directory: {run_path}")


class MissingRunArtifactError(RunAnalysisValidationError):
    """Raised when a required run artifact file is missing."""

    def __init__(self, run_path: Path, artifact_name: str) -> None:
        super().__init__(f"Missing required artifact '{artifact_name}' in {run_path}")


class RunAnalysisOutputExistsError(RunAnalysisError):
    """Raised when a run_analysis output file already exists."""

    def __init__(self, output_path: Path) -> None:
        super().__init__(f"Output already exists: {output_path}")
