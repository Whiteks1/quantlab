"""
compare_runs.py – Stage J: side-by-side comparison of QuantLab runs.

Accepts 2+ run directories, normalises their metrics, produces a sorted
comparison table, and identifies the best run by a chosen metric.

Artifacts written:
 - compare_report.json  (strict, allow_nan=False)
 - compare_report.md

Functions
---------
compare_runs(run_dirs, sort_by)            -> dict
render_comparison_md(payload)              -> str
write_comparison(run_dirs, out_path, sort_by) -> tuple[str, str]
"""

from __future__ import annotations

import json
import math
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Re-use the single source of truth from run_index
from quantlab.reporting.run_index import load_run_summary, _sanitize_for_json


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compare_runs(
    run_dirs: List[str | Path],
    sort_by: str = "sharpe_simple",
) -> Dict[str, Any]:
    """
    Build a comparison payload for the given run directories.

    Loads a normalised summary for each directory, sorts by *sort_by*
    (descending, NaN/None last), and tags the best run.

    Parameters
    ----------
    run_dirs:
        List of paths to completed run directories.
    sort_by:
        Metric column to rank by (default: ``"sharpe_simple"``).

    Returns
    -------
    dict
        ``{"generated_at", "sort_by", "best_run_id", "best_run_path",
           "n_runs", "runs": [sorted list of summaries]}``
    """
    summaries: List[Dict[str, Any]] = []
    for d in run_dirs:
        try:
            s = load_run_summary(d)
            summaries.append(s)
        except Exception as exc:  # noqa: BLE001
            import warnings
            warnings.warn(f"[compare_runs] Skipping {d}: {exc}")

    # Sort: put None/NaN last, descending for numeric metrics
    def _sort_key(row: Dict[str, Any]) -> float:
        val = row.get(sort_by)
        if val is None:
            return float("-inf")
        try:
            f = float(val)
            return float("-inf") if not math.isfinite(f) else f
        except (TypeError, ValueError):
            return float("-inf")

    summaries.sort(key=_sort_key, reverse=True)

    best_run_id: Optional[str] = None
    best_run_path: Optional[str] = None
    if summaries:
        best = summaries[0]
        best_run_id = best.get("run_id")
        best_run_path = best.get("path")

    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "sort_by": sort_by,
        "n_runs": len(summaries),
        "best_run_id": best_run_id,
        "best_run_path": best_run_path,
        "runs": summaries,
    }


def render_comparison_md(payload: Dict[str, Any]) -> str:
    """
    Render a human-readable Markdown comparison report.

    Parameters
    ----------
    payload:
        Dict returned by :func:`compare_runs`.

    Returns
    -------
    str
        Markdown string.
    """
    runs = payload.get("runs", [])
    sort_by = payload.get("sort_by", "sharpe_simple")

    lines = [
        "# Run Comparison",
        "",
        "## Summary",
        "",
        f"- **Generated at:** {payload.get('generated_at')}",
        f"- **Runs compared:** {payload.get('n_runs', len(runs))}",
        f"- **Ranked by:** `{sort_by}`",
        "",
        "## Best Run",
        "",
        f"- **run_id:** `{payload.get('best_run_id')}`",
        f"- **path:** `{payload.get('best_run_path')}`",
        "",
        "## Ranking",
        "",
    ]

    if not runs:
        lines.append("_No runs to compare._")
        lines.extend(["", "## Runs Compared", "", "_None._"])
        return "\n".join(lines)

    display_cols = [
        "run_id", "mode", "created_at", "sharpe_simple",
        "total_return", "max_drawdown", "trades", "path",
    ]
    df = pd.DataFrame(runs)
    rank_cols = [c for c in display_cols if c in df.columns]
    lines.append(df[rank_cols].to_markdown(index=False))

    lines.extend([
        "",
        "## Runs Compared",
        "",
    ])
    path_col = [r.get("path", "unknown") for r in runs]
    for p in path_col:
        lines.append(f"- `{p}`")

    return "\n".join(lines)


def write_comparison(
    run_dirs: List[str | Path],
    out_path: Optional[str | Path] = None,
    sort_by: str = "sharpe_simple",
) -> Tuple[str, str]:
    """
    Compare *run_dirs*, write results to *out_path*.

    Artifacts created:
    - ``compare_report.json``  (strict JSON, allow_nan=False)
    - ``compare_report.md``

    Parameters
    ----------
    run_dirs:
        List of run directory paths to compare.
    out_path:
        Directory where artifacts are written.  Defaults to current working
        directory.
    sort_by:
        Metric to rank by (default: ``"sharpe_simple"``).

    Returns
    -------
    tuple[str, str]
        Absolute paths to (json, md).
    """
    out = Path(out_path) if out_path else Path(".")
    out.mkdir(parents=True, exist_ok=True)

    payload = compare_runs(run_dirs, sort_by=sort_by)
    payload = _sanitize_for_json(payload)

    json_path = out / "compare_report.json"
    md_path = out / "compare_report.md"

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, allow_nan=False)

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_comparison_md(payload))

    return str(json_path), str(md_path)
