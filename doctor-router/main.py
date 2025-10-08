import pygame

from shared.constants import WIDTH, HEIGHT
from view.canvas import init


def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TSP Solver using Pygame")
    clock = pygame.time.Clock()

    init(screen, clock)


if __name__ == '__main__':
    run()
