import os
import json
import math
import datetime
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import pandas as pd
from quantlab.reporting.report_summary import build_standard_summary
from quantlab.runs.artifacts import (
    CANONICAL_CONFIG_FILENAME,
    CANONICAL_METADATA_FILENAME,
    CANONICAL_METRICS_FILENAME,
    CANONICAL_REPORT_FILENAME,
    CONFIG_RESOLVED_YAML_FILENAME,
    LEGACY_METADATA_FILENAMES,
    PAPER_SESSION_METADATA_FILENAME,
    canonical_paper_artifact_names,
    canonical_run_artifact_names,
    load_json_with_fallback,
)


def _build_machine_contract(
    *,
    command: str,
    status: str,
    request_id: Optional[str],
    run_id: Optional[str],
    mode: str,
    summary: Dict[str, Any],
    best_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    contract: Dict[str, Any] = {
        "schema_version": "1.0",
        "contract_type": f"quantlab.{command}.result",
        "command": command,
        "status": status,
        "request_id": request_id,
        "run_id": run_id,
        "mode": mode,
        "summary": summary,
        "artifacts": canonical_run_artifact_names(),
    }
    if best_result is not None:
        contract["best_result"] = best_result
    return contract


def _artifact_names_for_command(command: str) -> Dict[str, Any]:
    if command == "paper":
        return canonical_paper_artifact_names()
    return canonical_run_artifact_names()

def _sanitize_for_json(obj: Any) -> Any:
    """
    Recursively convert non-finite floats (NaN, Inf) to None for strict JSON.
    """
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(x) for x in obj]
    elif isinstance(obj, float):
        if not math.isfinite(obj):
            return None
    return obj

def build_report(run_dir: str) -> Dict[str, Any]:
    """
    Builds a standardized report dictionary from run artifacts.
    """
    run_path = Path(run_dir)
    meta, meta_path = load_json_with_fallback(
        run_path,
        CANONICAL_METADATA_FILENAME,
        PAPER_SESSION_METADATA_FILENAME,
        *LEGACY_METADATA_FILENAMES,
    )
    if not meta_path:
        raise FileNotFoundError(f"metadata.json not found in {run_dir}")

    metrics, _metrics_path = load_json_with_fallback(run_path, CANONICAL_METRICS_FILENAME)
    config_json, _config_json_path = load_json_with_fallback(run_path, CANONICAL_CONFIG_FILENAME)
        
    mode = meta.get("mode", "grid")
    command = meta.get("command") or ("sweep" if mode in {"grid", "walkforward"} else mode)
    
    report = {
        "schema_version": "1.0",
        "artifact_type": "quantlab_run_report",
        "status": meta.get("status", "success"),
        "header": {
            "run_id": meta.get("run_id"),
            "mode": mode,
            "created_at": meta.get("created_at"),
            "git_commit": meta.get("git_commit"),
            "python_version": meta.get("python_version"),
            "config_path": meta.get("config_path"),
            "config_hash": meta.get("config_hash"),
            "request_id": meta.get("request_id"),
        }
    }
    
    # Reproduce section
    # If the exact command isn't in meta, we can try to reconstruct it
    # For now, let's just use what's in meta or a dummy if missing
    config_path = meta.get("config_path", "config.yaml")
    if command == "run":
        reproduce_command = (
            "python main.py "
            f"--ticker {config_json.get('ticker', 'ETH-USD')} "
            f"--start {config_json.get('start', '2023-01-01')} "
            f"--end {config_json.get('end', '2024-01-01')}"
        )
    else:
        reproduce_command = (
            f"python main.py --sweep {config_path} --sweep_outdir {run_path.parent}"
        )
    report["reproduce"] = {
        "command": reproduce_command
    }

    config_resolved_path = run_path / CONFIG_RESOLVED_YAML_FILENAME
    if config_json:
        report["config_resolved"] = config_json
    elif config_resolved_path.exists():
        import yaml
        with open(config_resolved_path, "r", encoding="utf-8") as f:
            try:
                report["config_resolved"] = yaml.safe_load(f)
            except yaml.YAMLError:
                pass

    if mode == "grid":
        lb_path = run_path / "leaderboard.csv"
        if not lb_path.exists():
            lb_path = run_path / "experiments.csv"
            
        if lb_path.exists():
            df = pd.read_csv(lb_path)
            sort_cols = [c for c in ["sharpe_simple", "total_return"] if c in df.columns]
            if sort_cols:
                df = df.sort_values(sort_cols, ascending=[False] * len(sort_cols))
            report["results"] = df.head(10).to_dict(orient="records")
        else:
            report["results"] = []
            
    elif mode == "walkforward":
        oos_lb_path = run_path / "oos_leaderboard.csv"
        summary_path = run_path / "walkforward_summary.csv"
        
        report["oos_leaderboard"] = []
        if oos_lb_path.exists():
            df_oos = pd.read_csv(oos_lb_path)
            report["oos_leaderboard"] = df_oos.head(10).to_dict(orient="records")
            
        report["summary"] = []
        if summary_path.exists():
            df_sum = pd.read_csv(summary_path)
            report["summary"] = df_sum.to_dict(orient="records")
    else:
        report["results"] = []
        best_result = metrics.get("best_result")
        if isinstance(best_result, dict) and best_result:
            report["results"] = [_sanitize_for_json(best_result)]
            
    # Gather artifacts
    artifacts = []
    for f in run_path.iterdir():
        if f.is_file():
            artifacts.append({
                "file_name": f.name,
                "size_bytes": f.stat().st_size
            })
    report["artifacts"] = sorted(artifacts, key=lambda x: x["file_name"])
            
    # Standardized summary for Stepbit.
    # For plain `run`, prefer the already-persisted metrics payload so the
    # top-level `summary` mirrors the canonical machine-facing KPI block.
    summary_source = metrics if command == "run" else report
    standard_summary = build_standard_summary(summary_source)
    best_result = (report.get("results") or report.get("oos_leaderboard") or [None])[0]
    machine_summary = metrics.get("summary") or standard_summary
    if command == "sweep":
        report["machine_contract"] = _build_machine_contract(
            command="sweep",
            status=report["status"],
            request_id=meta.get("request_id"),
            run_id=report["header"].get("run_id"),
            mode=mode,
            summary=machine_summary,
            best_result=best_result,
        )
    elif command == "run":
        report["machine_contract"] = _build_machine_contract(
            command="run",
            status=report["status"],
            request_id=meta.get("request_id"),
            run_id=report["header"].get("run_id"),
            mode=mode,
            summary=machine_summary,
        )
    elif command == "paper":
        report["machine_contract"] = _build_machine_contract(
            command="paper",
            status=report["status"],
            request_id=meta.get("request_id"),
            run_id=report["header"].get("run_id"),
            mode=mode,
            summary=machine_summary,
        )

    if "machine_contract" in report:
        report["machine_contract"]["artifacts"] = _artifact_names_for_command(command)

    # Preserve legacy summary structures (e.g. walkforward summary tables)
    # and add the machine-readable KPI block additively.
    if "summary" in report:
        report["kpi_summary"] = standard_summary
    else:
        report["summary"] = standard_summary
    
    return _sanitize_for_json(report)

