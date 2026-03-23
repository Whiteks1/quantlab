"""
run_index.py – Stage J: global run registry for QuantLab.

Scans a root directory (e.g. outputs/runs) for completed run folders,
normalises their summary metrics, and writes a global index as:
 - runs_index.csv
 - runs_index.json  (strict, allow_nan=False)
 - runs_index.md

Functions
---------
scan_runs(root_dir)           -> Iterator[Path]
load_run_summary(run_dir)     -> dict
build_runs_index(root_dir)    -> dict
render_runs_index_md(payload) -> str
write_runs_index(root_dir)    -> tuple[str, str, str]
"""

from __future__ import annotations

import json
import math
import datetime
import warnings
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import pandas as pd
from quantlab.runs.artifacts import (
    CANONICAL_METADATA_FILENAME,
    CANONICAL_METRICS_FILENAME,
    CANONICAL_REPORT_FILENAME,
    LEGACY_METADATA_FILENAMES,
    LEGACY_REPORT_FILENAMES,
    load_json_with_fallback,
)


# ---------------------------------------------------------------------------
# JSON sanitisation (same logic as run_report.py / runner.py)
# ---------------------------------------------------------------------------

def _sanitize_for_json(obj: Any) -> Any:
    """Recursively convert non-finite floats (NaN, ±Inf) to None."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(x) for x in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SUMMARY_FIELDS = [
    "run_id", "mode", "created_at", "git_commit",
    "ticker", "start", "end",
    "sharpe_simple", "total_return", "max_drawdown", "trades",
    "path",
]


def _is_valid_run_dir(path: Path) -> bool:
    """A folder is a valid run if it has canonical or legacy metadata/report artifacts."""
    return any(
        (path / name).exists()
        for name in (
            CANONICAL_METADATA_FILENAME,
            CANONICAL_REPORT_FILENAME,
            *LEGACY_METADATA_FILENAMES,
            *LEGACY_REPORT_FILENAMES,
        )
    )


def _extract_top_metric(report: Dict[str, Any], key: str) -> Optional[float]:
    """Pull a metric from the first results/oos_leaderboard row in the report."""
    for section in ("results", "oos_leaderboard"):
        rows = report.get(section, [])
        if rows and isinstance(rows, list) and isinstance(rows[0], dict):
            val = rows[0].get(key)
            if val is not None:
                try:
                    return float(val)
                except (TypeError, ValueError):
                    pass
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_runs(root_dir: str | Path) -> Iterator[Path]:
    """
    Yield valid run sub-directories inside *root_dir*.

    A directory is considered valid when it contains at least one of:
    canonical metadata/report artifacts or their legacy equivalents. Invalid or missing directories
    are silently skipped.

    Parameters
    ----------
    root_dir:
        Path to the root directory that contains individual run folders
        (e.g. ``outputs/runs``).

    Yields
    ------
    Path
        Absolute ``Path`` objects for each valid run directory.
    """
    root = Path(root_dir)
    if not root.is_dir():
        return
    for child in sorted(root.iterdir()):
        if child.is_dir() and _is_valid_run_dir(child):
            yield child


def load_run_summary(run_dir: str | Path) -> Dict[str, Any]:
    """
    Load a normalised summary dict for a single run directory.

    Resolution order:
    1. ``report.json`` (preferred – canonical machine artifact)
    2. ``run_report.json`` (legacy fallback)
    3. ``metadata.json`` (canonical metadata fallback)
    4. ``meta.json`` (legacy metadata fallback)

    Missing fields are set to ``None``.  The function never raises; it
    returns a partial dict with at minimum ``{"path": str(run_dir)}``.

    Parameters
    ----------
    run_dir:
        Path to a single completed run directory.

    Returns
    -------
    dict
        Flat dict with keys from ``_SUMMARY_FIELDS``.
    """
    path = Path(run_dir)
    summary: Dict[str, Any] = {f: None for f in _SUMMARY_FIELDS}
    summary["path"] = str(path)

    source: Dict[str, Any] = {}
    metrics_source: Dict[str, Any] = {}
    try:
        source, _ = load_json_with_fallback(
            path,
            CANONICAL_REPORT_FILENAME,
            *LEGACY_REPORT_FILENAMES,
            CANONICAL_METADATA_FILENAME,
            *LEGACY_METADATA_FILENAMES,
        )
        metrics_source, _ = load_json_with_fallback(path, CANONICAL_METRICS_FILENAME)
    except Exception as exc:  # noqa: BLE001
        warnings.warn(f"[run_index] Could not read {run_dir}: {exc}")
        return summary

    # --- Header / meta fields ---
    header = source.get("header", source)  # report.json has "header"; metadata.json is flat
    for field in ("run_id", "mode", "created_at", "git_commit"):
        summary[field] = header.get(field)

    # Config fields may be nested inside report.json → config_resolved
    config = source.get("config_resolved", {}) or {}
    for field in ("ticker", "start", "end"):
        summary[field] = config.get(field) or header.get(field)

    # --- Metric fields: top result row OR summary/top10 from metadata ---
    for metric in ("sharpe_simple", "total_return", "max_drawdown", "trades"):
        val = _extract_top_metric(source, metric)
        if val is None:
            metrics_summary = metrics_source.get("summary", {}) if isinstance(metrics_source, dict) else {}
            raw_metric = metrics_summary.get(metric)
            if raw_metric is not None:
                try:
                    val = float(raw_metric)
                except (TypeError, ValueError):
                    pass
        if val is None:
            # Try metadata top10
            top10 = source.get("top10", [])
            if top10 and isinstance(top10[0], dict):
                raw = top10[0].get(metric)
                if raw is not None:
                    try:
                        val = float(raw)
                    except (TypeError, ValueError):
                        pass
        summary[metric] = val

    # run_id fallback
    if summary["run_id"] is None:
        summary["run_id"] = path.name

    return summary


def build_runs_index(root_dir: str | Path) -> Dict[str, Any]:
    """
    Scan *root_dir* and build a complete registry of all valid runs.

    Parameters
    ----------
    root_dir:
        Root directory containing individual run sub-directories.

    Returns
    -------
    dict
        ``{"generated_at": ISO str, "root_dir": str, "runs": [list of summaries]}``
    """
    runs: List[Dict[str, Any]] = []
    for run_path in scan_runs(root_dir):
        try:
            summary = load_run_summary(run_path)
            runs.append(summary)
        except Exception as exc:  # noqa: BLE001
            warnings.warn(f"[run_index] Skipping {run_path}: {exc}")

    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "root_dir": str(root_dir),
        "n_runs": len(runs),
        "runs": runs,
    }


def render_runs_index_md(payload: Dict[str, Any]) -> str:
    """
    Render a human-readable Markdown document for the runs index.

    Parameters
    ----------
    payload:
        Dict returned by :func:`build_runs_index`.

    Returns
    -------
    str
        Markdown string.
    """
    runs = payload.get("runs", [])
    lines = [
        "# Runs Index",
        "",
        "## Summary",
        "",
        f"- **Root directory:** `{payload.get('root_dir')}`",
        f"- **Generated at:** {payload.get('generated_at')}",
        f"- **Total runs found:** {payload.get('n_runs', len(runs))}",
        "",
        "## Runs",
        "",
    ]

    if not runs:
        lines.append("_No valid run directories found._")
        return "\n".join(lines)

    display_cols = [
        "run_id", "mode", "created_at", "sharpe_simple",
        "total_return", "max_drawdown", "trades", "path",
    ]
    df = pd.DataFrame(runs)
    # Keep only columns that exist
    cols = [c for c in display_cols if c in df.columns]
    lines.append(df[cols].to_markdown(index=False))
    return "\n".join(lines)


def write_runs_index(
    root_dir: str | Path,
) -> Tuple[str, str, str]:
    """
    Build the runs index and write three artifacts into *root_dir*:

    - ``runs_index.csv``
    - ``runs_index.json``  (strict, allow_nan=False)
    - ``runs_index.md``

    Parameters
    ----------
    root_dir:
        Root runs directory (e.g. ``outputs/runs``).

    Returns
    -------
    tuple[str, str, str]
        Absolute paths to (csv, json, md).
    """
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)

    payload = build_runs_index(root)
    payload = _sanitize_for_json(payload)

    runs = payload.get("runs", [])
    df = pd.DataFrame(runs) if runs else pd.DataFrame(columns=_SUMMARY_FIELDS)

    csv_path = root / "runs_index.csv"
    json_path = root / "runs_index.json"
    md_path = root / "runs_index.md"

    df.to_csv(csv_path, index=False)

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, allow_nan=False)

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_runs_index_md(payload))

    return str(csv_path), str(json_path), str(md_path)
