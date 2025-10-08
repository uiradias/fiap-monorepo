from typing import List, Tuple

import pygame

from domain.location import Location
from domain.route import Route
from shared.constants import NODE_RADIUS, RED


def draw_locations(screen: pygame.Surface, locations: List[Location]) -> None:
    for location in locations:
        pygame.draw.circle(screen, RED, tuple([location.lng, location.lat]), NODE_RADIUS)


def draw_route(screen: pygame.Surface, route: Route, rgb_color: Tuple[int, int, int], width: int = 1):
    path = [(stop.location.lng, stop.location.lat) for stop in route.stops]
    pygame.draw.lines(screen, rgb_color, True, path, width=width)
