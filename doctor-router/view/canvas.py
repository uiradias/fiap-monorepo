import pygame

from algo.core import best_solution
from algo.population import generate_random_locations, generate_random_population
from shared.constants import WHITE, N_LOCATIONS, WIDTH, HEIGHT, N_VEHICLES, SRC_LAT, SRC_LNG, POPULATION_SIZE, FPS, \
    ROUTE_PATH_COLORS
from view.drawing import draw_locations, draw_route, draw_src


def init(screen, clock):
    locations = generate_random_locations(N_LOCATIONS, WIDTH, HEIGHT, padding=10)
    population = generate_random_population(
        locations,
        N_VEHICLES,
        SRC_LAT,
        SRC_LNG,
        POPULATION_SIZE
    )

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

        draw_src(screen, SRC_LAT, SRC_LNG)
        draw_locations(screen, locations)

        the_best = best_solution(population)
        for route in the_best:
            color = ROUTE_PATH_COLORS[route.id]
            draw_route(screen, route, color, width=3)

        # draw current state
        pygame.display.flip()
        clock.tick(FPS)
