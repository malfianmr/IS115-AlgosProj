"""Shared helper functions for all dispatch policies.

Every policy file imports only from this module, as the project brief asks.
The helpers are grouped by the idea they belong to:

    A. Basic tools               (waiting parcels, grouping, range/time checks)
    B. Greedy nearest neighbour  (Week 11 greedy TSP; Week 7 hash map)
    C. Urgency                   (Week 7 heap / priority queue)
    D. 2-opt local search        (Week 11 local search)
    E. Zones                     (Week 9 graph + BFS; Week 5 queue; Week 7 hash map)
    F. Waiting for a fuller van  (threshold heuristic)

Only the Python standard library is used. Inputs are never modified.

Notation used in the complexity notes:
    P = parcels seen so far, L = locations (36), k = stops in one trip,
    Z = areas (6), I = 2-opt passes (at most MAX_PASSES).
"""

import heapq
from collections import deque
from typing import Dict, List, Optional, Set

HUB = "HUB"
EPS = 1e-9            # tolerance for float rounding when sizes add up exactly to capacity
MAX_PASSES = 50       # safety cap on 2-opt improvement passes
LINK_KM = 10.0        # two locations at most this far apart are in the same area
PLANNING_INTERVAL = 10.0  # minutes between planning rounds (from the brief)


# ---------------------------------------------------------------------------
# A. Basic tools
# ---------------------------------------------------------------------------

def waiting_parcels(parcel: Dict[str, dict]) -> List[str]:
    """IDs of parcels not yet assigned or delivered, in arrival order.

    Time O(P log P) (the sort). Space O(P).
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

    Time O(n) for n parcel IDs. Space O(n).
    """

    groups: Dict[str, List[str]] = {}
    for parcel_id in parcel_ids:
        location = parcel[parcel_id]["delivery_location_id"]
        groups.setdefault(location, []).append(parcel_id)
    return groups


def can_extend(travelled: float, here: str, there: str,
               distances: Dict[str, Dict[str, float]], departure: float, context: dict) -> bool:
    """True if the van can go here -> there and still get back to the hub in range and on time.

    travelled = km from the hub to `here` (not counting the return leg).
    At 60 km/h, km equals minutes. Time O(1).
    """

    round_trip = travelled + distances[here][there] + distances[there][HUB]
    if round_trip > context["max_trip_distance_km"] + EPS:
        return False
    return departure + round_trip <= context["return_cutoff"]


def route_distance(locations: List[str], distances: Dict[str, Dict[str, float]]) -> float:
    """Total km for HUB -> locations in order -> HUB. Time O(k)."""

    total = 0.0
    here = HUB
    for there in locations:
        total += distances[here][there]
        here = there
    return total + distances[here][HUB]


# ---------------------------------------------------------------------------
# B. Greedy nearest neighbour (Week 11 "1st greedy algorithm for TSP")
# ---------------------------------------------------------------------------

def nearest_neighbour_fill(parcel: Dict[str, dict], context: dict,
                           groups: Dict[str, List[str]],
                           first_stop: Optional[str] = None) -> List[str]:
    """Build one trip greedily: always drive to the closest location with waiting parcels.

    groups     : hash map location -> parcels (the loading order inside each list is kept)
    first_stop : if given, the first stop is this location instead of the closest one

    At each stop, take as many of that location's parcels as still fit.
    Stop when the van is full or no location can be reached and returned from in time.
    The `groups` dictionary is consumed (popped) as stops are visited.

    Time O(L^2): up to L stops, each scanning up to L candidates. Space O(k).
    """

    distances = context["travel_distance"]
    capacity = context["capacity"]
    departure = context["current_time"] + context["departure_delay"]

    route: List[str] = []
    load = 0.0
    travelled = 0.0  # km from the hub to the current stop
    here = HUB
    next_stop = first_stop

    while groups:
        if next_stop is None:
            # Greedy choice: the closest location we can still reach and return from.
            for location in groups:
                if not can_extend(travelled, here, location, distances, departure, context):
                    continue
                if next_stop is None or (distances[here][location], location) < (distances[here][next_stop], next_stop):
                    next_stop = location
            if next_stop is None:
                break

        # Take as many parcels for this location as still fit.
        taken_any = False
        for parcel_id in groups.pop(next_stop):
            size = parcel[parcel_id]["size"]
            if load + size <= capacity + EPS:
                route.append(parcel_id)
                load += size
                taken_any = True
        if taken_any:
            travelled += distances[here][next_stop]
            here = next_stop
        next_stop = None
        if load >= capacity - EPS:
            break

    return route


