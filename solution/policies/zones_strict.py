from solution.policies.helpers import get_my_zone, parcels_in_zone, build_urgent_trip, tidy_trip

def dispatch(parcel, context):
    # Step 1: only the waiting parcels in my own zone
    my_parcels = parcels_in_zone(parcel, get_my_zone(context))
    if len(my_parcels) == 0:
        return []                               # my zone is empty: wait at the hub

    # Step 2: build the trip like Rule 2, using only my zone's parcels
    trip = build_urgent_trip(my_parcels, context)

    # Step 3: tidy the order of the locations with 2-opt (Rule 3)
    return tidy_trip(my_parcels, trip, context["travel_distance"])
