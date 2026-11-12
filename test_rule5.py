from solution.policies.helpers import should_go_now

town = {
    "HUB": {"HUB": 0,  "L1": 20, "L2": 22, "L3": 21, "L4": 40, "L5": 42},
    "L1":  {"HUB": 20, "L1": 0,  "L2": 4,  "L3": 5,  "L4": 35, "L5": 36},
    "L2":  {"HUB": 22, "L1": 4,  "L2": 0,  "L3": 6,  "L4": 33, "L5": 34},
    "L3":  {"HUB": 21, "L1": 5,  "L2": 6,  "L3": 0,  "L4": 31, "L5": 32},
    "L4":  {"HUB": 40, "L1": 35, "L2": 33, "L3": 31, "L4": 0,  "L5": 5},
    "L5":  {"HUB": 42, "L1": 36, "L2": 34, "L3": 32, "L4": 5,  "L5": 0},
}

def make_context(time):
    return {"current_time": time, "vehicle_id": 2, "capacity": 30.0, "travel_distance": town,
            "departure_delay": 30.0, "return_cutoff": 1080.0, "max_trip_distance_km": 320.0,
            "fleet": {1: {}, 2: {}, 3: {}}}

def make_parcel(location, deadline, size):
    return {"arrival_time": 480.0, "delivery_location_id": location,
            "delivery_window_start": 540.0, "delivery_window_end": deadline,
            "size": size, "delivery_time": None, "vehicle_assigned": None, "trip_id": None}

trip = ["P2", "P3"]       # L4 then L5, total size 8 (only 27% of 30)

relaxed = {"P2": make_parcel("L4", 720.0, 5.0), "P3": make_parcel("L5", 720.0, 3.0)}
tight   = {"P2": make_parcel("L4", 720.0, 5.0), "P3": make_parcel("L5", 620.0, 3.0)}

print("A:", should_go_now(trip, relaxed, make_context(540.0), 0.9))   # expect False (wait)
print("B:", should_go_now(trip, relaxed, make_context(540.0), 0.2))   # expect True  (full enough)
print("C:", should_go_now(trip, tight,   make_context(540.0), 0.9))   # expect True  (P3 would turn late)
print("D:", should_go_now(trip, relaxed, make_context(1040.0), 0.9))  # expect True  (last chance)