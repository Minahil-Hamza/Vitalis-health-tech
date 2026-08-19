"""Clinical record model."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RecordType(str, enum.Enum):
    """Type of clinical record."""

    VISIT = "visit"
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    ADMISSION = "admission"
    DISCHARGE = "discharge"


class Record(Base):
    """A clinical record (visit, prescription, lab report, admission, or discharge)."""

    __tablename__ = "records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False)
    facility_id: Mapped[str] = mapped_column(String(36), ForeignKey("facilities.id"), nullable=False)
    author_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    record_type: Mapped[RecordType] = mapped_column(
        Enum(RecordType, values_callable=lambda e: [m.value for m in e]), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    # Only set (and only meaningful) for record_type == PRESCRIPTION, so the drug
    # interaction/allergy safety checks have something to check against.
    drug_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
