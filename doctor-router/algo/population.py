import random
from typing import List

import math

from domain.location import Location
from domain.route import Route
from shared.utils import euclidean_distance


def generate_random_locations(n: int, width: int, height: int, padding: int = 0) -> List[Location]:
    locations = []
    for i in range(n):
        lat = random.uniform(padding, height - padding)
        lng = random.uniform(width / 2 + padding, width - padding)
        locations.append(
            Location(
                id=f"Location_{i + 1}",
                lat=lat,
                lng=lng
            )
        )
    return locations


def generate_random_population(locations: List[Location],
                               vehicles: List[str],
                               src_lat: float,
                               src_lng: float,
                               population_size: int) -> List[List[Route]]:
    population = []
    strategies = ['random', 'cluster']
    for i in range(population_size):
        strat = random.choices(strategies, weights=[0.2, 0.8], k=1)[0]
        individual = _generate_individual(locations, vehicles, src_lat, src_lng, strat)
        population.append(individual)

    return population


def _generate_individual(locations: List[Location],
                         vehicles: List[str],
                         src_lat: float,
                         src_lng: float,
                         strategy: str = 'random') -> List[Route]:
    n_vehicles = len(vehicles)

    if strategy == 'random':
        suffled = locations[:]
        random.shuffle(suffled)
        groups = _split_into_chunk(suffled, n_vehicles)

    elif strategy == 'cluster':
        clusters = _kmeans_geo(locations, n_vehicles, iters=8)
        groups = clusters

    else:
        # fallback: random
        suffled = locations[:]
        random.shuffle(suffled)
        groups = _split_into_chunk(suffled, n_vehicles)

    if len(groups) < n_vehicles:
        # if necessary, append empty groups to fill # groups == # vehicles
        groups += [[] for _ in range(n_vehicles - len(groups))]
    elif len(groups) > n_vehicles:
        # if necessary, distribute exceeding groups randomly between existing vehicles
        extras = groups[n_vehicles:]
        groups = groups[:n_vehicles]
        for ex in extras:
            groups[random.randrange(n_vehicles)].extend(ex)

    routes = []
    for idx in range(n_vehicles):
        locations = _order_locations_by_nn(groups[idx])
        routes.append(Route(id=f"route_{idx + 1000}",
                            vehicle=f"vehicle_{idx + 1}",
                            locations=random.sample(locations, len(locations)),
                            src_lat=src_lat,
                            src_lng=src_lng))
    return routes


def _order_locations_by_nn(locations: List[Location]) -> List[Location]:
    if not locations:
        return []
    if len(locations) == 1:
        return locations[:]

    matrix = _build_distance_matrix(locations)
    indices = _nearest_neighbor_indices(matrix, start_index=0)
    return [locations[i] for i in indices]


def _build_distance_matrix(locations: List[Location]) -> List[List[float]]:
    n = len(locations)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0.0
            else:
                loc_1 = locations[i]
                loc_2 = locations[j]
                matrix[i][j] = euclidean_distance(loc_1.lat, loc_1.lng, loc_2.lat, loc_2.lng)
    return matrix


def _nearest_neighbor_indices(distance_matrix: List[List[float]], start_index: int = 0) -> List[int]:
    n = len(distance_matrix)
    visited = [False] * n
    route = [start_index]
    visited[start_index] = True

    for _ in range(n - 1):
        last = route[-1]
        nearest = None
        nearest_dist = float('inf')
        for j in range(n):
            if not visited[j] and distance_matrix[last][j] < nearest_dist:
                nearest = j
                nearest_dist = distance_matrix[last][j]
        if nearest is None:
            break
        route.append(nearest)
        visited[nearest] = True

    return route


def _split_into_chunk(locations: List[Location], num_vehicles: int) -> List[List[Location]]:
    random.shuffle(locations)
    chunk_size = math.ceil(len(locations) / num_vehicles)
    return [locations[i:i + chunk_size] for i in range(0, len(locations), chunk_size)]


def _kmeans_geo(locations: List[Location], k: int, iters: int) -> List[List[Location]]:
    """
    Group locations into k groups (clusters) where locations within the same cluster are
    geographically close to each other.

    1. Determine centroid of each cluster based on random locations
    2. Assign each location to its closest centroid
    3. Recalculate centroid of each cluster based on the average of the locations within the cluster
    4. Repeat steps 2 and 3 until break condition is met (number of iterations)
    """
    if k >= len(locations):
        return [[l] for l in locations]

    # initialize cluster centroids by choosing random locations
    centroids = random.sample(locations, k)

    clusters = []
    for _ in range(iters):
        clusters = [[] for _ in range(k)]

        # assign each location to the closest centroid
        for l in locations:
            best = None
            best_dist = float('inf')
            for i, c in enumerate(centroids):
                distance = euclidean_distance(l.lat, l.lng, c.lat, c.lng)
                if distance < best_dist:
                    best = i
                    best_dist = distance
            clusters[best].append(l)

        # recalculate new cluster centroids based on the avg location of the locations assigned to each cluster
        new_centroids = []
        for cluster in clusters:
            if not cluster:
                new_centroids.append(random.choice(locations))
            else:
                avg_lat = sum([l.lat for l in cluster]) / len(cluster)
                avg_lng = sum([l.lng for l in cluster]) / len(cluster)
                new_centroid = Location('new-centroid', avg_lat, avg_lng)
                new_centroids.append(new_centroid)
        centroids = new_centroids

    # if any cluster has more than ceil(N / n_clusters), redistribute to the emptiest one (rebalance clusters)
    target_size = len(locations) // k
    extras = []
    for cluster in clusters:
        while len(cluster) > target_size + 1:
            extras.append(cluster.pop())

    for cluster in clusters:
        while len(cluster) < target_size and extras:
            cluster.append(extras.pop())

    return clusters
