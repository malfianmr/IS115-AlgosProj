"""Rule 3: Urgent First + Nearest Neighbour + 2-opt local search.

Idea in simple words:
    1. Build the trip exactly like Rule 2 (urgent first stop, then nearest neighbour).
    2. Improve the order of the stops with 2-opt: reverse a part of the route
       whenever that makes the route shorter, until no reversal helps.
    The parcels on the van do not change, and the route can only get shorter,
    so capacity, range and the 18:00 return still hold.

Algorithms:      greedy construction (Week 11) + 2-opt local search (Week 11).
Data structures: heap and hash map (Week 7).

Complexity per dispatch call:
    Rule 2 trip O(P log P + L^2) + 2-opt O(I * k^3)
    Total time O(P log P + L^2 + I * k^3). Space O(P + k).
"""

from typing import Dict, List

from solution.policies.helpers import improve_with_two_opt, urgent_nearest_trip


def dispatch(parcel: Dict[str, dict], context: dict) -> List[str]:
    # 1. Which parcels, and a first order: urgent first stop + nearest neighbour.
    route = urgent_nearest_trip(parcel, context)
    # 2. Local search: shorten the stop order with 2-opt.
    return improve_with_two_opt(parcel, route, context["travel_distance"])