from dataclasses import dataclass
from typing import List

from domain.stop import Stop


@dataclass(frozen=True)
class Route:
    id: str
    stops: List[Stop]
