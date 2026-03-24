import datetime as _dt
import json
import os
from pathlib import Path
from typing import Any

from quantlab.execution.forward_eval import (
    load_candidate_from_run,
    run_forward_evaluation,
    write_forward_eval_artifacts,
    load_forward_session,
)
from quantlab.reporting.forward_report import write_forward_report
from quantlab.data.sources import fetch_ohlc


def _load_forward_summary(report_path: str) -> dict[str, Any]:
    try:
        with open(report_path, "r", encoding="utf-8") as fh:
            report = json.load(fh)
    except Exception:
        return {}

    return report.get("summary", {}) or report.get("kpi_summary", {})


def run_forward_mode(args) -> dict | None:
    """
    Stage L: orchestrate a forward evaluation session from CLI args.

    Returns a metadata dictionary on success, or None on failure/mismatch.
    """
    resume_dir = getattr(args, "resume_forward", None)
    run_dir = getattr(args, "forward_eval", None)

    if resume_dir:
        print(f"\n=== STAGE L.2: RESUMING FORWARD SESSION ===")
        print(f"  Session dir: {resume_dir}")
        try:
            session_data = load_forward_session(resume_dir)
        except ValueError as e:
            print(f"ERROR: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Could not load session: {e}")
            return None

        candidate = session_data["candidate"]
        initial_state = session_data["portfolio_state"]
        out_dir = resume_dir
        initial_historical = {
            "historic_trades": session_data["historic_trades"],
            "historic_equity": session_data["historic_equity"],
        }
    else:
        print(f"\n=== STAGE L: FORWARD EVALUATION ===")
        print(f"  Source run : {run_dir}")
        candidate = None
        initial_state = None

        out_dir = args.forward_outdir
        if out_dir is None:
            session_tag = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            out_dir = os.path.join("outputs", "forward_runs", f"fwd_{session_tag}")
        initial_historical = None

    fwd_start = getattr(args, "forward_start", None)
    fwd_end = getattr(args, "forward_end", None)

    if not candidate:
        metric = getattr(args, "forward_metric", "sharpe_simple")
        print(f"\n[1/4] Loading candidate (metric={metric})...")
        candidate = load_candidate_from_run(run_dir, metric=metric)

    print(f"  Strategy  : {candidate.strategy_name}")
    print(f"  Source ID : {candidate.source_run_id}")
    print(f"  Params    : {candidate.params}")

    ticker = candidate.ticker or args.ticker
    interval = candidate.interval or args.interval

    today = _dt.date.today().isoformat()
    active_start = fwd_start or (initial_state.original_eval_start if initial_state else today)
    active_end = fwd_end or today

    fetch_start = active_start
    try:
        start_dt = _dt.datetime.strptime(active_start, "%Y-%m-%d")
        fetch_start = (start_dt - _dt.timedelta(days=400)).strftime("%Y-%m-%d")
    except Exception:
        pass

    print(f"\n[2/4] Fetching OHLC data ({ticker}, {fetch_start} → {active_end}, {interval})...")
    df = fetch_ohlc(ticker, fetch_start, active_end, interval=interval)
    print(f"  Bars fetched: {len(df)}")

    print(f"\n[3/4] Running forward paper evaluation...")
    try:
        result = run_forward_evaluation(
            candidate=candidate,
            df=df,
            initial_cash=args.initial_cash,
            eval_start=active_start,
            eval_end=active_end,
            initial_state=initial_state,
        )
    except Exception as e:
        print(f"ERROR: Forward evaluation failed: {e}")
        return None

    ps = result["portfolio_state"]
    print(f"  Bars evaluated : {result['bars_evaluated']}")
    print(f"  Trades (segment): {len(result['trades'])}")
    print(f"  Ending equity  : {ps.current_equity:,.4f}")

    print(f"\n[4/4] Writing artifacts to {out_dir}...")
    os.makedirs(out_dir, exist_ok=True)
    written_files = write_forward_eval_artifacts(
        result,
        out_dir,
        initial_historical=initial_historical,
    )
    json_p, md_p = write_forward_report(out_dir)
    written_files += [json_p, md_p]

    for f in written_files:
        print(f"  → {f}")

    return {
        "run_id": os.path.basename(out_dir),
        "artifacts_path": out_dir,
        "report_path": json_p,
        "status": "success",
        "summary": _load_forward_summary(json_p),
        "mode": "forward",
        "runs_index_root": str(Path("outputs") / "runs"),
    }


def handle_forward_commands(
    args,
) -> dict | None:
    """
    Handle forward-evaluation related CLI modes.
    """
    if args.forward_eval or args.resume_forward:
        return run_forward_mode(args)

    return None
