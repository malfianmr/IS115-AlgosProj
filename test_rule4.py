from solution.policies.helpers import (build_zone_links, build_zones, share_vans,
                                       get_my_zone, parcels_in_zone)

# ------------------------------------------------------------
# Test town: two zones
#   Zone A: L1, L2, L3 (4-6 km apart, about 20 km from the hub)
#   Zone B: L4, L5     (5 km apart, about 40 km from the hub)
#   The two zones are 30+ km apart.
# ------------------------------------------------------------
town = {
    "HUB": {"HUB": 0,  "L1": 20, "L2": 22, "L3": 21, "L4": 40, "L5": 42},
    "L1":  {"HUB": 20, "L1": 0,  "L2": 4,  "L3": 5,  "L4": 35, "L5": 36},
    "L2":  {"HUB": 22, "L1": 4,  "L2": 0,  "L3": 6,  "L4": 33, "L5": 34},
    "L3":  {"HUB": 21, "L1": 5,  "L2": 6,  "L3": 0,  "L4": 31, "L5": 32},
    "L4":  {"HUB": 40, "L1": 35, "L2": 33, "L3": 31, "L4": 0,  "L5": 5},
    "L5":  {"HUB": 42, "L1": 36, "L2": 34, "L3": 32, "L4": 5,  "L5": 0},
}

print("--- Step 1: build_zone_links")
print(build_zone_links(town))
# expect {'L1': ['L2', 'L3'], 'L2': ['L1', 'L3'], 'L3': ['L1', 'L2'], 'L4': ['L5'], 'L5': ['L4']}

print("--- Step 2: build_zones")
zones = build_zones(town)
print(zones)
# expect [['L1', 'L2', 'L3'], ['L4', 'L5']]

print("--- Step 3: share_vans (3 vans)")
van_zone = share_vans(zones, town, [1, 2, 3])
for van in van_zone:
    print(van, sorted(van_zone[van]))
# expect:
# 1 ['L1', 'L2', 'L3']
# 2 ['L4', 'L5']
# 3 ['L4', 'L5']

print("--- Step 4a: get_my_zone (van 2)")
def make_context(vehicle_id):
    return {
        "current_time": 540.0, "vehicle_id": vehicle_id, "capacity": 30.0,
        "travel_distance": town,
        "departure_delay": 30.0, "return_cutoff": 1080.0, "max_trip_distance_km": 320.0,
        "fleet": {1: {}, 2: {}, 3: {}},
    }

print(sorted(get_my_zone(make_context(2))))     # expect ['L4', 'L5']
print(sorted(get_my_zone(make_context(1))))     # expect ['L1', 'L2', 'L3']

print("--- Step 4b: parcels_in_zone")
zone_parcels = {
    "Q1": {"delivery_location_id": "L1", "vehicle_assigned": None, "delivery_time": None},
    "Q2": {"delivery_location_id": "L4", "vehicle_assigned": None, "delivery_time": None},
    "Q3": {"delivery_location_id": "L5", "vehicle_assigned": 3,    "delivery_time": None},
    "Q4": {"delivery_location_id": "L5", "vehicle_assigned": None, "delivery_time": None},
}
print(sorted(parcels_in_zone(zone_parcels, {"L4", "L5"})))   # expect ['Q2', 'Q4']


# ------------------------------------------------------------
# Full parcels for the policy tests (Sections 5 and 6)
# ------------------------------------------------------------
def make_parcel(arrival, location, deadline, size, assigned=None):
    return {"arrival_time": arrival, "delivery_location_id": location,
            "delivery_window_start": 540.0, "delivery_window_end": deadline,
            "size": size, "delivery_time": None, "vehicle_assigned": assigned, "trip_id": None}

parcel = {
    "P1": make_parcel(480.0, "L1", 700.0, 4.0),     # zone A
    "P2": make_parcel(480.0, "L4", 720.0, 5.0),     # zone B
    "P3": make_parcel(490.0, "L5", 720.0, 3.0),     # zone B
}

# Same parcels, but P1 is already on a van, so zone A has nothing waiting
parcel_zone_a_empty = {
    "P1": make_parcel(480.0, "L1", 700.0, 4.0, assigned=3),
    "P2": make_parcel(480.0, "L4", 720.0, 5.0),
    "P3": make_parcel(490.0, "L5", 720.0, 3.0),
}


# ---- Section 5: zones_strict.py  (remove the # once the file is written) ----
# from solution.policies.zones_strict import dispatch as strict_dispatch
# print("--- Step 5: zones_strict")
# print(strict_dispatch(parcel, make_context(1)))               # expect ['P1']
# print(strict_dispatch(parcel, make_context(2)))               # expect ['P2', 'P3']
# print(strict_dispatch(parcel_zone_a_empty, make_context(1)))  # expect []   (my zone is empty: wait)


# ---- Section 6: zones_help.py  (remove the # once the file is written) ----
# from solution.policies.zones_help import dispatch as help_dispatch
# print("--- Step 6: zones_help")
# print(help_dispatch(parcel, make_context(1)))                 # expect ['P1']
# print(help_dispatch(parcel_zone_a_empty, make_context(1)))    # expect ['P2', 'P3']   (helps zone B)