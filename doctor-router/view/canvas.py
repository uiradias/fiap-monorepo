import pygame

from algo.core import best_solution
from algo.population import generate_random_routes, generate_random_locations
from shared.constants import WHITE, N_LOCATIONS, WIDTH, HEIGHT, BLUE
from view.drawing import draw_locations, draw_route

# Define constant values
# pygame
FPS = 30


def init(screen, clock):
    locations = generate_random_locations(N_LOCATIONS, WIDTH, HEIGHT, padding=10)
    pupulation = generate_random_routes(locations)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False

        # set background color
        screen.fill(WHITE)

        draw_locations(screen, locations)
        draw_route(screen, best_solution(pupulation), BLUE, width=3)

        # draw current state
        pygame.display.flip()
        clock.tick(FPS)
