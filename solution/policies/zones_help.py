"""Rule 4b: Zones with helping - own area first, help the busiest area when free.

Idea in simple words:
    Same as Rule 4a, but if a van's own area has nothing waiting, it does not
    sit idle: it helps the area with the most waiting parcels (by total size),
    building that trip with Rule 3. The trip still stays inside one area.

Algorithms / data structures: as Rule 4a.
Complexity per dispatch call: as Rule 4a, plus O(P) to total the waiting
    load in each area. Space O(L^2 + P).
"""

from typing import Dict, List

from solution.policies.urgent_nearest_2opt import dispatch as rule3_dispatch
from solution.policies.zones import find_areas, only_locations, van_areas


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    my_area = van_areas(context)[context["vehicle_id"]]
    mine = only_locations(parcel, my_area)
    if mine:
        return rule3_dispatch(mine, context)

    # Own area is empty: help the area with the largest waiting load.
    best, best_load = None, 0.0
    for area in find_areas(context["travel_distance"]):
        waiting = only_locations(parcel, set(area))
        load = sum(rec["size"] for rec in waiting.values())
        if load > best_load:
            best, best_load = waiting, load
    if best is None:
        return []
    return rule3_dispatch(best, context)
