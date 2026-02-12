"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PatientModel(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    codename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    sessions: Mapped[List["AnalysisSessionModel"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class AnalysisSessionModel(Base):
    __tablename__ = "analysis_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    video_s3_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    results_s3_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    emotion_summary: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    clinical_indicators: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    patient: Mapped["PatientModel"] = relationship(back_populates="sessions")

    __table_args__ = (
        Index("ix_analysis_sessions_patient_id", "patient_id"),
        Index("ix_analysis_sessions_status", "status"),
        Index("ix_analysis_sessions_created_at", "created_at"),
    )
