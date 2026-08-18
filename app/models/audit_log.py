"""Append-only audit log model. No update or delete path exists for this table anywhere."""
import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditAction(str, enum.Enum):
    """Actions recorded in the audit log."""

    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    VIEWED_SUMMARY = "viewed_summary"
    CREATED_RECORD = "created_record"
    UPDATED_PATIENT = "updated_patient"
    ADDED_MEDICATION = "added_medication"


class AuditLog(Base):
    """Append-only record of security- and clinical-relevant actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    facility_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("facilities.id"), nullable=True)
    patient_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, values_callable=lambda e: [m.value for m in e]), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
