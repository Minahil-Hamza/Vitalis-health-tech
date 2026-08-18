"""Writes audit log entries. This is the only supported way to create them: no
update or delete function exists for AuditLog anywhere in the codebase."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditLog


def log_action(
    db: Session,
    action: AuditAction,
    user_id: Optional[str] = None,
    facility_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Insert an append-only audit log row and return it."""
    entry = AuditLog(
        action=action,
        user_id=user_id,
        facility_id=facility_id,
        patient_id=patient_id,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
