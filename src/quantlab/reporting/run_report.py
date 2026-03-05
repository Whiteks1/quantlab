import os
import json
import math
import datetime
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import pandas as pd

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
    meta_path = run_path / "meta.json"
    
    if not meta_path.exists():
        raise FileNotFoundError(f"meta.json not found in {run_dir}")
        
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    mode = meta.get("mode", "grid")
    
    report = {
        "header": {
            "run_id": meta.get("run_id"),
            "mode": mode,
            "created_at": meta.get("created_at"),
            "git_commit": meta.get("git_commit"),
            "python_version": meta.get("python_version"),
            "config_path": meta.get("config_path"),
            "config_hash": meta.get("config_hash"),
        }
    }
    
    # Reproduce section
    # If the exact command isn't in meta, we can try to reconstruct it
    # For now, let's just use what's in meta or a dummy if missing
    config_path = meta.get("config_path", "config.yaml")
    report["reproduce"] = {
        "command": f"python main.py --sweep {config_path} --sweep_outdir {run_path.parent}"
    }

    config_resolved_path = run_path / "config_resolved.yaml"
    if config_resolved_path.exists():
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
            
    # Gather artifacts
    artifacts = []
    for f in run_path.iterdir():
        if f.is_file():
            artifacts.append({
                "file_name": f.name,
                "size_bytes": f.stat().st_size
            })
    report["artifacts"] = sorted(artifacts, key=lambda x: x["file_name"])
            
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
            df_sum = pd.DataFrame(summary)
            lines.append(df_sum.to_markdown(index=False))
        else:
            lines.append("No summary results found.")
            
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
    Builds and writes report.md and report.json to the run directory.
    """
    report = build_report(run_dir)
    run_path = Path(run_dir)
    
    md_path = run_path / "report.md"
    json_path = run_path / "report.json"
    
    md_content = render_report_md(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, allow_nan=False)
        
    return str(md_path), str(json_path)
