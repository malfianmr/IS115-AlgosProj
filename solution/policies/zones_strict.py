"""Rule 4a: Zones (strict) - each van only delivers inside its own area.

Idea in simple words:
    1. Split the town into areas automatically: join locations that are at
       most 10 km apart, and find the groups (connected components) with BFS.
    2. Give each van one area (far areas get more vans).
    3. When a van is free, it only looks at waiting parcels for its own area
       and builds the trip like Rule 3 (urgent first, nearest neighbour, 2-opt).
       If its area has nothing waiting, it stays at the hub.

Algorithms:      BFS connected components (Weeks 9-10) + greedy + 2-opt (Week 11).
Data structures: graph (Week 9), queue (Week 5), heap + hash maps (Week 7).

Complexity per dispatch call:
    find areas O(L^2) + filter parcels O(P) + Rule 3 trip on the area's parcels
    Total time O(L^2 + P log P + I * k^3), with k <= locations in one area. Space O(L^2 + P).
"""

from typing import Dict, List

from solution.policies.helpers import my_area, only_locations, urgent_nearest_2opt_trip


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    # 1-2. This van's area (BFS on the nearby-locations graph, then vans shared out).
    area = my_area(context)
    # 3. Only parcels for my area; nothing waiting -> stay at the hub.
    mine = only_locations(parcel, area)
    if not mine:
        return []
    return urgent_nearest_2opt_trip(mine, context)