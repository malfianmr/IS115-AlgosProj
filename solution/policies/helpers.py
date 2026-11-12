import heapq

HUB = "HUB"

# =====================================================================
# Waiting Parcel, Group By Location, Fill Van, Check Hard Constraints Functions
# =====================================================================

#Get waiting parcels arranged in earliest arrival
def get_waiting_parcels(parcel):
    parcel_list = []

    for parcel_id in parcel:
        # Check if parcel waiting to be assigned
        if parcel[parcel_id]["vehicle_assigned"] == None and parcel[parcel_id]["delivery_time"] == None: 
            current_parcel_tuple = (parcel[parcel_id]["arrival_time"], parcel_id)
            parcel_list.append(current_parcel_tuple)

    parcel_list.sort()

    sorted_parcel_id_list = []

    #Add the parcel ID's in order to a new list
    for i in range(len(parcel_list)):
        sorted_parcel_id_list.append(parcel_list[i][1])

    return sorted_parcel_id_list

#Group parcels by location
def group_by_location(parcel, waiting):
    #Create a dictionary for the different locations
    groups = {}

    #Add the parcel to the respective locations
    for parcel_id in waiting:
        location = parcel[parcel_id]["delivery_location_id"]

        if location not in groups:
            groups[location] = []

        groups[location].append(parcel_id)

    return groups

#Checks if going to next location satisfies the hard rules
def check_hard_rules(total_current_km, current_location, next_location, context):

    #Check context what's the current total travel km so far
    distance = context["travel_distance"]

    #Add total distance + the distance from here to next location and then back to the hub after that next parcel
    total_km = total_current_km + distance[current_location][next_location] + distance[next_location][HUB]

    #Time van leaves hub + 30 min loading
    leave_time = context["current_time"] + context["departure_delay"]

    #Check if exceed 320km
    if total_km > context["max_trip_distance_km"]:
        return False

    #Check if exceed 6pm
    if leave_time + total_km > context["return_cutoff"]:
        return False

    return True

# =====================================================================
# Greedy 1 Algorithm
# =====================================================================

def closest_reachable_location(groups, current_location, total_current_km, context):
    distance = context["travel_distance"]

    best_location = None
    best_km = None

    for location in groups:
        #Checks if passes the rules or not, if False it skips
        if not check_hard_rules(total_current_km, current_location, location, context):
            continue

        #Save current distance
        km = distance[current_location][location]

        if best_location == None or km < best_km or (km == best_km and location < best_location):
            best_location = location
            best_km = km

    return best_location

def fill_van(parcel, context, groups, first_location=None):
    distance = context["travel_distance"]
    capacity = context["capacity"]

    #Empty van starting at the hub
    trip = []
    load = 0.0
    total_current_km = 0.0
    current_location = HUB

    next_location = first_location

    while len(groups) > 0:

        if next_location == None:
            next_location = closest_reachable_location(groups, current_location, total_current_km, context)
            if next_location == None:
                break

        reachable_parcels = groups.pop(next_location)

        loaded = False
        for parcel_id in reachable_parcels:
            size = parcel[parcel_id]["size"]
            if load + size <= capacity:
                trip.append(parcel_id)
                load = load + size
                loaded = True

        if loaded:
            total_current_km = total_current_km + distance[current_location][next_location]
            current_location = next_location

        next_location = None #Next parcel

        if load >= capacity:
            break

    return trip

# =====================================================================
# Urgent deliveries comes first functions, deadlines which are missed will be skipped by using Heap
# =====================================================================

def most_urgent_location(parcel, waiting, context):
    distance = context["travel_distance"]
    leave_time = context["current_time"] + context["departure_delay"]

    #Place all waiting parcels into a min-heap (earliest deadline gets delivered first)
    heap = []
    for parcel_id in waiting:
        deadline = parcel[parcel_id]["delivery_window_end"]
        arrival = parcel[parcel_id]["arrival_time"]

        heapq.heappush(heap, (deadline, arrival, parcel_id))

    backup_location = None

    while len(heap) > 0:
        deadline, arrival, parcel_id = heapq.heappop(heap)
        location = parcel[parcel_id]["delivery_location_id"]

        if not check_hard_rules(0.0, HUB, location, context):
            #Van cannot get there so skip
            continue 

        if backup_location is None:
            #Remember the most urgent reachable stop
            backup_location = location 

        arrive_time = leave_time + distance[HUB][location]
        if arrive_time <= deadline:
            return location

    return backup_location

#Sorted heap within their locations
def sort_by_deadline(parcel, parcel_ids):
    tuples = []
    for parcel_id in parcel_ids:
        current_parcel = parcel[parcel_id]
        tuples.append((current_parcel["delivery_window_end"], current_parcel["arrival_time"], parcel_id))

    tuples.sort()

    sorted_parcel_id = []
    for i in range(len(tuples)):
        sorted_parcel_id.append(tuples[i][2])

    return sorted_parcel_id 

def build_urgent_trip(parcel, context):
    waiting = get_waiting_parcels(parcel)                
    if len(waiting) == 0:
        return []
    
    first_location = most_urgent_location(parcel, waiting, context)   #Most urgent stop (heap)
    if first_location is None:
        return []
    
    groups = group_by_location(parcel, waiting)                 #Group by location
    for location in groups:
        groups[location] = sort_by_deadline(parcel, groups[location])  #Most urgent first at each location
    
    return fill_van(parcel, context, groups, first_location)    #Build the trip from first_location

# =====================================================================
# 2-Opt Algorithms for making the route more efficient
# =====================================================================
def route_length(locations, distance):
    total = 0.0
    current_location = HUB

    for location in locations:
        total = total + distance[current_location][location]
        current_location = location

    total = total + distance[current_location][HUB]
    return total

