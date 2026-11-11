"""Helper functions shared by all the delivery rules.

Every rule file imports from here, as the project brief asks.
Written to be easy to read: plain loops, short functions, lots of comments.

Words used below:
    parcel   = the dictionary of all parcels (from the simulator)
    context  = the dictionary with time, distances and van limits (from the simulator)
    trip     = a list of parcel IDs, in delivery order
    stop     = a delivery location, e.g. "L001"

Parts of this file:
    A. Basic tools
    B. Build a trip     (greedy nearest neighbour, Week 11 + heap, Week 7)
    C. Tidy a trip      (2-opt local search, Week 11)
    D. Areas            (graph + BFS, Weeks 5 and 9)
    E. Go now or wait?

Letters used in the Big-O notes:
    P = parcels, L = locations (36), k = stops in one trip, Z = areas (6)
"""

import heapq

HUB = "HUB"
TINY = 0.000000001   # tiny allowance so rounding errors (e.g. 26.999999999999993) do not change a decision


# =====================================================================
# PART A: Basic tools
# =====================================================================

def get_waiting_parcels(parcel):
    """Return the IDs of parcels still at the hub, oldest first.  O(P log P)"""
    pairs = []
    for parcel_id in parcel:
        info = parcel[parcel_id]
        # Waiting = not on a van yet AND not delivered yet
        if info["vehicle_assigned"] is None and info["delivery_time"] is None:
            pairs.append((info["arrival_time"], parcel_id))
    pairs.sort()                      # sorts by arrival time, then by ID (Week 3 sorting)

    waiting = []
    for arrival_time, parcel_id in pairs:
        waiting.append(parcel_id)
    return waiting


def group_by_stop(parcel, parcel_ids):
    """Hash map (Week 7): stop -> list of parcel IDs going there.  O(P)"""
    groups = {}
    for parcel_id in parcel_ids:
        stop = parcel[parcel_id]["delivery_location_id"]
        if stop not in groups:
            groups[stop] = []         # first parcel for this stop: make an empty list
        groups[stop].append(parcel_id)
    return groups


def can_go_and_come_back(km_so_far, here, there, context):
    """Can the van drive here -> there, then back to the hub, within 320 km and by 18:00?  O(1)"""
    dist = context["travel_distance"]
    leave_time = context["current_time"] + context["departure_delay"]

    total_km = km_so_far + dist[here][there] + dist[there][HUB]

    if total_km > context["max_trip_distance_km"] + TINY:
        return False                  # too far for the battery
    if leave_time + total_km > context["return_cutoff"]:
        return False                  # back after 18:00 (60 km/h, so 1 km = 1 minute)
    return True


def route_length(stops, dist):
    """Total km for: HUB -> each stop in order -> back to HUB.  O(k)"""
    total = 0.0
    here = HUB
    for stop in stops:
        total = total + dist[here][stop]
        here = stop
    total = total + dist[here][HUB]   # drive back to the hub
    return total


# =====================================================================
# PART B: Build a trip (greedy nearest neighbour + heap for urgency)
# =====================================================================

def closest_reachable_stop(groups, here, km_so_far, context):
    """Greedy step (Week 11): the closest stop with waiting parcels that the van can still reach.  O(L)"""
    dist = context["travel_distance"]
    best_stop = None
    best_km = None
    for stop in groups:
        if not can_go_and_come_back(km_so_far, here, stop, context):
            continue
        km = dist[here][stop]
        # Closer wins; if two are equally close, the smaller name wins (so results never change)
        if best_stop is None or km < best_km or (km == best_km and stop < best_stop):
            best_stop = stop
            best_km = km
    return best_stop


def fill_van(parcel, context, groups, first_stop):
    """Greedy nearest neighbour (Week 11): from the hub, keep driving to the closest stop
    and load what fits, until the van is full or nothing else can be reached.

    groups     = hash map stop -> parcels (loaded in the order of each list)
    first_stop = a stop to visit first, or None to start with the closest stop
    O(L^2): up to L stops, each time checking up to L stops.
    """
    dist = context["travel_distance"]
    capacity = context["capacity"]

    trip = []
    load = 0.0
    km_so_far = 0.0
    here = HUB
    next_stop = first_stop

    while len(groups) > 0:
        if next_stop is None:
            next_stop = closest_reachable_stop(groups, here, km_so_far, context)
            if next_stop is None:
                break                 # nothing reachable: trip is finished

        # Load this stop's parcels (as many as fit), and remove the stop from the list
        loaded_something = False
        for parcel_id in groups.pop(next_stop):
            size = parcel[parcel_id]["size"]
            if load + size <= capacity + TINY:
                trip.append(parcel_id)
                load = load + size
                loaded_something = True

        if loaded_something:
            km_so_far = km_so_far + dist[here][next_stop]      # the van moves to this stop
            here = next_stop

        next_stop = None              # next time round: pick the closest stop again
        if load >= capacity - TINY:
            break                     # van is full: trip is finished

    return trip


