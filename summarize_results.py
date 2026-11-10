"""Print a comparison table of average metrics for every policy in results/.

Usage: python3 summarize_results.py [policy ...]
Writes results/summary.csv with per-policy, per-day numbers.
"""

import csv
import json
import sys
from pathlib import Path

KEYS = ["total_daily_cost", "total_km", "on_time_rate", "late_parcels",
        "undelivered_parcels", "number_of_trips"]


def main() -> None:
    root = Path("results")
    policies = sys.argv[1:] or sorted(p.name for p in root.iterdir() if p.is_dir())
    rows = []
    print(f"{'policy':<22}{'avg cost':>10}{'avg km':>9}{'on-time':>9}{'late':>7}{'undeliv':>9}{'trips':>7}")
    for policy in policies:
        days = sorted((root / policy).glob("day_*/metrics.json"))
        if not days:
            continue
        metrics = [json.loads(path.read_text()) for path in days]
        for path, m in zip(days, metrics):
            rows.append({"policy": policy, "day": path.parent.name, **{k: m[k] for k in KEYS}})
        avg = {k: sum(m[k] for m in metrics) / len(metrics) for k in KEYS}
        print(f"{policy:<22}{avg['total_daily_cost']:>10.0f}{avg['total_km']:>9.0f}"
              f"{avg['on_time_rate'] * 100:>8.1f}%{avg['late_parcels']:>7.0f}"
              f"{avg['undelivered_parcels']:>9.0f}{avg['number_of_trips']:>7.1f}")
    with open(root / "summary.csv", "w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["policy", "day"] + KEYS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
