"""Pydantic schemas for the paginated patient access-history JSON view."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.audit_log import AuditAction


class AccessHistoryEntryOut(BaseModel):
    """A single audit row: who did what, when, from which facility."""

    id: int
    action: AuditAction
    timestamp: datetime
    user_name: Optional[str] = None
    facility_name: Optional[str] = None
    override_reason: Optional[str] = None


class AccessHistoryPageOut(BaseModel):
    """One page of a patient's access history."""

    entries: list[AccessHistoryEntryOut]
    page: int
    total_pages: int
