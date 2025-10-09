from typing import List, Tuple

import pygame

from domain.location import Location
from domain.route import Route
from shared.constants import NODE_RADIUS, RED, BROWN


def draw_src(screen: pygame.Surface, src_lat, src_lng) -> None:
    pygame.draw.circle(screen, BROWN, tuple([src_lng, src_lat]), NODE_RADIUS)


def draw_locations(screen: pygame.Surface, locations: List[Location]) -> None:
    for location in locations:
        pygame.draw.circle(screen, RED, tuple([location.lng, location.lat]), NODE_RADIUS)


def draw_route(screen: pygame.Surface, route: Route, rgb_color: Tuple[int, int, int], width: int = 1):
    path = [(route.src_lng, route.src_lat)]
    for stop in route.stops:
        path.append((stop.location.lng, stop.location.lat))
    path.append((route.src_lng, route.src_lat))
    pygame.draw.lines(screen, rgb_color, True, path, width=width)
