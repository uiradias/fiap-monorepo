import math

from domain.route import Route


def calculate_fitness(route: Route) -> float:
    return _calculate_distance(route)


def _calculate_distance(route: Route) -> float:
    stops_distance = 0
    n = len(route.stops)
    for i in range(n):
        loc_1 = route.stops[i].location
        loc_2 = route.stops[(i + 1) % n].location
        stops_distance += _euclidean_distance(loc_1.lat, loc_1.lng, loc_2.lat, loc_2.lng)

    first_loc = route.stops[0].location
    last_loc = route.stops[n - 1].location

    src_to_first_stop = _euclidean_distance(route.src_lat, route.src_lng, first_loc.lat, first_loc.lng)
    last_stop_to_src = _euclidean_distance(last_loc.lat, last_loc.lng, last_loc.lat, last_loc.lng)

    return stops_distance + src_to_first_stop + last_stop_to_src


def _euclidean_distance(lat_1: float, lng_1: float, lat_2: float, lng_2: float) -> float:
    return math.sqrt((lat_1 - lat_2) ** 2 + (lng_1 - lng_2) ** 2)
