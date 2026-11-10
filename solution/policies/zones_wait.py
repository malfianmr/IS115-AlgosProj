"""Shared logic for Rule 5: Zones + help + "wait for a fuller van".

Idea in simple words:
    Build the trip exactly like Rule 4b. Then decide: go now, or wait?
      - Go if the van is at least MIN_FILL full (e.g. 50% of capacity).
      - Otherwise, go anyway if waiting 10 more minutes would cause harm:
          * a parcel on this trip that is on time now would become late, or
          * the trip would no longer fit before the 18:00 return, or
          * this is the last planning round of the day.
      - Otherwise wait (return []), so more parcels can arrive and fill the van.

This is the "wait vs go now" trade-off: waiting fills vans (fewer km per
parcel) but risks late parcels.

Complexity per dispatch call: Rule 4b + O(k) to check the trip's arrival
times (k = parcels on the trip). Space as Rule 4b.

Each zones_wait_XX.py module calls dispatch_with_wait with its own MIN_FILL,
so each setting gets its own results folder.
"""

from typing import Dict, List

from solution.policies.helpers import HUB
from solution.policies.zones_help import dispatch as rule4b_dispatch

PLANNING_INTERVAL = 10.0  # minutes between planning rounds (from the brief)


def harm_if_wait(route: List[str], parcel: Dict[str, dict], context: dict) -> bool:
    """True if delaying this trip by one planning round would hurt."""

    distances = context["travel_distance"]
    now = context["current_time"]
    delay = context["departure_delay"]
    later = now + PLANNING_INTERVAL

    # Last chance: no later planning round can still depart before the cutoff.
    if later + delay >= context["return_cutoff"]:
        return True

    depart_now = now + delay
    km = 0.0
    here = HUB
    for parcel_id in route:
        there = parcel[parcel_id]["delivery_location_id"]
        km += distances[here][there]
        here = there
        deadline = parcel[parcel_id]["delivery_window_end"]
        # On time if we go now, late if we leave 10 minutes later.
        if depart_now + km <= deadline < depart_now + PLANNING_INTERVAL + km:
            return True
    km += distances[here][HUB]
    # Trip would no longer fit before the return cutoff.
    return depart_now + PLANNING_INTERVAL + km > context["return_cutoff"]


def dispatch_with_wait(parcel: Dict[str, dict], context: dict, min_fill: float) -> List[str]:
    route = rule4b_dispatch(parcel, context)
    if not route:
        return route
    load = sum(parcel[p]["size"] for p in route)
    if load >= min_fill * context["capacity"]:
        return route
    if harm_if_wait(route, parcel, context):
        return route
    return []
