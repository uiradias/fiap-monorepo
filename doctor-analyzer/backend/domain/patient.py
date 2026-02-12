"""Patient domain model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Patient:
    """Patient entity."""

    id: str
    codename: str
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "codename": self.codename,
            "created_at": self.created_at.isoformat(),
        }
