import pygame

from algo.core import best_solution
from algo.population import generate_random_locations, generate_random_population
from shared.constants import WHITE, N_LOCATIONS, WIDTH, HEIGHT, N_VEHICLES, SRC_LAT, SRC_LNG, POPULATION_SIZE, FPS, \
    ROUTE_PATH_COLORS
from view.drawing import draw_locations, draw_route, draw_src, draw_plot


def init(screen, clock):
    locations = generate_random_locations(N_LOCATIONS, WIDTH, HEIGHT, padding=10)
    population = generate_random_population(
        locations,
        N_VEHICLES,
        SRC_LAT,
        SRC_LNG,
        POPULATION_SIZE
    )
    best_fitness_values = []

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

        the_best = best_solution(population)
        the_best_population = the_best[0]
        the_best_fitness = the_best[1]
        best_fitness_values.append(the_best_fitness)

        draw_plot(
            screen,
            list(range(len(best_fitness_values))),
            best_fitness_values,
            y_label="Fitness - Distance (pxls)",
            region_horizontal="left",
            region_vertical="center")

        draw_src(screen, SRC_LAT, SRC_LNG)
        draw_locations(screen, locations)

        for route in the_best_population:
            color = ROUTE_PATH_COLORS[route.id]
            draw_route(screen, route, color, width=3)

        # draw current state
        pygame.display.flip()
        clock.tick(FPS)
