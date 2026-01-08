"""Patient domain models using dataclasses for immutability and type safety."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Demographics:
    """Patient demographic information."""

    name: str
    age: int
    gender: str
    blood_type: str
    date_of_birth: str
    contact: str


@dataclass(frozen=True)
class Condition:
    """Medical condition record."""

    name: str
    diagnosed_date: str
    status: str
    severity: str
    notes: str


@dataclass(frozen=True)
class Medication:
    """Medication record."""

    name: str
    dosage: str
    frequency: str
    start_date: str
    purpose: str


@dataclass(frozen=True)
class Allergy:
    """Allergy record."""

    allergen: str
    reaction: str
    severity: str


@dataclass(frozen=True)
class LabResult:
    """Laboratory result record."""

    test: str
    value: str
    date: str
    reference_range: str
    status: str


@dataclass(frozen=True)
class Vitals:
    """Patient vital signs."""

    weight: Optional[str] = None
    height: Optional[str] = None
    bmi: Optional[str] = None


@dataclass(frozen=True)
class Visit:
    """Patient visit record."""

    date: str
    reason: str
    provider: str
    notes: str
    vitals: Optional[Vitals] = None


@dataclass(frozen=True)
class Patient:
    """Complete patient record."""

    id: str
    demographics: Demographics
    conditions: List[Condition] = field(default_factory=list)
    medications: List[Medication] = field(default_factory=list)
    allergies: List[Allergy] = field(default_factory=list)
    lab_results: List[LabResult] = field(default_factory=list)
    visits: List[Visit] = field(default_factory=list)

    def to_document_text(self) -> str:
        """Convert patient record to searchable text document."""
        sections = [
            f"Patient ID: {self.id}",
            f"Name: {self.demographics.name}",
            f"Age: {self.demographics.age}",
            f"Gender: {self.demographics.gender}",
            f"Blood Type: {self.demographics.blood_type}",
            "",
            "=== CONDITIONS ===",
        ]

        for condition in self.conditions:
            sections.append(
                f"- {condition.name} (Diagnosed: {condition.diagnosed_date}, "
                f"Status: {condition.status}, Severity: {condition.severity})"
            )
            sections.append(f"  Notes: {condition.notes}")

        sections.append("")
        sections.append("=== MEDICATIONS ===")
        for med in self.medications:
            sections.append(
                f"- {med.name} {med.dosage} ({med.frequency}) - {med.purpose}"
            )

        sections.append("")
        sections.append("=== ALLERGIES ===")
        if self.allergies:
            for allergy in self.allergies:
                sections.append(
                    f"- {allergy.allergen}: {allergy.reaction} (Severity: {allergy.severity})"
                )
        else:
            sections.append("- No known allergies")

        sections.append("")
        sections.append("=== LAB RESULTS ===")
        for lab in self.lab_results:
            sections.append(
                f"- {lab.test}: {lab.value} (Reference: {lab.reference_range}, "
                f"Status: {lab.status}) - Date: {lab.date}"
            )

        sections.append("")
        sections.append("=== VISIT HISTORY ===")
        for visit in self.visits:
            sections.append(f"- {visit.date}: {visit.reason} (Provider: {visit.provider})")
            sections.append(f"  Notes: {visit.notes}")

        return "\n".join(sections)

    @classmethod
    def from_dict(cls, data: dict) -> "Patient":
        """Create Patient instance from dictionary."""
        demographics = Demographics(
            name=data["demographics"]["name"],
            age=data["demographics"]["age"],
            gender=data["demographics"]["gender"],
            blood_type=data["demographics"]["blood_type"],
            date_of_birth=data["demographics"]["date_of_birth"],
            contact=data["demographics"]["contact"],
        )

        conditions = [
            Condition(
                name=c["name"],
                diagnosed_date=c["diagnosed_date"],
                status=c["status"],
                severity=c["severity"],
                notes=c["notes"],
            )
            for c in data.get("conditions", [])
        ]

        medications = [
            Medication(
                name=m["name"],
                dosage=m["dosage"],
                frequency=m["frequency"],
                start_date=m["start_date"],
                purpose=m["purpose"],
            )
            for m in data.get("medications", [])
        ]

        allergies = [
            Allergy(
                allergen=a["allergen"],
                reaction=a["reaction"],
                severity=a["severity"],
            )
            for a in data.get("allergies", [])
        ]

        lab_results = [
            LabResult(
                test=l["test"],
                value=l["value"],
                date=l["date"],
                reference_range=l["reference_range"],
                status=l["status"],
            )
            for l in data.get("lab_results", [])
        ]

        visits = []
        for v in data.get("visits", []):
            vitals = None
            if "vitals" in v:
                vitals = Vitals(
                    weight=v["vitals"].get("weight"),
                    height=v["vitals"].get("height"),
                    bmi=v["vitals"].get("bmi"),
                )
            visits.append(
                Visit(
                    date=v["date"],
                    reason=v["reason"],
                    provider=v["provider"],
                    notes=v["notes"],
                    vitals=vitals,
                )
            )

        return cls(
            id=data["id"],
            demographics=demographics,
            conditions=conditions,
            medications=medications,
            allergies=allergies,
            lab_results=lab_results,
            visits=visits,
        )
