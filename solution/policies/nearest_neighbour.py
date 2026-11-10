"""Rule 1: Nearest Neighbour (greedy).

Idea in simple words:
    The van starts at the hub. It drives to the closest location that has
    waiting parcels and takes all of them (as many as fit). From there it goes
    to the next closest location with waiting parcels, and so on, until the van
    is full or no more stops fit within range and the 18:00 return time.

Algorithm:      greedy nearest-neighbour TSP construction (Week 11).
Data structure: hash map location -> waiting parcels (Week 7), so all parcels
                for one place can be taken in one step.

Complexity per dispatch call (P = parcels seen so far, L = locations with
waiting parcels, at most 36):
    collect + sort waiting parcels: O(P log P)
    group by location (hash map):    O(P)
    greedy loop: up to L stops, each scanning up to L candidates: O(L^2)
    Total time O(P log P + L^2). Space O(P).
Delivery windows are ignored by this rule.
"""

from typing import Dict, List

from solution.policies.helpers import EPS, HUB, can_extend, group_by_location, waiting_parcels


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    distances = context["travel_distance"]
    capacity = context["capacity"]
    departure = context["current_time"] + context["departure_delay"]

    groups = group_by_location(parcel, waiting_parcels(parcel))

    route: List[str] = []
    load = 0.0
    travelled = 0.0  # km from the hub to the current stop
    here = HUB

    while groups:
        # Greedy choice: the closest location we can still reach and return from.
        best = None
        for location in groups:
            if not can_extend(travelled, here, location, distances, departure, context):
                continue
            if best is None or (distances[here][location], location) < (distances[here][best], best):
                best = location
        if best is None:
            break

        # Take as many parcels for this location as still fit (arrival order).
        taken_any = False
        for parcel_id in groups.pop(best):
            size = parcel[parcel_id]["size"]
            if load + size <= capacity + EPS:
                route.append(parcel_id)
                load += size
                taken_any = True
        if taken_any:
            travelled += distances[here][best]
            here = best
        if load >= capacity - EPS:
            break

    return route
