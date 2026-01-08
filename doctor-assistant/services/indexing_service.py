"""Service for indexing patient data into the vector store."""

import json
from pathlib import Path
from typing import List

from domain.patient import Patient
from infrastructure.vector_store import VectorStore


class IndexingService:
    """
    Service for loading and indexing patient data.

    Handles reading patient records from JSON and storing them
    in ChromaDB for semantic search.
    """

    def __init__(self, vector_store: VectorStore, data_path: str):
        """
        Initialize the indexing service.

        Args:
            vector_store: The vector store to index into.
            data_path: Path to the patients JSON file.
        """
        self._vector_store = vector_store
        self._data_path = Path(data_path)

    def load_patients(self) -> List[Patient]:
        """
        Load patients from the JSON file.

        Returns:
            List of Patient objects.

        Raises:
            FileNotFoundError: If data file doesn't exist.
            json.JSONDecodeError: If file contains invalid JSON.
        """
        if not self._data_path.exists():
            raise FileNotFoundError(f"Patient data file not found: {self._data_path}")

        with open(self._data_path, "r") as f:
            data = json.load(f)

        return [Patient.from_dict(p) for p in data.get("patients", [])]

    def index_patients(self, patients: List[Patient]) -> int:
        """
        Index patient records into the vector store.

        Creates searchable documents from patient data.

        Args:
            patients: List of patients to index.

        Returns:
            Number of documents indexed.
        """
        texts = []
        metadatas = []
        ids = []

        for patient in patients:
            # Create main patient document
            doc_text = patient.to_document_text()
            texts.append(doc_text)
            metadatas.append({
                "patient_id": patient.id,
                "patient_name": patient.demographics.name,
                "document_type": "full_record",
            })
            ids.append(f"{patient.id}_full")

            # Create separate documents for conditions
            for i, condition in enumerate(patient.conditions):
                condition_text = (
                    f"Patient: {patient.demographics.name} (ID: {patient.id})\n"
                    f"Condition: {condition.name}\n"
                    f"Diagnosed: {condition.diagnosed_date}\n"
                    f"Status: {condition.status}\n"
                    f"Severity: {condition.severity}\n"
                    f"Notes: {condition.notes}"
                )
                texts.append(condition_text)
                metadatas.append({
                    "patient_id": patient.id,
                    "patient_name": patient.demographics.name,
                    "document_type": "condition",
                    "condition_name": condition.name,
                })
                ids.append(f"{patient.id}_condition_{i}")

            # Create separate documents for visits
            for i, visit in enumerate(patient.visits):
                visit_text = (
                    f"Patient: {patient.demographics.name} (ID: {patient.id})\n"
                    f"Visit Date: {visit.date}\n"
                    f"Reason: {visit.reason}\n"
                    f"Provider: {visit.provider}\n"
                    f"Notes: {visit.notes}"
                )
                if visit.vitals:
                    visit_text += (
                        f"\nVitals - Weight: {visit.vitals.weight}, "
                        f"Height: {visit.vitals.height}, BMI: {visit.vitals.bmi}"
                    )
                texts.append(visit_text)
                metadatas.append({
                    "patient_id": patient.id,
                    "patient_name": patient.demographics.name,
                    "document_type": "visit",
                    "visit_date": visit.date,
                })
                ids.append(f"{patient.id}_visit_{i}")

            # Create medication summary document
            if patient.medications:
                med_text = (
                    f"Patient: {patient.demographics.name} (ID: {patient.id})\n"
                    f"Current Medications:\n"
                )
                for med in patient.medications:
                    med_text += (
                        f"- {med.name} {med.dosage} ({med.frequency}) "
                        f"for {med.purpose}\n"
                    )
                texts.append(med_text)
                metadatas.append({
                    "patient_id": patient.id,
                    "patient_name": patient.demographics.name,
                    "document_type": "medications",
                })
                ids.append(f"{patient.id}_medications")

            # Create allergy document
            if patient.allergies:
                allergy_text = (
                    f"Patient: {patient.demographics.name} (ID: {patient.id})\n"
                    f"Allergies:\n"
                )
                for allergy in patient.allergies:
                    allergy_text += (
                        f"- {allergy.allergen}: {allergy.reaction} "
                        f"(Severity: {allergy.severity})\n"
                    )
                texts.append(allergy_text)
                metadatas.append({
                    "patient_id": patient.id,
                    "patient_name": patient.demographics.name,
                    "document_type": "allergies",
                })
                ids.append(f"{patient.id}_allergies")

            # Create lab results document
            if patient.lab_results:
                lab_text = (
                    f"Patient: {patient.demographics.name} (ID: {patient.id})\n"
                    f"Lab Results:\n"
                )
                for lab in patient.lab_results:
                    lab_text += (
                        f"- {lab.test}: {lab.value} "
                        f"(Reference: {lab.reference_range}, Status: {lab.status}) "
                        f"Date: {lab.date}\n"
                    )
                texts.append(lab_text)
                metadatas.append({
                    "patient_id": patient.id,
                    "patient_name": patient.demographics.name,
                    "document_type": "lab_results",
                })
                ids.append(f"{patient.id}_labs")

        # Index all documents
        self._vector_store.add_documents(
            texts=texts,
            metadatas=metadatas,
            ids=ids,
        )

        return len(texts)

    def reindex_all(self) -> int:
        """
        Clear and reindex all patient data.

        Returns:
            Number of documents indexed.
        """
        self._vector_store.clear_collection()
        patients = self.load_patients()
        return self.index_patients(patients)
