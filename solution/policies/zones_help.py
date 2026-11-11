"""Rule 4b: Zones with helping - own area first, help the busiest area when free.

Idea in simple words:
    Same as Rule 4a, but if a van's own area has nothing waiting, it does not
    sit idle: it helps the area with the most waiting parcels (by total size).
    The trip still stays inside one area.

Algorithms:      BFS connected components (Weeks 9-10) + greedy + 2-opt (Week 11).
Data structures: graph (Week 9), queue (Week 5), heap + hash maps (Week 7).

Complexity per dispatch call:
    as Rule 4a, plus O(L^2 + Z * P) to find the busiest area when helping.
    Total time O(L^2 + Z * P + P log P + I * k^3). Space O(L^2 + P).
"""

from typing import Dict, List

from solution.policies.helpers import (busiest_area_parcels, my_area, only_locations,
                                       urgent_nearest_2opt_trip)


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    # 1. Own area first.
    mine = only_locations(parcel, my_area(context))
    if mine:
        return urgent_nearest_2opt_trip(mine, context)

    # 2. Own area empty: help the area with the largest waiting load.
    busiest = busiest_area_parcels(parcel, context)
    if busiest is None:
        return []
    return urgent_nearest_2opt_trip(busiest, context)