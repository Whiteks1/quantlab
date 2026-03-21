import os
import json
import pandas as pd
from typing import Dict, Any, Optional

from .trade_analytics import load_trades_csv, compute_round_trips, aggregate_trade_metrics
from .report_summary import build_standard_summary

def build_report_payload(trades_csv_path: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Builds a dictionary containing all metrics and trade data for reporting.
    """
    if not os.path.exists(trades_csv_path):
        return {}

    trades_df = load_trades_csv(trades_csv_path)
    if trades_df.empty:
        payload = {"meta": meta or {}, "metrics": {}, "trades": []}
        payload["summary"] = build_standard_summary(payload)
        return payload

    round_trips = compute_round_trips(trades_df)
    metrics = aggregate_trade_metrics(round_trips)

    # Convert to list of dicts for JSON/MD, handling timestamps
    trades_list = []
    if not round_trips.empty:
        # We use a copy to avoid side effects on the original DF
        rt_display = round_trips.copy()
        for col in ["entry_time", "exit_time"]:
            if col in rt_display.columns:
                rt_display[col] = rt_display[col].apply(lambda x: x.isoformat() if hasattr(x, "isoformat") else str(x))
        trades_list = rt_display.to_dict(orient="records")

    payload = {
        "meta": meta or {},
        "metrics": metrics,
        "trades": trades_list
    }
    
    # Add standardized summary
    payload["summary"] = build_standard_summary(payload)
    
    return payload

def render_report_md(payload: Dict[str, Any]) -> str:
    """
    Renders the report payload into a Markdown string.
    """
    meta = payload.get("meta", {})
    metrics = payload.get("metrics", {})
    trades = payload.get("trades", [])

    ticker = meta.get("ticker", "Unknown")
    strategy = meta.get("strategy_name", "Unknown")

    lines = [
        f"# Strategy Report: {ticker}",
        f"**Strategy:** {strategy}\n",
        "## Backtest Overview",
        "| Metric | Value |",
        "| :--- | :--- |"
    ]

    # Use backtest metrics if provided in meta
    bt_metrics = meta.get("backtest_metrics", {})
    if bt_metrics:
        lines.append(f"| Total Return | {bt_metrics.get('total_return', 0):.2%} |")
        lines.append(f"| Max Drawdown | {bt_metrics.get('max_drawdown', 0):.2%} |")
        lines.append(f"| Sharpe Ratio | {bt_metrics.get('sharpe_simple', 0):.2f} |")
        lines.append(f"| Total Days | {bt_metrics.get('days', 0)} |")
    
    lines.append("\n## Trade-Level Analytics")
    lines.append("| Statistic | Value |")
    lines.append("| :--- | :--- |")
    lines.append(f"| Total Trades | {metrics.get('trades', 0)} |")
    lines.append(f"| Win Rate | {metrics.get('win_rate_trades', 0):.2%} |")
    lines.append(f"| Profit Factor | {metrics.get('profit_factor', 0):.2f} |")
    lines.append(f"| Expectancy | {metrics.get('expectancy_net', 0):.4f} |")
    lines.append(f"| Average Win | {metrics.get('avg_win', 0):.4f} |")
    lines.append(f"| Average Loss | {metrics.get('avg_loss', 0):.4f} |")
    lines.append(f"| Total Net PnL | {metrics.get('total_net_pnl', 0):.2f} |\n")

    if trades:
        lines.append("## Last Trades (Roundtrips)")
        lines.append("| Entry Time | Exit Time | Qty | Entry Price | Exit Price | Net PnL | PnL % |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        
        # Show last 20
        for t in trades[-20:]:
            lines.append(
                f"| {t['entry_time']} | {t['exit_time']} | {t['qty']:.4f} | "
                f"{t['entry_price']:.2f} | {t['exit_price']:.2f} | "
                f"{t['net_pnl']:.2f} | {t['pnl_pct']:.2%} |"
            )
    else:
        lines.append("No trades recorded.")

    return "\n".join(lines)

def write_report(trades_csv_path: str, out_md_path: str = "outputs/report.md", 
                 out_json_path: str = "outputs/report.json", meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Builds, renders and writes the report to files.
    """
    payload = build_report_payload(trades_csv_path, meta)
    
    # MD
    md_content = render_report_md(payload)
    os.makedirs(os.path.dirname(out_md_path), exist_ok=True)
    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # JSON
    if out_json_path:
        os.makedirs(os.path.dirname(out_json_path), exist_ok=True)
        with open(out_json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    return payload