def render_report_md(report: Dict[str, Any]) -> str:
    """
    Renders the report dict to Markdown.
    """
    h = report["header"]
    lines = [
        f"# Run Report: {h.get('run_id')}",
        "",
        "## Metadata",
        f"- **Mode:** {h.get('mode')}",
        f"- **Created At:** {h.get('created_at')}",
        f"- **Config Path:** {h.get('config_path')}",
        f"- **Git Commit:** `{h.get('git_commit')}`",
    ]
    
    py_version = h.get('python_version')
    if py_version:
        lines.append(f"- **Python:** `{py_version.split()[0]}`")
    
    lines.extend([
        "",
        "## Reproduce",
        "```bash",
        f"{report.get('reproduce', {}).get('command', 'N/A')}",
        "```",
        ""
    ])
    
    config_resolved = report.get("config_resolved")
    if config_resolved:
        lines.extend([
            "## Config",
            "```yaml",
            json.dumps(config_resolved, indent=2) if isinstance(config_resolved, dict) else str(config_resolved),
            "```",
            ""
        ])
    
    if h.get("mode") == "grid":
        lines.append("## Top 10 Results (Grid Search)")
        results = report.get("results", [])
        if results:
            df = pd.DataFrame(results)
            lines.append(df.to_markdown(index=False))
        else:
            lines.append("No results found.")
            
    elif h.get("mode") == "walkforward":
        lines.append("## Out-Of-Sample Leaderboard")
        oos = report.get("oos_leaderboard", [])
        if oos:
            df_oos = pd.DataFrame(oos)
            lines.append(df_oos.to_markdown(index=False))
        else:
            lines.append("No OOS results found.")
            
        lines.append("\n## Walkforward Summary")
        summary = report.get("summary", [])
        if summary:
            df_sum = pd.DataFrame([summary]).T.reset_index()
            df_sum.columns = ["metric", "value"]
            lines.append(df_sum.to_markdown(index=False))
        else:
            lines.append("No summary results found.")
    else:
        lines.append("## Result Summary")
        results = report.get("results", [])
        if results:
            df = pd.DataFrame(results)
            lines.append(df.to_markdown(index=False))
        else:
            lines.append("No result rows found.")
            
    lines.append("\n## Artifacts")
    artifacts = report.get("artifacts", [])
    if artifacts:
        df_art = pd.DataFrame(artifacts)
        lines.append(df_art.to_markdown(index=False))
    else:
        lines.append("No artifacts found.")
            
    return "\n".join(lines)

def write_report(run_dir: str) -> Tuple[str, str]:
    """
    Builds and writes reporting artifacts to the run directory.
    
    Writes:
    - report.json (canonical)
    - run_report.md
    """
    report = build_report(run_dir)
    run_path = Path(run_dir)
    
    md_path = run_path / "run_report.md"
    json_path = run_path / CANONICAL_REPORT_FILENAME
    
    md_content = render_report_md(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    # Write canonical artifact
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, allow_nan=False)

    return str(md_path), str(json_path)