# ---------------------------------------------------------------------------
# C. Urgency (Week 7 heap / priority queue)
# ---------------------------------------------------------------------------

def urgency_key(parcel: Dict[str, dict], parcel_id: str):
    """Sort key: earliest deadline first, then earliest arrival, then ID."""

    record = parcel[parcel_id]
    return (record["delivery_window_end"], record["arrival_time"], parcel_id)


def pick_urgent_first_stop(parcel: Dict[str, dict], waiting: List[str], context: dict) -> Optional[str]:
    """Location of the most urgent parcel that can still be delivered on time.

    All waiting parcels go into a min-heap keyed by deadline. We pop until we
    find a parcel the van can reach on time (driving straight there). If none
    can be on time, the most urgent reachable parcel is used instead.

    Time O(P) to heapify + O(log P) per pop, worst case O(P log P). Space O(P).
    """

    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]

    heap = [urgency_key(parcel, p) for p in waiting]
    heapq.heapify(heap)

    fallback = None
    while heap:
        deadline, _, parcel_id = heapq.heappop(heap)
        location = parcel[parcel_id]["delivery_location_id"]
        if not can_extend(0.0, HUB, location, distances, departure, context):
            continue  # cannot reach and return in time at all
        if fallback is None:
            fallback = location  # most urgent reachable parcel
        if departure + distances[HUB][location] <= deadline:
            return location  # most urgent parcel that can still be on time
    return fallback


def urgent_nearest_trip(parcel: Dict[str, dict], context: dict) -> List[str]:
    """Rule 2's trip: urgent first stop (heap), then greedy nearest neighbour.

    Inside each location the most urgent parcels are loaded first.
    Time O(P log P + L^2). Space O(P).
    """

    waiting = waiting_parcels(parcel)
    if not waiting:
        return []
    first_stop = pick_urgent_first_stop(parcel, waiting, context)
    if first_stop is None:
        return []

    groups = group_by_location(parcel, waiting)
    for parcel_ids in groups.values():
        parcel_ids.sort(key=lambda p: urgency_key(parcel, p))
    return nearest_neighbour_fill(parcel, context, groups, first_stop=first_stop)


# ---------------------------------------------------------------------------
# D. 2-opt local search (Week 11)
# ---------------------------------------------------------------------------

def two_opt(stops: List[str], distances: Dict[str, Dict[str, float]]) -> List[str]:
    """Improve the order of stops with 2-opt until no move shortens the route.

    A 2-opt move reverses one segment of the route (removes two edges and
    reconnects the tour). Keep any move that makes the route shorter.
    Time O(k^2) moves per pass x O(k) to measure each = O(k^3) per pass,
    at most MAX_PASSES passes. Space O(k).
    """

    best = list(stops)
    best_km = route_distance(best, distances)
    for _ in range(MAX_PASSES):
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                candidate_km = route_distance(candidate, distances)
                if candidate_km < best_km - EPS:
                    best, best_km = candidate, candidate_km
                    improved = True
        if not improved:
            break
    return best


def improve_with_two_opt(parcel: Dict[str, dict], route: List[str],
                         distances: Dict[str, Dict[str, float]]) -> List[str]:
    """Reorder a trip's stops with 2-opt; parcels for the same stop stay together.

    The set of parcels does not change (capacity still holds) and the route can
    only get shorter (range and the 18:00 return still hold).
    """

    if len(route) < 2:
        return route
    stops: List[str] = []
    by_stop: Dict[str, List[str]] = {}
    for parcel_id in route:
        location = parcel[parcel_id]["delivery_location_id"]
        if location not in by_stop:
            stops.append(location)
            by_stop[location] = []
        by_stop[location].append(parcel_id)

    better_stops = two_opt(stops, distances)
    return [parcel_id for location in better_stops for parcel_id in by_stop[location]]


