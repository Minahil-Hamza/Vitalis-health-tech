"""Chronic condition model."""
import uuid
from datetime import date as date_type

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Condition(Base):
    """A chronic condition recorded for a patient."""

    __tablename__ = "conditions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnosed_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
