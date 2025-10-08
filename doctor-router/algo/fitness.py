import math

from domain.location import Location
from domain.route import Route


def calculate_fitness(route: Route) -> float:
    distance = 0
    n = len(route.stops)
    for i in range(n):
        distance += calculate_distance(route.stops[i].location, route.stops[(i + 1) % n].location)
    return distance


def calculate_distance(location_1: Location, location_2: Location) -> float:
    return math.sqrt((location_2.lat - location_1.lat) ** 2 + (location_2.lng - location_1.lng) ** 2)
