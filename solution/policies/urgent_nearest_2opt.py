"""Rule 3: Urgent First + Nearest Neighbour + 2-opt local search.

Idea in simple words:
    1. Build the trip exactly like Rule 2 (which parcels go, and a first order).
    2. Look at the list of stops (locations). Try every 2-opt move: cut the
       route in two places and reverse the middle part. If the route gets
       shorter, keep the change. Repeat until no move makes it shorter
       (a "2-opt optimal" route: no crossings).
    3. Deliver parcels in the improved stop order.
    The set of parcels does not change, so capacity still holds, and the
    route can only get shorter, so range and the 18:00 return still hold.

Algorithms:      greedy construction (Rule 2) + 2-opt local search (Week 11).
Data structures: heap and hash map from Rule 2 (Week 7).

Complexity per dispatch call (P = parcels seen so far, k = stops in the trip):
    Rule 2 construction:        O(P log P + L^2)
    one 2-opt pass:             O(k^2) moves, each checked in O(k) -> O(k^3)
                                (route length is recomputed for simplicity)
    passes until no improvement: bounded by a fixed cap (MAX_PASSES)
    Total time O(P log P + L^2 + MAX_PASSES * k^3). Space O(P + k).
    k is small in practice (most trips have under 25 stops).
"""

from typing import Dict, List

from solution.policies.helpers import EPS, route_distance
from solution.policies.urgent_nearest import dispatch as rule2_dispatch

MAX_PASSES = 50  # safety cap on improvement passes


def two_opt(stops: List[str], distances: Dict[str, Dict[str, float]]) -> List[str]:
    """Improve the order of stops with 2-opt until no move shortens the route."""

    best = list(stops)
    best_km = route_distance(best, distances)
    for _ in range(MAX_PASSES):
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                candidate_km = route_distance(candidate, distances)
                if candidate_km < best_km - EPS:
                    best, best_km = candidate, candidate_km
                    improved = True
        if not improved:
            break
    return best


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    route = rule2_dispatch(parcel, context)
    if len(route) < 2:
        return route

    # Stop list in first-visit order, with the parcels for each stop.
    stops: List[str] = []
    by_stop: Dict[str, List[str]] = {}
    for parcel_id in route:
        location = parcel[parcel_id]["delivery_location_id"]
        if location not in by_stop:
            stops.append(location)
            by_stop[location] = []
        by_stop[location].append(parcel_id)

    better_stops = two_opt(stops, context["travel_distance"])
    return [parcel_id for location in better_stops for parcel_id in by_stop[location]]
