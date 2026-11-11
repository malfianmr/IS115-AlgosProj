"""Rule 4a: Zones (strict) - each van only delivers inside its own area.

The stops are split into areas (stops 10 km or less apart are linked; BFS finds
the groups). Each van gets one area; far areas get more vans. A van only builds
trips from its own area's parcels, like Rule 3. If its area is empty, it waits.

Algorithms:      BFS (Weeks 9-10) + greedy + 2-opt (Week 11)
Data structures: graph (Week 9), queue (Week 5), heap + hash maps (Week 7)
Big-O per call:  O(L^2 + P log P + k^3 per 2-opt pass)
"""

from solution.policies.helpers import build_trip, get_my_area, parcels_in_area, tidy_trip


def dispatch(parcel, context):
    # Step 1: parcels waiting in my own area
    my_parcels = parcels_in_area(parcel, get_my_area(context))
    if len(my_parcels) == 0:
        return []                                    # my area is empty: stay at the hub

    # Step 2: build the trip like Rule 2, using only my area's parcels
    trip = build_trip(my_parcels, context)

    # Step 3: tidy the order of the stops with 2-opt
    return tidy_trip(my_parcels, trip, context["travel_distance"])
