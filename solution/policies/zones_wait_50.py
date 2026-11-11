"""Rule 5: Zones + help + wait for a fuller van.

The only difference between the zones_wait_XX files is MIN_FILL below
(zones_wait_30 uses 0.3, zones_wait_90 uses 0.9, and so on).

Idea in simple words:
    1. Build the trip exactly like Rule 4b (own area first, else help the
       busiest area; urgent first stop, nearest neighbour, 2-opt).
    2. Decide: go now, or wait 10 minutes for more parcels?
         - Go if the van is at least MIN_FILL full.
         - Otherwise go anyway if waiting would cause harm: a parcel on this
           trip would turn late, the van could no longer be back by 18:00,
           or this is the last planning round.
         - Otherwise wait (return []), so more parcels can fill the van.

Algorithms:      BFS (Weeks 9-10) + greedy + 2-opt (Week 11) + a threshold heuristic.
Data structures: graph (Week 9), queue (Week 5), heap + hash maps (Week 7).

Complexity per dispatch call:
    as Rule 4b, plus O(k) for the go-or-wait check.
    Total time O(L^2 + Z * P + P log P + I * k^3). Space O(L^2 + P).
"""

from typing import Dict, List

from solution.policies.helpers import (busiest_area_parcels, go_now, my_area, only_locations,
                                       urgent_nearest_2opt_trip)

MIN_FILL = 0.5  # share of capacity needed before a van leaves without a reason to hurry


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    # 1. Build the trip like Rule 4b: own area first, else help the busiest area.
    mine = only_locations(parcel, my_area(context))
    if mine:
        route = urgent_nearest_2opt_trip(mine, context)
    else:
        busiest = busiest_area_parcels(parcel, context)
        route = urgent_nearest_2opt_trip(busiest, context) if busiest is not None else []
    if not route:
        return []

    # 2. Go now, or wait for a fuller van?
    if go_now(route, parcel, context, MIN_FILL):
        return route
    return []