def reverse_part(locations, i, j):

    #Reversing the middle section
    before = locations[:i]
    middle = locations[i:j + 1]
    after = locations[j + 1:]
    middle.reverse()
    return before + middle + after

def two_opt(locations, distance):
    best = list(locations) #Copy of locations
    best_km = route_length(best, distance)

    passes = 0
    improved = True
    while improved and passes < 50:
        improved = False
        passes = passes + 1
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                new_route = reverse_part(best, i, j)
                new_km = route_length(new_route, distance)
                if new_km < best_km:
                    best = new_route
                    best_km = new_km
                    improved = True

    return best

#Sorting them into the order of their parcel_id and locations
def tidy_trip(parcel, trip, distance):

    #If less than two trips then don't need to rearrange
    if len(trip) < 2:
        return trip

    locations = []
    parcels_at = {}

    for parcel_id in trip:
        location = parcel[parcel_id]["delivery_location_id"]
        if location not in parcels_at:
            locations.append(location)
            parcels_at[location] = []
        parcels_at[location].append(parcel_id)

    better_stops = two_opt(locations, distance)

    new_trip = []
    for location in better_stops:
        for parcel_id in parcels_at[location]:
            new_trip.append(parcel_id)
    return new_trip

# =====================================================================
# Vans can only deliver to their assigned zones/area
# =====================================================================

def build_zone_links(distance):

    locations = []
    for location in distance:
        if location != "HUB":
            locations.append(location)
    locations.sort()

    links = {}
    for location in locations:
        links[location] = []

    for a in locations:
        for b in locations:
            if a < b and min(distance[a][b], distance[b][a] <= 10):
                links[a].append(b)
                links[b].append(a)

    return links

def build_zones(distance):
    links = build_zone_links(distance)

    seen = set()
    zones = []

    for location in sorted(links):
        if location in seen:
            continue

        seen.add(location)
        queue = [location]
        zone = []

        while len(queue) > 0:
            here = queue.pop(0)
            zone.append(here)

            for next_location in links[here]:
                if next_location not in seen:
                    seen.add(next_location)
                    queue.append(next_location)
        zone.sort()
        zones.append(zone)

    return zones

def share_vans(zones, distance, van_ids):

    #How much work each zone is: total km from the hub to its locations
    work = []
    for zone in zones:
        total_km = 0
        for location in zone:
            total_km = total_km + distance[HUB][location]        
        work.append(total_km)

    #Every zone starts with 1 van
    vans_per_zone = []
    for zone in zones:
        vans_per_zone.append(1)                                

    #Hand out the spare vans one at a time (greedy)
    spare = len(van_ids) - len(zones)
    while spare > 0:
        best = 0
        for k in range(len(zones)):
            if work[k] / vans_per_zone[k] > work[best] / vans_per_zone[best]:
                best = k
        vans_per_zone[best] = vans_per_zone[best] + 1                                
        spare = spare - 1                                              

    #Give out van numbers in order: zone 0 first, then zone 1, ...
    van_zone = {}
    sorted_vans = sorted(van_ids)
    position = 0
    for k in range(len(zones)):
        for count in range(vans_per_zone[k]):
            van_zone[sorted_vans[position]] = set(zones[k])
            position = position + 1

    return van_zone

def get_my_zone(context):
    distance = context["travel_distance"]
    zones = build_zones(distance)                              
    van_ids = list(context["fleet"].keys())                 
    van_zone = share_vans(zones, distance, van_ids)            
    return van_zone[context["vehicle_id"]]

def parcels_in_zone(parcel, zone):
    result = {}
    for parcel_id in parcel:
        info = parcel[parcel_id]
        waiting = info["vehicle_assigned"] is None and info["delivery_time"] is None
        if waiting and info["delivery_location_id"] in zone:                  
            result[parcel_id] = info                        
    return result

def busiest_zone_parcels(parcel, context):
    best_parcels = {}
    best_load = 0.0

    for zone in build_zones(context["travel_distance"]):
        zone_parcels = parcels_in_zone(parcel, set(zone))

        #Add up the size of everything waiting in this zone
        load = 0.0
        for parcel_id in zone_parcels:
            load = load + zone_parcels[parcel_id]["size"]           

        if load > best_load:                                           
            best_parcels = zone_parcels
            best_load = load                                     

    return best_parcels

# =====================================================================
# Vans can only deliver at a specific load
# =====================================================================

def should_go_now(trip, parcel, context, min_fill):
    distance = context["travel_distance"]
    capacity = context["capacity"]

    #Check if Full enough?
    load = 0.0
    for parcel_id in trip:
        load = load + parcel[parcel_id]["size"]                       
    if load >= min_fill * capacity:
        return True

    leave_now = context["current_time"] + context["departure_delay"]
    leave_later = leave_now + 10                                  

    #Last chance?
    if leave_later >= context["return_cutoff"]:
        return True

    #Would a parcel be on time now, but late if we wait?
    km = 0.0
    current_location = HUB
    for parcel_id in trip:
        location = parcel[parcel_id]["delivery_location_id"]
        km = km + distance[current_location][location]
        current_location = location
        deadline = parcel[parcel_id]["delivery_window_end"]

        on_time_now = leave_now + km <= deadline
        late_if_wait = leave_later + km > deadline                         
        if on_time_now and late_if_wait:
            return True

    #If we wait, would the van get back after 18:00?
    km = km + distance[current_location][HUB]                      
    if leave_later + km > context["return_cutoff"]:
        return True

    return False                                                     