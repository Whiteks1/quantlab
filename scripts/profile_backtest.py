from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from quantlab.backtest.profiling import build_backtest_profile_report


def _parse_sizes(raw: str) -> tuple[int, ...]:
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("sizes must not be empty")
    try:
        values = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("sizes must be comma-separated integers") from exc
    if any(value <= 0 for value in values):
        raise argparse.ArgumentTypeError("sizes must be positive integers")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile QuantLab's backtest engine on synthetic workloads."
    )
    parser.add_argument(
        "--sizes",
        type=_parse_sizes,
        default=(1_000, 10_000, 100_000),
        help="Comma-separated workload sizes. Default: 1000,10000,100000",
    )
    parser.add_argument("--repeats", type=int, default=3, help="Timed repeats per size.")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup runs per size.")
    parser.add_argument(
        "--slippage-mode",
        choices=("fixed", "atr"),
        default="fixed",
        help="Backtest slippage mode to profile.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Synthetic data seed.")
    parser.add_argument(
        "--json-out",
        help="Optional path for a JSON report artifact.",
    )
    args = parser.parse_args()

    report = build_backtest_profile_report(
        sizes=args.sizes,
        repeats=args.repeats,
        warmup=args.warmup,
        slippage_mode=args.slippage_mode,
        seed=args.seed,
    )

    print("QuantLab backtest profiling")
    print(f"  sizes         : {', '.join(str(size) for size in report['sizes'])}")
    print(f"  repeats       : {report['repeats']}")
    print(f"  warmup        : {report['warmup']}")
    print(f"  slippage_mode : {report['slippage_mode']}")
    print("")
    for workload in report["workloads"]:
        print(f"rows={workload['rows']}")
        print(f"  mean_seconds        : {workload['mean_seconds']:.6f}")
        print(f"  median_seconds      : {workload['median_seconds']:.6f}")
        print(f"  min_seconds         : {workload['min_seconds']:.6f}")
        print(f"  rows_per_second_avg : {workload['rows_per_second_mean']:.2f}")
        print(f"  rows_per_second_max : {workload['rows_per_second_peak']:.2f}")
        print(f"  trade_count         : {workload['trade_count']}")
        print(f"  final_equity        : {workload['final_equity']:.6f}")
        print("")

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Saved JSON report: {out_path}")


if __name__ == "__main__":
    main()
