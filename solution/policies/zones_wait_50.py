"""Rule 5: Zones + help + wait for a fuller van.

The only difference between the zones_wait_XX files is MIN_FILL below
(zones_wait_30 uses 0.3, zones_wait_90 uses 0.9, and so on).

Build the trip like Rule 4b. Then go only if the van is at least MIN_FILL full,
or if waiting 10 more minutes would cause a problem (a parcel would turn late,
the van could not be back by 18:00, or it is the last chance to leave).
Otherwise wait, so more parcels can arrive and fill the van.

Algorithms:      BFS (Weeks 9-10) + greedy + 2-opt (Week 11) + a "wait or go" rule
Data structures: graph (Week 9), queue (Week 5), heap + hash maps (Week 7)
Big-O per call:  O(L^2 + Z x P + P log P + k^3 per 2-opt pass)
"""

from solution.policies.helpers import (build_trip, busiest_area_parcels, get_my_area,
                                       parcels_in_area, should_go_now, tidy_trip)

MIN_FILL = 0.5   # how full the van must be, unless waiting would cause a problem


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
    trip = tidy_trip(my_parcels, trip, context["travel_distance"])
    if len(trip) == 0:
        return []

    # Step 5: go now, or wait 10 minutes for more parcels?
    if should_go_now(trip, parcel, context, MIN_FILL):
        return trip
    return []
