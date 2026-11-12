import csv
import json
from pathlib import Path
from simulator.simulator import main as run_sim
from solution.performance_monitor import main as run_monitor

POLICIES = [
    "baseline", "greedy", "greedy_heap", "greedy_heap_2opt",
    "zones_strict", "zones_help",
    "zones_wait_30", "zones_wait_40", "zones_wait_50", "zones_wait_60",
    "zones_wait_70", "zones_wait_80", "zones_wait_90", "zones_wait_100",
]

METRIC_KEYS = [
    "total_daily_cost",
    "total_km",
    "total_parcels",
    "on_time_parcels",
    "late_parcels",
    "undelivered_parcels",
    "on_time_rate",
    "number_of_trips",
]

DATA_DIR = "data"
RESULTS_ROOT = Path("results")
OUTPUT_CSV = "all_policies_summary.csv"


def run_all_and_summarize(start_day: int = 1, end_day: int = 20) -> None:
    summary_rows = []

    for policy in POLICIES:
        policy_module = f"solution.policies.{policy}"
        daily_metrics = []

        for day_num in range(start_day, end_day + 1):
            day_str = f"day_{day_num:03d}"
            out_dir = RESULTS_ROOT / policy / day_str
            log_path = out_dir / "log.txt"
            metrics_path = out_dir / "metrics.json"

            # 1. Run simulator
            sim_exit = run_sim([
                "--policy", policy_module,
                "--data", DATA_DIR,
                "--day", day_str,
                "--output", str(out_dir),
            ])
            if sim_exit != 0:
                print(f"Stopping {policy}: simulator failed on {day_str}.")
                break

            # 2. Run performance monitor
            mon_exit = run_monitor([
                "--data", DATA_DIR,
                "--day", day_str,
                "--log", str(log_path),
            ])
            if mon_exit != 0:
                print(f"Stopping {policy}: monitor failed on {day_str}.")
                break

            # 3. Collect day's metrics
            with metrics_path.open("r", encoding="utf-8") as f:
                daily_metrics.append(json.load(f))

        print(f"done {policy}")

        # 4. Compute 20-day averages for this policy
        if daily_metrics:
            num_days = len(daily_metrics)
            row = {"policy": policy}
            for key in METRIC_KEYS:
                avg_val = sum(m[key] for m in daily_metrics) / num_days
                decimals = 4 if key == "on_time_rate" else 2
                row[key] = round(avg_val, decimals)
            summary_rows.append(row)

    # 5. Export combined comparison table
    if summary_rows:
        fieldnames = ["policy"] + METRIC_KEYS
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_rows)
        print(f"\nSaved combined summary for {len(summary_rows)} policies to {OUTPUT_CSV}!")


if __name__ == "__main__":
    run_all_and_summarize(1, 20)