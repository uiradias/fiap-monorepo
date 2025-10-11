from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Location:
    id: str
    lat: float
    lng: float
