"""Step 5 analysis: runtime of each policy, day-to-day spread, and penalty sensitivity.

Usage (from the project root, after running every policy with run_all.sh):
    python3 analysis.py
Writes results/analysis_runtime.csv, results/analysis_daily.csv and
results/analysis_sensitivity.csv, and prints the tables.
"""

import csv
import json
import statistics
import tempfile
import time
from pathlib import Path

from simulator.loaders import day_input_paths
from simulator.simulator import Simulator, load_policy

POLICIES = ["baseline", "nearest_neighbour", "urgent_nearest", "urgent_nearest_2opt",
            "zones_strict", "zones_help"]
DAYS = [f"day_{i:03d}" for i in range(1, 21)]
RESULTS = Path("results")


def runtime_table():
    """Time only the policy's dispatch() calls (not the simulator) over all 20 days."""

    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for name in POLICIES:
            policy = load_policy(f"solution.policies.{name}")
            stats = {"calls": 0, "seconds": 0.0, "max": 0.0}

            def timed(parcel, context, policy=policy, stats=stats):
                start = time.perf_counter()
                result = policy(parcel, context)
                spent = time.perf_counter() - start
                stats["calls"] += 1
                stats["seconds"] += spent
                stats["max"] = max(stats["max"], spent)
                return result

            for day in DAYS:
                paths = day_input_paths(Path("data"), day)
                Simulator(*paths, dispatch_policy=timed).run(Path(tmp) / f"{name}_{day}.txt")
            rows.append({
                "policy": name,
                "dispatch_calls_per_day": round(stats["calls"] / len(DAYS), 1),
                "avg_ms_per_call": round(1000 * stats["seconds"] / stats["calls"], 3),
                "max_ms_per_call": round(1000 * stats["max"], 3),
                "policy_seconds_per_day": round(stats["seconds"] / len(DAYS), 3),
            })
    return rows


def load_metrics():
    data = {}
    for name in POLICIES:
        data[name] = [json.loads((RESULTS / name / day / "metrics.json").read_text()) for day in DAYS]
    return data


def daily_table(data):
    base = [m["total_daily_cost"] for m in data["baseline"]]
    rows = []
    for name in POLICIES:
        costs = [m["total_daily_cost"] for m in data[name]]
        rows.append({
            "policy": name,
            "mean_cost": round(statistics.mean(costs), 2),
            "std_cost": round(statistics.stdev(costs), 2),
            "min_cost": round(min(costs), 2),
            "max_cost": round(max(costs), 2),
            "saving_vs_baseline_pct": round(100 * (1 - statistics.mean(costs) / statistics.mean(base)), 1),
        })
    return rows


def sensitivity_table(data):
    """Recompute average cost under other price assumptions; report the winner."""

    rows = []
    for per_km in (0.25, 0.50, 1.00):
        for late in (2.0, 5.0, 10.0):
            for missed in (10.0, 15.0, 30.0):
                if missed < late:
                    continue
                avg = {}
                for name in POLICIES:
                    avg[name] = statistics.mean(
                        m["total_km"] * per_km + m["late_parcels"] * late + m["undelivered_parcels"] * missed
                        for m in data[name]
                    )
                ranking = sorted(avg, key=avg.get)
                rows.append({"cost_per_km": per_km, "late_penalty": late, "missed_penalty": missed,
                             "winner": ranking[0], "second": ranking[1],
                             **{name: round(avg[name], 1) for name in POLICIES}})
    return rows


def write(rows, filename):
    with open(RESULTS / filename, "w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def show(rows, keys):
    print("  ".join(f"{k:>22}" for k in keys))
    for row in rows:
        print("  ".join(f"{str(row[k]):>22}" for k in keys))
    print()


def main():
    data = load_metrics()
    daily = daily_table(data)
    write(daily, "analysis_daily.csv")
    show(daily, list(daily[0].keys()))

    sens = sensitivity_table(data)
    write(sens, "analysis_sensitivity.csv")
    show(sens, ["cost_per_km", "late_penalty", "missed_penalty", "winner", "second"])

    runtime = runtime_table()
    write(runtime, "analysis_runtime.csv")
    show(runtime, list(runtime[0].keys()))


if __name__ == "__main__":
    main()
