"""Patient model — one record per CNIC, shared across facilities."""
import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Gender(str, enum.Enum):
    """Patient gender."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Patient(Base):
    """A patient identified by CNIC, visible across facilities (subject to consent)."""

    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cnic: Mapped[str] = mapped_column(String(15), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, values_callable=lambda e: [m.value for m in e]), nullable=False)
    blood_group: Mapped[str | None] = mapped_column(String(5), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    consent_sharing: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_facility_id: Mapped[str] = mapped_column(String(36), ForeignKey("facilities.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
