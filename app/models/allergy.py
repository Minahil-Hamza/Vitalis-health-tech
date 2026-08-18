"""Allergy model."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Severity(str, enum.Enum):
    """Allergy severity."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class Allergy(Base):
    """A recorded patient allergy."""

    __tablename__ = "allergies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    substance: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, values_callable=lambda e: [m.value for m in e]), nullable=False
    )
    noted_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
