from solution.policies.helpers import (get_my_zone, parcels_in_zone, busiest_zone_parcels, build_urgent_trip, tidy_trip, should_go_now)

"""
    For now, before this policy Vans just go deliver straight away if they have parcels to deliver. However, we now wait until a certain percentage of load before the van goes.
"""

MIN_FILL = 0.3   # the van must be 90% full, unless waiting would cause a problem


def dispatch(parcel, context):
    #Only the waiting parcels in my own zone
    my_parcels = parcels_in_zone(parcel, get_my_zone(context))

    #My zone is empty, so help the busiest zone
    if len(my_parcels) == 0:
        my_parcels = busiest_zone_parcels(parcel, context)
    if len(my_parcels) == 0:
        return []

    #Build the trip (Rule 2) and tidy it (Rule 3)
    trip = build_urgent_trip(my_parcels, context)
    trip = tidy_trip(my_parcels, trip, context["travel_distance"])
    if len(trip) == 0:
        return []

    #Go now, or wait 10 minutes for more parcels?
    if should_go_now(trip, parcel, context, MIN_FILL):
        return trip
    return []