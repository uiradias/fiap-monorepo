import random
from typing import List, Tuple

from algo.fitness import calculate_fitness
from domain.location import Location
from domain.route import Route


def best_solution(population: List[List[Route]]) -> Tuple[List[Route], Tuple[int, float]]:
    population, population_fitness = _sort_population_by_fitness(population, calculate_population_fitness(population))
    return population[0], population_fitness[0]


def calculate_population_fitness(population: List[List[Route]]) -> List[Tuple[int, float]]:
    fitness = []
    for solution in population:
        fitness.append(calculate_fitness(solution))

    return fitness


def _sort_population_by_fitness(
        population: List[List[Route]],
        fitness: List[Tuple[int, float]]
) -> Tuple[List[List[Route]], List[Tuple[int, float]]]:
    paired = list(zip(population, fitness))
    paired_sorted = sorted(paired, key=lambda x: x[1])

    sorted_population, sorted_fitness = zip(*paired_sorted)

    return list(sorted_population), list(sorted_fitness)


def flatten_and_structure(individual: List[Route]) -> List[Location]:
    return [c for r in individual for c in r.locations]


def rebuild(flat: List[Location], structure: List[Route]) -> List[Route]:
    routes = []
    i = 0
    for route in structure:
        routes.append(Route(id=route.id,
                            src_lat=route.src_lat,
                            src_lng=route.src_lng,
                            vehicle=route.vehicle,
                            locations=flat[i:i + len(route.locations)]))
        i += len(route.locations)
    return routes


def order_crossover(parent1: List[Location], parent2: List[Location]) -> List[Location]:
    """
    Perform order crossover (OX) between two parent sequences to create a child sequence.

    Parameters:
    - parent1 (List[Location]): The first parent sequence.
    - parent2 (List[Location]): The second parent sequence.

    Returns:
    List[Location]: The child sequence resulting from the order crossover.
    """
    length = len(parent1)

    # Choose two random indices for the crossover
    start_index = random.randint(0, length - 1)
    end_index = random.randint(start_index + 1, length)

    # Initialize the child with a copy of the substring from parent1
    child = parent1[start_index:end_index]

    # Fill in the remaining positions with genes from parent2
    remaining_positions = [i for i in range(length) if i < start_index or i >= end_index]
    remaining_genes = [gene for gene in parent2 if gene not in child]

    for position, gene in zip(remaining_positions, remaining_genes):
        child.insert(position, gene)

    return child


def crossover(parent1: List[Route], parent2: List[Route]):
    p1_flat = flatten_and_structure(parent1)
    p2_flat = flatten_and_structure(parent2)

    child1_flat = order_crossover(p1_flat, p2_flat)

    child1 = rebuild(child1_flat, parent1)

    return child1
