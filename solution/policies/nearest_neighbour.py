"""Rule 1: Nearest Neighbour (greedy).

Idea in simple words:
    The van starts at the hub. It drives to the closest location that has
    waiting parcels and takes all of them (as many as fit). From there it goes
    to the next closest location with waiting parcels, and so on, until the van
    is full or no more stops fit within range and the 18:00 return time.

Algorithm:      greedy nearest-neighbour TSP construction (Week 11).
Data structure: hash map location -> waiting parcels (Week 7).

Complexity per dispatch call:
    waiting parcels (sort) O(P log P) + group by location O(P) + greedy fill O(L^2)
    Total time O(P log P + L^2). Space O(P).
Delivery windows are ignored by this rule.
"""

from typing import Dict, List

from solution.policies.helpers import group_by_location, nearest_neighbour_fill, waiting_parcels


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    # 1. Hash map: location -> its waiting parcels (arrival order).
    groups = group_by_location(parcel, waiting_parcels(parcel))
    # 2. Greedy: from the hub, always go to the closest location next.
    return nearest_neighbour_fill(parcel, context, groups)