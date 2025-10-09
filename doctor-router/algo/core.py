from typing import List, Tuple

from algo.fitness import calculate_fitness
from domain.route import Route


def best_solution(population: List[List[Route]]) -> Tuple[List[Route], float]:
    population, population_fitness = sort_population_by_fitness(population, calculate_population_fitness(population))
    return population[0], population_fitness[0]


def calculate_population_fitness(population: List[List[Route]]) -> List[float]:
    fitness = []
    for solution in population:
        solution_fitness = []
        for route in solution:
            solution_fitness.append(calculate_fitness(route))
        fitness.append(max(solution_fitness))

    return fitness


def sort_population_by_fitness(population: List[List[Route]], fitness: List[float]) -> Tuple[
    List[List[Route]], List[float]]:
    return sorted(population, key=lambda solution: fitness[population.index(solution)]), sorted(fitness)
