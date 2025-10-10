from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg

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
    for location in route.locations:
        path.append((location.lng, location.lat))
    path.append((route.src_lng, route.src_lat))
    pygame.draw.lines(screen, rgb_color, True, path, width=width)


def draw_plot(
        screen: pygame.Surface,
        x: list,
        y: list,
        x_label: str = 'Generation',
        y_label: str = 'Fitness',
        region_horizontal: str = 'center',  # 'left', 'center', 'right'
        region_vertical: str = 'center'  # 'top', 'center', 'bottom'
) -> None:
    fig, ax = plt.subplots(figsize=(4, 4), dpi=50)
    ax.plot(x, y)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    plt.tight_layout()

    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    raw_data = renderer.buffer_rgba()

    arr = np.asarray(raw_data)
    rgb_str = arr[:, :, :3].tobytes()
    size = canvas.get_width_height()
    surf = pygame.image.fromstring(rgb_str, size, "RGB")

    screen_width = screen.get_width()
    screen_height = screen.get_height()

    # calcula posição horizontal
    if region_horizontal == 'left':
        x_pos = 0
    elif region_horizontal == 'center':
        x_pos = (screen_width - size[0]) // 2
    elif region_horizontal == 'right':
        x_pos = screen_width - size[0]
    else:
        raise ValueError("region_horizontal deve ser 'left', 'center' ou 'right'")

    # calcula posição vertical
    if region_vertical == 'top':
        y_pos = 0
    elif region_vertical == 'center':
        y_pos = (screen_height - size[1]) // 2
    elif region_vertical == 'bottom':
        y_pos = screen_height - size[1]
    else:
        raise ValueError("region_vertical deve ser 'top', 'center' ou 'bottom'")

    screen.blit(surf, (x_pos, y_pos))
