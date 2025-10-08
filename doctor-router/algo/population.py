import random
from typing import List

from domain.location import Location
from domain.route import Route
from domain.stop import Stop
from shared.constants import POPULATION_SIZE


def generate_random_routes(locations: List[Location]) -> List[Route]:
    stops = generate_stops_from_locations(locations)
    return [
        Route(id=f"route_{i + 1}", stops=random.sample(stops, len(stops)))
        for i in range(POPULATION_SIZE)
    ]


def generate_random_locations(n: int, width: int, height: int, padding: int = 0) -> List[Location]:
    locations = []
    for i in range(n):
        lat = random.uniform(padding, height - padding)
        lng = random.uniform(padding, width - padding)
        locations.append(
            Location(
                id=f"Location_{i + 1}",
                lat=lat,
                lng=lng
            )
        )
    return locations


def generate_stops_from_locations(locations):
    return [
        Stop(id=f"stop_{i + 1}", location=loc)
        for i, loc in enumerate(locations)
    ]
