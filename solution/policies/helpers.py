"""Shared helper functions for the dispatch policies.

Only the Python standard library is used. All inputs are treated as read-only.
"""

from typing import Dict, List

HUB = "HUB"
EPS = 1e-9  # small tolerance for float rounding when sizes add up exactly to capacity


def waiting_parcels(parcel: Dict[str, dict]) -> List[str]:
    """Return IDs of parcels not yet assigned or delivered, in arrival order.

    Time: O(P log P) for P parcels seen so far (the sort). Space: O(P).
    """

    waiting = [
        parcel_id
        for parcel_id, record in parcel.items()
        if record["vehicle_assigned"] is None and record["delivery_time"] is None
    ]
    waiting.sort(key=lambda parcel_id: (parcel[parcel_id]["arrival_time"], parcel_id))
    return waiting


def group_by_location(parcel: Dict[str, dict], parcel_ids: List[str]) -> Dict[str, List[str]]:
    """Hash map: location ID -> list of parcel IDs going there (order kept).

    Time: O(n) for n parcel IDs. Space: O(n).
    """

    groups: Dict[str, List[str]] = {}
    for parcel_id in parcel_ids:
        location = parcel[parcel_id]["delivery_location_id"]
        groups.setdefault(location, []).append(parcel_id)
    return groups


def can_extend(
    travelled: float,
    here: str,
    there: str,
    distances: Dict[str, Dict[str, float]],
    departure: float,
    context: dict,
) -> bool:
    """True if the van can go here -> there and still get back to the hub in range and on time.

    travelled is the km from the hub to `here` (not counting the return leg).
    At 60 km/h, km equals minutes. Time: O(1).
    """

    round_trip = travelled + distances[here][there] + distances[there][HUB]
    if round_trip > context["max_trip_distance_km"] + EPS:
        return False
    return departure + round_trip <= context["return_cutoff"]


def route_distance(locations: List[str], distances: Dict[str, Dict[str, float]]) -> float:
    """Total km for HUB -> locations in order -> HUB. Time: O(k) for k stops."""

    total = 0.0
    here = HUB
    for there in locations:
        total += distances[here][there]
        here = there
    return total + distances[here][HUB]
