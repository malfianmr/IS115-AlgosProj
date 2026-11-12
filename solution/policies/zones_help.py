from solution.policies.helpers import (get_my_zone, parcels_in_zone, busiest_zone_parcels, build_urgent_trip, tidy_trip)


def dispatch(parcel, context):
    # Step 1: only the waiting parcels in my own zone
    my_parcels = parcels_in_zone(parcel, get_my_zone(context))

    # Step 2: my zone is empty, so help the busiest zone instead
    if len(my_parcels) == 0:
        my_parcels = busiest_zone_parcels(parcel, context)
    if len(my_parcels) == 0:
        return []                               # every zone is empty: wait at the hub

    # Step 3: build the trip like Rule 2
    trip = build_urgent_trip(my_parcels, context)

    # Step 4: tidy with 2-opt
    return tidy_trip(my_parcels, trip, context["travel_distance"])