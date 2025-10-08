from dataclasses import dataclass

@dataclass(frozen=True)
class Location:
    id: str
    lat: float
    lng: float
