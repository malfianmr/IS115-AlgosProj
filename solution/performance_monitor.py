"""Calculate performance metrics from one simulation run's event log."""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from simulator.loaders import day_input_paths

HUB = "HUB"

# Cost assumptions (see report): electric vans, $ per km covers energy,
# driver time and wear; penalties cover complaints, vouchers and redelivery.
COST_PER_KM = 0.50
LATE_PENALTY = 5.0
MISSED_PENALTY = 15.0


def calculate_metrics(
    parcels: List[Dict[str, str]],
    distances: List[Dict[str, str]],
    config: Dict[str, Any],
    events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Return a JSON-serializable dictionary for the chosen performance metric.

    parcels and distances are the rows of the day's CSV files, config is the
    contents of config.json, and events are the records from the run's log.
    CSV values are strings, so convert them before calculating. In particular,
    parcel times are "HH:MM" strings while event times are minutes after
    midnight: "17:00" is 17 * 60 = 1020.
    """

    # Main metric: Total Daily Cost (lower is better)
    #   cost = km driven x COST_PER_KM
    #        + late parcels x LATE_PENALTY        (delivered after window end)
    #        + undelivered parcels x MISSED_PENALTY
    # Early deliveries (before window start) are free.

    # Look up distances quickly: dist[(origin, destination)] -> km
    dist = {}
    for row in distances:
        dist[(row["location_1"], row["location_2"])] = float(row["dist"])

    # Look up each parcel's destination and window end by its ID
    parcel_info = {}
    for row in parcels:
        parcel_info[row["parcel_id"]] = {
            "location": row["delivery_location_id"],
            "window_end": hhmm_to_minutes(row["delivery_window_end"]),
        }

    # Group deliveries by trip. The log is in time order, so each list is
    # already in the order the van visited the stops.
    trips = {}
    on_time = 0
    late = 0
    for event in events:
        if event["event_type"] != "delivery":
            continue
        key = (event["vehicle_id"], event["trip_id"])
        if key not in trips:
            trips[key] = []           # first delivery of this trip: make an empty list
        trips[key].append(event["parcel_id"])
        if event["time"] <= parcel_info[event["parcel_id"]]["window_end"]:
            on_time += 1
        else:
            late += 1

    # Km driven: HUB -> each stop in order -> back to HUB, for every trip
    total_km = 0.0
    for stops in trips.values():
        here = HUB
        for parcel_id in stops:
            there = parcel_info[parcel_id]["location"]
            total_km += dist[(here, there)]
            here = there
        total_km += dist[(here, HUB)]

    total_parcels = len(parcels)
    undelivered = total_parcels - on_time - late

    km_cost = total_km * COST_PER_KM
    late_cost = late * LATE_PENALTY
    missed_cost = undelivered * MISSED_PENALTY
    total_cost = km_cost + late_cost + missed_cost

    return {
        "total_daily_cost": round(total_cost, 2),
        "km_cost": round(km_cost, 2),
        "late_cost": round(late_cost, 2),
        "undelivered_cost": round(missed_cost, 2),
        "total_km": round(total_km, 2),
        "total_parcels": total_parcels,
        "on_time_parcels": on_time,
        "late_parcels": late,
        "undelivered_parcels": undelivered,
        "on_time_rate": round(on_time / total_parcels, 4) if total_parcels else 0.0,
        "number_of_trips": len(trips),
    }


def hhmm_to_minutes(text: str) -> float:
    """Convert "HH:MM" to minutes after midnight, e.g. "17:00" -> 1020."""

    hours, minutes = text.split(":")
    return int(hours) * 60 + int(minutes)


def main(argv: Optional[List[str]] = None) -> int:
    """Load one day's inputs and event log, then write the metrics report."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"),
                        help="directory containing dist.csv, config.json and demand/")
    parser.add_argument("--day", required=True, help="day identifier, for example day_001")
    parser.add_argument("--log", type=Path, required=True,
                        help="event log from a simulator run")
    parser.add_argument("--output", type=Path,
                        help="JSON report (default: metrics.json beside the selected log)")
    args = parser.parse_args(argv)
    try:
        parcel_path, distance_path, config_path = day_input_paths(args.data, args.day)
        output = args.output if args.output is not None else args.log.with_name("metrics.json")
        # The input files all live in the data directory, so this also protects them.
        if output.resolve() == args.data.resolve() or args.data.resolve() in output.resolve().parents:
            raise ValueError("report output must be outside the input data directory")
        if output.resolve() == args.log.resolve():
            raise ValueError("report output must not overwrite the log")
        with parcel_path.open(newline="", encoding="utf-8-sig") as stream:
            parcels = list(csv.DictReader(stream))
        with distance_path.open(newline="", encoding="utf-8-sig") as stream:
            distances = list(csv.DictReader(stream))
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        with args.log.open(encoding="utf-8") as stream:
            events = [json.loads(line) for line in stream if line.strip()]
        metrics = calculate_metrics(parcels, distances, config, events)
        report = json.dumps(metrics, indent=2, allow_nan=False) + "\n"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(f"Metrics report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
