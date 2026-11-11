"""Rule 3: Urgent First + Nearest Neighbour + 2-opt.

Build the trip like Rule 2, then tidy the order of the stops with 2-opt:
keep reversing a part of the route while that makes it shorter.
The parcels do not change and the route only gets shorter, so no limit can be broken.

Algorithms:      greedy (Week 11) + 2-opt local search (Week 11)
Data structures: heap and hash map (Week 7)
Big-O per call:  O(P log P + L^2 + k^3 per 2-opt pass)
"""

from solution.policies.helpers import build_trip, tidy_trip


def dispatch(parcel, context):
    # Step 1: build the trip like Rule 2
    trip = build_trip(parcel, context)

    # Step 2: tidy the order of the stops with 2-opt
    return tidy_trip(parcel, trip, context["travel_distance"])
