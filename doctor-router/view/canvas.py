import itertools
import json
import os
import random
from dataclasses import asdict
from typing import List

import pygame

from algo.core import best_solution, crossover
from algo.population import generate_random_locations, generate_random_population
from domain.route import Route
from shared.constants import WHITE, N_LOCATIONS, WIDTH, HEIGHT, SRC_LAT, SRC_LNG, POPULATION_SIZE, FPS, \
    ROUTE_PATH_COLORS
from view.drawing import draw_locations, draw_route, draw_src, draw_plot


def init(screen, clock):
    generation_counter = itertools.count(start=1)  # Start the counter at 1
    locations = generate_random_locations(N_LOCATIONS, WIDTH, HEIGHT, padding=10)
    vehicles = ['equipment_1', 'equipment_2', 'equipment_3']
    population = generate_random_population(
        locations,
        vehicles,
        SRC_LAT,
        SRC_LNG,
        POPULATION_SIZE
    )
    best_fitness_values = []
    best_current_solution = None

    solution_output_dst = os.path.join('..', 'doctor-router-chatbot', 'data', 'routes.json')
    os.makedirs(os.path.dirname(solution_output_dst), exist_ok=True)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False

        generation = next(generation_counter)

        # set background color
        screen.fill(WHITE)

        the_best = best_solution(population)
        the_best_solution = the_best[0]
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

        for route in the_best_solution:
            color = ROUTE_PATH_COLORS[route.id]
            draw_route(screen, route, color, width=3)

        print(f"Generation {generation}: Best fitness = {round(the_best_fitness, 2)}")

        new_population = [the_best_solution]  # Keep the best individual: ELITISM

        if best_current_solution is None or best_current_solution != the_best_solution:
            best_current_solution = the_best_solution
            _persist_best_solution(solution_output_dst, best_current_solution)

        while len(new_population) < POPULATION_SIZE:
            parent1, parent2 = random.choices(population, k=2)
            child1 = crossover(parent1, parent2)
            new_population.append(child1)

        population = new_population

        # draw current state
        pygame.display.flip()
        clock.tick(FPS)


def _persist_best_solution(solution_output_dst, best_solution: List[Route]):
    json.dump([asdict(s) for s in best_solution], open(solution_output_dst, "w"), indent=4, ensure_ascii=False)
