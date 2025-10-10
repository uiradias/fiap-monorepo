import math

def euclidean_distance(lat_1: float, lng_1: float, lat_2: float, lng_2: float) -> float:
    return math.sqrt((lat_1 - lat_2) ** 2 + (lng_1 - lng_2) ** 2)