def most_urgent_stop(parcel, waiting, context):
    """Use a heap (Week 7) to find the stop of the most urgent parcel that can still be on time.
    O(P log P)"""
    dist = context["travel_distance"]
    leave_time = context["current_time"] + context["departure_delay"]

    # Put every waiting parcel into a min-heap, smallest deadline on top
    heap = []
    for parcel_id in waiting:
        info = parcel[parcel_id]
        heapq.heappush(heap, (info["delivery_window_end"], info["arrival_time"], parcel_id))

    backup_stop = None
    while len(heap) > 0:
        deadline, arrival_time, parcel_id = heapq.heappop(heap)   # most urgent parcel left
        stop = parcel[parcel_id]["delivery_location_id"]

        if not can_go_and_come_back(0.0, HUB, stop, context):
            continue                  # van cannot even get there and back in time: skip

        if backup_stop is None:
            backup_stop = stop        # remember the most urgent reachable stop, just in case

        arrive_time = leave_time + dist[HUB][stop]
        if arrive_time <= deadline:
            return stop               # can still be on time: start the trip here

    return backup_stop                # nobody can be on time: use the backup


def sort_by_deadline(parcel, parcel_ids):
    """Return the parcel IDs sorted so the earliest deadline comes first."""
    triples = []
    for parcel_id in parcel_ids:
        info = parcel[parcel_id]
        triples.append((info["delivery_window_end"], info["arrival_time"], parcel_id))
    triples.sort()

    result = []
    for deadline, arrival_time, parcel_id in triples:
        result.append(parcel_id)
    return result


def build_trip(parcel, context):
    """Rule 2's trip: start at the most urgent stop (heap), then keep going to the closest stop.
    O(P log P + L^2)"""
    waiting = get_waiting_parcels(parcel)
    if len(waiting) == 0:
        return []

    first_stop = most_urgent_stop(parcel, waiting, context)
    if first_stop is None:
        return []

    groups = group_by_stop(parcel, waiting)
    for stop in groups:
        groups[stop] = sort_by_deadline(parcel, groups[stop])  # urgent parcels load first

    return fill_van(parcel, context, groups, first_stop)


# =====================================================================
# PART C: Tidy the trip (2-opt local search, Week 11)
# =====================================================================

def reverse_part(stops, i, j):
    """Return a new list where stops[i] .. stops[j] are in reverse order."""
    before = stops[:i]
    middle = stops[i:j + 1]
    after = stops[j + 1:]
    middle.reverse()
    return before + middle + after


def two_opt(stops, dist):
    """Keep reversing parts of the route while that makes it shorter.
    O(k^2) reversals per pass, each measured in O(k), at most 50 passes."""
    best = list(stops)
    best_km = route_length(best, dist)

    passes = 0
    improved = True
    while improved and passes < 50:              # 50 = safety limit
        improved = False
        passes = passes + 1
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                new_route = reverse_part(best, i, j)
                new_km = route_length(new_route, dist)
                if new_km < best_km - TINY:      # shorter? keep it
                    best = new_route
                    best_km = new_km
                    improved = True
    return best


def tidy_trip(parcel, trip, dist):
    """Reorder the trip's stops with 2-opt. Parcels for the same stop stay together.
    The parcels do not change and the route only gets shorter, so no limit can be broken."""
    if len(trip) < 2:
        return trip

    # 1. Turn the parcel list into a stop list (each stop once, in visiting order)
    stops = []
    parcels_at = {}                              # hash map: stop -> its parcels on this trip
    for parcel_id in trip:
        stop = parcel[parcel_id]["delivery_location_id"]
        if stop not in parcels_at:
            stops.append(stop)
            parcels_at[stop] = []
        parcels_at[stop].append(parcel_id)

    # 2. Find a shorter order for the stops
    better_stops = two_opt(stops, dist)

    # 3. Turn it back into a parcel list
    new_trip = []
    for stop in better_stops:
        for parcel_id in parcels_at[stop]:
            new_trip.append(parcel_id)
    return new_trip


# =====================================================================
# PART D: Areas (graph + BFS, Weeks 5 and 9)
# =====================================================================

def find_areas(dist):
    """Split the stops into areas: stops 10 km or less apart are linked (graph),
    and BFS finds each group of linked stops (connected components).  O(L^2)"""

    # 1. All stops except the hub, in name order
    stops = []
    for stop in dist:
        if stop != HUB:
            stops.append(stop)
    stops.sort()

    # 2. Build the graph as an adjacency list: stop -> list of nearby stops
    neighbours = {}
    for stop in stops:
        neighbours[stop] = []
    for a in stops:
        for b in stops:
            if a < b and min(dist[a][b], dist[b][a]) <= 10.0:
                neighbours[a].append(b)
                neighbours[b].append(a)

    # 3. BFS from each stop that is not in an area yet
    seen = set()
    areas = []
    for start in stops:
        if start in seen:
            continue
        seen.add(start)
        queue = [start]                          # a simple queue made from a list
        area = []
        while len(queue) > 0:
            here = queue.pop(0)                  # dequeue from the front
            area.append(here)
            for nxt in neighbours[here]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)            # enqueue at the back
        area.sort()
        areas.append(area)
    return areas


