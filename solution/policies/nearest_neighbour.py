"""Rule 1: Nearest Neighbour (greedy).

The van starts at the hub, drives to the closest stop with waiting parcels and
loads what fits, then the next closest stop, and so on, until it is full or
nothing else can be reached in time.

Algorithm:      greedy nearest neighbour for TSP (Week 11)
Data structure: hash map stop -> parcels (Week 7)
Big-O per call: O(P log P + L^2)
Deadlines are not used by this rule.
"""

from solution.policies.helpers import fill_van, get_waiting_parcels, group_by_stop


def dispatch(parcel, context):
    # Step 1: all waiting parcels, oldest first
    waiting = get_waiting_parcels(parcel)

    # Step 2: group them by stop (hash map)
    groups = group_by_stop(parcel, waiting)

    # Step 3: from the hub, keep driving to the closest stop (no special first stop)
    return fill_van(parcel, context, groups, None)
