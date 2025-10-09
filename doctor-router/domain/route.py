from dataclasses import dataclass
from typing import List

from domain.stop import Stop


@dataclass(frozen=True)
class Route:
    id: str
    vehicle: str
    src_lat: float
    src_lng: float
    stops: List[Stop]
