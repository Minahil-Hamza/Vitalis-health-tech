"""Medication model. A medication is "current" while stopped_at is null."""
import uuid
from datetime import date as date_type

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Medication(Base):
    """A medication (current or past) recorded for a patient."""

    __tablename__ = "medications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    drug_name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dose: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[date_type] = mapped_column(Date, nullable=False)
    stopped_at: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    prescribed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    facility_id: Mapped[str] = mapped_column(String(36), ForeignKey("facilities.id"), nullable=False)
