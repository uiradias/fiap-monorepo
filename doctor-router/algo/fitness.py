from typing import Tuple, List

from domain.route import Route
from shared.constants import VEHICLE_AUTONOMY
from shared.utils import euclidean_distance


def calculate_fitness(individual: List[Route]) -> Tuple[int, float]:
    violations = 0
    total_distance = 0
    for route in individual:
        dist = _calculate_distance(route)
        total_distance += dist
        if dist > VEHICLE_AUTONOMY:
            violations += 1
    return violations, total_distance


def _calculate_distance(route: Route) -> float:
    location_distance = 0
    n = len(route.locations)
    for i in range(n):
        loc_1 = route.locations[i]
        loc_2 = route.locations[(i + 1) % n]
        location_distance += euclidean_distance(loc_1.lat, loc_1.lng, loc_2.lat, loc_2.lng)

    first_loc = route.locations[0]
    last_loc = route.locations[n - 1]

    src_to_first_stop = euclidean_distance(route.src_lat, route.src_lng, first_loc.lat, first_loc.lng)
    last_stop_to_src = euclidean_distance(last_loc.lat, last_loc.lng, last_loc.lat, last_loc.lng)

    return location_distance + src_to_first_stop + last_stop_to_src