def share_vans(areas, dist, van_ids):
    """Hash map: van ID -> set of stops in its area.

    Far areas take longer to reach, so they get more vans:
      1. work of an area = number of stops x average km from the hub
      2. fair share of vans = total vans x (its work / all work), e.g. 1.96
      3. round down (but every area gets at least 1 van)
      4. spare vans go to the areas with the biggest decimal part (largest remainder)
    """
    # 1. Work per area
    work = []
    for area in areas:
        total_km = 0.0
        for stop in area:
            total_km = total_km + dist[HUB][stop]
        work.append(len(area) * total_km / len(area))

    all_work = 0.0
    for w in work:
        all_work = all_work + w
    number_of_vans = len(van_ids)

    # 2-3. Fair share, rounded down, at least 1
    share = []
    vans = []
    for k in range(len(areas)):
        exact = number_of_vans * work[k] / all_work
        share.append(exact)
        whole = int(exact)
        if whole < 1:
            whole = 1
        vans.append(whole)

    # 4. Order the areas by decimal part, biggest first (ties: earlier area first)
    by_decimal = []
    for k in range(len(areas)):
        by_decimal.append((-(share[k] - int(share[k])), k))
    by_decimal.sort()

    # Hand out spare vans, biggest decimal first
    i = 0
    while sum(vans) < number_of_vans:
        k = by_decimal[i % len(areas)][1]
        vans[k] = vans[k] + 1
        i = i + 1

    # Too many (only possible because every area got at least 1): take one back
    # from the area that got the most more than its fair share
    while sum(vans) > number_of_vans:
        best = 0
        for k in range(len(areas)):
            extra = vans[k] - share[k]
            best_extra = vans[best] - share[best]
            if extra > best_extra or (extra == best_extra and vans[k] > vans[best]):
                best = k
        vans[best] = vans[best] - 1

    # Give the vans out in order: van 1, 2, ... to area 1, then area 2, ...
    van_area = {}
    sorted_vans = sorted(van_ids)
    position = 0
    for k in range(len(areas)):
        for count in range(vans[k]):
            van_area[sorted_vans[position]] = set(areas[k])
            position = position + 1
    return van_area


def get_my_area(context):
    """The set of stops this van is in charge of.  O(L^2)"""
    dist = context["travel_distance"]
    areas = find_areas(dist)
    van_ids = list(context["fleet"].keys())
    van_area = share_vans(areas, dist, van_ids)
    return van_area[context["vehicle_id"]]


def parcels_in_area(parcel, area):
    """A smaller dictionary with only the waiting parcels for stops in this area.  O(P)"""
    result = {}
    for parcel_id in parcel:
        info = parcel[parcel_id]
        waiting = info["vehicle_assigned"] is None and info["delivery_time"] is None
        if waiting and info["delivery_location_id"] in area:
            result[parcel_id] = info
    return result


def busiest_area_parcels(parcel, context):
    """The waiting parcels of the area with the most waiting (by total size). Empty if none.
    O(L^2 + Z x P)"""
    best_parcels = {}
    best_load = 0.0
    for area in find_areas(context["travel_distance"]):
        area_parcels = parcels_in_area(parcel, set(area))
        load = 0.0
        for parcel_id in area_parcels:
            load = load + area_parcels[parcel_id]["size"]
        if load > best_load + TINY:              # TINY: equal loads count as a tie, first area kept
            best_parcels = area_parcels
            best_load = load
    return best_parcels


# =====================================================================
# PART E: Go now or wait?
# =====================================================================

def should_go_now(trip, parcel, context, min_fill):
    """Go if the van is full enough, or if waiting 10 more minutes would cause a problem.  O(k)"""
    dist = context["travel_distance"]
    capacity = context["capacity"]

    # 1. Full enough? (e.g. min_fill 0.9 means at least 27 of 30)
    load = 0.0
    for parcel_id in trip:
        load = load + parcel[parcel_id]["size"]
    if load >= min_fill * capacity - TINY:       # TINY: adding decimals can give 26.999999999999993
        return True

    leave_now = context["current_time"] + context["departure_delay"]
    leave_later = leave_now + 10                 # next planning round is 10 minutes later

    # 2. Last chance? If we wait, the van would leave at or after 18:00
    if leave_later >= context["return_cutoff"]:
        return True

    # 3. Would a parcel on this trip be on time now, but late if we wait?
    km = 0.0
    here = HUB
    for parcel_id in trip:
        stop = parcel[parcel_id]["delivery_location_id"]
        km = km + dist[here][stop]
        here = stop
        deadline = parcel[parcel_id]["delivery_window_end"]
        on_time_now = leave_now + km <= deadline
        late_if_wait = leave_later + km > deadline
        if on_time_now and late_if_wait:
            return True

    # 4. If we wait, would the van get back after 18:00?
    km = km + dist[here][HUB]
    if leave_later + km > context["return_cutoff"]:
        return True

    return False                                 # safe to wait for more parcels
