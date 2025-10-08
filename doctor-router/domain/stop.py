from dataclasses import dataclass

from domain.location import Location


@dataclass(frozen=True)
class Stop:
    id: str
    location: Location
