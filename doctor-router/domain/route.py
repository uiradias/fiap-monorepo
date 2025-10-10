from dataclasses import dataclass
from typing import List

from domain.location import Location


@dataclass(frozen=True)
class Route:
    id: str
    vehicle: str
    src_lat: float
    src_lng: float
    locations: List[Location]
