from solution.policies.helpers import build_urgent_trip, tidy_trip

"""
Now, we try to improve the trip. The trips may have cross sections
and the route is not optimized, we try to make the route more efficient by 
using the algorithm 2-Opt.
"""

def dispatch(parcel, context):
    trip = build_urgent_trip(parcel, context)        
    return tidy_trip(parcel, trip, context["travel_distance"])