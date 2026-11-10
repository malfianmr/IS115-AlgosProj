"""Rule 2: Urgent First + Nearest Neighbour.

Idea in simple words:
    1. Put all waiting parcels in a heap ordered by deadline (window end).
    2. Pop the most urgent parcel that can still arrive on time if the van
       goes straight there. Its location becomes the first stop.
       (If no parcel can still be on time, use the most urgent one anyway.)
    3. From there, fill the van with Rule 1: go to the closest location with
       waiting parcels, again and again, until full or out of range/time.
    Inside each location, the most urgent parcels are loaded first.

Algorithm:       greedy nearest-neighbour construction (Week 11), seeded by urgency.
Data structures: binary min-heap / priority queue on deadline (Week 7, heapq);
                 hash map location -> parcels (Week 7).

Complexity per dispatch call (P = parcels seen so far, L = locations, at most 36):
    collect waiting parcels: O(P log P)
    build heap (heapify):    O(P)
    pop until a feasible seed: O(k log P) for k pops, worst case O(P log P)
    group by location:       O(P)
    nearest-neighbour fill:  O(L^2)
    Total time O(P log P + L^2). Space O(P).
"""

import heapq
from typing import Dict, List

from solution.policies.helpers import EPS, HUB, can_extend, group_by_location, waiting_parcels


def pick_seed(parcel: Dict[str, dict], waiting: List[str], context: dict) -> str:
    """Return the location of the most urgent parcel that can still be on time."""

    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]

    # Min-heap keyed by (deadline, arrival time, parcel ID).
    heap = [
        (parcel[p]["delivery_window_end"], parcel[p]["arrival_time"], p)
        for p in waiting
    ]
    heapq.heapify(heap)

    fallback = None
    while heap:
        deadline, _, parcel_id = heapq.heappop(heap)
        location = parcel[parcel_id]["delivery_location_id"]
        if not can_extend(0.0, HUB, location, distances, departure, context):
            continue  # cannot reach and return in time at all
        if fallback is None:
            fallback = location  # most urgent reachable parcel
        if departure + distances[HUB][location] <= deadline:
            return location  # most urgent parcel that can still be on time
    return fallback


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    distances = context["travel_distance"]
    capacity = context["capacity"]
    departure = context["current_time"] + context["departure_delay"]

    waiting = waiting_parcels(parcel)
    if not waiting:
        return []
    seed = pick_seed(parcel, waiting, context)
    if seed is None:
        return []

    groups = group_by_location(parcel, waiting)
    # Load the most urgent parcels first within each location.
    for parcel_ids in groups.values():
        parcel_ids.sort(key=lambda p: (parcel[p]["delivery_window_end"], parcel[p]["arrival_time"], p))

    route: List[str] = []
    load = 0.0
    travelled = 0.0
    here = HUB
    next_stop = seed  # first stop chosen by urgency, the rest by distance

    while groups:
        if next_stop is None:
            for location in groups:
                if not can_extend(travelled, here, location, distances, departure, context):
                    continue
                if next_stop is None or (distances[here][location], location) < (distances[here][next_stop], next_stop):
                    next_stop = location
            if next_stop is None:
                break

        taken_any = False
        for parcel_id in groups.pop(next_stop):
            size = parcel[parcel_id]["size"]
            if load + size <= capacity + EPS:
                route.append(parcel_id)
                load += size
                taken_any = True
        if taken_any:
            travelled += distances[here][next_stop]
            here = next_stop
        next_stop = None
        if load >= capacity - EPS:
            break

    return route
