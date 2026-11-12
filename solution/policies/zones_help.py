from solution.policies.helpers import (get_my_zone, parcels_in_zone, busiest_zone_parcels, build_urgent_trip, tidy_trip)
"""
    Here we experiment with the idea of the vans being only able to collect and send parcels in their own respective zones. However, if they do not have any parcels in their zone,
    they can take other people's parcel who are busy.
"""


def dispatch(parcel, context):
    #Get only the waiting parcels in my own zone
    my_parcels = parcels_in_zone(parcel, get_my_zone(context))

    #If zone is empty, go help the busiest zone instead
    if len(my_parcels) == 0:
        my_parcels = busiest_zone_parcels(parcel, context)
    if len(my_parcels) == 0:
        return []                               # every zone is empty: wait at the hub

    #Build the trip like Rule 2
    trip = build_urgent_trip(my_parcels, context)

    #Tidy with 2-opt
    return tidy_trip(my_parcels, trip, context["travel_distance"])