import csv
import json
from pathlib import Path
# Import your custom calculate_metrics function (update module path if needed)
from solution.performance_monitor import calculate_metrics
from simulator.loaders import day_input_paths

# Configuration
POLICY_NAME = "zones_wait_90"  # Update to match your policy folder name in results/
DATA_DIR = Path("data")
RESULTS_DIR = Path("results") / POLICY_NAME
OUTPUT_CSV = f"{POLICY_NAME}_20_days_summary.csv"

def generate_20_day_summary(start_day: int = 1, end_day: int = 20):
    daily_rows = []
    
    # Columns to include in the daily rows and average summary
    metric_keys = [
        "total_daily_cost",
        "total_km",
        "total_parcels",
        "on_time_parcels",
        "late_parcels",
        "undelivered_parcels",
        "on_time_rate",
        "number_of_trips",
    ]

    for day_num in range(start_day, end_day + 1):
        day_str = f"day_{day_num:03d}"
        log_path = RESULTS_DIR / day_str / "log.txt"
        
        if not log_path.exists():
            print(f"Skipping {day_str}: log.txt not found at {log_path}")
            continue

        # Load day inputs and event log
        parcel_path, distance_path, config_path = day_input_paths(DATA_DIR, day_str)
        with parcel_path.open(newline="", encoding="utf-8-sig") as f:
            parcels = list(csv.DictReader(f))
        with distance_path.open(newline="", encoding="utf-8-sig") as f:
            distances = list(csv.DictReader(f))
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        with log_path.open(encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip()]

        # Calculate metrics using your function
        metrics = calculate_metrics(parcels, distances, config, events)
        
        # Build row for this day
        row = {"day": day_str}
        for key in metric_keys:
            row[key] = metrics[key]
        daily_rows.append(row)

    if not daily_rows:
        print("No simulation logs found. Please run the simulator first.")
        return

    # Calculate averages across all processed days
    num_days = len(daily_rows)
    avg_row = {"day": f"AVERAGE ({num_days} days)"}
    for key in metric_keys:
        avg_val = sum(row[key] for row in daily_rows) / num_days
        # Keep 4 decimal places for on_time_rate, 2 for others
        decimals = 4 if key == "on_time_rate" else 2
        avg_row[key] = round(avg_val, decimals)

    # Write daily rows + summary average row to CSV
    fieldnames = ["day"] + metric_keys
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(daily_rows)
        writer.writerow(avg_row)

    print(f"Summary successfully saved to {OUTPUT_CSV}!")

if __name__ == "__main__":
    generate_20_day_summary(1, 20)