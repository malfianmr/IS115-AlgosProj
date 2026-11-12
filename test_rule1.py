from solution.policies.greedy import dispatch

parcel = {
    "P001": {"arrival_time": 480.0, "delivery_location_id": "L001",
             "delivery_window_start": 540.0, "delivery_window_end": 660.0,
             "size": 4.0, "delivery_time": None, "vehicle_assigned": None, "trip_id": None},
    "P002": {"arrival_time": 510.0, "delivery_location_id": "L002",
             "delivery_window_start": 540.0, "delivery_window_end": 720.0,
             "size": 6.0, "delivery_time": None, "vehicle_assigned": None, "trip_id": None},
    "P003": {"arrival_time": 480.0, "delivery_location_id": "L002",
             "delivery_window_start": 540.0, "delivery_window_end": 720.0,
             "size": 2.0, "delivery_time": None, "vehicle_assigned": None, "trip_id": None},
}

context = {
    "current_time": 540.0, "vehicle_id": 1, "capacity": 30.0,
    "travel_distance": {
        "HUB":  {"HUB": 0.0,  "L001": 10.0, "L002": 15.0},
        "L001": {"HUB": 10.0, "L001": 0.0,  "L002": 8.0},
        "L002": {"HUB": 15.0, "L001": 8.0,  "L002": 0.0},
    },
    "departure_delay": 30.0, "return_cutoff": 1080.0, "max_trip_distance_km": 320.0,
    "fleet": {1: {"available_at": 540.0, "max_trip_distance_km": 320.0}},
}

print(dispatch(parcel, context))