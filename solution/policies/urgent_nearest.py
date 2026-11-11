"""Rule 2: Urgent First + Nearest Neighbour.

A heap finds the most urgent parcel that can still arrive on time; its stop
is visited first. After that the van keeps driving to the closest stop, like
Rule 1. At each stop, the most urgent parcels are loaded first.

Algorithm:       greedy nearest neighbour (Week 11), started at the most urgent stop
Data structures: heap / priority queue (Week 7), hash map (Week 7)
Big-O per call:  O(P log P + L^2)
"""

from solution.policies.helpers import build_trip


def dispatch(parcel, context):
    # Most urgent stop first (heap), then the closest stop each time
    return build_trip(parcel, context)
