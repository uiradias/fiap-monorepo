import random
from typing import List

import math

from domain.location import Location
from domain.route import Route
from domain.stop import Stop


def generate_random_population(locations: List[Location],
                               num_vehicles: int,
                               src_lat: float,
                               src_lng: float,
                               population_size: int) -> List[List[Route]]:
    clusters = _split_into_clusters(locations, num_vehicles)
    population = []
    for p_idx in range(population_size):
        individual = []
        for i, cluster in enumerate(clusters, start=1):
            stops = _generate_stops_from_locations(cluster)
            individual.append(
                Route(id=f"route_{i + 1000}",
                      vehicle=f"vehicle_{i + 1}",
                      stops=random.sample(stops, len(stops)),
                      src_lat=src_lat,
                      src_lng=src_lng))
        population.append(individual)

    return population


def generate_random_locations(n: int, width: int, height: int, padding: int = 0) -> List[Location]:
    locations = []
    for i in range(n):
        lat = random.uniform(padding, height - padding)
        lng = random.uniform(width / 2 + padding, width - padding)
        locations.append(
            Location(
                id=f"Location_{i + 1}",
                lat=lat,
                lng=lng
            )
        )
    return locations


def _split_into_clusters(locations: List[Location], num_vehicles: int) -> List[List[Location]]:
    random.shuffle(locations)
    chunk_size = math.ceil(len(locations) / num_vehicles)
    return [locations[i:i + chunk_size] for i in range(0, len(locations), chunk_size)]


def _generate_stops_from_locations(locations: List[Location]):
    return [
        Stop(id=f"stop_{i + 1}", location=loc)
        for i, loc in enumerate(locations)
    ]
