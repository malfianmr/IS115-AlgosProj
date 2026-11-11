"""Rule 4b: Zones with helping - own area first, help the busiest area when free.

Same as Rule 4a, but if a van's own area is empty, it helps the area with the
most waiting parcels (by total size). The trip still stays inside one area.

Algorithms:      BFS (Weeks 9-10) + greedy + 2-opt (Week 11)
Data structures: graph (Week 9), queue (Week 5), heap + hash maps (Week 7)
Big-O per call:  O(L^2 + Z x P + P log P + k^3 per 2-opt pass)
"""

from solution.policies.helpers import (build_trip, busiest_area_parcels, get_my_area,
                                       parcels_in_area, tidy_trip)


def dispatch(parcel, context):
    # Step 1: parcels waiting in my own area
    my_parcels = parcels_in_area(parcel, get_my_area(context))

    # Step 2: if my area is empty, help the busiest area instead
    if len(my_parcels) == 0:
        my_parcels = busiest_area_parcels(parcel, context)
    if len(my_parcels) == 0:
        return []                                    # nothing anywhere: stay at the hub

    # Step 3: build the trip (urgent stop first, then closest stop next)
    trip = build_trip(my_parcels, context)

    # Step 4: tidy the order of the stops with 2-opt
    return tidy_trip(my_parcels, trip, context["travel_distance"])
