"""Pure validator for run_analysis inputs."""

import re
from pathlib import Path

from .errors import (
    InvalidRunIdError,
    MissingRunArtifactError,
    RunPathNotDirectoryError,
    RunPathNotFoundError,
)

REQUIRED_RUN_FILES: tuple[str, ...] = ("metadata.json", "metrics.json", "report.json")
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def validate_run_input(run_id: str, runs_root: str | Path) -> Path:
    """Validate run_id and minimal run artifact structure.

    Args:
        run_id: Identifier expected under outputs/runs/<run_id>/.
        runs_root: Base directory containing run directories.

    Returns:
        The validated run directory path.
    """
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        raise InvalidRunIdError(run_id)

    run_path = Path(runs_root) / run_id
    if not run_path.exists():
        raise RunPathNotFoundError(run_path)
    if not run_path.is_dir():
        raise RunPathNotDirectoryError(run_path)

    for file_name in REQUIRED_RUN_FILES:
        artifact_path = run_path / file_name
        if not artifact_path.is_file():
            raise MissingRunArtifactError(run_path, file_name)

    return run_path
