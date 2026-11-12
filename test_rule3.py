from solution.policies.helpers import route_length, reverse_part, two_opt, tidy_trip
from solution.policies.greedy_heap_2opt import dispatch

# ------------------------------------------------------------
# Test map: 4 locations at the corners of a square, hub below
#
#      D ──10── C
#      │        │
#     10       10        diagonals A–C and B–D = 14
#      │        │
#      A ──10── B
#        \    /
#         HUB            HUB → A or B = 7, HUB → C or D = 16
# ------------------------------------------------------------
square = {
    "HUB": {"HUB": 0,  "A": 7,  "B": 7,  "C": 16, "D": 16},
    "A":   {"HUB": 7,  "A": 0,  "B": 10, "C": 14, "D": 10},
    "B":   {"HUB": 7,  "A": 10, "B": 0,  "C": 10, "D": 14},
    "C":   {"HUB": 16, "A": 14, "B": 10, "C": 0,  "D": 10},
    "D":   {"HUB": 16, "A": 10, "B": 14, "C": 10, "D": 0},
}

print("--- Step 1: route_length")
print(route_length(["A", "C", "B", "D"], square))   # expect 61.0
print(route_length(["B", "C", "D", "A"], square))   # expect 44.0
print(route_length([], square))                     # expect 0.0

print("--- Step 2: reverse_part")
route = ["A", "C", "B", "D"]
print(reverse_part(route, 1, 2))   # expect ['A', 'B', 'C', 'D']
print(reverse_part(route, 0, 3))   # expect ['D', 'B', 'C', 'A']
print(reverse_part(route, 2, 3))   # expect ['A', 'C', 'D', 'B']
print(route)                       # expect ['A', 'C', 'B', 'D']   (original unchanged)

print("--- Step 3: two_opt")
better = two_opt(["A", "C", "B", "D"], square)
print(better)                         # expect ['B', 'C', 'D', 'A']
print(route_length(better, square))   # expect 44.0

print("--- Step 4: tidy_trip")
square_parcels = {
    "X1": {"delivery_location_id": "A"},
    "X2": {"delivery_location_id": "C"},
    "X3": {"delivery_location_id": "C"},
    "X4": {"delivery_location_id": "B"},
    "X5": {"delivery_location_id": "D"},
}
print(tidy_trip(square_parcels, ["X1", "X2", "X3", "X4", "X5"], square))
# expect ['X4', 'X2', 'X3', 'X5', 'X1']
print(tidy_trip(square_parcels, ["X1"], square))
# expect ['X1']   (only 1 parcel, nothing to reorder)

print("--- Step 5: Rule 3 dispatch")
parcel = {
    "P001": {"arrival_time": 480.0, "delivery_location_id": "L001",
             "delivery_window_start": 540.0, "delivery_window_end": 660.0,
             "size": 4.0, "delivery_time": None, "vehicle_assigned": None, "trip_id": None},
    "P002": {"arrival_time": 510.0, "delivery_location_id": "L002",
             "delivery_window_start": 540.0, "delivery_window_end": 720.0,
             "size": 6.0, "delivery_time": None, "vehicle_assigned": None, "trip_id": None},
    "P003": {"arrival_time": 480.0, "delivery_location_id": "L002",
             "delivery_window_start": 540.0, "delivery_window_end": 600.0,
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

print(dispatch(parcel, context))   # expect ['P003', 'P002', 'P001']