def urgent_nearest_2opt_trip(parcel: Dict[str, dict], context: dict) -> List[str]:
    """Rule 3's trip: urgent_nearest_trip, then 2-opt on the stop order."""

    route = urgent_nearest_trip(parcel, context)
    return improve_with_two_opt(parcel, route, context["travel_distance"])


# ---------------------------------------------------------------------------
# E. Zones (Week 9 graph + BFS, Week 5 queue, Week 7 hash map)
# ---------------------------------------------------------------------------

def find_areas(distances: Dict[str, Dict[str, float]]) -> List[List[str]]:
    """Split the town into areas = connected components of the 'nearby locations' graph.

    Graph: each location is a vertex; an edge joins two locations at most
    LINK_KM apart. Components are found with breadth-first search (queue).
    Time O(L^2) (every pair checked once). Space O(L^2) adjacency lists worst case.
    """

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
    """Hash map vehicle_id -> set of locations in its area.

    Far areas take longer to reach, so they get more vans. Each area's weight is
    (number of locations x average distance from the hub); vans are shared in
    proportion to weight (at least one each) by the largest-remainder method.
    Time O(Z log Z).
    """

    weights = [len(area) * sum(distances[HUB][loc] for loc in area) / len(area) for area in areas]
    n_vans = len(vehicle_ids)
    total = sum(weights)
    exact = [n_vans * w / total for w in weights]
    counts = [max(1, int(x)) for x in exact]
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


def my_area(context: dict) -> Set[str]:
    """Locations in the area of the van being planned (context['vehicle_id'])."""

    distances = context["travel_distance"]
    areas = find_areas(distances)
    return assign_vans(areas, distances, list(context["fleet"].keys()))[context["vehicle_id"]]


def only_locations(parcel: Dict[str, dict], locations: Set[str]) -> Dict[str, dict]:
    """Waiting parcels whose destination is in `locations`. Time O(P)."""

    return {
        pid: rec for pid, rec in parcel.items()
        if rec["vehicle_assigned"] is None and rec["delivery_time"] is None
        and rec["delivery_location_id"] in locations
    }


def busiest_area_parcels(parcel: Dict[str, dict], context: dict) -> Optional[Dict[str, dict]]:
    """Waiting parcels of the area with the largest total waiting size (None if all empty).

    Time O(L^2 + Z * P).
    """

    best, best_load = None, 0.0
    for area in find_areas(context["travel_distance"]):
        waiting = only_locations(parcel, set(area))
        load = sum(rec["size"] for rec in waiting.values())
        if load > best_load:
            best, best_load = waiting, load
    return best


# ---------------------------------------------------------------------------
# F. Waiting for a fuller van
# ---------------------------------------------------------------------------

def harm_if_wait(route: List[str], parcel: Dict[str, dict], context: dict) -> bool:
    """True if delaying this trip by one planning round (10 min) would hurt.

    Harm = a parcel on the trip that is on time now would become late, or the
    trip would no longer fit before the 18:00 return, or this is the last
    planning round that can still depart. Time O(k).
    """

    distances = context["travel_distance"]
    now = context["current_time"]
    delay = context["departure_delay"]
    later = now + PLANNING_INTERVAL

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
        if depart_now + km <= deadline < depart_now + PLANNING_INTERVAL + km:
            return True
    km += distances[here][HUB]
    return depart_now + PLANNING_INTERVAL + km > context["return_cutoff"]


def go_now(route: List[str], parcel: Dict[str, dict], context: dict, min_fill: float) -> bool:
    """Go if the van is at least min_fill full, or if waiting would cause harm. Time O(k)."""

    load = sum(parcel[p]["size"] for p in route)
    if load >= min_fill * context["capacity"]:
        return True
    return harm_if_wait(route, parcel, context)