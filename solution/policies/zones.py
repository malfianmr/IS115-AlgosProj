"""Shared zone logic for Rule 4 (each van is in charge of an area).

Step A - find the areas (Week 9 graphs + Week 10 graph algorithms):
    Build a graph: every location is a vertex; join two locations with an
    edge if they are at most LINK_KM apart. Each connected component is one
    area. Components are found with breadth-first search using a queue
    (Week 5). Time O(L^2) for L locations (every pair is checked once),
    space O(L^2) for the adjacency lists in the worst case.

Step B - give vans to areas:
    Far areas take longer to reach, so they get more vans. Each area's weight
    is (number of locations x average distance from the hub). Vans are shared
    out in proportion to weight (every area gets at least one), using the
    largest-remainder method. Time O(Z log Z) for Z areas.

The result is a hash map vehicle_id -> set of locations (Week 7).
Only context["travel_distance"] and context["fleet"] are used, so no data
files are read during the simulation.
"""

from collections import deque
from typing import Dict, List, Set

from solution.policies.helpers import HUB

LINK_KM = 10.0  # two locations closer than this are in the same area


def find_areas(distances: Dict[str, Dict[str, float]]) -> List[List[str]]:
    """Connected components of the 'nearby locations' graph, using BFS."""

    locations = sorted(loc for loc in distances if loc != HUB)
    neighbours: Dict[str, List[str]] = {loc: [] for loc in locations}
    for i, a in enumerate(locations):
        for b in locations[i + 1:]:
            if min(distances[a][b], distances[b][a]) <= LINK_KM:
                neighbours[a].append(b)
                neighbours[b].append(a)

    seen: Set[str] = set()
    areas: List[List[str]] = []
    for start in locations:
        if start in seen:
            continue
        seen.add(start)
        queue = deque([start])
        area = []
        while queue:
            here = queue.popleft()
            area.append(here)
            for nxt in neighbours[here]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        areas.append(sorted(area))
    return areas


def assign_vans(areas: List[List[str]], distances: Dict[str, Dict[str, float]],
                vehicle_ids: List[int]) -> Dict[int, Set[str]]:
    """Share vans across areas in proportion to (size x average hub distance)."""

    weights = [len(area) * sum(distances[HUB][loc] for loc in area) / len(area) for area in areas]
    n_vans = len(vehicle_ids)
    total = sum(weights)
    exact = [n_vans * w / total for w in weights]
    counts = [max(1, int(x)) for x in exact]
    # Hand out remaining vans to the largest remainders; take back if over.
    order = sorted(range(len(areas)), key=lambda i: exact[i] - int(exact[i]), reverse=True)
    k = 0
    while sum(counts) < n_vans:
        counts[order[k % len(order)]] += 1
        k += 1
    while sum(counts) > n_vans:
        i = max(range(len(areas)), key=lambda i: (counts[i] - exact[i], counts[i]))
        counts[i] -= 1

    van_area: Dict[int, Set[str]] = {}
    vans = sorted(vehicle_ids)
    pos = 0
    for area, count in zip(areas, counts):
        for _ in range(count):
            van_area[vans[pos]] = set(area)
            pos += 1
    return van_area


def van_areas(context: dict) -> Dict[int, Set[str]]:
    distances = context["travel_distance"]
    return assign_vans(find_areas(distances), distances, list(context["fleet"].keys()))


def only_locations(parcel: Dict[str, dict], locations: Set[str]) -> Dict[str, dict]:
    """Waiting parcels whose destination is in `locations`. Time O(P)."""

    return {
        pid: rec for pid, rec in parcel.items()
        if rec["vehicle_assigned"] is None and rec["delivery_time"] is None
        and rec["delivery_location_id"] in locations
    }
