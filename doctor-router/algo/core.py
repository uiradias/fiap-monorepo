from typing import List, Tuple

from algo.fitness import calculate_fitness
from domain.route import Route


def best_solution(population: List[Route]) -> Route:
    population, population_fitness = sort_population_by_fitness(population, calculate_population_fitness(population))
    return population[0]


def calculate_population_fitness(population: List[Route]) -> List[float]:
    return [calculate_fitness(route) for route in population]


def sort_population_by_fitness(population: List[Route], fitness: List[float]) -> Tuple[List[Route], List[float]]:
    return sorted(population, key=lambda route: fitness[population.index(route)]), sorted(fitness)
