"""Rule 4a: Zones (strict) - each van only delivers inside its own area.

Idea in simple words:
    The town is split into areas automatically (see zones.py). Each van is
    given one area. When a van is free, it only looks at waiting parcels for
    its own area and builds the trip with Rule 3 (urgent first, nearest
    neighbour, then 2-opt). If its area has nothing waiting, it stays at the hub.

Algorithms:      BFS connected components (Week 10) + Rule 3 (Week 11).
Data structures: graph (Week 9), queue (Week 5), heap + hash maps (Week 7).

Complexity per dispatch call: O(L^2) to find areas + O(P) to filter parcels
    + Rule 3 on the area's parcels. Space O(L^2 + P).
"""

from typing import Dict, List

from solution.policies.urgent_nearest_2opt import dispatch as rule3_dispatch
from solution.policies.zones import only_locations, van_areas


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    my_area = van_areas(context)[context["vehicle_id"]]
    mine = only_locations(parcel, my_area)
    if not mine:
        return []
    return rule3_dispatch(mine, context)
