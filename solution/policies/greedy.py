from solution.policies.helpers import get_waiting_parcels, group_by_location, fill_van

"""
We try to use Greedy 1 for the first experiment algorithm as this seems like
a TSP problem
"""

def dispatch(parcel, context):
    waiting = get_waiting_parcels(parcel)
    groups = group_by_location(parcel, waiting)
    return fill_van(parcel, context, groups)